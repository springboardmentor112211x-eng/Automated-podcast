import whisper


def transcribe_audio(audio_path: str, model_size: str = "base", translate: bool = False) -> dict:
    """
    Transcribe audio file using OpenAI Whisper.
    
    Args:
        audio_path: Path to the audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        translate: If True, translate to English
    
    Returns:
        dict with 'text' and 'segments' keys
    """
    model = whisper.load_model(model_size)
    task = "translate" if translate else "transcribe"
    result = model.transcribe(audio_path, task=task)
    return result


def transcribe_with_timestamps(audio_path: str, model_size: str = "base") -> list:
    """
    Transcribe and return segments with timestamps.
    
    Returns:
        List of segments with start, end, and text
    """
    result = transcribe_audio(audio_path, model_size)
    return result.get("segments", [])
