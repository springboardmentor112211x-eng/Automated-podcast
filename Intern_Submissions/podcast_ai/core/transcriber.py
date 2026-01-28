_model = None

def get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model("base")
    return _model

def transcribe_audio(file_path):
    model = get_model()
    result = model.transcribe(file_path)
    return result["text"]
