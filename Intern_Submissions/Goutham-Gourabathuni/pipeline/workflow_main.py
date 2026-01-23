from pipeline.audio import normalize_audio
from pipeline.chunker import chunk_audio
from pipeline.asr import transcribe
from pipeline.summarizer import summarize_text
from pipeline.text_preprocessor import segment_into_sentences
from pipeline.embeddings import embed_sentences
from pipeline.topic_segmentation import (
    detect_topic_boundaries_embeddings,
    get_topic_segments
)
from pipeline.topic_titles import generate_titles


def estimate_confidence(text: str) -> str:
    """
    Simple heuristic confidence estimator.
    Explainable & cheap.
    """
    if not text or len(text.split()) < 30:
        return "low"
    if len(text.split()) < 80:
        return "medium"
    return "high"


def run_pipeline(audio_path):
    # 1️⃣ Audio preprocessing
    print("🎧 Normalizing audio...")
    normalized = normalize_audio(audio_path)
    print("✂️ Chunking audio...")
    chunks = chunk_audio(normalized)
    print(f"🔊 Total chunks created: {len(chunks)}")
    transcript = transcribe(chunks)
    print(f"📝 Transcript segments: {len(transcript)}")

    if not transcript:
        return {
            "transcript": [],
            "episode_summary": "",
            "topics": []
        }

    # Full transcript text (episode-level context)
    full_text = " ".join(seg.get("text", "") for seg in transcript).strip()
    print(f"🗒 Full transcript length: {len(full_text.split())} words")

    # 2️⃣ Episode summary (SAFE)
    episode_summary = summarize_text(
        full_text,
        max_length=120,
        min_length=60
    )

    if not episode_summary:
        episode_summary = full_text[:500]

    if len(full_text.split()) < 150:
        episode_summary = (
            "⚠️ Episode summary may be incomplete due to limited transcript length.\n\n"
            + episode_summary
        )
        
    print("🧾 Episode summary generated.")
    
    # 3️⃣ Sentence extraction
    sentences = segment_into_sentences(transcript)
    print(f"🧠 Sentences extracted: {len(sentences)}")

    if not sentences:
        return {
            "transcript": transcript,
            "episode_summary": episode_summary,
            "topics": []
        }

    # 4️⃣ Sentence embeddings
    embeddings = embed_sentences(sentences)
    print(f"📐 Embeddings generated: {len(embeddings)}")

    # 5️⃣ Topic boundary detection (CORRECT ARG)
    boundaries = detect_topic_boundaries_embeddings(
        embeddings=embeddings,
        similarity_threshold=0.65
    )
    print(f"🔖 Topic boundaries detected: {len(boundaries)}")

    # 6️⃣ Build topic segments
    segments = get_topic_segments(
        boundaries=boundaries,
        sentences=sentences
    )
    print(f"🗂 Topic segments created: {len(segments)}")

    # 7️⃣ Build topics with approximate timing
    topics = []

    total_duration = max(transcript[-1].get("end", 0.0), 0.0)
    total_sentences = max(len(sentences), 1)
    seconds_per_sentence = total_duration / total_sentences

    sentence_cursor = 0

    for i, seg in enumerate(segments, 1):
        sentence_count = seg["sentence_count"]

        start_time = round(sentence_cursor * seconds_per_sentence, 2)
        end_time = round(
            (sentence_cursor + sentence_count) * seconds_per_sentence, 2
        )

        topic_text = seg["text"].strip()

        topic = {
            "id": i,
            "text": topic_text,
            "summary": summarize_text(topic_text),
            "confidence": estimate_confidence(topic_text),
            "start": max(0.0, start_time),
            "end": min(max(end_time, start_time), total_duration)
        }

        topics.append(topic)
        sentence_cursor += sentence_count

    # 8️⃣ Generate titles AFTER topics exist
    topics = generate_titles(topics)
    print(f"🏷 Topic titles generated.")

    # 9️⃣ Safety: ensure every topic has a title
    for i, topic in enumerate(topics, 1):
        if not topic.get("title"):
            topic["title"] = f"Topic {i}"

    return {
        "transcript": transcript,
        "episode_summary": episode_summary,
        "topics": topics
    }
