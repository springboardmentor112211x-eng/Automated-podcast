
import numpy as np
import torch
from transformers import pipeline
from typing import List, Dict, Any
import torchaudio


class WhisperWrapper:
    def __init__(self, model_name: str, device: str, sr: int = 16000):
        self.device = device
        self.sr = sr
        self.device_id = 0 if device == "cuda" else -1
        self.pipeline = self._load_pipeline(model_name)

    def _load_pipeline(self, model_name: str):
        print(f"Loading Whisper Model: {model_name}")
        try:
            return pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=self.device_id,
                chunk_length_s=30,
            )
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            return None

    def transcribe_translate(self, audio_data: np.ndarray, progress_callback=None) -> List[Dict]:
        if self.pipeline is None:
            raise RuntimeError("ASR pipeline not loaded.")

        print("Running Transcription/Translation...")
        
        generate_kwargs = {"task": "translate", "return_timestamps": True}
        
        # Calculate chunks
        chunk_duration = 30 # seconds
        chunk_samples = chunk_duration * self.sr
        total_samples = len(audio_data)
        total_chunks = int(np.ceil(total_samples / chunk_samples))
        
        all_chunks = []
        
        # Process chunks
        print(f"Audio Data Shape: {audio_data.shape}")
        for i in range(total_chunks):
            start_sample = i * chunk_samples
            end_sample = min((i + 1) * chunk_samples, total_samples)
            
            # Extract chunk
            audio_chunk = audio_data[start_sample:end_sample]
            
            # Skip empty chunks
            if len(audio_chunk) == 0:
                print(f"Chunk {i}: Empty audio data.")
                continue
                
            # Run inference on chunk
            input_data = {"array": audio_chunk, "sampling_rate": self.sr}
            
            try:
                print(f"Processing chunk {i+1}/{total_chunks}...")
                result = self.pipeline(input_data, generate_kwargs=generate_kwargs)
                print(f"Chunk {i+1} Raw Result: {result}")
                chunk_segments = result.get("chunks", [])
                
                # If no chunks returned but text exists (short audio), wrap it
                if not chunk_segments and result.get("text"):
                    chunk_segments = [{"timestamp": (0.0, len(audio_chunk)/self.sr), "text": result["text"]}]

                # Adjust timestamps and add to list
                time_offset = i * chunk_duration
                for seg in chunk_segments:
                    start = seg["timestamp"][0]
                    end = seg["timestamp"][1]
                    
                    if start is None: start = 0.0
                    if end is None: end = 0.0 
                    
                    seg["timestamp"] = (start + time_offset, end + time_offset)
                    all_chunks.append(seg)
                    
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
            
            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_chunks)

        return all_chunks
