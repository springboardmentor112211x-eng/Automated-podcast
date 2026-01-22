import os
import json
import streamlit as st

st.set_page_config(page_title="Audio Analysis Dashboard", layout="wide")

st.title("🎙️ Automated Podcast Transcription & Topic Segmentation")
st.subheader("Audio Analysis")

# --------- Helper functions ----------
def load_text_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --------- Sidebar ----------
st.sidebar.header(" Navigation")
section = st.sidebar.radio("Go to", ["Overview", "Transcript", "Topics & Summaries", "Download Outputs"])

# --------- Files present ----------
transcript_path = "full_transcript.txt"
cleaned_path = "cleaned_transcript.txt"
topics_json_path = "final_topics_output.json"

full_transcript = load_text_file(transcript_path)
cleaned_transcript = load_text_file(cleaned_path)
topics_data = load_json(topics_json_path)

# --------- Overview ----------
if section == "Overview":
    st.info("✅ This dashboard shows transcript, topics, labels, and summaries generated from podcast/TED audio.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Transcript Available", "Yes" if len(full_transcript) > 0 else "No")
    col2.metric("Cleaned Transcript Available", "Yes" if len(cleaned_transcript) > 0 else "No")
    col3.metric("Topics JSON Available", "Yes" if topics_data else "No")

    st.markdown("### 📂 Current Project Files")
    st.write(os.listdir("."))

# --------- Transcript ----------
elif section == "Transcript":
    st.markdown("## 📝 Transcript Viewer")
    tab1, tab2 = st.tabs(["Full Transcript", "Cleaned Transcript"])

    with tab1:
        if len(full_transcript) == 0:
            st.warning("full_transcript.txt not found.")
        else:
            st.text_area("Full Transcript", full_transcript, height=450)

    with tab2:
        if len(cleaned_transcript) == 0:
            st.warning("cleaned_transcript.txt not found.")
        else:
            st.text_area("Cleaned Transcript", cleaned_transcript, height=450)

# --------- Topics ----------
elif section == "Topics & Summaries":
    st.markdown("## 🧩 Topics & Summaries")

    if not topics_data:
        st.error("final_topics_output.json not found. Please generate topics first.")
    else:
        total_topics = topics_data.get("total_topics", 0)
        topics = topics_data.get("topics", [])

        st.success(f"✅ Total Topics: {total_topics}")

        # Search filter
        query = st.text_input("🔎 Search in topic labels / summaries", "")

        for t in topics:
            label = t.get("topic_label", f"Topic {t.get('topic_id')}")
            summary = t.get("summary", "")
            text = t.get("text", "")

            searchable = (label + " " + summary + " " + text).lower()
            if query.strip() and query.lower() not in searchable:
                continue

            with st.expander(f"📌 Topic {t.get('topic_id')} — {label}", expanded=False):
                c1, c2 = st.columns([1, 1])

                with c1:
                    st.markdown("### ✅ Summary")
                    st.write(summary if summary else "(No summary found)")

                with c2:
                    st.markdown("### 📄 Topic Text")
                    st.write(text[:2500] + ("..." if len(text) > 2500 else ""))

# --------- Download ----------
elif section == "Download Outputs":
    st.markdown("## ⬇️ Download Outputs")

    if os.path.exists(topics_json_path):
        with open(topics_json_path, "rb") as f:
            st.download_button("Download Topics JSON", f, file_name="final_topics_output.json")

    if os.path.exists(transcript_path):
        with open(transcript_path, "rb") as f:
            st.download_button("Download Full Transcript", f, file_name="full_transcript.txt")

    if os.path.exists(cleaned_path):
        with open(cleaned_path, "rb") as f:
            st.download_button("Download Cleaned Transcript", f, file_name="cleaned_transcript.txt")

    st.caption("")
