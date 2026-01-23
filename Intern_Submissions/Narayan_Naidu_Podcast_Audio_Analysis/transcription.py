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
            torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            return pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=self.device_id,
                chunk_length_s=30,
                torch_dtype=torch_dtype, # Critical for speed/memory on GPU
            )
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            return None

    def transcribe_translate(self, audio_data: np.ndarray, progress_callback=None) -> List[Dict]:
        """
        Transcribe audio in large chunks to balance context, memory, and UX.
        """
        import torch
        from memory_utils import clear_gpu_memory
        
        if self.pipeline is None:
            raise RuntimeError("ASR pipeline not loaded.")


        clear_gpu_memory()
        
        generate_kwargs = {"task": "translate", "return_timestamps": True}
        
        CHUNK_DURATION = 30 # seconds
        chunk_samples = CHUNK_DURATION * self.sr
        total_samples = len(audio_data)
        total_chunks = int(np.ceil(total_samples / chunk_samples))
        
        all_segments = []
        
        for i in range(total_chunks):
            start_sample = i * chunk_samples
            end_sample = min((i + 1) * chunk_samples, total_samples)
            
            chunk = audio_data[start_sample:end_sample]
            if len(chunk) == 0: continue
            
            try:
                # Clear memory periodically
                if i % 5 == 0: clear_gpu_memory()
                
                with torch.no_grad():
                    # Batch size 4 for speed within the chunk
                    result = self.pipeline(
                        {"array": chunk, "sampling_rate": self.sr},
                        generate_kwargs=generate_kwargs,
                        batch_size=4, 
                        return_timestamps=True
                    )
                
                # Parse and offset timestamps
                time_offset = i * CHUNK_DURATION
                chunk_segs = self._parse_pipeline_result(result, chunk)
                
                for seg in chunk_segs:
                    seg["start"] += time_offset
                    seg["end"] += time_offset
                    all_segments.append(seg)
                    
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                # Try to limp along if one chunk fails
                
            # Update UI
            if progress_callback:
                progress_callback(i + 1, total_chunks)
        
        return sorted(all_segments, key=lambda x: x["start"])

    def _parse_pipeline_result(self, result, audio_data):
        """Helper to parse raw pipeline output."""
        all_segments = []
        chunk_segments = result.get("chunks", [])
        
        if not chunk_segments and result.get("text"):
            chunk_segments = [{"timestamp": (0.0, len(audio_data)/self.sr), "text": result["text"]}]

        for seg in chunk_segments:
            start = seg.get("timestamp", [0.0, 0.0])[0]
            end = seg.get("timestamp", [0.0, 0.0])[1]
            text = seg.get("text", "").strip()
            
            # Sanitize timestamps
            if start is None: start = 0.0
            if end is None: end = len(audio_data)/self.sr
            
            if text:
                all_segments.append({"start": start, "end": end, "text": text})
        
        return sorted(all_segments, key=lambda x: x["start"])



