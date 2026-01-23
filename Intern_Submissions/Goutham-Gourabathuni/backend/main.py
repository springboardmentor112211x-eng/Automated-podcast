from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import shutil
import os
import uuid

from pipeline.workflow_main import run_pipeline
from pipeline.pdf_exporter import generate_pdf
from pipeline.gemini_qa import answer_question
# from pipeline.openai_qa import answer_question  # switch later if needed

# -----------------------------
# App setup
# -----------------------------

app = FastAPI(title="PodC Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "media/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Global in-memory state
# -----------------------------

LAST_TRANSCRIPT_TEXT = ""
run_pipeline_last_result = None

# -----------------------------
# Health check and root
# -----------------------------

@app.get("/")
def root():
    return {"status": "Backend is working",
            "message": "I am watching youuuuu..."}

@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# Process podcast
# -----------------------------

@app.post("/process")
async def process_podcast(file: UploadFile = File(...)):
    global LAST_TRANSCRIPT_TEXT, run_pipeline_last_result

    try:
        # 1️⃣ Save uploaded file
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2️⃣ Run pipeline ONCE
        result = run_pipeline(file_path)

        # 3️⃣ Store global state for Q&A + PDF
        transcript = result.get("transcript", [])
        LAST_TRANSCRIPT_TEXT = " ".join(
            seg.get("text", "") for seg in transcript
        )
        run_pipeline_last_result = result

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Q&A endpoint (Gemini)
# -----------------------------

@app.get("/ask")
def ask_question(question: str):
    if not LAST_TRANSCRIPT_TEXT:
        return {"answer": "No podcast has been processed yet."}

    try:
        answer = answer_question(
            question=question,
            context=LAST_TRANSCRIPT_TEXT
        )
        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Download PDF
# -----------------------------

@app.post("/download-pdf")
def download_pdf():
    try:
        if not run_pipeline_last_result:
            raise HTTPException(
                status_code=400,
                detail="No podcast processed yet"
            )

        pdf_path = generate_pdf(
            topics=run_pipeline_last_result["topics"],
            episode_summary=run_pipeline_last_result.get("episode_summary")
        )

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="podc_summary.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
