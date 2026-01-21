import numpy as np

def chunk_audio(
    audio,
    sr,
    chunk_sec=30,
    overlap_sec=5
):
    """
    Overlapping audio chunking for ASR robustness.

    Example:
    30s chunks with 5s overlap.
    """

    chunk_size = int(chunk_sec * sr)
    overlap_size = int(overlap_sec * sr)

    chunks = []
    start = 0

    while start < len(audio):
        end = start + chunk_size
        chunk = audio[start:end]

        if len(chunk) > 0:
            chunks.append(chunk.astype(np.float32))

        start += chunk_size - overlap_size

    return chunks