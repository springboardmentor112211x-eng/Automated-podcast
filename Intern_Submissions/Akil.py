import streamlit as st
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
import chromadb
import os
import re
from datetime import datetime

st.set_page_config(page_title="Podcast Knowledge Extractor", layout="wide")

# Configuration
MODEL_SIZE = "distil-large-v3"          # change to "large-v3" for significantly better quality
DEVICE = "cuda" if os.path.exists("/usr/local/cuda") else "cpu"
MAX_MINUTES = 60
SENTENCES_PER_CHUNK = 12                # how many sentences per segment

@st.cache_resource
def load_components():
    whisper = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type="int8" if DEVICE == "cpu" else "float16"
    )
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="./podcast_db")
    collection = client.get_or_create_collection("segments")
    return whisper, embedder, collection

whisper, embedder, collection = load_components()

st.title("Podcast → Full Transcription + Segments + Search")
st.caption(f"Max {MAX_MINUTES} minutes • Local processing • Full text everywhere")

uploaded = st.file_uploader("Upload podcast (mp3/wav/m4a)", type=["mp3", "wav", "m4a"])

if uploaded:
    st.audio(uploaded)
    
    if st.button("Process Podcast", type="primary"):
        with st.spinner("Transcribing and segmenting audio..."):
            save_path = f"temp_{uploaded.name}"
            with open(save_path, "wb") as f:
                f.write(uploaded.getvalue())

            try:
                # Transcription
                segments_gen, info = whisper.transcribe(
                    save_path,
                    language="en",
                    vad_filter=True,
                    beam_size=5
                )

                segments = list(segments_gen)

                duration_min = info.duration / 60
                if duration_min > MAX_MINUTES:
                    st.error(f"Audio is too long ({duration_min:.1f} min). Maximum allowed: {MAX_MINUTES} min.")
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    st.stop()

                # Full continuous text
                full_text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())

                if not full_text.strip():
                    st.error("No speech detected in the audio.")
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    st.stop()

                # Split into sentences for chunking
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_text) if s.strip()]

                knowledge_items = []

                for i in range(0, len(sentences), SENTENCES_PER_CHUNK):
                    chunk_sentences = sentences[i:i + SENTENCES_PER_CHUNK]
                    segment_full_text = " ".join(chunk_sentences)

                    start_time = segments[i].start if i < len(segments) else 0.0
                    
                    # Summary = first sentence only (still useful for titles)
                    summary = chunk_sentences[0] if chunk_sentences else ""

                    embedding = embedder.encode(segment_full_text).tolist()

                    doc_id = f"{uploaded.name}_{i:04d}"

                    collection.upsert(
                        ids=[doc_id],
                        embeddings=[embedding],
                        documents=[segment_full_text],
                        metadatas=[{
                            "episode": uploaded.name,
                            "part": i//SENTENCES_PER_CHUNK + 1,
                            "summary": summary,
                            "time_start": start_time,
                            "processed": datetime.now().isoformat()
                        }]
                    )

                    knowledge_items.append({
                        "part": i//SENTENCES_PER_CHUNK + 1,
                        "summary": summary,
                        "full_text": segment_full_text,
                        "start_time": start_time
                    })

                st.success(f"Done! • {len(knowledge_items)} segments • {duration_min:.1f} minutes")

                # ── TABS ─────────────────────────────────────────────────────
                tab1, tab2, tab3 = st.tabs([
                    "📜 Full Transcription",
                    "📋 Segment Summaries",
                    "🔍 Full Segments"
                ])

                with tab1:
                    st.markdown("### Complete Episode Transcription")
                    st.text_area(
                        "Full continuous transcript",
                        value=full_text,
                        height=550,
                        disabled=True
                    )

                with tab2:
                    st.markdown("### Segment Summaries (first sentence only)")
                    for item in knowledge_items:
                        st.subheader(f"Part {item['part']}  (~{item['start_time']:.0f}s)")
                        st.markdown(item["summary"])
                        st.markdown("---")

                with tab3:
                    st.markdown("### Segments – Complete Text")
                    for item in knowledge_items:
                        with st.expander(f"Part {item['part']}  •  {item['start_time']:.0f}s"):
                            st.markdown("**Full transcription of this segment:**")
                            st.markdown(item["full_text"])
                            st.caption(f"Approximate start time: {item['start_time']:.1f} seconds")

                # ── Search ───────────────────────────────────────────────────
                st.subheader("Search inside the episode")
                query = st.text_input("Keyword or question...")
                if query:
                    q_emb = embedder.encode(query).tolist()
                    hits = collection.query(
                        query_embeddings=[q_emb],
                        n_results=5,
                        where={"episode": uploaded.name}
                    )

                    if hits['documents'][0]:
                        for doc, meta, dist in zip(hits['documents'][0], hits['metadatas'][0], hits['distances'][0]):
                            st.markdown(f"**Part {meta['part']}**  ·  similarity: {1-dist:.3f}")
                            st.markdown(doc)
                            st.caption(f"First sentence: {meta['summary']}")
                            st.markdown("---")
                    else:
                        st.info("No relevant segments found.")

                if os.path.exists(save_path):
                    os.remove(save_path)

            except Exception as e:
                st.error(f"Processing failed: {str(e)}")
                if os.path.exists(save_path):
                    os.remove(save_path)

st.caption("Dependencies: faster-whisper • sentence-transformers • chromadb • streamlit")