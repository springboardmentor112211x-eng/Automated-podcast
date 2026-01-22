import librosa
import numpy as np

class AudioPreprocessor:
    def __init__(self, target_sr=16000):
        self.target_sr = target_sr

    def preprocess(self, audio, sr):
        # Resample 
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        
        # Convert to mono 
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio)
            
        # Standardize volume
        audio = librosa.util.normalize(audio)
        
        # Remove silence 
        audio, _ = librosa.effects.trim(audio, top_db=25)
        
        return audio, self.target_sr
