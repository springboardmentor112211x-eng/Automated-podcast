import streamlit as st
import numpy as np
import os
import io
import tempfile
import librosa
import librosa.display
import soundfile as sf
import matplotlib.pyplot as plt
import numpy as np
from model_pipeline import AudioPipeline

# Suppress Windows/Joblib/KMeans warnings
os.environ["LOKY_MAX_CPU_COUNT"] = "4" 
os.environ["OMP_NUM_THREADS"] = "1"

# Fix for NumPy 2.0 compat on Python 3.13
if not hasattr(np, 'NAN'):
    np.NAN = np.nan
    np.float_ = np.float64

st.set_page_config(page_title="Audio Analyzer", layout="wide")

st.title("Audio Analyzer")

st.markdown("""
<style>
.tooltip {
  position: relative;
  display: inline-block;
  cursor: help;
  border-bottom: 1px dotted #777; /* Visual cue */
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 250px;
  background-color: #333;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 10px;
  position: absolute;
  z-index: 1;
  bottom: 125%; /* Position above */
  left: 50%;
  margin-left: -125px; /* Center */
  opacity: 0;
  transition: opacity 0.3s;
  font-size: 0.85rem;
  font-weight: normal;
  box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}

/* Card Style for Results */
.result-card {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    transition: transform 0.2s;
}
.result-card:hover {
    background-color: rgba(255, 255, 255, 0.08);
}
.result-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-weight: bold;
    color: #e0e0e0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 5px;
}
.result-text {
    font-size: 16px;
    line-height: 1.6;
    color: #f0f0f0;
}
.highlight {
    color: #4CAF50;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
### About
This tool analyzes podcasts and audio discussions. Upload an MP3 or WAV file to get:
- Speaker-separated transcription with timestamps
- Topic segmentation
- Per-topic summaries
- Audio statistics and spectrogram
""")

# --- Sidebar / Controls ---
st.sidebar.header("Configuration")
diarization_model = st.sidebar.text_input("Diarization Model", "pyannote/speaker-diarization-3.1")
whisper_model = st.sidebar.text_input("Whisper Model", "openai/whisper-large-v3")
num_clusters = 8 # Default topics



# --- File Upload ---
uploaded_file = st.file_uploader("Upload Audio File", type=['mp3', 'wav'])

def render_tooltip(label, value, description):
    """
    Creates an HTML tooltip structure compatible with Streamlit's st.markdown.
    """
    html = f"""
    <div class="tooltip">
        <strong>{label}:</strong> {value}
        <span class="tooltiptext">{description}</span>
    </div>
    """
    return html

def get_pipeline():
    # Helper to load pipeline only once
    if 'pipeline' not in st.session_state:
        with st.spinner("Initializing AI Models (this may take a minute)..."):
            try:
                st.session_state.pipeline = AudioPipeline(
                    whisper_model=whisper_model, 
                    diarization_pipeline=diarization_model
                )
                st.success("Models loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load models: {e}")
                st.info("Ensure you have a valid Hugging Face token set (huggingface-cli login) and PyTorch installed.")
                return None
    return st.session_state.pipeline

