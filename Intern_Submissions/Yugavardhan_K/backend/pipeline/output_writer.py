import os

def _fmt(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def write_transcript(transcript, out_dir):
    """
    Writes full transcript with timestamps
    """
    path = os.path.join(out_dir, "transcript.txt")
    with open(path, "w", encoding="utf-8") as f:
        for seg in transcript:
            start = _fmt(seg["start"])
            end = _fmt(seg["end"])
            speaker = seg.get("speaker", "SPEAKER")
            text = seg["text"]
            f.write(f"[{start} → {end}] {speaker}: {text}\n")
    return path


def write_topics_timeline(topics, out_dir):
    """
    Writes only topic titles + timestamps
    """
    path = os.path.join(out_dir, "topics_timeline.txt")
    with open(path, "w", encoding="utf-8") as f:
        for i, t in enumerate(topics, 1):
            f.write(
                f"{i}. {_fmt(t['start_time'])} → {_fmt(t['end_time'])}\n"
                f"   {t['title']}\n\n"
            )
    return path


def write_topics_with_summaries(topics, out_dir):
    """
    Writes topic titles + summaries + timestamps
    """
    path = os.path.join(out_dir, "topics_with_summaries.txt")
    with open(path, "w", encoding="utf-8") as f:
        for i, t in enumerate(topics, 1):
            f.write(
                f"{i}. {t['title']}\n"
                f"   Time: {_fmt(t['start_time'])} → {_fmt(t['end_time'])}\n"
                f"   Summary:\n{t['summary']}\n\n"
            )
    return path