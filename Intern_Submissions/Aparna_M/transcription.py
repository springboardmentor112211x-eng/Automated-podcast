import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import re

class Transcriber:
    def __init__(self, model_name="openai/whisper-small", device=None):
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def chunk_audio(self, audio, sr, chunk_sec=30, overlap_sec=5):
        chunk_size = chunk_sec * sr
        overlap_size = overlap_sec * sr
        chunks, start = [], 0
        while start < len(audio):
            end = start + chunk_size
            chunks.append(audio[start:end])
            start = end - overlap_size if end < len(audio) else len(audio)
        return chunks

    

    def transcribe(self, chunk, sr, offset=0): 
        inputs = self.processor(chunk, sampling_rate=sr, return_tensors="pt").input_features.to(self.device)
        
        with torch.no_grad():
            
            predicted_ids = self.model.generate(inputs, return_timestamps=True, condition_on_prev_tokens=False, max_new_tokens=440)
        
        raw_decoded = self.processor.batch_decode(predicted_ids, decode_with_timestamps=True)[0]
        text_only = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        sentence_data = []
        
        matches = re.findall(r"<\|(\d+\.\d+)\|>(.*?)<\|", raw_decoded)
        
        for ts, text in matches:
            if len(text.strip().split()) > 2:
            
                sentence_data.append({
                    "time": float(ts) + offset, 
                    "text": text.strip()
                })
        return text_only, sentence_data
