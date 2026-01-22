from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize.punkt import PunktSentenceTokenizer

def segment_topics(transcriptions, threshold=0.65):
    """
    Segments transcript into topics while preserving timestamps.
    """

    # Flatten segments
    sentences = []
    segments_info = []

    for chunk in transcriptions:
        for seg in chunk["segments"]:
            sentences.append(seg["text"])
            segments_info.append((seg["start"], seg["end"]))

    # Sentence embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences)

    # Topic boundaries
    boundaries = [0]
    for i in range(len(embeddings)-1):
        sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
        if sim < threshold:
            boundaries.append(i+1)
    boundaries.append(len(sentences))

    # Build topic list
    topics = []
    for i in range(len(boundaries)-1):
        start_idx = boundaries[i]
        end_idx = boundaries[i+1]-1
        topic_text = " ".join(sentences[start_idx:end_idx+1])
        topic_start = segments_info[start_idx][0]
        topic_end = segments_info[end_idx][1]

        topics.append({
            "topic_id": i+1,
            "text": topic_text,
            "start_time": round(topic_start, 2),
            "end_time": round(topic_end, 2)
        })

    return topics