if uploaded_file is not None:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    st.session_state['file_path'] = tmp_file_path
    
    # --- Audio Details ---
    st.header("Audio Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("File Summary")
        try:
            info = sf.info(tmp_file_path)
            
            st.markdown(render_tooltip("Channels", info.channels, 
                "The number of independent audio streams. '1' means Mono (sound comes from one direction), '2' means Stereo (sound has left and right depth)."), unsafe_allow_html=True)
            
            st.markdown(render_tooltip("Sample Rate", f"{info.samplerate} Hz", 
                "How many snapshots of sound are taken per second. Higher values (like 44100 Hz) mean clearer, higher-quality audio, similar to high-resolution video."), unsafe_allow_html=True)
            
            st.markdown(render_tooltip("Duration", f"{info.duration:.2f} s", 
                "The total length of the audio recording in seconds."), unsafe_allow_html=True)
            
            st.markdown(render_tooltip("Format", info.format, 
                "The type of digital container used to store the audio, like MP3 (compressed) or WAV (high quality)."), unsafe_allow_html=True)
            
            st.markdown(render_tooltip("Subtype", info.subtype, 
                "The specific encoding method used within the file format, allowing for different quality or compression levels."), unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Could not read file info: {e}")

    # Load for detailed metrics (using librosa) - Cached via Session State
    if 'audio_data' not in st.session_state or st.session_state.get('audio_file_path') != tmp_file_path:
        with st.spinner("Analyzing Audio Characteristics..."):
            y, sr = librosa.load(tmp_file_path, sr=None)
            
            # Generate Spectrogram Figure
            fig, ax = plt.subplots(figsize=(10, 3))
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
            S_dB = librosa.power_to_db(S, ref=np.max)
            img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax)
            fig.colorbar(img, ax=ax, format='%+2.0f dB')
            ax.set_title('Mel-frequency spectrogram')
            
            # Save to buffer for download
            buf = io.BytesIO()
            fig.savefig(buf, format="pdf", bbox_inches='tight')
            buf.seek(0)
            
            st.session_state['audio_data'] = {
                'y': y,
                'sr': sr,
                'fig': fig,
                'buf': buf
            }
            st.session_state['audio_file_path'] = tmp_file_path

    # Retrieve from cache
    audio_data = st.session_state['audio_data']
    y = audio_data['y']
    sr = audio_data['sr']
    fig = audio_data['fig']
    buf = audio_data['buf'] 
    
    with col2:
        st.subheader("Audio Details")
        st.markdown(render_tooltip("Samples Read", len(y), 
            "The total number of individual data points processed. Think of this as the number of 'frames' in the audio file."), unsafe_allow_html=True)
            
        st.markdown(render_tooltip("Max Amplitude", f"{np.max(np.abs(y)):.4f}", 
            "The loudest single moment in the audio. A value close to 1.0 is maximum loudness; near 0 is silent."), unsafe_allow_html=True)
            
        st.markdown(render_tooltip("RMS Amplitude", f"{np.sqrt(np.mean(y**2)):.4f}", 
            "Root Mean Square Amplitude: The average 'loudness' level you actually perceive throughout the recording."), unsafe_allow_html=True)
            
        st.markdown(render_tooltip("DC Offset", f"{np.mean(y):.6f}", 
            "A technical measurement of the audio signal's center. It should be perfectly zero; significantly non-zero values indicate a recording quality issue."), unsafe_allow_html=True)

    # Spectrogram
    st.markdown(f"""
    <div class="tooltip">
        <h3>Mel Spectrogram</h3>
        <span class="tooltiptext">A visual map of the audio's frequencies over time. The x-axis is time, the y-axis is pitch (frequency), and brighter colors represent louder sounds.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.pyplot(fig)
    
    st.download_button(
        label="Download Spectrogram (PDF)",
        data=buf,
        file_name="mel_spectrogram.pdf",
        mime="application/pdf"
    )

    # --- Pipeline Execution ---
    st.header("AI Processing")
    
    if st.button("Run Analysis Pipeline"):
        pipeline = get_pipeline()
        if pipeline:
            try:
                # 1. Load & Process
                with st.spinner("Preprocessing Audio..."):
                    pipeline.load_audio(tmp_file_path)
                
                # 2. Diarization
                with st.spinner("Running Speaker Diarization..."):
                    pipeline.diarize() 
                
                # 3. Transcription
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total):
                    progress = float(current) / float(total)
                    progress_bar.progress(progress)
                    status_text.text(f"Transcribing segment {current}/{total}...")

                with st.spinner("Transcribing & Translating..."):
                    pipeline.transcribe_translate(progress_callback=update_progress)
                
                status_text.empty()
                progress_bar.empty()
                
                # 4. Segmentation
                with st.spinner("Segmenting Topics..."):
                    pipeline.segment_topics(num_clusters=num_clusters)
                
                # 5. Summarization
                with st.spinner("Generating Summaries..."):
                    summaries = pipeline.summarize_segments()
                
                st.session_state['results'] = {
                    "transcription": pipeline.transcription_result,
                    "topics": pipeline.topic_segments,
                    "summaries": summaries
                }
                st.success("Analysis Complete!")
                
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")



    # --- Helper Functions ---
    def render_paginated_list(data, unique_key, render_item_func, items_per_page=10):
        """
        Renders a list of items with pagination controls.
        """
        if f'page_{unique_key}' not in st.session_state:
            st.session_state[f'page_{unique_key}'] = 0
        
        page = st.session_state[f'page_{unique_key}']
        total_pages = (len(data) - 1) // items_per_page + 1
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_items = data[start_idx:end_idx]
        
        # Render items
        for item in current_items:
            render_item_func(item)
            
        # Pagination Controls
        if total_pages > 1:
            c1, c2, c3 = st.columns([1, 8, 1])
            with c1:
                if st.button("Previous", key=f"prev_{unique_key}"):
                    if page > 0:
                        st.session_state[f'page_{unique_key}'] -= 1
                        st.rerun()
            with c3:
                if st.button("Next", key=f"next_{unique_key}"):
                    if page < total_pages - 1:
                        st.session_state[f'page_{unique_key}'] += 1
                        st.rerun()
            with c2:
                st.write(f"Page {page + 1} of {total_pages}")

    def format_transcription(data):
        text = ""
        for seg in data:
            start = f"{seg['start']:.1f}s"
            end = f"{seg['end']:.1f}s"
            text += f"[{start} - {end}] {seg['speaker']}: {seg['text']}\n"
        return text

    def format_topics(data):
        text = "Topic ID | Start | End | Content\n"
        text += "-" * 50 + "\n"
        for seg in data:
             text += f"{seg['topic_id'] + 1} | {seg['start']:.1f}s | {seg['end']:.1f}s | {seg['text']}\n"
        return text

    def format_summaries(data):
        text = ""
        for item in data:
            topic_name = item.get('topic_name', f"Topic {item['topic_id'] + 1}")
            text += f"### {topic_name} ({item['start']:.1f}s - {item['end']:.1f}s)\n"
            text += f"{item['summary']}\n\n"
        return text

    # --- Display Results ---
    if 'results' in st.session_state:
        results = st.session_state['results']
        
        tab1, tab2, tab3 = st.tabs(["Full Transcription", "Topic Segments", "Summaries"])
        
        with tab1:
            st.subheader("Full Transcription")
            
            # Download Button
            txt_data = format_transcription(results["transcription"])
            st.download_button("Download Transcription (.txt)", txt_data, file_name="transcription.txt", mime="text/plain")
            
            def render_transcription_item(seg):
                start = f"{seg['start']:.1f}s"
                end = f"{seg['end']:.1f}s"
                speaker = seg['speaker']
                text = seg['text']
                
                html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="highlight">{speaker}</span>
                        <span>{start} - {end}</span>
                    </div>
                    <div class="result-text">{text}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

            render_paginated_list(results["transcription"], "transcription_tab", render_transcription_item)

        with tab2:
            st.subheader("Topic Segments")
            
            # Download Button
            txt_topics = format_topics(results["topics"])
            st.download_button("Download Topics (.txt)", txt_topics, file_name="topic_segments.txt", mime="text/plain")

            # Wrapper for paginated list
            def render_topic_item(seg):
                topic_id = seg['topic_id']
                start = f"{seg['start']:.1f}s"
                end = f"{seg['end']:.1f}s"
                text = seg['text']
                
                html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="highlight">Topic {topic_id + 1}</span>
                        <span>{start} - {end}</span>
                    </div>
                    <div class="result-text">{text}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

            render_paginated_list(results["topics"], "topics_tab", render_topic_item)


        with tab3:
            st.subheader("Topic Summaries")
            
            # Download Button
            txt_summaries = format_summaries(results["summaries"])
            st.download_button("Download Summaries (.txt)", txt_summaries, file_name="summaries.txt", mime="text/plain")

            def render_summary_item(item):
                topic_id = item['topic_id']
                topic_name = item.get('topic_name', f"Topic {topic_id + 1}")
                start = f"{item['start']:.1f}s"
                end = f"{item['end']:.1f}s"
                summary_text = item["summary"]
                
                html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="highlight">{topic_name}</span>
                        <span>{start} - {end}</span>
                    </div>
                    <div class="result-text">{summary_text}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
            
            render_paginated_list(results["summaries"], "summaries_tab", render_summary_item)

else:
    st.info("Please upload a file to begin.")
