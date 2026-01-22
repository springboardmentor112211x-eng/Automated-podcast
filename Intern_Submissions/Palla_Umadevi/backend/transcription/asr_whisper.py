import os
import torch
import whisper

# ---------------------------------------------------
# Model initialization (loaded once at startup)
# ---------------------------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium").to(device)


def transcribe_chunks(chunk_dir):
    """
    Transcribes all WAV files inside `chunk_dir` sequentially
    and returns timestamped segments.

    Args:
        chunk_dir (str): Absolute path to directory containing WAV chunks

    Returns:
        List[dict]: Chunk-level transcriptions with timestamps
    """

    if not os.path.isdir(chunk_dir):
        raise ValueError(f"Chunk directory not found: {chunk_dir}")

    transcriptions = []

    # Collect absolute paths of WAV chunks (FFmpeg-safe)
    chunk_files = sorted(
        os.path.join(chunk_dir, f)
        for f in os.listdir(chunk_dir)
        if f.lower().endswith(".wav")
    )

    if not chunk_files:
        raise ValueError("No WAV chunks found for transcription")

    # Transcribe sequentially (memory-safe for long podcasts)
    for i, chunk_path in enumerate(chunk_files):
        result = model.transcribe(
            chunk_path,
            language="en",
            word_timestamps=True,
            fp16=torch.cuda.is_available()
        )

        transcriptions.append({
            "chunk_id": i,
            "file": os.path.basename(chunk_path),
            "text": result["text"].strip(),
            "segments": [
                {
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip()
                }
                for seg in result.get("segments", [])
            ]
        })

    return transcriptions
