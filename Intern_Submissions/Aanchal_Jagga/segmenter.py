def topic_segmentation(transcript: str, chunk_words=140):
    """
    Simple topic segmentation:
    - Splits transcript into word-based chunks
    - Assigns topic title using keyword rules
    """
    words = transcript.split()
    raw_segments = []

    for i in range(0, len(words), chunk_words):
        seg = " ".join(words[i:i+chunk_words]).strip()
        if seg:
            raw_segments.append(seg)

    topics = []
    for idx, seg in enumerate(raw_segments):
        topics.append({
            "topic_id": idx + 1,
            "title": generate_topic_title(seg),
            "content": seg
        })

    return topics

def generate_topic_title(text: str):
    t = text.lower()

    if any(k in t for k in ["ai", "machine learning", "model", "llm"]):
        return "AI / Machine Learning"
    if any(k in t for k in ["internship", "project", "submission", "deadline"]):
        return "Project / Internship"
    if any(k in t for k in ["startup", "business", "market", "revenue"]):
        return "Business & Growth"
    if any(k in t for k in ["health", "gym", "workout", "diet"]):
        return "Health & Lifestyle"

    return "General Discussion"
