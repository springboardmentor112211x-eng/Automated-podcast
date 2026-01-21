import numpy as np
from faster_whisper import WhisperModel

_model = None

def _get_model():
    global _model
    if _model is None:
        print("⏳ Loading Whisper model (this can take 1–2 minutes on CPU)...")
        _model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )
        print("✅ Whisper model loaded")
    return _model


def warmup_whisper():
    model = _get_model()
    dummy = np.zeros(16000 * 2, dtype=np.float32)
    list(model.transcribe(dummy))


def transcribe_chunks(chunks, sr):
    model = _get_model()
    segments = []
    offset = 0.0

    for idx, chunk in enumerate(chunks):
        results, info = model.transcribe(
            chunk,
            language="en",
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500
            }
        )

        max_end = 0.0
        for r in results:
            segments.append({
                "start": r.start + offset,
                "end": r.end + offset,
                "text": r.text.strip(),
                "confidence": round(r.avg_logprob, 3)
            })
            max_end = max(max_end, r.end)

        offset += max_end

    segments = deduplicate_segments(segments)
    return segments

def deduplicate_segments(segments, time_tol=0.3):
    """
    Remove duplicate ASR segments caused by overlapping chunks.
    """
    deduped = []

    for seg in segments:
        if not deduped:
            deduped.append(seg)
            continue

        last = deduped[-1]

        # Overlapping time + similar text
        if (
            abs(seg["start"] - last["start"]) < time_tol and
            seg["text"] == last["text"]
        ):
            continue

        deduped.append(seg)

    return deduped

def is_sentence_complete(text: str) -> bool:
    """
    Heuristic to detect sentence completion.
    """
    text = text.strip()
    if not text:
        return False
    return text.endswith((".", "?", "!", "…"))


def merge_asr_segments(
    segments,
    max_pause=1.2,          # tolerate natural pauses
    max_words=120,          # allow long coherent speech
    max_duration=60.0,      # hard safety cap
    min_duration=8.0        # drop junk segments
):
    """
    Merge Whisper ASR segments into long, coherent utterances.
    """
    if not segments:
        return []

    merged = []
    buffer = segments[0].copy()

    for seg in segments[1:]:
        pause = seg["start"] - buffer["end"]
        duration = buffer["end"] - buffer["start"]
        word_count = len(buffer["text"].split())

        can_merge = (
            pause <= max_pause
            and word_count < max_words
            and duration < max_duration
            and not is_sentence_complete(buffer["text"])
        )

        if can_merge:
            buffer["text"] += " " + seg["text"]
            buffer["end"] = seg["end"]
        else:
            # finalize buffer
            if duration >= min_duration:
                merged.append(buffer)

            buffer = seg.copy()

    # append last buffer
    if (buffer["end"] - buffer["start"]) >= min_duration:
        merged.append(buffer)

    print("ASR segments after merge:", len(merged))
    print("Avg segment length:",
      sum(seg["end"]-seg["start"] for seg in merged)/len(merged))
    return merged