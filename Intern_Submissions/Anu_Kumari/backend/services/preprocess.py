"""High-level preprocessing orchestration (robust).

This module wraps the chunk->metadata->transcribe->postprocess->embed steps with
safe error handling and logging so it is suitable to call as a background task
from `backend.main`.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

from backend.services.pipeline import (
    chunk_audio,
    create_metadata_csv,
    transcribe_chunks,
)
from backend.services.text_postprocess import postprocess_transcripts
from backend.services.embeddings import generate_embeddings
from backend.services.topic_segmentation import run_topic_segmentation
from backend.services.summarizer import generate_topic_summaries, generate_global_summary
from backend.services.topic_labeling import generate_topic_labels

logger = logging.getLogger(__name__)


def run_preprocessing(
    audio_path: str,
    *,
    fail_fast: bool = False,
    chunk_duration: int = 30,
    do_postprocess: bool = True,
    do_embeddings: bool = True,
    do_topic_steps: bool = True,
) -> Dict[str, Any]:
    """Run preprocessing for a single audio file safely.

    Returns a dict: {"status": "success"|"failed", "metadata_csv": str|None, "error": str|None}
    """
    audio_path_p = Path(audio_path)
    if not audio_path_p.exists():
        msg = f"Input audio file does not exist: {audio_path}"
        logger.error(msg)
        if fail_fast:
            raise FileNotFoundError(msg)
        return {"status": "failed", "error": msg, "metadata_csv": None}

    result: Dict[str, Any] = {"status": "failed", "error": None, "metadata_csv": None}

    try:
        logger.info("Chunking audio: %s (duration=%s)", audio_path, chunk_duration)
        chunk_dir, durations = chunk_audio(str(audio_path_p), chunk_duration=chunk_duration)
    except Exception as exc:
        msg = f"Chunking failed: {exc}"
        logger.exception(msg)
        if fail_fast:
            raise
        result.update({"error": msg})
        return result

    try:
        logger.info("Creating metadata CSV")
        metadata_csv_path = create_metadata_csv(audio_path=str(audio_path_p), chunk_dir=chunk_dir, durations=durations)
        result["metadata_csv"] = str(metadata_csv_path)
    except Exception as exc:
        msg = f"Metadata CSV creation failed: {exc}"
        logger.exception(msg)
        if fail_fast:
            raise
        result.update({"error": msg})
        return result

    try:
        logger.info("Transcribing %s", metadata_csv_path)
        transcribe_chunks(str(metadata_csv_path))
    except Exception as exc:
        msg = f"Transcription failed: {exc}"
        logger.exception(msg)
        if fail_fast:
            raise
        result.update({"error": msg})

    if do_postprocess:
        try:
            logger.info("Postprocessing transcripts: %s", metadata_csv_path)
            postprocess_transcripts(str(metadata_csv_path))
        except Exception as exc:
            msg = f"Postprocessing failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

    if do_embeddings:
        try:
            logger.info("Generating embeddings: %s", metadata_csv_path)
            generate_embeddings(str(metadata_csv_path))
        except Exception as exc:
            msg = f"Embedding generation failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

    # Topic segmentation, summaries and labels (to feed frontend expectations)
    if do_topic_steps:
        try:
            # Determine processed directory from chunk dir
            processed_dir = Path(str(chunk_dir))
            topics_csv = processed_dir / "topics.csv"
            logger.info("Running topic segmentation -> %s", topics_csv)
            run_topic_segmentation(
                input_csv=str(metadata_csv_path),
                output_csv=str(topics_csv),
            )
        except Exception as exc:
            msg = f"Topic segmentation failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

        try:
            summaries_csv = processed_dir / "topic_summaries.csv"
            logger.info("Generating topic summaries -> %s", summaries_csv)
            generate_topic_summaries(
                input_csv=str(topics_csv),
                output_csv=str(summaries_csv),
            )
        except Exception as exc:
            msg = f"Topic summarization failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

        try:
            labels_csv = processed_dir / "topic_labels.csv"
            logger.info("Generating topic labels -> %s", labels_csv)
            generate_topic_labels(
                input_csv=str(topics_csv),
                output_csv=str(labels_csv),
            )
        except Exception as exc:
            msg = f"Topic labeling failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

        # Global summary (optional but nice to have)
        try:
            global_summary_txt = processed_dir / "global_summary.txt"
            logger.info("Generating global summary -> %s", global_summary_txt)
            generate_global_summary(
                input_csv=str(topics_csv),
                output_txt=str(global_summary_txt),
            )
        except Exception as exc:
            msg = f"Global summarization failed: {exc}"
            logger.exception(msg)
            if fail_fast:
                raise
            result.update({"error": msg})

    result["status"] = "success"
    return result


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run preprocessing for an audio file")
    ap.add_argument("audio", help="Path to the audio file")
    ap.add_argument("--fail-fast", action="store_true", help="Raise on first error")

    args = ap.parse_args()
    print(run_preprocessing(args.audio, fail_fast=args.fail_fast))
