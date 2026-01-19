import re
from sklearn.feature_extraction.text import TfidfVectorizer


def clean_text(text: str) -> str:
    """Basic cleaning for better keyword extraction."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # remove symbols
    text = re.sub(r"\s+", " ", text).strip()  # normalize spaces
    return text


def generate_title_from_keywords(chunk: str, top_k: int = 3) -> str:
    """
    Auto-generates a short topic title using TF-IDF keywords.
    No predefined categories required.
    """
    cleaned = clean_text(chunk)

    # If chunk is too small, fallback
    if len(cleaned.split()) < 10:
        return "General Topic"

    # TF-IDF on a single chunk isn't useful, so we use a trick:
    # Split the chunk into sentences and compute TF-IDF across them.
    sentences = [s.strip() for s in re.split(r"[.!?]", cleaned) if len(s.strip()) > 0]

    # If no good sentences found, fallback
    if len(sentences) < 2:
        return "General Topic"

    vectorizer = TfidfVectorizer(stop_words="english", max_features=50)
    tfidf_matrix = vectorizer.fit_transform(sentences)

    # Compute average TF-IDF score for each word
    scores = tfidf_matrix.mean(axis=0).A1
    words = vectorizer.get_feature_names_out()

    # Get top keywords
    top_indices = scores.argsort()[::-1][:top_k]
    keywords = [words[i] for i in top_indices if scores[i] > 0]

    if not keywords:
        return "General Topic"

    # Title formatting
    title = " • ".join(keywords[:top_k])
    return title.title()


def topic_segmentation(transcript: str, max_words_per_topic: int = 140) -> list[dict]:
    """
    Segments transcript into chunks by word length.
    Generates a title for each chunk automatically using TF-IDF keywords.
    """
    words = transcript.split()
    topics = []

    start = 0
    topic_id = 1

    while start < len(words):
        end = min(start + max_words_per_topic, len(words))
        chunk = " ".join(words[start:end]).strip()

        title = generate_title_from_keywords(chunk)

        topics.append({
            "topic_id": topic_id,
            "title": title,
            "content": chunk
        })

        topic_id += 1
        start = end

    return topics
