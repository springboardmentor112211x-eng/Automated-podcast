# backend/services/topic_summary.py

import argparse
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def summarize_topic(texts: List[str], max_sentences: int = 3, stop_words: Optional[str] = "english") -> str:
    """Simple extractive summarization using TF-IDF sentence scoring.

    - If number of texts <= max_sentences, returns their concatenation.
    - If TF-IDF cannot be computed (empty vocabulary), falls back to first `max_sentences` texts.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return ""

    if len(texts) <= max_sentences:
        return " ".join(texts)

    vectorizer = TfidfVectorizer(stop_words=stop_words)
    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError as exc:
        # e.g., empty vocabulary due to stop words; fallback to first N sentences
        logger.warning("TF-IDF failed (%s). Falling back to first %d sentences.", exc, max_sentences)
        return " ".join(texts[:max_sentences])

    sentence_scores = tfidf.sum(axis=1).A1
    top_indices = np.argsort(sentence_scores)[::-1][:max_sentences]

    # Keep original order for readability
    top_sentences = [texts[i] for i in sorted(top_indices)]
    return " ".join(top_sentences)


def generate_topic_summaries(
    input_csv: str,
    output_csv: str,
    max_sentences: int = 3,
    stop_words: Optional[str] = "english",
):
    """Generates summaries for each topic_id and writes an output CSV.

    Returns the DataFrame of summaries for programmatic use and testing.
    """
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)

    df = pd.read_csv(input_csv)

    required_cols = {"topic_id", "clean_transcript"}
    if not required_cols.issubset(df.columns):
        raise ValueError("CSV must contain topic_id and clean_transcript columns")

    summaries = []

    for topic_id, group in df.groupby("topic_id"):
        texts = (
            group["clean_transcript"]
            .dropna()
            .astype(str)
            .tolist()
        )

        summary = summarize_topic(texts, max_sentences=max_sentences, stop_words=stop_words)

        summaries.append({
            "topic_id": topic_id,
            "topic_summary": summary
        })

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(output_csv, index=False)

    logger.info("Topic-wise summarization completed. Saved to: %s", output_csv)
    return summary_df


def generate_global_summary(
    input_csv: str,
    output_txt: str,
    max_sentences: int = 5,
    stop_words: Optional[str] = "english",
):
    """Generate a single global summary from all clean transcripts.

    Writes the summary to a text file and returns the summary string.
    """
    input_csv = Path(input_csv)
    df = pd.read_csv(input_csv)

    if "clean_transcript" not in df.columns:
        raise ValueError("CSV must contain clean_transcript column")

    texts = df["clean_transcript"].dropna().astype(str).tolist()
    summary = summarize_topic(texts, max_sentences=max_sentences, stop_words=stop_words)

    Path(output_txt).parent.mkdir(parents=True, exist_ok=True)
    Path(output_txt).write_text(summary, encoding="utf-8")
    logger.info("Global summary written to: %s", output_txt)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate topic-wise summaries")
    parser.add_argument("input_csv", help="Input CSV with topic_id")
    parser.add_argument("output_csv", help="Output CSV for topic summaries")
    parser.add_argument("--max-sentences", type=int, default=3)

    args = parser.parse_args()

    generate_topic_summaries(
        args.input_csv,
        args.output_csv,
        max_sentences=args.max_sentences
    )
