import os
import torch
import whisper

# Load Whisper model once
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium").to(device)

def transcribe_chunks(chunk_dir):
    """
    Transcribes all WAV files in chunk_dir using Whisper medium model.
    Returns list of segments with timestamps.
    """
    if not os.path.isdir(chunk_dir):
        raise ValueError(f"Chunk directory not found: {chunk_dir}")

    chunk_files = sorted(
        os.path.join(chunk_dir, f) for f in os.listdir(chunk_dir) if f.lower().endswith(".wav")
    )

    if not chunk_files:
        raise ValueError("No WAV chunks found for transcription")

    transcriptions = []

    for i, chunk_path in enumerate(chunk_files):
        result = model.transcribe(
            chunk_path,
            language="en",
            word_timestamps=True,
            fp16=torch.cuda.is_available()
        )

        for seg in result.get("segments", []):
            transcriptions.append({
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip()
            })

    return transcriptions
