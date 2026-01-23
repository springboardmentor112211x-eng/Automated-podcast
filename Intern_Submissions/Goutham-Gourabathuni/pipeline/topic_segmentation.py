import numpy as np
from sklearn.metrics.pairwise import cosine_distances, cosine_similarity

def detect_topic_boundaries_embeddings(
    embeddings,
    similarity_threshold=0.65,
    min_sentences_per_topic=5
):
    """
    Detect topic boundaries based on cosine similarity
    between consecutive sentence embeddings.

    Args:
        embeddings (np.ndarray): shape (N, D)
        similarity_threshold (float): lower = more topics
        min_sentences_per_topic (int): prevents tiny topics

    Returns:
        List[int]: indices where a new topic starts
    """

    if embeddings is None or len(embeddings) < 2:
        return []

    embeddings = np.asarray(embeddings)
    boundaries = []
    last_boundary = 0

    for i in range(1, len(embeddings)):
        sim = cosine_similarity(
            embeddings[i - 1:i],
            embeddings[i:i + 1]
        )[0][0]

        # Topic break condition
        if (
            sim < similarity_threshold
            and (i - last_boundary) >= min_sentences_per_topic
        ):
            boundaries.append(i)
            last_boundary = i

    return boundaries


def refine_boundaries_with_context(
    boundaries,
    embeddings,
    context_window=2
):
    """
    Refine boundaries by selecting the strongest
    similarity drop within a local context window.
    """
    if not boundaries or len(embeddings) < 2:
        return boundaries

    refined = []
    embeddings = np.asarray(embeddings)

    for idx in boundaries:
        start = max(1, idx - context_window)
        end = min(len(embeddings) - 1, idx + context_window)

        best_idx = idx
        max_jump = 0.0

        for i in range(start, end):
            d1 = cosine_distances(
                embeddings[i - 1:i],
                embeddings[i:i + 1]
            )[0][0]
            d2 = cosine_distances(
                embeddings[i:i + 1],
                embeddings[i + 1:i + 2]
            )[0][0]

            jump = abs(d2 - d1)
            if jump > max_jump:
                max_jump = jump
                best_idx = i

        refined.append(best_idx)

    return sorted(set(refined))


def get_topic_segments(
    boundaries,
    sentences,
    timestamps=None
):
    """
    Build topic segments from boundaries.

    Args:
        boundaries (List[int])
        sentences (List[str])
        timestamps (List[dict], optional)

    Returns:
        List[dict]: topic segments
    """
    segments = []

    if not sentences:
        return segments

    if not boundaries:
        return [{
            "text": " ".join(sentences),
            "start_idx": 0,
            "end_idx": len(sentences) - 1,
            "sentence_count": len(sentences),
            "start_time": timestamps[0]["start"] if timestamps else 0.0,
            "end_time": timestamps[-1]["end"] if timestamps else 0.0
        }]

    start = 0

    for b in boundaries:
        segment = {
            "text": " ".join(sentences[start:b]),
            "start_idx": start,
            "end_idx": b - 1,
            "sentence_count": b - start,
            "start_time": timestamps[start]["start"] if timestamps else 0.0,
            "end_time": timestamps[b - 1]["end"] if timestamps else 0.0
        }

        if segment["text"].strip():
            segments.append(segment)

        start = b

    # Final segment
    if start < len(sentences):
        segments.append({
            "text": " ".join(sentences[start:]),
            "start_idx": start,
            "end_idx": len(sentences) - 1,
            "sentence_count": len(sentences) - start,
            "start_time": timestamps[start]["start"] if timestamps else 0.0,
            "end_time": timestamps[-1]["end"] if timestamps else 0.0
        })

    return segments
