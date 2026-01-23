from keybert import KeyBERT

kw_model = KeyBERT("all-MiniLM-L6-v2")

def label_topics(topic_segments):
    """
    Adds keywords and topic info for each topic segment.
    """
    labeled = []

    for i, segs in enumerate(topic_segments):
        text = " ".join(s["text"] for s in segs)
        keywords = kw_model.extract_keywords(text, top_n=3)

        labeled.append({
            "topic_id": i + 1,
            "start_time": segs[0]["start"],
            "end_time": segs[-1]["end"],
            "keywords": ", ".join(k[0] for k in keywords),
            "text": text
        })

    return labeled
