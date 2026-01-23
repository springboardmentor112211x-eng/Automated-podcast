from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def segment_topics(segments, threshold=0.65):
    """
    Segments transcripts into topics based on similarity threshold.
    Returns list of topic segments (list of segment dicts).
    """
    if not segments:
        return []

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [s["text"] for s in segments]
    emb = model.encode(texts)

    topics = []
    current = [segments[0]]

    for i in range(1, len(segments)):
        sim = cosine_similarity([emb[i-1]], [emb[i]])[0][0]
        if sim < threshold:
            topics.append(current)
            current = []
        current.append(segments[i])

    topics.append(current)
    return topics
