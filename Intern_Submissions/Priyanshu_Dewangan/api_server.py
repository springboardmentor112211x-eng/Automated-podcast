"""
API Server for Background Podcast Processing
FastAPI-based server for async audio processing
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import json
from audio_processor import AudioProcessor
from rag_system import RAGSystem
import asyncio
from datetime import datetime

app = FastAPI(
    title="Podcast Insights API",
    description="API for podcast transcription, summarization, and Q&A",
    version="1.0.0"
)

# Global state
processing_jobs = {}
rag_systems = {}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/upload-podcast")
async def upload_podcast(file: UploadFile = File(...)):
    """
    Upload and process podcast
    Returns: job_id for tracking
    """
    try:
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            temp_path = tmp_file.name
        
        # Generate job ID
        job_id = f"job_{datetime.now().timestamp()}"
        
        # Create processing task
        async def process_task():
            try:
                processor = AudioProcessor(output_dir=f"./outputs/{job_id}")
                
                # Process audio
                transcript_data = processor.process_audio(temp_path)
                summaries_data = processor.generate_summaries(transcript_data)
                
                # Initialize RAG
                rag = RAGSystem(db_path=f"./dbs/{job_id}")
                rag.index_documents(summaries_data)
                
                # Store results
                processing_jobs[job_id] = {
                    "status": "completed",
                    "transcript": transcript_data,
                    "summaries": summaries_data,
                    "timestamp": datetime.now().isoformat()
                }
                rag_systems[job_id] = rag
                
            except Exception as e:
                processing_jobs[job_id] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # Start async task
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
        asyncio.create_task(process_task())
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Your podcast is being processed"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "timestamp": job.get("timestamp")
    }


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get processing results"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="Processing not completed")
    
    return {
        "job_id": job_id,
        "transcript": job.get("transcript"),
        "summaries": job.get("summaries")
    }


@app.post("/api/ask/{job_id}")
async def ask_question(job_id: str, query: dict):
    """Ask a question about the podcast"""
    if job_id not in rag_systems:
        raise HTTPException(status_code=404, detail="Job not found")
    
    question = query.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question required")
    
    rag = rag_systems[job_id]
    result = rag.answer_question(question)
    
    return result


@app.get("/api/chapters/{job_id}")
async def get_chapters(job_id: str):
    """Get all chapters for a job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="Processing not completed")
    
    summaries = job.get("summaries", [])
    
    return {
        "job_id": job_id,
        "chapters": [
            {
                "id": ch["topic_id"],
                "title": ch["title"],
                "summary": ch["final_summary"],
                "start_time": ch.get("start_time", "N/A")
            }
            for ch in summaries
        ]
    }


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    os.makedirs("./outputs", exist_ok=True)
    os.makedirs("./dbs", exist_ok=True)
    print("API Server Ready")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
