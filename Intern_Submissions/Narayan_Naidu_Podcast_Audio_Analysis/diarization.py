
import os
import torch
import torch.torch_version 
import pyannote.audio.core.task
from pyannote.audio import Pipeline
from typing import List, Dict

class DiarizationWrapper:
    def __init__(self, model_name: str, device: str):
        self.device = device
        self.model_name = model_name
        self.pipeline = self._load_pipeline()

    def _load_pipeline(self):
        print(f"Loading Diarization Pipeline: {self.model_name}")
        
        # Ensure HF Token is set in environment for pyannote 
        from huggingface_hub import HfFolder
        token = HfFolder.get_token()
        if token:
            print("Hugging Face token found, setting HF_TOKEN env var.")
            os.environ["HF_TOKEN"] = token
            
        try:
            try:
                if hasattr(torch.serialization, "add_safe_globals"):
                    torch.serialization.add_safe_globals([
                        torch.torch_version.TorchVersion,
                        pyannote.audio.core.task.Specifications,
                        pyannote.audio.core.task.Problem,
                        pyannote.audio.core.task.Resolution
                    ])
            except Exception:
                pass 

            pipeline = Pipeline.from_pretrained(self.model_name)

            if self.device == "cuda":
                pipeline.to(torch.device("cuda"))
            
            return pipeline
        except Exception as e:
            print(f"CRITICAL ERROR loading diarization pipeline: {e}")
            print("\nPOSSIBLE FIXES:")
            print("1. Accept the license at: https://huggingface.co/pyannote/speaker-diarization-3.1")
            print("2. Accept the license at: https://huggingface.co/pyannote/segmentation-3.0")
            print("3. Ensure you are logged in: 'hf auth login'")
            print("4. If 'WeightsUnpickler' error persists, try downgrading PyTorch to <2.6\n")
            raise e

    def run(self, audio_file_path: str) -> List[Dict]:
        if not self.pipeline:
             raise RuntimeError("Diarization pipeline not loaded.")
             
        print("Running Speaker Diarization...")
        # Run pipeline
        diarization = self.pipeline(audio_file_path)
        

        
        if hasattr(diarization, "speaker_diarization"):
            diarization = diarization.speaker_diarization
            
        results = []
        speaker_map = {}
        next_speaker_id = 1
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker not in speaker_map:
                speaker_map[speaker] = f"Speaker {next_speaker_id}"
                next_speaker_id += 1
                
            results.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker_map[speaker]
            })
        
        return results
