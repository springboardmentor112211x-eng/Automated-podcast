"""Test script for transcription + segmentation"""

from src.transcription.transcriber import transcribe_audio
from src.segmentation.segmenter import (
    segment_by_time,
    segment_by_silence,
    create_transcript_with_timestamps
)

# Path to your audio file
AUDIO_PATH = r"C:\Users\navpr\OneDrive\Desktop\INFOSYS INTERNSHIP\AUDIO.mpeg"

print("Transcribing audio... (this may take a few minutes)")
result = transcribe_audio(AUDIO_PATH, model_size="base")

segments = result.get("segments", [])
print(f"\nFound {len(segments)} segments\n")

# Show formatted transcript with timestamps
print("=" * 50)
print("TRANSCRIPT WITH TIMESTAMPS:")
print("=" * 50)
formatted = create_transcript_with_timestamps(segments)
print(formatted)

# Show time-based chunks (30 second chunks)
print("\n" + "=" * 50)
print("CHUNKED BY TIME (30 seconds each):")
print("=" * 50)
chunks = segment_by_time(segments, chunk_duration=30)
for i, chunk in enumerate(chunks, 1):
    print(f"\n--- Chunk {i} ({chunk['start']:.1f}s - {chunk['end']:.1f}s) ---")
    print(chunk["text"])
