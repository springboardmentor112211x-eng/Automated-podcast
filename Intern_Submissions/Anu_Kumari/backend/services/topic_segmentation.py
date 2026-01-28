"""Topic segmentation utilities.

Provides `run_topic_segmentation` which clusters sentence embeddings into topic
ids and writes the result to `output_csv`.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from ast import literal_eval

logger = logging.getLogger(__name__)


def _parse_embedding(val) -> Optional[np.ndarray]:
    """Parse an embedding value from CSV into a numpy array or return None.

    Accepts lists, numpy arrays, JSON strings or Python literal strings.
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None

    if isinstance(val, (list, tuple, np.ndarray)):
        return np.asarray(val, dtype=np.float32)

    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        # Try JSON first (fast for our serialization). Fallback to literal_eval.
        try:
            parsed = json.loads(s)
            return np.asarray(parsed, dtype=np.float32)
        except Exception:
            try:
                parsed = literal_eval(s)
                return np.asarray(parsed, dtype=np.float32)
            except Exception:
                logger.debug("Failed to parse embedding: %s", s)
                return None

    return None


def run_topic_segmentation(
    input_csv: str,
    output_csv: str,
    distance_threshold: float = 1.2,
    n_clusters: Optional[int] = None,
    normalize: bool = True,
):
    """Groups sentence embeddings into topics and saves CSV with a `topic_id` column.

    Parameters:
    - input_csv: path to CSV that contains an `embedding` column (JSON or Python list strings).
    - output_csv: destination path for CSV with added `topic_id` column.
    - distance_threshold: passed to AgglomerativeClustering when n_clusters is None.
    - n_clusters: if provided, will be used instead of distance_threshold.
    - normalize: whether to L2-normalize embeddings before clustering (recommended for cosine distance).

    Returns: path to written CSV
    """
    logger.info("Loading embeddings CSV: %s", input_csv)
    df = pd.read_csv(input_csv)

    if "embedding" not in df.columns:
        raise ValueError("Input CSV must contain an 'embedding' column")

    # Parse embeddings safely and drop rows that we cannot parse
    parsed = df["embedding"].apply(_parse_embedding)
    valid_mask = parsed.notna()

    if not valid_mask.any():
        raise ValueError("No valid embeddings found in input CSV")

    if valid_mask.all():
        logger.info("All rows contain embeddings (%d rows)", len(df))
    else:
        logger.warning("%d/%d rows have valid embeddings; dropping invalid rows", valid_mask.sum(), len(df))

    df_valid = df.loc[valid_mask].copy()
    embeddings = np.vstack(parsed[valid_mask].values)

    if normalize:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

    n_samples = embeddings.shape[0]
    if n_samples < 2:
        logger.info("Not enough samples for clustering (n=%d); assigning single topic 0", n_samples)
        df_valid["topic_id"] = 0
    else:
        logger.info("Running topic segmentation on %d samples", n_samples)
        kwargs = {"metric": "cosine", "linkage": "average"}
        if n_clusters is not None:
            kwargs["n_clusters"] = n_clusters
        else:
            kwargs["distance_threshold"] = distance_threshold
            kwargs["n_clusters"] = None

        clustering = AgglomerativeClustering(**kwargs)
        try:
            topic_ids = clustering.fit_predict(embeddings)
        except TypeError:
            # Older sklearn may use `affinity` instead of `metric` for some versions
            kwargs.pop("metric", None)
            kwargs["affinity"] = "cosine"
            clustering = AgglomerativeClustering(**kwargs)
            topic_ids = clustering.fit_predict(embeddings)

        df_valid["topic_id"] = topic_ids

    # Merge topic ids back into original dataframe, keeping invalid rows without topic_id
    df = df.merge(df_valid[["embedding", "topic_id"]], on="embedding", how="left")

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    n_topics = int(df_valid["topic_id"].nunique()) if "topic_id" in df_valid.columns else 0
    logger.info("Topic segmentation complete: %d topics; saved to %s", n_topics, output_csv)

    return str(output_csv)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run topic segmentation on embeddings CSV")
    ap.add_argument("input_csv", help="CSV with an 'embedding' column (JSON or Python list strings)")
    ap.add_argument("output_csv", help="Destination CSV to write with 'topic_id' column")
    ap.add_argument("--distance-threshold", type=float, default=1.2)
    ap.add_argument("--n-clusters", type=int, default=None)
    args = ap.parse_args()

    run_topic_segmentation(args.input_csv, args.output_csv, distance_threshold=args.distance_threshold, n_clusters=args.n_clusters)
