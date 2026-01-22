import streamlit as st
import io
from audioload import AudioLoader
from audiopreprocessing import AudioPreprocessor
from transcription import Transcriber
from textpreprocessing import TextProcessor
from topicsegmentation import TopicSegmenter
from topiclabel import TopicLabeller
from summarization import Summarizer

# ---  MODEL CACHING ---
@st.cache_resource
def get_pipeline():
    """Load models once and keep them in RAM."""
    return {
        "loader": AudioLoader(),
        "preprocessor": AudioPreprocessor(),
        "transcriber": Transcriber(),
        "text_processor": TextProcessor(),
        "segmenter": TopicSegmenter(),
        "labeller": TopicLabeller(),
        "summarizer": Summarizer()
    }


pipeline = get_pipeline()


st.set_page_config(page_title="AI Audio Indexer", layout="centered", page_icon="🎙️")


if "final_results" not in st.session_state:
    st.session_state.final_results = None


st.title("🎙️ Automated Transcription & Topic Segmentation")
st.markdown("Upload your audio to generate a structured, searchable index with AI-generated titles and summaries.")


uploaded_file = st.file_uploader("Upload an MP3 or WAV file", type=["mp3", "wav"])

if uploaded_file:
    st.audio(uploaded_file)
    
    
    if st.button("🚀 Start Audio Analysis", use_container_width=True):
        
        st.session_state.final_results = None
        
        
        loader = pipeline["loader"]
        preprocessor = pipeline["preprocessor"]
        transcriber = pipeline["transcriber"]
        text_processor = pipeline["text_processor"]
        segmenter = pipeline["segmenter"]
        labeller = pipeline["labeller"]
        summarizer = pipeline["summarizer"]

        
        with st.status("Step 1: Preparing audio signal...", expanded=True) as status:
            audio_bytes = uploaded_file.read()
            audio, sr = loader.load(io.BytesIO(audio_bytes))
            audio, sr = preprocessor.preprocess(audio, sr)
            
            
            st.write("Step 2: Transcribing Audio Content...")
            chunks = transcriber.chunk_audio(audio, sr)
            sentence_objs = []
            
            p_bar = st.progress(0)
            for i, chunk in enumerate(chunks):
                current_offset = i * (30 - 5)
                _, objs = transcriber.transcribe(chunk, sr, offset=current_offset)
                sentence_objs.extend(objs)
                p_bar.progress((i + 1) / len(chunks))

            
            st.write("Step 3: Cleaning Text Overlaps...")
            sentences, times = text_processor.deduplicate(sentence_objs)

            
            st.write("Step 4: Grouping Topics...")
            segments, segment_times = segmenter.segment(sentences, times)

            
            st.write("Step 5: Generating AI Titles & Summaries...")
            final_output = []
            for i, seg in enumerate(segments):
                paragraph = " ".join(seg).strip()
                title, kws = labeller.label_topic(paragraph)
                summary = summarizer.summarize(paragraph)
                timestamp = f"{int(segment_times[i]//60):02d}:{int(segment_times[i]%60):02d}"
                
                final_output.append({
                    "timestamp": timestamp,
                    "title": title,
                    "summary": summary,
                    "segment": paragraph,
                    "kws": kws
                })
            
            st.session_state.final_results = final_output
            status.update(label="Analysis Complete!", state="complete", expanded=False)


if st.session_state.final_results:
    st.divider()
    
    
    report_text = f"ANALYSIS REPORT: {uploaded_file.name if uploaded_file else 'Audio'}\n" + "="*40 + "\n\n"
    for out in st.session_state.final_results:
        report_text += f"[{out['timestamp']}] {out['title'].upper()}\n"
        report_text += f"Keywords: {', '.join(out['kws'])}\n"
        report_text += f"Summary: {out['summary']}\n\n"
        report_text += f"{out['segment']}\n"
        report_text += "-"*40 + "\n\n"

    st.download_button(
        label="📥 Download Full Report (TXT)",
        data=report_text,
        file_name="audio_analysis_report.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.subheader("📄 Segmented Index")
    for out in st.session_state.final_results:
        with st.expander(f"**[{out['timestamp']}] {out['title']}**"):
            st.write(f"**Keywords:** {', '.join(out['kws'])}")
            st.info(f"**Summary:** {out['summary']}")
            st.markdown(f"*{out['segment']}*")