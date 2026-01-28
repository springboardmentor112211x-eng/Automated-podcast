_model = None


def _load_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model("base")
    return _model


def transcribe_audio(audio_path: str) -> str:
    try:
        model = _load_model()
        result = model.transcribe(audio_path)
        return result["text"].strip()
    except Exception as e:
        import traceback
        print("ASR error:", e)
        print(traceback.format_exc())

        # Detect missing ffmpeg / Windows 'file not found' error and try a Python-only fallback
        is_ffmpeg_missing = (
            isinstance(e, FileNotFoundError)
            or getattr(e, "errno", None) == 2
            or "ffmpeg" in str(e).lower()
        )

        if is_ffmpeg_missing:
            try:
                print(f"ASR fallback activated for: {audio_path} — ffmpeg not found; loading with librosa...")
                import librosa

                y, sr = librosa.load(audio_path, sr=16000, mono=True)
                model = _load_model()
                result = model.transcribe(y)
                text = result["text"].strip()
                print(f"ASR fallback succeeded for: {audio_path}")
                return text
            except Exception as e2:
                print(f"ASR fallback failed for: {audio_path} —", e2)
                print(traceback.format_exc())

        return ""
