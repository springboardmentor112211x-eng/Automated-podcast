from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticSearchEngine:
    def __init__(self, topic_segments):
        self.topic_segments = topic_segments
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([t["content"] for t in topic_segments])

    def search(self, query, top_k=3):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sims.argsort()[::-1][:top_k]

        results = []
        for idx in ranked:
            results.append({
                "topic_id": self.topic_segments[idx]["topic_id"],
                "title": self.topic_segments[idx]["title"],
                "score": float(sims[idx]),
                "snippet": self.topic_segments[idx]["content"][:180] + "..."
            })
        return results

    def qa(self, question):
        """
        Simple Q&A:
        - retrieves most relevant topic chunk
        - answers using grounded extracted context (no hallucination)
        """
        results = self.search(question, top_k=1)
        best = results[0]

        context = next(
            t["content"] for t in self.topic_segments if t["topic_id"] == best["topic_id"]
        )

        answer = (
            f"Based on the transcript segment titled '{best['title']}', "
            f"the relevant information is:\n\n{context[:500]}..."
        )

        return {
            "question": question,
            "best_topic": best,
            "answer": answer
        }
