"""
Segmentation module for splitting transcripts by time, speaker, or topic.
"""


def segment_by_time(segments: list, chunk_duration: float = 60.0) -> list:
    """
    Group transcript segments into chunks by time duration.
    
    Args:
        segments: List of Whisper segments with 'start', 'end', 'text'
        chunk_duration: Duration of each chunk in seconds (default 60s)
    
    Returns:
        List of chunks with combined text and time ranges
    """
    if not segments:
        return []
    
    chunks = []
    current_chunk = {"start": segments[0]["start"], "texts": [], "end": 0}
    
    for seg in segments:
        if seg["start"] - current_chunk["start"] >= chunk_duration:
            # Save current chunk and start new one
            current_chunk["end"] = seg["start"]
            current_chunk["text"] = " ".join(current_chunk["texts"])
            del current_chunk["texts"]
            chunks.append(current_chunk)
            current_chunk = {"start": seg["start"], "texts": [], "end": 0}
        
        current_chunk["texts"].append(seg["text"].strip())
    
    # Don't forget the last chunk
    if current_chunk["texts"]:
        current_chunk["end"] = segments[-1]["end"]
        current_chunk["text"] = " ".join(current_chunk["texts"])
        del current_chunk["texts"]
        chunks.append(current_chunk)
    
    return chunks


def segment_by_silence(segments: list, silence_threshold: float = 2.0) -> list:
    """
    Split transcript at long pauses/silences.
    
    Args:
        segments: List of Whisper segments
        silence_threshold: Minimum silence duration to split (seconds)
    
    Returns:
        List of segments split at silences
    """
    if not segments:
        return []
    
    result = []
    current_segment = {
        "start": segments[0]["start"],
        "texts": [segments[0]["text"].strip()],
        "end": segments[0]["end"]
    }
    
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i-1]["end"]
        
        if gap >= silence_threshold:
            # Silence detected - save current and start new
            current_segment["text"] = " ".join(current_segment["texts"])
            del current_segment["texts"]
            result.append(current_segment)
            current_segment = {
                "start": segments[i]["start"],
                "texts": [],
                "end": 0
            }
        
        current_segment["texts"].append(segments[i]["text"].strip())
        current_segment["end"] = segments[i]["end"]
    
    # Save last segment
    if current_segment["texts"]:
        current_segment["text"] = " ".join(current_segment["texts"])
        del current_segment["texts"]
        result.append(current_segment)
    
    return result


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def create_transcript_with_timestamps(segments: list) -> str:
    """
    Create formatted transcript with timestamps.
    
    Args:
        segments: List of Whisper segments
    
    Returns:
        Formatted string with timestamps
    """
    lines = []
    for seg in segments:
        timestamp = format_timestamp(seg["start"])
        lines.append(f"[{timestamp}] {seg['text'].strip()}")
    return "\n".join(lines)
