import numpy as np
import torch
from typing import List, Dict, Union

# Import new modules
from audio_utils import load_and_preprocess_audio
from diarization import DiarizationWrapper
from transcription import WhisperWrapper
from nlp_service import NLPProcessor
from memory_utils import clear_gpu_memory, get_gpu_memory_info

class AudioPipeline:
    """
    A pipeline for audio processing: Diarization, Transcription/Translation, 
    Topic Segmentation, and Summarization.
    """

    def __init__(self, 
                 whisper_model: str = "openai/whisper-large-v3", 
                 diarization_pipeline: str = "pyannote/speaker-diarization-3.1",
                 device: Union[str, int] = None,
                 memory_efficient: bool = True):
        """
        Initialize the pipeline configuration.
        Models are NOT loaded here - they are loaded lazily when needed.
        """
        self.device = device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")
        self.memory_efficient = memory_efficient
        
        # Model configuration (stored for lazy loading)
        self.whisper_model_name = whisper_model
        self.diarization_model_name = diarization_pipeline
        
        # Print GPU info
        gpu_info = get_gpu_memory_info()
        if gpu_info.get("available"):
            print(f"GPU Total: {gpu_info['total_gb']:.2f} GB, Free: {gpu_info['free_gb']:.2f} GB")
        
        # Module placeholders (lazy loaded)
        self._diarization_module = None
        self._transcription_module = None
        self._nlp_module = None

        # State storage
        self.audio_data = None
        self.sr = 16000
        self.file_path = None
        self.processed_file_path = None
        self.diarization_result = None
        self.transcription_result = None
        self.topic_segments = None
    
    @property
    def diarization_module(self):
        """Lazy load diarization module."""
        if self._diarization_module is None:

            clear_gpu_memory()
            self._diarization_module = DiarizationWrapper(self.diarization_model_name, self.device)
        return self._diarization_module
    
    @property
    def transcription_module(self):
        """Lazy load transcription module."""
        if self._transcription_module is None:

            clear_gpu_memory()
            self._transcription_module = WhisperWrapper(self.whisper_model_name, self.device)
        return self._transcription_module
    
    @property
    def nlp_module(self):
        """Lazy load NLP module."""
        if self._nlp_module is None:

            clear_gpu_memory()
            self._nlp_module = NLPProcessor(self.device)
        return self._nlp_module
    
    def _unload_module(self, module_name: str):
        """Unload a specific module to free GPU memory."""
        from memory_utils import unload_model
        
        if module_name == "diarization" and self._diarization_module is not None:
            if hasattr(self._diarization_module, 'pipeline'):
                unload_model(self._diarization_module.pipeline)
            self._diarization_module = None
            
        elif module_name == "transcription" and self._transcription_module is not None:
            if hasattr(self._transcription_module, 'pipeline'):
                unload_model(self._transcription_module.pipeline)
            self._transcription_module = None
            
        elif module_name == "nlp" and self._nlp_module is not None:
            if hasattr(self._nlp_module, 'sbert'):
                unload_model(self._nlp_module.sbert)
            if hasattr(self._nlp_module, 'summarizer'):
                unload_model(self._nlp_module.summarizer)
            self._nlp_module = None
        
        clear_gpu_memory()

    def load_audio(self, file_path: str) -> np.ndarray:
        """
        Load, preprocess (convert to mono 16kHz, denoise, normalize), and store audio.
        """
        self.file_path = file_path
        self.audio_data, self.processed_file_path = load_and_preprocess_audio(file_path, self.sr)
        return self.audio_data

    def diarize(self, min_speakers=None, max_speakers=None) -> List[Dict]:
        """
        Run speaker diarization on the loaded audio.
        """
        if self.processed_file_path is None:
            raise RuntimeError("Audio not loaded. Call load_audio() first.")

        self.diarization_result = self.diarization_module.run(self.processed_file_path, min_speakers=min_speakers, max_speakers=max_speakers)
        
        # Free GPU memory after diarization if memory_efficient mode is on
        if self.memory_efficient:
            self._unload_module("diarization")
        
        return self.diarization_result

    def transcribe_translate(self, timestamped=True, progress_callback=None) -> List[Dict]:
        if self.audio_data is None:
            if self.processed_file_path:
                import librosa
                import os
                if os.path.exists(self.processed_file_path):
                    self.audio_data, _ = librosa.load(self.processed_file_path, sr=self.sr)
                else:
                    raise RuntimeError("Audio not loaded.")
            else:
                raise RuntimeError("Audio not loaded.")

        # Get transcription segments 
        transcription_segments = self.transcription_module.transcribe_translate(
            self.audio_data, progress_callback
        )
        
        # Free GPU memory
        if self.memory_efficient:
            self._unload_module("transcription")
        
        if not self.diarization_result:
            return self._format_no_diarization(transcription_segments)
        

        
        # 1. Create speaker map
        speaker_map = {}
        next_speaker_id = 1
        for turn in self.diarization_result:
            orig = turn["speaker"]
            if orig not in speaker_map:
                speaker_map[orig] = f"Speaker {next_speaker_id}"
                next_speaker_id += 1
        
        # 2. Assign each transcription segment to a speaker
        assigned_segments = []
        
        for seg in transcription_segments:
            seg_start = seg["start"]
            seg_end = seg["end"]
            
            best_speaker = "Unknown"
            max_overlap = 0
            
            # Find matching turn
            for turn in self.diarization_result:
                overlap_start = max(seg_start, turn["start"])
                overlap_end = min(seg_end, turn["end"])
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = speaker_map.get(turn["speaker"], "Unknown")
            
            if best_speaker == "Unknown" and self.diarization_result:
                min_dist = float('inf')
                for turn in self.diarization_result:
                    dist = min(abs(seg_start - turn["end"]), abs(seg_end - turn["start"]))
                    if dist < min_dist:
                        min_dist = dist
                        best_speaker = speaker_map.get(turn["speaker"], "Unknown")

            assigned_segments.append({
                "start": seg_start,
                "end": seg_end,
                "text": seg["text"],
                "speaker": best_speaker
            })

        # 3. Merge contiguous segments with same speaker
        final_segments = []
        if not assigned_segments:
            self.transcription_result = []
            return []

        current_speaker = assigned_segments[0]["speaker"]
        current_texts = [assigned_segments[0]["text"]]
        current_start = assigned_segments[0]["start"]
        last_end = assigned_segments[0]["end"]
        
        for i in range(1, len(assigned_segments)):
            seg = assigned_segments[i]
            
            if seg["speaker"] == current_speaker:
                current_texts.append(seg["text"])
                last_end = seg["end"]
            else:
                final_segments.append({
                    "start": current_start,
                    "end": last_end,
                    "speaker": current_speaker,
                    "text": " ".join(current_texts)
                })
                # Start new
                current_speaker = seg["speaker"]
                current_texts = [seg["text"]]
                current_start = seg["start"]
                last_end = seg["end"]
        
        # Add final segment
        final_segments.append({
            "start": current_start,
            "end": last_end,
            "speaker": current_speaker,
            "text": " ".join(current_texts)
        })
        
        self.transcription_result = final_segments
        return final_segments

    def _format_no_diarization(self, segments):
        final_segments = []
        for seg in segments:
            end = seg["end"]
            if end <= seg["start"]: end = seg["start"] + 1.0
            final_segments.append({
                "start": seg["start"],
                "end": end,
                "speaker": "Unknown",
                "text": seg["text"].strip()
            })
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
