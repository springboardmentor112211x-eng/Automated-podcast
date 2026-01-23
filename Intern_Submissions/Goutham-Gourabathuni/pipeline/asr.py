import whisper

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcribe(chunks):
    model = _get_model()
    results = []
    offset = 0.0

    for chunk in chunks:
        out = model.transcribe(chunk, fp16=False)
        for s in out.get("segments", []):
            results.append({
                "start": s["start"] + offset,
                "end": s["end"] + offset,
                "text": s["text"].strip()
            })
        if out.get("segments"):
            offset += out["segments"][-1]["end"]

    return results
