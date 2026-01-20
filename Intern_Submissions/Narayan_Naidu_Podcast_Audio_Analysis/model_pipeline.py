
import numpy as np
import torch
from typing import List, Dict, Union

# Import new modules
from audio_utils import load_and_preprocess_audio
from diarization import DiarizationWrapper
from transcription import WhisperWrapper
from nlp_service import NLPProcessor

class AudioPipeline:
    """
    A pipeline for audio processing: Diarization, Transcription/Translation, 
    Topic Segmentation, and Summarization.
    Refactored to use modular components.
    """

    def __init__(self, 
                 whisper_model: str = "openai/whisper-large-v3", 
                 diarization_pipeline: str = "pyannote/speaker-diarization-3.1",
                 device: Union[str, int] = None):
        """
        Initialize the pipeline models.
        """
        self.device = device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"Initializing AudioPipeline on device: {self.device}")

        # Initialize sub-modules
        self.diarization_module = DiarizationWrapper(diarization_pipeline, self.device)
        self.transcription_module = WhisperWrapper(whisper_model, self.device)
        self.nlp_module = NLPProcessor(self.device)

        # State storage
        self.audio_data = None
        self.sr = 16000
        self.file_path = None
        self.processed_file_path = None
        self.diarization_result = None
        self.transcription_result = None
        self.topic_segments = None

    def load_audio(self, file_path: str) -> np.ndarray:
        """
        Load, preprocess (convert to mono 16kHz, denoise, normalize), and store audio.
        """
        self.file_path = file_path
        self.audio_data, self.processed_file_path = load_and_preprocess_audio(file_path, self.sr)
        return self.audio_data

    def diarize(self) -> List[Dict]:
        """
        Run speaker diarization on the loaded audio.
        """
        if self.processed_file_path is None:
            raise RuntimeError("Audio not loaded. Call load_audio() first.")

        self.diarization_result = self.diarization_module.run(self.processed_file_path)
        return self.diarization_result

    def transcribe_translate(self, timestamped=True, progress_callback=None) -> List[Dict]:
        """
        Run Whisper transcription (and translation). Merges with diarization if available.
        """
        if self.audio_data is None:
             # Fallback to loading if audio_data isn't in memory but file is
             if self.processed_file_path:
                 import librosa
                 import os
                 if os.path.exists(self.processed_file_path):
                     self.audio_data, _ = librosa.load(self.processed_file_path, sr=self.sr)
                 else:
                     raise RuntimeError("Audio not loaded.")
             else:
                raise RuntimeError("Audio not loaded.")

        all_chunks = self.transcription_module.transcribe_translate(self.audio_data, progress_callback)
        
        final_segments = []
        
        if self.diarization_result:
            print("Aligning transcription with speaker labels...")
            for chunk in all_chunks:
                chunk_start = chunk["timestamp"][0]
                chunk_end = chunk["timestamp"][1]
                
                if chunk_end <= chunk_start: chunk_end = chunk_start + 2.0
                
                text = chunk["text"]
                
                best_speaker = "Unknown"
                max_overlap = 0
                
                for diag_seg in self.diarization_result:
                    start = max(chunk_start, diag_seg["start"])
                    end = min(chunk_end, diag_seg["end"])
                    overlap = max(0, end - start)
                    
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_speaker = diag_seg["speaker"]
                
                final_segments.append({
                    "start": chunk_start,
                    "end": chunk_end,
                    "speaker": best_speaker,
                    "text": text.strip()
                })
        else:
            # If no diarization, just return segments
            for chunk in all_chunks:
                 start = chunk["timestamp"][0]
                 end = chunk["timestamp"][1]
                 if end <= start: end = start + 1.0
                 
                 final_segments.append({
                    "start": start,
                    "end": end,
                    "speaker": "Unknown",
                    "text": chunk["text"].strip()
                })

        final_segments.sort(key=lambda x: x["start"])
        
        unique_speakers = {}
        next_id = 1
        
        for seg in final_segments:
            original_speaker = seg["speaker"]
            if original_speaker == "Unknown":
                continue
                
            if original_speaker not in unique_speakers:
                unique_speakers[original_speaker] = f"Speaker {next_id}"
                next_id += 1
            
            seg["speaker"] = unique_speakers[original_speaker]

        self.transcription_result = final_segments
        return final_segments

    def segment_topics(self, num_clusters=5) -> List[Dict]:
        """
        Embed sentences and cluster them into topics.
        """
        if not self.transcription_result:
            raise RuntimeError("No transcription available. Run transcribe_translate() first.")
            
        self.topic_segments = self.nlp_module.segment_topics(self.transcription_result, num_clusters)
        return self.topic_segments

    def summarize_segments(self) -> List[Dict]:
        """
        Summarize the text of each topic segment.
        """
        if not self.topic_segments:
            raise RuntimeError("No topic segments. Run segment_topics() first.")

        return self.nlp_module.summarize_segments(self.topic_segments)
