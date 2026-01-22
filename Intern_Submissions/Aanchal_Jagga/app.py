import streamlit as st
import os
import time
import json
import torch

from transcriber import get_transcriber
from utils import chunk_audio, cleanup_chunks
from segmenter import topic_segmentation
from genai_insights import generate_summary
from safety import safety_check
from search_engine import SemanticSearchEngine

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Automated Podcast Platform", page_icon="🎙️")

st.title("🎙️ GenAI Podcast Platform (ASR + Topics + Search + Q&A)")
st.markdown("""
This platform performs:
- **ASR transcription** (Whisper)
- **Topic segmentation**
- **Structured summaries**
- **Semantic search**
- **Q&A grounded in transcript**
- **Safety + human review flow**
- **Cost-aware local processing**
""")

# -----------------------------
# Initialize session state
# -----------------------------
if "processed" not in st.session_state:
    st.session_state.processed = False

if "topics" not in st.session_state:
    st.session_state.topics = None

if "summary" not in st.session_state:
    st.session_state.summary = None

if "safety" not in st.session_state:
    st.session_state.safety = None

if "transcript" not in st.session_state:
    st.session_state.transcript = ""

if "output_json" not in st.session_state:
    st.session_state.output_json = None

if "search_engine" not in st.session_state:
    st.session_state.search_engine = None

# -----------------------------
# Sidebar Settings
# -----------------------------
st.sidebar.header("⚙️ Settings")

has_gpu = torch.cuda.is_available()
device_name = "CUDA GPU" if has_gpu else "CPU"
st.sidebar.write(f"**Device Detected:** {device_name}")

model_size = st.sidebar.selectbox(
    "Select Whisper Model Size",
    ["tiny", "base", "small", "medium", "large"],
    index=1,
    help="tiny/base = fast, medium/large = high accuracy but slow on CPU"
)

if not has_gpu and model_size in ["medium", "large"]:
    st.sidebar.warning("⚠️ You are on CPU. Medium/Large models may take a long time.")

st.sidebar.markdown("---")
st.sidebar.caption("Tip: For deployment (Streamlit Cloud), prefer **tiny/base**.")

# -----------------------------
# Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload Podcast Audio", type=["mp3", "wav", "m4a", "flac","mpeg", "mpg"])

if uploaded_file:
    temp_filename = f"temp_{uploaded_file.name}"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("🚀 Process Podcast"):
        start_time = time.time()

        with st.status("Processing pipeline...", expanded=True) as status:
            st.write(f"🔄 Loading Whisper model: **{model_size}**")
            engine = get_transcriber(model_size)

            st.write("✂️ Chunking audio (Sliding window)...")
            chunks = chunk_audio(temp_filename)

            st.write("📝 Transcribing chunks...")
            full_transcript = []
            progress = st.progress(0)

            for i, chunk_path in enumerate(chunks):
                text = engine.transcribe_chunk(chunk_path)
                full_transcript.append(text)
                progress.progress((i + 1) / len(chunks))

            status.update(label="✅ Transcription Completed", state="complete", expanded=False)

        transcript = " ".join(full_transcript).strip()
        duration = round(time.time() - start_time, 2)

        topics = topic_segmentation(transcript)
        summary = generate_summary(topics)
        safety = safety_check(transcript)

        confidence_score = 0.85 if len(transcript) > 150 else 0.55
        cost_note = "Cost optimized: Local Whisper + chunking + TF-IDF search (no paid LLM APIs)"

        search_engine = SemanticSearchEngine(topics)

        output_json = {
            "metadata": {
                "model": model_size,
                "device": engine.device,
                "chunks_processed": len(chunks),
                "runtime_seconds": duration,
                "confidence_score": confidence_score,
                "safety": safety,
                "cost_awareness": cost_note
            },
            "transcript": transcript,
            "topics": topics,
            "summary": summary
        }

        os.makedirs("outputs", exist_ok=True)
        with open("outputs/result.json", "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)

        # ✅ Store everything in session_state so it doesn't vanish on rerun
        st.session_state.processed = True
        st.session_state.transcript = transcript
        st.session_state.topics = topics
        st.session_state.summary = summary
        st.session_state.safety = safety
        st.session_state.output_json = output_json
        st.session_state.search_engine = search_engine

        st.success(f"✅ Completed in {duration} seconds")

        cleanup_chunks(chunks)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# -----------------------------
# Display results (persisted)
# -----------------------------
if st.session_state.processed:

    transcript = st.session_state.transcript
    topics = st.session_state.topics
    summary = st.session_state.summary
    safety = st.session_state.safety
    output_json = st.session_state.output_json
    search_engine = st.session_state.search_engine

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📜 Transcript")
        st.text_area("Transcript Output", transcript, height=350)
        st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")

    with col2:
        st.subheader("🧾 Logs")
        st.json({
            "Model": output_json["metadata"]["model"],
            "Device": output_json["metadata"]["device"],
            "Chunks": output_json["metadata"]["chunks_processed"],
            "Confidence": output_json["metadata"]["confidence_score"],
            "Safety_Action": safety["action"],
            "Cost": output_json["metadata"]["cost_awareness"]
        })

    st.subheader("📌 Topic Segments")
    for t in topics:
        with st.expander(f"Topic {t['topic_id']}: {t['title']}"):
            st.write(t["content"])

    st.subheader("✨ GenAI Insights")
    st.write("**Short Summary:**", summary["short_summary"])
    st.write("**Tags:**", ", ".join(summary["tags"]))
    st.write("**Bullet Summary:**")
    for b in summary["bullet_summary"]:
        st.write(b)

    st.subheader("🛡️ Safety & Human Review Flow")
    if not safety["is_safe"]:
        st.error("⚠️ Sensitive content detected → Human review required.")
        st.write("Flags:", safety["flags"])
    else:
        st.success("✅ Safe transcript → Auto-approved.")

    # ✅ Semantic Search (Now works after Enter)
    st.subheader("🔍 Semantic Search")
    query = st.text_input("Search inside the episode (example: AI, internship, business)", key="search_query")

    if query:
        results = search_engine.search(query, top_k=3)
        st.write("Top Matches:")
        st.json(results)

    # ✅ Q&A (Now works after Enter)
    st.subheader("❓ Q&A Over Episode")
    question = st.text_input("Ask a question (example: What is the main topic discussed?)", key="qa_question")

    if question:
        qa_result = search_engine.qa(question)
        st.write("Answer (Grounded):")
        st.write(qa_result["answer"])
        st.write("Retrieved Segment:")
        st.json(qa_result["best_topic"])

    st.download_button(
        "📥 Download Full Output JSON",
        data=json.dumps(output_json, indent=2, ensure_ascii=False),
        file_name="podcast_output.json",
        mime="application/json"
    )

else:
    st.info("Upload an audio file and click **Process Podcast** to generate transcript, topics, search and Q&A.")
