from sentence_transformers import SentenceTransformer
from transformers import pipeline
from typing import List, Dict

class NLPProcessor:
    def __init__(self, device: str):
        self.device_id = 0 if device == "cuda" else -1
        self.sbert = self._load_sbert()
        self.summarizer = self._load_summarizer()

    def _load_sbert(self):
        print("Loading Sentence-BERT...")
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def _load_summarizer(self):
        print("Loading BART Summarizer...")
        return pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=self.device_id
        )

    def segment_topics(self, segments: List[Dict], num_clusters: int = 5) -> List[Dict]:
        print("Segmenting topics (content-based analysis)...")
        
        if not segments:
            return []
        
        import re
        import numpy as np
        
        # Step 1: Extract all sentences with their time references
        all_sentences = []
        for seg in segments:
            text = seg["text"]
            start_time = seg["start"]
            end_time = seg["end"]
            
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                continue
            
            # Distribute time across sentences proportionally
            total_chars = sum(len(s) for s in sentences)
            current_time = start_time
            duration = end_time - start_time
            
            for sent in sentences:
                if total_chars > 0:
                    sent_duration = (len(sent) / total_chars) * duration
                else:
                    sent_duration = duration / len(sentences)
                
                all_sentences.append({
                    "text": sent,
                    "start": current_time,
                    "end": current_time + sent_duration
                })
                current_time += sent_duration
        
        if not all_sentences:
            return []
        
        # Step 2: Compute embeddings for all sentences
        texts = [s["text"] for s in all_sentences]
        embeddings = self.sbert.encode(texts)
        
        # Step 3: Detect topic boundaries using similarity drops
        SIMILARITY_THRESHOLD = 0.4  
        WINDOW_SIZE = 3  
        
        topic_boundaries = [0]  
        
        for i in range(WINDOW_SIZE, len(all_sentences) - WINDOW_SIZE):
            before_avg = np.mean(embeddings[i-WINDOW_SIZE:i], axis=0)
            after_avg = np.mean(embeddings[i:i+WINDOW_SIZE], axis=0)
            
            similarity = self._cosine_similarity(before_avg, after_avg)
            
            if similarity < SIMILARITY_THRESHOLD:
                if len(topic_boundaries) == 0 or i > topic_boundaries[-1] + WINDOW_SIZE:
                    topic_boundaries.append(i)
        
        # Step 4: Create topic segments
        topic_segments = []
        
        for idx, boundary_start in enumerate(topic_boundaries):
            if idx + 1 < len(topic_boundaries):
                boundary_end = topic_boundaries[idx + 1]
            else:
                boundary_end = len(all_sentences)
            
            topic_sentences = all_sentences[boundary_start:boundary_end]
            
            if topic_sentences:
                topic_text = " ".join([s["text"] for s in topic_sentences])
                topic_segments.append({
                    "topic_id": idx,
                    "start": topic_sentences[0]["start"],
                    "end": topic_sentences[-1]["end"],
                    "text": topic_text
                })
        
        if not topic_segments and all_sentences:
            topic_segments.append({
                "topic_id": 0,
                "start": all_sentences[0]["start"],
                "end": all_sentences[-1]["end"],
                "text": " ".join([s["text"] for s in all_sentences])
            })
        
        return topic_segments
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def summarize_segments(self, topic_segments: List[Dict]) -> List[Dict]:
        """
        Summarize the text of each topic segment.
        """
        if not topic_segments:
             return []

        print("Summarizing segments...")
        summaries = []
        for i, segment in enumerate(topic_segments):
            text = segment["text"]
            try:
                # Input length check
                input_tokens_est = len(text.split()) 
                
                if input_tokens_est < 10:
                    summary_text = text
                else:
                    adaptive_max = min(130, max(30, int(input_tokens_est * 0.6)))
                    adaptive_min = min(30, int(adaptive_max * 0.5))
                    
                    summary = self.summarizer(
                        text, 
                        max_length=adaptive_max, 
                        min_length=adaptive_min, 
                        do_sample=False, 
                        truncation=True
                    )
                    summary_text = summary[0]['summary_text']
            except Exception as e:
                print(f"Summarization failed for segment {i}: {e}")
                summary_text = text[:200] + "..."

            title = self._generate_title(text)

            summaries.append({
                "start": segment["start"],
                "end": segment["end"],
                "topic_id": segment["topic_id"],
                "summary": summary_text,
                "topic_name": title
            })
            
        return summaries

    def _generate_title(self, text: str) -> str:
        """
        Generate a short headline-style title for the topic.
        Input should be the summary of the topic.
        """
        try:
            title_summary = self.summarizer(text, max_length=10, min_length=3, do_sample=False, truncation=True)
            title = title_summary[0]['summary_text'].strip()
            
            if title.endswith('.'):
                title = title[:-1]
                
            return title
        except Exception:
            return "Topic Segment"
