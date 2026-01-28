"""Generate human-readable topic labels from clustered transcripts using TF-IDF.

This module keeps the original, simple heuristic (sum TF-IDF scores per topic) but
adds small robustness improvements and configuration options while preserving
core behavior.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def generate_topic_labels(
    input_csv: str,
    output_csv: str,
    top_n_words: int = 5,
    stop_words: Optional[str] = "english",
    ngram_range: Tuple[int, int] = (1, 1),
    min_df: int = 1,
    max_features: int = 50,
    empty_label: str = "Miscellaneous",
) -> pd.DataFrame:
    """Generate labels for each topic by extracting top TF-IDF keywords.

    Returns the labels dataframe (useful for testing and programmatic use).

    Core behavior: groups rows by `topic_id`, computes TF-IDF over `clean_transcript`
    for each group, sums TF-IDF scores per feature, then selects top words.
    """
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)

    df = pd.read_csv(input_csv)

    if "topic_id" not in df.columns or "clean_transcript" not in df.columns:
        raise ValueError("CSV must contain 'topic_id' and 'clean_transcript' columns")

    topic_labels = []

    for topic_id, group in df.groupby("topic_id"):
        texts = group["clean_transcript"].dropna().astype(str).tolist()

        if not texts:
            label = empty_label
        else:
            vectorizer = TfidfVectorizer(
                stop_words=stop_words,
                max_features=max_features,
                ngram_range=ngram_range,
                min_df=min_df,
            )
            tfidf = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            scores = tfidf.sum(axis=0).A1
            # Pair scores with tokens and make selection deterministic
            pairs = list(zip(scores, feature_names))
            pairs.sort(key=lambda s_t: (-s_t[0], s_t[1]))
            keywords = [token for _, token in pairs[:top_n_words]]

            label = ", ".join(keywords) if keywords else empty_label

        topic_labels.append({"topic_id": topic_id, "topic_label": label})

    label_df = pd.DataFrame(topic_labels)
    label_df.to_csv(output_csv, index=False)

    logger.info("Topic labeling completed. Saved to: %s", output_csv)
    return label_df


if __name__ == "__main__":
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Generate topic labels")
    parser.add_argument("input_csv", help="Input CSV with topic_id and clean_transcript")
    parser.add_argument("output_csv", help="Output CSV with topic labels")
    parser.add_argument("--top-n-words", type=int, default=5)
    parser.add_argument("--min-df", type=int, default=1)
    parser.add_argument("--max-features", type=int, default=50)
    parser.add_argument("--ngram-range", type=str, default="1,1", help="ngram_range as two comma-separated ints, e.g. 1,2")

    args = parser.parse_args()
    ngram = tuple(int(x) for x in args.ngram_range.split(","))

    generate_topic_labels(
        args.input_csv,
        args.output_csv,
        top_n_words=args.top_n_words,
        min_df=args.min_df,
        max_features=args.max_features,
        ngram_range=ngram,
    )
