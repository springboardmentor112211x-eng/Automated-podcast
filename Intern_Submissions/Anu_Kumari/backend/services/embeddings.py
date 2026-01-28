"""Utilities for generating and serializing embeddings for transcripts.

Key improvements:
- Lazy model loading (no heavy import-time work)
- Controlled encoding parameters (batch_size, progress bar)
- Safer CSV writing with backup or custom output path
- Serialize embeddings as compact JSON strings for robust round-trip
- Allows injecting a dummy model in tests
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from typing import Optional

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


_MODEL_CACHE: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    logger.info("Loading SentenceTransformer model '%s'", model_name)
    m = SentenceTransformer(model_name)
    _MODEL_CACHE[model_name] = m
    return m


def generate_embeddings(
    metadata_csv_path: str,
    inplace: bool = True,
    output_path: Optional[str] = None,
    model: Optional[SentenceTransformer] = None,
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    show_progress_bar: bool = False,
) -> str:
    """Generate embeddings for `clean_transcript` and save them in an `embedding` column.

    Parameters
    - metadata_csv_path: Path to input CSV
    - inplace: If True, overwrite input (a backup will be created). If False, write to a new file with `.clean` suffix unless `output_path` provided.
    - output_path: Optional explicit output path
    - model: Optional SentenceTransformer instance to use (useful for tests); if None, model_name is used to load one.
    - model_name: Name of the sentence-transformers model to load if `model` is None
    - batch_size: Batch size passed to `model.encode`
    - show_progress_bar: Passed to `model.encode`

    Returns the path to the written CSV file.
    """
    df = pd.read_csv(metadata_csv_path)

    if "clean_transcript" not in df.columns:
        logger.warning("Input CSV does not have 'clean_transcript' column. Filling with empty strings.")
        df["clean_transcript"] = ""

    texts = df["clean_transcript"].fillna("").astype(str).tolist()

    if model is None:
        model = _get_model(model_name)

    try:
        embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=show_progress_bar)
    except Exception as exc:  # keep narrow in real code but catch for safety here
        logger.exception("Failed to encode texts: %s", exc)
        raise

    # Ensure numpy array and float32 for compact serialization
    arr = np.asarray(embeddings, dtype=np.float32)

    # Convert each vector to a compact JSON string so CSV round-trips safely
    emb_json = [json.dumps(row.tolist(), separators=(",", ":")) for row in arr]

    df["embedding"] = emb_json

    # Decide output location and write safely
    if output_path:
        out_path = output_path
    elif inplace:
        backup_path = f"{metadata_csv_path}.bak"
        shutil.copyfile(metadata_csv_path, backup_path)
        out_path = metadata_csv_path
    else:
        base, ext = os.path.splitext(metadata_csv_path)
        out_path = f"{base}.clean{ext}"

    df.to_csv(out_path, index=False)
    logger.info("Embeddings generated and stored in %s", out_path)
    return out_path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Generate embeddings for transcripts in a CSV")
    ap.add_argument("csv", help="Path to metadata CSV")
    ap.add_argument("--no-inplace", dest="inplace", action="store_false", help="Do not overwrite the input file")
    ap.add_argument("--model", default="all-MiniLM-L6-v2", help="Model name to use")
    args = ap.parse_args()

    generate_embeddings(args.csv, inplace=args.inplace, model_name=args.model)
