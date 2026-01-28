from backend.services.preprocess import run_preprocessing
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import re
from pathlib import Path
import csv
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preload ASR model at startup to avoid long first-request delays
from backend.services import asr

@app.on_event("startup")
def on_startup():
    try:
        asr._load_model()
        print("ASR model preloaded")
    except Exception as e:
        print("ASR preload failed:", e)

# Configuration
RAW_AUDIO_DIR = Path("data/raw")
RAW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_MB = int(os.getenv("AUDIO_MAX_FILE_MB", "200"))
MAX_FILE_SIZE = MAX_FILE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
}


def secure_filename(filename: str) -> str:
    """Sanitize a filename by stripping path-separators and unsafe chars."""
    name = Path(filename).name  # strip any path components
    name = name.replace(" ", "_")
    # Allow only letters, numbers, dot, underscore and dash
    name = re.sub(r"[^A-Za-z0-9_.-]", "", name)
    if not name:
        name = "file"
    return name


@app.get("/")
def root():
    # Redirect to the upload form so visiting / shows the upload page immediately
    return RedirectResponse(url="/upload")


@app.get("/upload", response_class=HTMLResponse)
def upload_form():
    """Simple HTML form to test uploads from a browser."""
    return """
    <!doctype html>
    <html>
      <body>
        <h1>Upload audio file</h1>
        <form action="/upload-audio/" enctype="multipart/form-data" method="post">
          <input name="file" type="file" accept="audio/*">
          <input type="submit" value="Upload">
        </form>
      </body>
    </html>
    """


from fastapi import BackgroundTasks

@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...)
):
    # Basic type check
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {content_type}",
        )

    safe_name = secure_filename(file.filename or "upload")
    unique_id = uuid.uuid4().hex
    unique_name = f"{unique_id}_{safe_name}"
    file_path = RAW_AUDIO_DIR / unique_name

    # Stream write and enforce size limit
    try:
        total = 0
        with open(file_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_SIZE:
                    out_file.close()
                    file.file.close()
                    try:
                        file_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File is too large. Limit is {MAX_FILE_MB} MB.",
                    )
                out_file.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    finally:
        await file.close()

    return {"audio_id": unique_id}


@app.post("/process/{audio_id}")
async def process_audio(audio_id: str, background_tasks: BackgroundTasks):
    # Find the file
    files = list(RAW_AUDIO_DIR.glob(f"{audio_id}_*"))
    if not files:
        raise HTTPException(status_code=404, detail="Audio not found")
    file_path = files[0]
    # Run preprocessing in background
    background_tasks.add_task(run_preprocessing, str(file_path))
    return {"status": "processing"}


@app.get("/result/{audio_id}")
def get_result(audio_id: str):
    # Find the processed folder
    processed_dirs = list(Path("data/processed").glob(f"{audio_id}_*"))
    if not processed_dirs:
        return {"status": "processing"}
    processed_dir = processed_dirs[0]
    # Read the csvs
    topics_csv = processed_dir / "topics.csv"
    summaries_csv = processed_dir / "topic_summaries.csv"
    labels_csv = processed_dir / "topic_labels.csv"
    global_summary_txt = processed_dir / "global_summary.txt"
    if not topics_csv.exists() or not summaries_csv.exists() or not labels_csv.exists():
        return {"status": "processing"}
    with open(topics_csv, 'r') as f:
        topics = list(csv.DictReader(f))
    with open(summaries_csv, 'r') as f:
        summaries = list(csv.DictReader(f))
    with open(labels_csv, 'r') as f:
        labels = list(csv.DictReader(f))
    global_summary = ""
    if global_summary_txt.exists():
        try:
            global_summary = global_summary_txt.read_text(encoding="utf-8")
        except Exception:
            global_summary = ""
    return {"topics": topics, "summaries": summaries, "labels": labels, "global_summary": global_summary}
