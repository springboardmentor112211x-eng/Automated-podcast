from transformers import pipeline

_summarizer = None

def _get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1
        )
    return _summarizer

def summarize_topics(topics, llm=None):
    for t in topics:
        summary = generate_summary(t["text"])
        t["summary"] = summary
        t["title"] = generate_title(summary, llm=llm)

    return topics

def generate_summary(text):
    if not text or len(text.split()) < 120:
        return text.strip()

    try:
        summarizer = _get_summarizer()
        out = summarizer(
            text[:3500],
            max_length=150,
            min_length=60,
            do_sample=False
        )
        return out[0]["summary_text"]
    except Exception:
        # fallback: explain first + last context
        sentences = text.split(". ")
        return ". ".join(sentences[:3] + sentences[-3:])


def generate_title(summary: str, llm=None) -> str:
    """
    Generate a clean, abstract topic title from a summary.
    """

    if not summary or len(summary.strip()) < 20:
        return "General Discussion"

    # --- LLM PATH (preferred) ---
    if llm:
        prompt = f"""
You are an expert editor.

Generate a short, professional topic title (max 3 words)
from the following summary. Understand the context and
focus on key nouns and phrases.

Rules:
- NO sentences
- NO quotes
- NO filler words
- Capitalize Properly
- Noun phrase only

Summary:
{summary}

Title:
"""
        try:
            title = llm.generate(prompt).strip()
            title = title.replace('"', "").replace("'", "")
            return title[:60]
        except Exception:
            pass

    # --- FALLBACK (no LLM) ---
    # Use first strong noun phrase heuristic
    words = summary.split()
    cleaned = [
        w.capitalize()
        for w in words
        if w.isalpha() and len(w) > 3
    ]

    return " ".join(cleaned[:5]) or "Key Discussion"
