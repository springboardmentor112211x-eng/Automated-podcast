def generate_summary(topic_segments):
    """
    GenAI-style structured summary:
    - short summary
    - bullet summary
    - tags
    """
    bullets = []
    for seg in topic_segments[:6]:
        bullets.append(f"- {seg['title']}: {seg['content'][:120]}...")

    tags = list({seg["title"] for seg in topic_segments})

    return {
        "short_summary": "This podcast episode was automatically transcribed and segmented into meaningful topics.",
        "bullet_summary": bullets,
        "tags": tags[:8]
    }
