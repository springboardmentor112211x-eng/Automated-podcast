# pipeline/summarizer.py

"""
Abstractive Topic Summarization Module
Uses HuggingFace BART to generate concise, meaningful summaries
"""

import logging

logger = logging.getLogger(__name__)

_summarizer = None


def _get_summarizer():
    """
    Lazy-load the summarization model
    """
    global _summarizer
    if _summarizer is None:
        try:
            from transformers import pipeline

            logger.info("🔄 Loading BART summarization model...")
            _summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # CPU (safe)
            )
            logger.info("✅ Summarization model loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load summarizer: {e}")
            _summarizer = False

    return _summarizer if _summarizer else None


def _chunk_text(text, max_words=180):
    """
    Split long text into chunks for BART
    """
    words = text.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i:i + max_words])


def summarize_text(text, max_length=40, min_length=25):
    """
    Generate an abstractive summary of the given text.
    """

    if not text or len(text.strip()) < 80:
        return text.strip()[:150]

    summarizer = _get_summarizer()

    # Fallback if model unavailable
    if not summarizer:
        sentences = text.split(".")
        return sentences[0].strip() if sentences else text[:150]

    summaries = []

    try:
        for chunk in _chunk_text(text):
            summary = summarizer(
                chunk,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            if summary and isinstance(summary, list):
                summaries.append(summary[0]["summary_text"])

        # Final compression if multiple chunks
        final_summary = " ".join(summaries)

        if len(final_summary.split()) > max_length * 2:
            final_summary = summarizer(
                final_summary,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )[0]["summary_text"]

        return final_summary.strip()

    except Exception as e:
        logger.warning(f"⚠️ Summarization failed: {e}")
        sentences = text.split(".")
        return ". ".join(sentences[:2]).strip()
