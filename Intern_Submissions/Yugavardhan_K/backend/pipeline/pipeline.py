import os

from pipeline.audio_loader import load_and_preprocess_audio
from pipeline.audio_chunker import chunk_audio
from pipeline.transcriber import transcribe_chunks
from pipeline.text_preprocessor import preprocess_transcript
from pipeline.topic_segment import TopicSegmenter
# from pipeline.summarize import summarize_topics
from pipeline.output_writer import (
    write_transcript,
    write_topics_timeline,
    write_topics_with_summaries
)
from pipeline.visualizations import plot_topic_timeline
# from pipeline.llm import get_llm   # or wherever your LLM loader is
# llm = get_llm()
llm = None  # TODO: implement LLM loader
# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _to_media_url(media_url, rel_path):
    base = (media_url or "/media/").rstrip("/")
    parts = str(rel_path).replace("\\", "/").split("/")
    parts = [p for p in parts if p and p != "."]
    return base + "/" + "/".join(parts)


def compute_accuracy(transcript, topics):
    """
    Simple coverage-based accuracy proxy.
    Stable, deterministic, no ML dependency.
    """
    if not transcript or not topics:
        return 0.0

    total_audio = transcript[-1]["end"]
    covered = sum(t["end_time"] - t["start_time"] for t in topics)

    coverage = min(covered / total_audio, 1.0)
    topic_penalty = min(len(topics) / 15, 1.0)  # podcasts ≈ 5–10 topics

    return round(coverage * (1 - topic_penalty), 2)


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def run_pipeline(
    audio_path,
    media_dir="media",
    media_url="/media/",
    progress_cb=None,
    job_id=None,
):
    def up(step, percent):
        if progress_cb:
            progress_cb(step, percent)

    # -------------------------------
    up("Loading audio", 10)
    audio, sr = load_and_preprocess_audio(audio_path)

    # -------------------------------
    up("Chunking audio", 25)
    chunks = chunk_audio(audio, sr)

    # -------------------------------
    up("Transcribing (ASR)", 40)
    transcript = transcribe_chunks(chunks, sr)

    if not transcript:
        raise RuntimeError("ASR produced empty transcript")

    # -------------------------------
    up("Preprocessing transcript", 55)
    sentences = preprocess_transcript(transcript)

    # -------------------------------
    up("Topic segmentation", 70)
    segmenter = TopicSegmenter(llm=llm)
    topics = segmenter.segment(sentences)
    if not topics:
        raise RuntimeError("No topics detected")

    required_keys = {"title", "summary", "start_time", "end_time"}
    missing = required_keys - topics[0].keys()
    if missing:
        raise RuntimeError(f"Topic generation failed, missing: {missing}")

    if not topics:
        raise RuntimeError("No topics detected")

     # HARD VALIDATION (prevents silent garbage)
    for t in topics:
        if "title" not in t:
            t["title"] = "Untitled Topic"
        if "summary" not in t:
            t["summary"] = t["text"][:500] + "..."

    # -------------------------------
    up("Saving outputs", 95)
    out_dir = os.path.join(media_dir, "outputs", str(job_id or "default"))
    os.makedirs(out_dir, exist_ok=True)

    write_transcript(transcript, out_dir)
    write_topics_timeline(topics, out_dir)
    write_topics_with_summaries(topics, out_dir)

    # -------------------------------
    timeline_path = os.path.join(out_dir, "timeline.png")
    try:
        plot_topic_timeline(topics, timeline_path)
    except Exception:
        timeline_path = None

    up("Done", 100)

    # -------------------------------
    accuracy = compute_accuracy(transcript, topics)

    # URLs
    audio_url = None
    timeline_url = None

    try:
        rel = os.path.relpath(audio_path, media_dir)
        if not rel.startswith(".."):
            audio_url = _to_media_url(media_url, rel)
    except Exception:
        pass

    try:
        if timeline_path:
            rel = os.path.relpath(timeline_path, media_dir)
            if not rel.startswith(".."):
                timeline_url = _to_media_url(media_url, rel)
    except Exception:
        pass

    return {
        "transcript": transcript,
        "topics": topics,
        "timeline_image": timeline_url,
        "audio_url": audio_url,
        "metrics": {"accuracy": accuracy},
    }