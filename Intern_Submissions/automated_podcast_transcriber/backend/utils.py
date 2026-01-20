import os
import uuid
import asyncio
import random
from typing import List, Dict, Any

# Mocking the heavy models to save space and avoid installation issues
TOPIC_LABELS = ["Politics", "Technology", "Sports", "Weather", "Business", "Entertainment", "Health"]

def preprocess_audio(file_path: str, target_sr: int = 16000):
    # Mocked: returns dummy data
    return [0.0] * 1000, target_sr

def transcribe_audio(file_path: str):
    # Mocked: returns dummy transcription
    return {
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "Welcome to the podcast."},
            {"start": 5.0, "end": 10.0, "text": "Today we are talking about technology."}
        ]
    }

def stream_transcribe_audio(file_path: str, chunk_duration: int = 30):
    import time
    total_duration = 120  # 2 minutes mock
    
    sentences = [
        "Welcome to the Podcast Topic Analyzer demo.",
        "This is a real-time streaming transcription powered by simulated AI.",
        "We are currently analyzing the audio for semantic shifts.",
        "As the speaker continues, the topic segmentation engine identifies boundaries.",
        "In this segment, the discussion is shifting towards technology and its impact.",
        "Artificial Intelligence is revolutionizing how we process large datasets.",
        "Next, we might see a shift towards business and market trends.",
        "Companies are investing heavily in LLMs and generative models.",
        "This conclude our short demonstration of real-time processing.",
        "Thank you for watching the live transcription feed."
    ]
    
    for i, start_time in enumerate(range(0, total_duration, chunk_duration)):
        time.sleep(1)  # Simulate processing time
        end_time = min(start_time + chunk_duration, total_duration)
        
        chunk_segments = []
        num_sentences = 2
        for j in range(num_sentences):
            idx = (i * num_sentences + j) % len(sentences)
            seg_start = start_time + (j * (chunk_duration / num_sentences))
            seg_end = seg_start + (chunk_duration / num_sentences)
            chunk_segments.append({
                "start": seg_start,
                "end": seg_end,
                "text": sentences[idx]
            })
            
        yield {
            "segments": chunk_segments,
            "current_time": end_time,
            "total_duration": total_duration,
            "is_final": end_time >= total_duration
        }

def analyze_segments_live(all_segments: List[Dict[str, Any]], last_topic_end_idx: int):
    # Mocked: returns a new topic every few segments
    if len(all_segments) - last_topic_end_idx < 4:
        return [], last_topic_end_idx
        
    new_segments = all_segments[last_topic_end_idx:]
    category = random.choice(TOPIC_LABELS)
    
    new_topic = {
        "id": str(uuid.uuid4())[:8],
        "name": f"Topic: {category}",
        "startTime": new_segments[0]['start'],
        "endTime": new_segments[-1]['end'],
        "text": " ".join([s['text'] for s in new_segments[:2]]),
        "category": category,
        "confidence": random.uniform(0.85, 0.98)
    }
    
    return [new_topic], len(all_segments)

def segment_topics(transcription_result: Dict[str, Any]):
    # Mocked
    return [
        {
            "id": 1,
            "name": "Introduction",
            "startTime": 0.0,
            "endTime": 30.0,
            "text": "Welcome and overview of today's topics.",
            "category": "General",
            "confidence": 0.95
        }
    ]

def format_timestamp(seconds: float):
    td = float(seconds)
    hours = int(td // 3600)
    minutes = int((td % 3600) // 60)
    secs = int(td % 60)
    millis = int((td % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def generate_srt(segments):
    srt_content = ""
    for i, s in enumerate(segments):
        start = format_timestamp(s['start'])
        end = format_timestamp(s['end'])
        srt_content += f"{i+1}\n{start} --> {end}\n{s['text'].strip()}\n\n"
    return srt_content

def generate_csv(segments):
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Start", "End", "Text"])
    for s in segments:
        writer.writerow([s['start'], s['end'], s['text'].strip()])
    return output.getvalue()
