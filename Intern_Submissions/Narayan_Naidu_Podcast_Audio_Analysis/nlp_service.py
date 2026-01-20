
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
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
        """
        Embed sentences and cluster them into topics.
        """
        print("Segmenting topics...")
        
        if not segments:
            return []
            
        sentences = [seg["text"] for seg in segments]
        
        if len(sentences) < num_clusters:
            num_clusters = max(1, len(sentences))

        # Embed
        embeddings = self.sbert.encode(sentences)
        
        # Cluster
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        
        # Group consecutive segments with same label
        topic_segments = []

        current_topic_idx = labels[0]
        current_start = segments[0]["start"]
        current_text = [segments[0]["text"]]
        
        for i in range(1, len(segments)):
            label = labels[i]
            if label == current_topic_idx:
                current_text.append(segments[i]["text"])
            else:
                # Close current segment
                end_time = segments[i-1]["end"]
                topic_segments.append({
                    "start": current_start,
                    "end": end_time,
                    "topic_id": int(current_topic_idx), 
                    "text": " ".join(current_text)
                })
                # Start new
                current_topic_idx = label
                current_start = segments[i]["start"]
                current_text = [segments[i]["text"]]
        
        # Add last segment
        topic_segments.append({
            "start": current_start,
            "end": segments[-1]["end"],
            "topic_id": int(current_topic_idx),
            "text": " ".join(current_text)
        })
        
        for i, segment in enumerate(topic_segments):
            segment["topic_id"] = i

        return topic_segments

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
