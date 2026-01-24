"""
Audio analysis utilities for processing podcast audio.
"""

import os
from pydub import AudioSegment


def get_audio_info(audio_path: str) -> dict:
    """
    Get basic information about an audio file.
    
    Returns:
        dict with duration, channels, sample_rate, format
    """
    audio = AudioSegment.from_file(audio_path)
    return {
        "duration_seconds": len(audio) / 1000,
        "duration_formatted": format_duration(len(audio) / 1000),
        "channels": audio.channels,
        "sample_rate": audio.frame_rate,
        "format": os.path.splitext(audio_path)[1].lower(),
    }


def format_duration(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def convert_to_wav(input_path: str, output_path: str = None) -> str:
    """
    Convert audio file to WAV format.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output WAV (optional)
    
    Returns:
        Path to the WAV file
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.wav"
    
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path


def extract_clip(audio_path: str, start_sec: float, end_sec: float, output_path: str) -> str:
    """
    Extract a clip from an audio file.
    
    Args:
        audio_path: Path to source audio
        start_sec: Start time in seconds
        end_sec: End time in seconds
        output_path: Path to save the clip
    
    Returns:
        Path to the extracted clip
    """
    audio = AudioSegment.from_file(audio_path)
    clip = audio[start_sec * 1000 : end_sec * 1000]
    
    # Determine format from output extension
    ext = os.path.splitext(output_path)[1].lower().replace(".", "")
    if ext == "mp3":
        clip.export(output_path, format="mp3")
    else:
        clip.export(output_path, format="wav")
    
    return output_path


def normalize_audio(audio_path: str, output_path: str = None, target_dbfs: float = -20.0) -> str:
    """
    Normalize audio volume.
    
    Args:
        audio_path: Path to audio file
        output_path: Output path (optional, overwrites if not provided)
        target_dbfs: Target volume in dBFS (default -20)
    
    Returns:
        Path to normalized audio
    """
    if output_path is None:
        output_path = audio_path
    
    audio = AudioSegment.from_file(audio_path)
    change_in_dbfs = target_dbfs - audio.dBFS
    normalized = audio.apply_gain(change_in_dbfs)
    
    ext = os.path.splitext(output_path)[1].lower().replace(".", "")
    normalized.export(output_path, format=ext if ext else "wav")
    
    return output_path


def split_audio_by_segments(audio_path: str, segments: list, output_dir: str) -> list:
    """
    Split audio file into multiple files based on transcript segments.
    
    Args:
        audio_path: Path to source audio
        segments: List of dicts with 'start' and 'end' times
        output_dir: Directory to save clips
    
    Returns:
        List of paths to created clips
    """
    os.makedirs(output_dir, exist_ok=True)
    audio = AudioSegment.from_file(audio_path)
    
    output_paths = []
    for i, seg in enumerate(segments):
        start_ms = seg["start"] * 1000
        end_ms = seg["end"] * 1000
        clip = audio[start_ms:end_ms]
        
        output_path = os.path.join(output_dir, f"segment_{i+1:03d}.wav")
        clip.export(output_path, format="wav")
        output_paths.append(output_path)
    
    return output_paths


def detect_silence(audio_path: str, min_silence_ms: int = 1000, silence_thresh_db: int = -40) -> list:
    """
    Detect silent portions in audio.
    
    Args:
        audio_path: Path to audio file
        min_silence_ms: Minimum silence duration in milliseconds
        silence_thresh_db: Silence threshold in dB
    
    Returns:
        List of tuples (start_ms, end_ms) for each silent portion
    """
    from pydub.silence import detect_silence as pydub_detect_silence
    
    audio = AudioSegment.from_file(audio_path)
    silences = pydub_detect_silence(audio, min_silence_len=min_silence_ms, silence_thresh=silence_thresh_db)
    return silences


def remove_silence(audio_path: str, output_path: str, min_silence_ms: int = 1000, silence_thresh_db: int = -40) -> str:
    """
    Remove silent portions from audio.
    
    Args:
        audio_path: Path to audio file
        output_path: Output path for processed audio
        min_silence_ms: Minimum silence duration to remove
        silence_thresh_db: Silence threshold in dB
    
    Returns:
        Path to output file
    """
    from pydub.silence import split_on_silence
    
    audio = AudioSegment.from_file(audio_path)
    chunks = split_on_silence(audio, min_silence_len=min_silence_ms, silence_thresh=silence_thresh_db, keep_silence=200)
    
    if not chunks:
        # No silence found, return original
        audio.export(output_path, format="wav")
        return output_path
    
    combined = chunks[0]
    for chunk in chunks[1:]:
        combined += chunk
    
    combined.export(output_path, format="wav")
    return output_path


def get_volume_over_time(audio_path: str, chunk_ms: int = 1000) -> list:
    """
    Get volume levels over time.
    
    Args:
        audio_path: Path to audio file
        chunk_ms: Chunk size in milliseconds
    
    Returns:
        List of dicts with time and volume (dBFS)
    """
    audio = AudioSegment.from_file(audio_path)
    volumes = []
    
    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i:i + chunk_ms]
        volumes.append({
            "time_sec": i / 1000,
            "volume_dbfs": chunk.dBFS if len(chunk) > 0 else -100
        })
    
    return volumes


def merge_audio_files(audio_paths: list, output_path: str, crossfade_ms: int = 0) -> str:
    """
    Merge multiple audio files into one.
    
    Args:
        audio_paths: List of paths to audio files
        output_path: Output path for merged audio
        crossfade_ms: Crossfade duration between clips (0 for no crossfade)
    
    Returns:
        Path to merged audio file
    """
    if not audio_paths:
        raise ValueError("No audio files provided")
    
    combined = AudioSegment.from_file(audio_paths[0])
    
    for path in audio_paths[1:]:
        next_audio = AudioSegment.from_file(path)
        if crossfade_ms > 0:
            combined = combined.append(next_audio, crossfade=crossfade_ms)
        else:
            combined += next_audio
    
    ext = os.path.splitext(output_path)[1].lower().replace(".", "")
    combined.export(output_path, format=ext if ext else "wav")
    return output_path
