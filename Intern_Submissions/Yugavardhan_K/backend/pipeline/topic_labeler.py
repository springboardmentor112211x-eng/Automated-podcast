def label_topics(topics):
    for topic in topics:
        text = topic["text"].lower()

        if "introduction" in text:
            title = "Introduction"
        elif "conclusion" in text:
            title = "Conclusion"
        elif "example" in text:
            title = "Examples & Explanation"
        elif "problem" in text or "issue" in text:
            title = "Problem Discussion"
        else:
            # Fallback: first meaningful phrase
            title = topic["segments"][0]["text"][:60]

        topic["title"] = title.strip()

    return topics