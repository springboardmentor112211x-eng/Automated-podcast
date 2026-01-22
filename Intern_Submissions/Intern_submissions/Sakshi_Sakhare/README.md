# 🎧 Audio Analysis Project – Automated Podcast Transcription & Topic Segmentation

## ✅ Problem Statement
Build an automated system that converts podcast/TED audio into structured, searchable, topic-wise knowledge using GenAI.

Core features implemented:
- Audio ingestion
- Transcription (Whisper)
- Topic segmentation
- GenAI-powered insights (topic labels + summaries)
- UI/dashboard + downloadable outputs

---

## 🚀 What I Built
An end-to-end pipeline that takes a long audio file and produces:
- Full transcript
- Topic-wise segmented transcript
- Topic labels (keywords)
- Topic summaries
- Downloadable JSON output
- Streamlit dashboard to view everything

---

## 🏗️ Architecture / Pipeline
Audio File  
→ Audio Preprocessing (mono, 16kHz WAV)  
→ Chunking (30 seconds chunks + overlap)  
→ Speech-to-Text using Faster-Whisper  
→ Transcript Cleaning + Sentence Tokenization  
→ Sentence Embeddings (Sentence Transformers - MiniLM)  
→ Topic Segmentation (cosine similarity + min topic length)  
→ Topic Labeling (TF-IDF keywords)  
→ Topic Summarization (Transformers Summarizer)  
→ Streamlit Dashboard (View + Download)

---

## 🧠 Tech Stack
- Python
- Google Colab
- yt-dlp (dataset/audio download)
- pydub (audio preprocessing + chunking)
- Faster-Whisper (Speech-to-Text)
- NLTK (sentence tokenization)
- sentence-transformers (MiniLM embeddings)
- scikit-learn (cosine similarity + TF-IDF)
- transformers (summarization)
- Streamlit (UI/dashboard)

---

## 📌 Topic Segmentation Logic
- Sentences are embedded using MiniLM
- Cosine similarity between consecutive sentences is computed
- A similarity drop below a threshold marks a topic boundary
- Minimum number of sentences per topic is enforced to avoid over-segmentation

✅ Final Result: **15 meaningful topics generated**

---

## 📂 Files Included
- `app.py` → Streamlit dashboard
- `requirements.txt` → Dependencies
- `Audio_Analysis.ipynb` → Colab notebook (full pipeline)
- `final_topics_output.json` → Topic-wise labeled summaries output
- `full_transcript.txt` → Full transcript
- `cleaned_transcript.txt` → Cleaned transcript
- `chunk_transcripts.json` → Chunk-wise transcript output

---

## ▶️ How to Run (Local)
1) Install dependencies
```bash
pip install -r requirements.txt
2) Start Streamlit app
streamlit run app.py
