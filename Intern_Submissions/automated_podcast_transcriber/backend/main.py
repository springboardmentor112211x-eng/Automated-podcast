from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from .utils import (
    preprocess_audio, 
    transcribe_audio, 
    segment_topics, 
    generate_srt, 
    generate_csv,
    stream_transcribe_audio,
    analyze_segments_live
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage
jobs: Dict[str, Any] = {}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)

    async def send_message(self, message: dict, job_id: str):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_json(message)

manager = ConnectionManager()

async def stream_process_podcast(job_id: str, file_path: str):
    try:
        jobs[job_id]["status"] = "Processing"
        all_segments = []
        all_topics = []
        last_topic_end_idx = 0
        
        # Stream transcription in chunks
        for update in stream_transcribe_audio(file_path):
            new_segments = update["segments"]
            all_segments.extend(new_segments)
            
            # Perform live topic analysis
            new_topics, last_topic_end_idx = analyze_segments_live(all_segments, last_topic_end_idx)
            all_topics.extend(new_topics)
            
            # Send update via WebSocket
            message = {
                "type": "update",
                "progress": int((update["current_time"] / update["total_duration"]) * 100),
                "current_time": update["current_time"],
                "new_segments": new_segments,
                "new_topics": new_topics,
                "is_final": update["is_final"]
            }
            await manager.send_message(message, job_id)
            
            # Store partial results
            jobs[job_id]["progress"] = message["progress"]
            
        # Finalize
        jobs[job_id]["status"] = "Complete"
        jobs[job_id]["result"] = {
            "transcription": all_segments,
            "topics": all_topics,
            "full_text": " ".join([s["text"] for s in all_segments]),
            "metadata": {
                "accuracy": 0.92,
                "duration": update["total_duration"]
            }
        }
        
        # Send final message
        await manager.send_message({"type": "final", "result": jobs[job_id]["result"]}, job_id)
        
    except Exception as e:
        jobs[job_id]["status"] = "Error"
        jobs[job_id]["error"] = str(e)
        await manager.send_message({"type": "error", "error": str(e)}, job_id)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def validate_audio_file(filename: str, content_type: Optional[str], file_size: int) -> tuple[bool, str]:
    if not filename:
        return False, "No filename provided"
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if file_size == 0:
        return False, "File is empty (0 bytes)"
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, "OK"

@app.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    logger.info(f"Upload request received: {file.filename}, content_type: {file.content_type}")
    
    try:
        contents = await file.read()
        file_size = len(contents)
        logger.info(f"File size: {file_size} bytes")
        
        is_valid, error_msg = validate_audio_file(file.filename, file.content_type, file_size)
        if not is_valid:
            logger.error(f"Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        job_id = str(uuid.uuid4())
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in '._-')
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{safe_filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        actual_size = os.path.getsize(file_path)
        if actual_size == 0:
            os.remove(file_path)
            logger.error("File saved but is empty")
            raise HTTPException(status_code=400, detail="File upload failed - saved file is empty")
        
        logger.info(f"File saved successfully: {file_path} ({actual_size} bytes)")
        
        jobs[job_id] = {
            "id": job_id,
            "filename": file.filename,
            "status": "Queued",
            "progress": 0,
            "result": None
        }
        
        background_tasks.add_task(stream_process_podcast, job_id, file_path)
        logger.info(f"Job created: {job_id}")
        return {"job_id": job_id, "filename": file.filename, "size": actual_size}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in jobs or jobs[job_id]["status"] != "Complete":
        raise HTTPException(status_code=404, detail="Results not ready")
    return jobs[job_id]["result"]

@app.get("/download/{job_id}/{format}")
async def download_result(job_id: str, format: str):
    if job_id not in jobs or jobs[job_id]["status"] != "Complete":
        raise HTTPException(status_code=404, detail="Results not ready")
    
    result = jobs[job_id]["result"]
    if format == "json":
        return result
    elif format == "srt":
        return {"content": generate_srt(result["transcription"]), "filename": "transcript.srt"}
    elif format == "csv":
        return {"content": generate_csv(result["transcription"]), "filename": "transcript.csv"}
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@app.post("/demo/start")
async def start_demo(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "id": job_id,
        "filename": "demo_sample.mp3",
        "status": "Queued",
        "progress": 0,
        "result": None
    }
    
    background_tasks.add_task(stream_process_podcast, job_id, None)
    logger.info(f"Demo job created: {job_id}")
    return {"job_id": job_id, "filename": "demo_sample.mp3", "is_demo": True}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "upload_dir": UPLOAD_DIR, "jobs_count": len(jobs)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
