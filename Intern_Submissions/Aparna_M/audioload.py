import librosa

class AudioLoader:
    def __init__(self, target_sr=16000):
        self.target_sr = target_sr

    def load(self, file_path):
        audio, sr = librosa.load(file_path, sr=None)
        return audio, sr
