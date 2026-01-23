import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

# ---------------------------------
# Session State Initialization
# ---------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "data" not in st.session_state:
    st.session_state.data = None

if "processed" not in st.session_state:
    st.session_state.processed = False


# ---------------------------------
# Page Config (MUST BE FIRST STREAMLIT CALL)
# ---------------------------------
st.set_page_config(
    page_title="PodC",
    layout="centered"
)

# ---------------------------------
# Theme Toggle (STABLE)
# ---------------------------------
dark_mode = st.toggle(
    "🌙 Dark Mode",
    value=st.session_state.theme == "dark"
)

st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

# ---------------------------------
# Dynamic CSS
# ---------------------------------
if theme == "dark":
    bg_color = "#0e1117"
    text_color = "#ffffff"
    sub_color = "#c7c7c7"
    label_color = "#ffffff"
    button_bg = "#111827"
else:
    bg_color = "#ffffff"
    text_color = "#111111"
    sub_color = "#444444"
    label_color = "#111111"
    button_bg = "#111827"  # keep buttons dark for contrast

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');

    html, body, [class*="stApp"] {{
        background-color: {bg_color};
        color: {text_color};
    }}

    label {{
        color: {label_color} !important;
    }}

    .stButton button {{
        background-color: {button_bg};
        color: white !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }}

    .podc-title {{
        font-family: 'Pacifico', cursive;
        font-size: 96px;
        text-align: center;
        margin-bottom: -20px;
        color: {text_color};
    }}

    .podc-subtitle {{
        font-size: 28px;
        text-align: center;
        color: {sub_color};
        margin-bottom: 30px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------
# Header
# ---------------------------------
st.markdown('<div class="podc-title">PodC</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="podc-subtitle">The Automated Podcast Analyzer</div>',
    unsafe_allow_html=True
)

st.divider()

# ---------------------------------
# File Upload
# ---------------------------------
uploaded_file = st.file_uploader(
    "Upload a podcast audio file",
    type=["mp3", "wav", "m4a"]
)

if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

# ---------------------------------
# Process Podcast
# ---------------------------------
if st.session_state.uploaded_file and st.button("Process Podcast"):
    with st.spinner("Processing podcast..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/process",
                files={
                    "file": (
                        st.session_state.uploaded_file.name,
                        st.session_state.uploaded_file.getvalue(),
                        st.session_state.uploaded_file.type
                    )
                },
                timeout=900
            )
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Backend not reachable: {e}")
            st.stop()

    if res.status_code != 200:
        st.error("❌ Backend error while processing podcast")
        st.text(res.text)
        st.stop()

    st.session_state.data = res.json()
    st.session_state.processed = True
    st.success("✅ Podcast processed successfully!")

# ---------------------------------
# Render Results
# ---------------------------------
data = st.session_state.data

if data:
    # Episode Summary
    if data.get("episode_summary"):
        st.divider()
        st.subheader("🧠 Episode Summary")
        st.write(data["episode_summary"])

    # Topics
    if isinstance(data.get("topics"), list):
        st.divider()
        st.subheader("🧩 Topics")

        for idx, topic in enumerate(data["topics"], 1):
            st.markdown(f"### 🧩 Topic {idx}: {topic.get('title', 'Untitled')}")

            if topic.get("text"):
                st.write(topic["text"])

            if topic.get("summary"):
                st.caption(f"📝 **Summary:** {topic['summary']}")

            if "start" in topic and "end" in topic:
                st.caption(f"⏱ {topic['start']}s → {topic['end']}s")

            reviewed = st.checkbox(
                f"Mark Topic {idx} as reviewed",
                key=f"review_{idx}"
            )

            if reviewed:
                st.caption("✅ Reviewed by human")

# ---------------------------------
# Download PDF (ONLY AFTER PROCESSING)
# ---------------------------------
if st.session_state.processed:
    st.divider()
    if st.button("📄 Download Summary as PDF"):
        try:
            res = requests.post(f"{BACKEND_URL}/download-pdf", timeout=120)

            if res.status_code == 200:
                st.download_button(
                    label="⬇️ Click to download PDF",
                    data=res.content,
                    file_name="podc_summary.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Failed to generate PDF")
                st.text(res.text)

        except Exception as e:
            st.error(str(e))

# ---------------------------------
# Safety Notice
# ---------------------------------
st.info(
    "ℹ️ These topics and summaries are AI-generated. "
    "Please review them for accuracy before relying on them."
)

# ---------------------------------
# Q&A Section
# ---------------------------------
st.divider()
st.subheader("❓ Ask a question about the podcast")

question = st.text_input(
    "Your question",
    disabled=not st.session_state.processed
)

if question and st.button("Ask"):
    with st.spinner("Thinking..."):
        try:
            res = requests.get(
                f"{BACKEND_URL}/ask",
                params={"question": question},
                timeout=60
            )

            if res.status_code != 200:
                st.error("Backend error while answering")
                st.text(res.text)
            else:
                answer_data = res.json()
                st.success("✅ Answer")
                st.write(answer_data.get("answer", "No answer"))

        except Exception as e:
            st.error(str(e))
