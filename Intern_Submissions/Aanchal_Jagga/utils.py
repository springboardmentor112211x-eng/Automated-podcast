from pydub import AudioSegment
import os

def chunk_audio(file_path, chunk_length_ms=30000, overlap_ms=2000):
    """
    Sliding window chunking:
    - chunk_length_ms: size of each chunk (default 30 sec)
    - overlap_ms: overlap to avoid missing words at boundaries
    """
    audio = AudioSegment.from_file(file_path)
    duration = len(audio)
    chunks = []

    start = 0
    while start < duration:
        end = min(start + chunk_length_ms, duration)
        chunk = audio[start:end]

        chunk_filename = f"temp_chunk_{start}.wav"
        chunk.export(chunk_filename, format="wav")
        chunks.append(chunk_filename)

        start += (chunk_length_ms - overlap_ms)

    return chunks

def cleanup_chunks(chunks):
    for chunk in chunks:
        if os.path.exists(chunk):
            os.remove(chunk)
