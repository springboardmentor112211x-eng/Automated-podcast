"""
Audio Processing Module
Handles transcription, cleaning, segmentation, and summarization
"""

import librosa
import numpy as np
import warnings
from scipy.io import wavfile
import whisper
import nltk
try:
    from nltk.tokenize import sent_tokenize
    _NLTK_AVAILABLE = True
except Exception:
    _NLTK_AVAILABLE = False
import re
import os
from datetime import timedelta
from sentence_transformers import SentenceTransformer, util
import scipy.signal
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

warnings.filterwarnings('ignore')

# Download NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
except OSError:
    pass  # Already downloaded but in different format
    
try:
    nltk.data.find('tokenizers/punkt_tab')
except (LookupError, OSError):
    pass  # punkt_tab is optional, punkt is sufficient


class AudioProcessor:
    """Comprehensive audio processing pipeline"""
    
    def __init__(self, output_dir="./podcast_output", sample_rate=16000):
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.model_whisper = None
        self.embedding_model = None
        self.summarizer = None
        self.title_generator = None
        
        os.makedirs(output_dir, exist_ok=True)
        self._load_models()
    
    def _load_models(self):
        """Load all required models"""
        print("Loading models...")
        self.model_whisper = whisper.load_model("base")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.summarizer = pipeline(
            "summarization",
            model="knkarthick/MEETING_SUMMARY",
            device=-1  # CPU
        )
        self.title_generator = pipeline(
            "text2text-generation",
            model="Michau/t5-base-en-generate-headline"
        )
        print("✓ Models loaded")
    
    def process_audio(self, audio_path):
        """Main processing pipeline"""
        # 1. Load and preprocess
        print("Loading audio...")
        audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Calculate duration
        duration_seconds = len(audio_data) / sr
        duration_minutes = duration_seconds / 60
        duration_hours = duration_minutes / 60
        
        # Preprocessing
        print("Preprocessing audio...")
        audio_data = self._preprocess_audio(audio_data, sr)
        
        # 2. Transcription
        print("Transcribing with Whisper...")
        result = self.model_whisper.transcribe(audio_data, language="en", verbose=False)
        full_transcript = result["text"]
        segments = result["segments"]
        
        # 3. Cleaning
        print("Cleaning transcript...")
        cleaned_transcript = self._clean_text(full_transcript)
        
        # Tokenize with fallback
        if _NLTK_AVAILABLE:
            sentences = sent_tokenize(cleaned_transcript)
        else:
            # Simple fallback tokenization
            sentences = cleaned_transcript.replace('! ', '!SPLIT').replace('? ', '?SPLIT').split('SPLIT')
            sentences = [s.strip() for s in sentences if s.strip()]
        
        # 4. Save results
        return {
            "full_transcript": full_transcript,
            "cleaned_transcript": cleaned_transcript,
            "sentences": sentences,
            "segments": segments,
            "duration": f"{duration_hours:.2f}h ({int(duration_minutes)}m)",
            "duration_seconds": duration_seconds,
            "sample_rate": sr
        }
    
    def _preprocess_audio(self, audio_data, sr):
        """Preprocess audio: normalize, trim silence"""
        # Convert to mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)
        
        # Normalize
        max_val = np.max(np.abs(audio_data))
        audio_data = audio_data / max_val if max_val > 0 else audio_data
        
        # Resample if needed
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
        
        # Trim silence
        audio_data, _ = librosa.effects.trim(audio_data, top_db=40)
        
        return audio_data
    
    def _clean_text(self, text):
        """Clean transcribed text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove filler words
        filler_words = ['um', 'uh', 'hmm', 'like', 'you know', 'i mean']
        for filler in filler_words:
            text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
        
        # Fix spacing
        text = re.sub(r'\s+([?.!,;:])', r'\1', text)
        text = ' '.join(text.split())
        
        return text
    
    def generate_summaries(self, transcript_data):
        """Generate hybrid summaries for each topic"""
        sentences = transcript_data["sentences"]
        cleaned_transcript = transcript_data["cleaned_transcript"]
        
        # Segment by topics
        print("Segmenting into topics...")
        segments, _, _ = self._segment_topics(sentences)
        
        # Generate titles
        print("Generating chapter titles...")
        chapter_titles = self._generate_titles(segments)
        
        # Create summaries
        print("Creating hybrid summaries...")
        summaries = []
        
        for i, segment in enumerate(segments):
            title = chapter_titles[i] if i < len(chapter_titles) else f"Chapter {i+1}"
            
            # Extractive
            extractive = self._get_textrank_summary(segment, ratio=0.40)
            
            # Abstractive
            abstractive = self._get_abstractive_summary(extractive, title)
            
            summaries.append({
                "topic_id": i,
                "title": title,
                "original_text": segment,
                "final_summary": abstractive,
                "start_time": f"~{int(i * len(cleaned_transcript) / (len(segments) * 50))}m"  # Approximate
            })
        
        return summaries
    
    def _segment_topics(self, sentences, window_size=4, prominence=0.02):
        """YouTube-style topic segmentation"""
        embeddings = self.embedding_model.encode(sentences, show_progress_bar=False)
        n = len(sentences)
        cosine_scores = []
        
        for i in range(n - 1):
            end_current = min(i + window_size, n)
            start_next = i + 1
            end_next = min(start_next + window_size, n)
            
            current_emb = np.mean(embeddings[i:end_current], axis=0)
            next_emb = np.mean(embeddings[start_next:end_next], axis=0)
            
            score = util.cos_sim(current_emb, next_emb).item()
            cosine_scores.append(score)
        
        cosine_scores = np.array(cosine_scores)
        peaks, _ = scipy.signal.find_peaks(-cosine_scores, prominence=prominence, distance=20)
        
        split_indices = [0] + list(peaks + 1) + [n]
        segments = []
        
        for i in range(len(split_indices) - 1):
            start = split_indices[i]
            end = split_indices[i + 1]
            segment_text = ' '.join(sentences[start:end])
            segments.append(segment_text)
        
        if len(segments) < 2:
            chunk_size = len(sentences) // 5
            segments = [' '.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
        
        return segments, cosine_scores, peaks
    
    def _generate_titles(self, segments):
        """Generate titles for each segment"""
        titles = []
        for segment in segments:
            try:
                title_input = "headline: " + segment[:1000]
                title_out = self.title_generator(
                    title_input,
                    max_new_tokens=32,
                    min_length=4,
                    do_sample=False
                )
                raw_title = title_out[0]['generated_text'].strip()
                title = self._clean_title(raw_title).title()
            except:
                title = f"Chapter {len(titles) + 1}"
            
            titles.append(title)
        
        return titles
    
    def _clean_title(self, title):
        """Clean up generated title"""
        title = title.strip().rstrip(".,;-")
        stopwords = ["and", "or", "but", "the", "a", "an", "of", "to", "in", "for", "with"]
        words = title.split()
        if words and words[-1].lower() in stopwords:
            title = " ".join(words[:-1])
        return title.strip()
    
    def _get_textrank_summary(self, text, ratio=0.4, min_sentences=5):
        """TextRank extractive summarization"""
        # Tokenize with fallback
        if _NLTK_AVAILABLE:
            sentences = sent_tokenize(text)
        else:
            # Simple fallback tokenization
            sentences = text.replace('! ', '!SPLIT').replace('? ', '?SPLIT').split('SPLIT')
            sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= min_sentences:
            return text
        
        try:
            embeddings = self.embedding_model.encode(sentences, show_progress_bar=False)
            sim_matrix = cosine_similarity(embeddings)
            nx_graph = nx.from_numpy_array(sim_matrix)
            scores = nx.pagerank(nx_graph)
            
            ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
            num_sentences = max(min_sentences, int(len(sentences) * ratio))
            selected = ranked[:num_sentences]
            
            selected_text = []
            for sent in sentences:
                if any(sent == s[1] for s in selected):
                    selected_text.append(sent)
            
            return " ".join(selected_text)
        except:
            return text
    
    def _get_abstractive_summary(self, text, title):
        """Abstractive summarization"""
        try:
            input_text = f"Topic: {title}. Content: {text}"
            if len(input_text) > 4000:
                input_text = input_text[:4000]
            
            summary = self.summarizer(
                input_text,
                max_length=150,
                min_length=40,
                do_sample=False
            )[0]['summary_text']
            
            return summary
        except:
            return text[:200] + "..."
