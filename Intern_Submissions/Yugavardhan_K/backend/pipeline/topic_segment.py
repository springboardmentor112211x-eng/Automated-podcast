from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pipeline.summarize import generate_title, generate_summary
import numpy as np

class TopicSegmenter:
    def __init__(
        self,
        llm,
        model_name="all-MiniLM-L6-v2",
        min_duration=120.0,        # ⬅️ 2 minutes minimum (PODCAST SAFE)
        min_words=250,             # ⬅️ avoid micro topics
        similarity_threshold=0.58, # ⬅️ lower = fewer splits
        window_size=10
    ):
        self.model = SentenceTransformer(model_name)
        self.min_duration = min_duration
        self.min_words = min_words
        self.similarity_threshold = similarity_threshold
        self.window_size = window_size

    def segment(self, sentences):
        if not sentences:
            return []

        topics = []
        buffer = [sentences[0]]

        def block_text(block):
            return " ".join(s["text"] for s in block)

        def block_duration(block):
            return block[-1]["end"] - block[0]["start"]

        for i in range(1, len(sentences)):
            buffer.append(sentences[i])

            if len(buffer) < self.window_size:
                continue

            prev_block = buffer[:-1]
            curr_block = buffer[-self.window_size:]

            prev_text = block_text(prev_block)
            curr_text = block_text(curr_block)

            if len(prev_text.split()) < self.min_words:
                continue

            emb_prev = np.asarray(self.model.encode(prev_text, convert_to_numpy=True)).reshape(1, -1)
            emb_curr = np.asarray(self.model.encode(curr_text, convert_to_numpy=True)).reshape(1, -1)

            sim = cosine_similarity(
                emb_prev, emb_curr
            )[0][0]

            duration = block_duration(prev_block)

            if sim < self.similarity_threshold and duration >= self.min_duration:
                topics.append(self._build_topic(prev_block))
                buffer = curr_block.copy()

        if buffer:
            topics.append(self._build_topic(buffer))

        return topics

    def _build_topic(self, block):
        text = " ".join(s["text"] for s in block)
        start = block[0]["start"]
        end = block[-1]["end"]

        title = generate_title(text)
        summary = generate_summary(text)

        return {
            "start_time": float(start),
            "end_time": float(end),
            "text": text,
            "title": title,
            "summary": summary,
            "confidence": round(min(1.0, len(text.split()) / 500), 2)
        }