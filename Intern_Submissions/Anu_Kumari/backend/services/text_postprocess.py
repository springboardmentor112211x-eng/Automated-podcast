"""Text post-processing utilities.

This module provides a small, clear text cleaning function and a CSV post-processing
helper that adds a `clean_transcript` column while handling common edge cases
(such as "NA"/missing transcripts) and providing safer file output options.
"""

from typing import Optional, Sequence
import os
import shutil
import logging
import re

import pandas as pd


logger = logging.getLogger(__name__)


def clean_text(text: str, keep_apostrophe: bool = True, keep_hyphen: bool = True) -> str:
    """Normalize and clean a transcript string while preserving Unicode letters.

    - Lowercases text
    - Collapses repeated whitespace into a single space
    - Removes characters that are not letters/digits/allowed punctuation
    - Removes underscores and trims surrounding whitespace

    Parameters
    - text: input string
    - keep_apostrophe, keep_hyphen: whether to preserve ' and - characters
    """
    if not isinstance(text, str):
        return text

    # Basic normalization
    text = text.strip()
    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    # Build allowed character set using Unicode word characters (letters/digits/underscore)
    # and a small set of punctuation. We remove underscores afterwards.
    punct = r"\.,\?"
    if keep_apostrophe:
        punct += "'"
    if keep_hyphen:
        punct += r"\-"

    pattern = rf"[^\w\s{punct}]"
    text = re.sub(pattern, "", text, flags=re.UNICODE)

    # Remove underscores introduced by \w
    text = text.replace("_", "")

    # Remove spaces before punctuation (e.g., "word ," -> "word,")
    text = re.sub(r"\s+([.,?'\-])", r"\1", text)

    return text.strip()


def postprocess_transcripts(
    metadata_csv_path: str,
    inplace: bool = True,
    output_path: Optional[str] = None,
    na_values: Optional[Sequence[str]] = None,
    keep_apostrophe: bool = True,
    keep_hyphen: bool = True,
) -> str:
    """Read a metadata CSV, add a `clean_transcript` column, and write the result.

    Behavior notes:
    - Common NA tokens (e.g., "NA", "N/A") are treated as missing and left as NaN in
      `clean_transcript`.
    - If `inplace` is True a backup copy of the original CSV is created with a
      `.bak` suffix before overwriting.
    - If `output_path` is provided it is used as the destination regardless of
      `inplace`.

    Returns the path to the written CSV file.
    """
    if na_values is None:
        na_values = ["NA", "N/A", "na", "n/a", ""]

    df = pd.read_csv(metadata_csv_path, na_values=na_values, keep_default_na=True)

    if "transcript" not in df.columns:
        raise ValueError("CSV must contain a 'transcript' column")

    # Initialize clean_transcript with missing values and only process present transcripts
    df["clean_transcript"] = pd.NA

    mask = df["transcript"].notna()
    if mask.any():
        df.loc[mask, "clean_transcript"] = (
            df.loc[mask, "transcript"].astype(str).apply(
                lambda t: clean_text(t, keep_apostrophe=keep_apostrophe, keep_hyphen=keep_hyphen)
            )
        )

    # Decide output location
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
    logger.info("Text post-processing completed. Output saved to %s", out_path)

    return out_path


if __name__ == "__main__":
    # Minimal CLI for convenience
    import argparse

    ap = argparse.ArgumentParser(description="Postprocess transcripts in a metadata CSV")
    ap.add_argument("csv", help="Path to the metadata CSV")
    ap.add_argument("--no-inplace", dest="inplace", action="store_false", help="Do not overwrite the input file")
    args = ap.parse_args()

    postprocess_transcripts(args.csv, inplace=args.inplace)
