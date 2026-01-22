import streamlit as st
import requests
import tempfile
import os

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Automated Podcast Transcription System",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Automated Podcast Transcription System")
st.markdown("""
Upload your **WAV or MP3 audio** and get an **automated transcription** with topic segmentation, 
timestamps, keywords, and summaries. Perfect for podcasts, lectures, or long-form audio.
""")

API_URL = "http://127.0.0.1:8000/api/transcribe/"

uploaded_file = st.file_uploader(
    "Upload Audio File (WAV / MP3)",
    type=["wav", "mp3"]
)

if uploaded_file:
    st.audio(uploaded_file)

    if st.button("🔍 Transcribe Podcast"):
        with st.spinner("Processing audio... This may take a few minutes for long files"):
            try:
                # Save to temp file
                suffix = os.path.splitext(uploaded_file.name)[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    temp_path = tmp.name

                # Send to backend
                with open(temp_path, "rb") as f:
                    response = requests.post(
                        API_URL,
                        files={"file": f},
                        timeout=None
                    )

                os.remove(temp_path)

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Transcription Completed")
                    st.subheader("📊 Topics & Timestamps")

                    # ----------------------------
                    # Table Headers
                    # ----------------------------
                    st.markdown("""
                        <style>
                        .topic-header {
                            font-size: 16px;
                            font-weight: bold;
                            background-color: #f0f2f6;
                            padding: 8px;
                            border-radius: 5px;
                        }
                        .topic-box {
                            border-left: 4px solid #4CAF50;
                            padding: 8px;
                            margin-bottom: 10px;
                            background-color: #fafafa;
                        }
                        .badge {
                            display:inline-block;
                            padding:2px 6px;
                            margin:2px;
                            font-size:12px;
                            font-weight:bold;
                            color:white;
                            background-color:#4CAF50;
                            border-radius:4px;
                        }
                        </style>
                    """, unsafe_allow_html=True)

                    for topic in data["topics"]:
                        with st.expander(f"⏱ {topic['start_time']}s – {topic['end_time']}s | Topic {topic['topic_id']} | {topic['title']}"):
                            st.markdown(f"**Start Time:** {topic['start_time']} s  |  **End Time:** {topic['end_time']} s  |  **Topic ID:** {topic['topic_id']}")
                            # Keywords badges
                            keywords = topic["keywords"].split(", ")
                            st.markdown(" ".join([f'<span class="badge">{k}</span>' for k in keywords]), unsafe_allow_html=True)
                            st.markdown("**Summary:**")
                            st.write(topic["summary"])
                            st.markdown("**Transcript:**")
                            st.write(topic["text"])

                else:
                    st.error("❌ Backend Error")
                    st.code(response.text)

            except Exception as e:
                st.error("Upload failed")
                st.exception(e)
