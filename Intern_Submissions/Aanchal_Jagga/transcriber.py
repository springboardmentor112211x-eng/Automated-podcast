import torch
import whisper

class SpeechArchitect:
    def __init__(self, model_size="base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"--- Architect Log: Using {self.device.upper()} ---")
        self.model = whisper.load_model(model_size, device=self.device)

    def transcribe_chunk(self, audio_path):
        try:
            result = self.model.transcribe(audio_path, fp16=(self.device == "cuda"))
            return result.get("text", "").strip()
        except Exception as e:
            return f"[ERROR] Transcription failed: {str(e)}"

_cache = {}

@torch.no_grad()
def get_transcriber(model_size="base"):
    if model_size not in _cache:
        _cache[model_size] = SpeechArchitect(model_size)
    return _cache[model_size]
