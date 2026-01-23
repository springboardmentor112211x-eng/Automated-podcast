![PodC-banner](images/PodC%20-%20banner.png)

# PodC - The Automated Podcast Summarizer

## Problem

Podcasts are long, unstructured, and difficult to search or analyze.
Users often want summaries, topic-wise breakdowns, and answers to questions without listening to hours of audio.

This system solves that problem by:

- Automatically converting podcast audio into text
- Segmenting conversations into meaningful topics
- Generating summaries and insights using GenAI
- Enabling Q&A over the podcast content
- Exporting structured results as a PDF for offline use

The result is structured, searchable, topic-wise knowledge from raw audio.

---

## Architecture

PodC follows a modular, production-style GenAI pipeline:

1. Audio ingestion via Streamlit UI
2. Automatic Speech Recognition (Whisper)
3. Text cleaning & sentence segmentation
4. Sentence embedding using MiniLM
5. Topic boundary detection via cosine similarity
6. Topic grouping and enrichment
7. Topic summaries & episode-level summary
8. Optional Q&A using LLMs (Gemini / OpenAI)
9. PDF export for offline review

The system prioritizes explainability, cost-efficiency, and safety.

---

## Tech Stack

ASR
- OpenAI Whisper (via asr.py) for speech-to-text transcription

LLMs / GenAI
- Gemini 2.5 Flash (for Q&A over podcast context)
- HuggingFace BART (for episode-level summarization)
- Sentence-BERT (MiniLM) for embeddings & topic segmentation

ML / NLP
- Sentence embeddings (SentenceTransformers)
- Cosine similarity–based topic boundary detection
- TF-IDF + noun phrase extraction for topic titles

Backend
- FastAPI (REST APIs)
- Python modular pipeline design

UI
- Streamlit (interactive web app)
- Dark / Light mode toggle
- Human review controls

Other
- PDF generation (ReportLab)
- Environment variables via .env

| Component                   | Technology                       | Version / Model         |
| --------------------------- | -------------------------------- | ----------------------- |
| **Backend Framework**       | FastAPI                          | 0.128.0                 |
| **Frontend UI**             | Streamlit                        | 1.53.0                  |
| **ASR (Speech-to-Text)**    | OpenAI Whisper                   | base/latest - 20250625  |
| **Audio Processing**        | FFmpeg + Python                  | Latest                  |
| **Embeddings**              | Sentence-BERT                    | all-MiniLM-L6-v2        |
| **Topic Segmentation**      | Cosine Similarity (scikit-learn) | 1.8.0                   |
| **Text Processing**         | NLTK + spaCy                     | 3.9.2 + 3.8.11          |
| **Summarization (Episode)** | HuggingFace BART                 | facebook/bart-large-cnn |
| **Topic Title Generation**  | TF-IDF + spaCy noun chunks       | scikit-learn            |
| **Q&A / GenAI**             | Google Gemini                    | gemini-2.5-flash        |
| **PDF Export**              | ReportLab                        | 4.4.9                   |
| **ML Framework**            | PyTorch                          | 2.9.1                   |
| **Environment Management**  | python-dotenv                    | 1.2.1                   |

---

## Pipeline
```

Audio Upload
   ↓
Audio Normalization
   ↓
Chunking (long audio support)
   ↓
ASR (Whisper transcription)
   ↓
Text Cleaning & Sentence Extraction
   ↓
Sentence Embeddings
   ↓
Topic Boundary Detection
   ↓
Topic Segmentation
   ↓
Topic Titles + Summaries
   ↓
Episode-Level Summary
   ↓
Q&A + PDF Export

```
---

## Repo Structure
```

Intern_Submissions/
└── Goutham-Gourabathuni/
    ├── backend/
    │   └── main.py              # FastAPI entry point
    │
    ├── frontend/
    │   └── app.py               # Streamlit UI
    │
    ├── pipeline/
    │   ├── workflow_main.py     # Main pipeline orchestration
    │   ├── audio.py
    │   ├── chunker.py
    │   ├── asr.py
    │   ├── text_preprocessor.py
    │   ├── embeddings.py
    │   ├── topic_segmentation.py
    │   ├── topic_titles.py
    │   ├── summarizer.py
    │   ├── gemini_qa.py
    │   └── pdf_exporter.py
    │
    ├── media/
    │   ├── uploads/             # Uploaded audio
    │   ├── chunks/              # Audio chunks
    │   └── pdfs/                # Generated PDFs
    │
    ├── .env
    ├── requirements.txt
    ├── README.md
    └── demo.md

```
---

## Prompt Strategy

Q&A Prompt Design
- Strict system instruction to use ONLY podcast context
- Explicit refusal instruction if information is missing
- Clear separation between context and question

Example strategy:
- Prevent hallucinations by enforcing context-only answers
- Fallback responses for insufficient information
- No user input is executed as code (prompt-injection safe)

Summarization
- Uses deterministic summarization (do_sample=False)
- Length-controlled summaries to avoid verbose outputs

---

## Safety Handling

This system includes multiple safety mechanisms:

- Confidence scoring for topic reliability
- Fallback behavior when transcripts or context are insufficient
- Q&A disabled or constrained when context is weak
- Human review indicators in the UI
- No blind trust in LLM outputs

All AI-generated outputs are intended to assist, not replace, human judgment.

---

## Cost Optimization

1. Lazy loading of heavy models (BART, Sentence-BERT)
2. Embeddings computed once per episode, reused across steps
3. No vector database required (in-memory embeddings)
4. CPU-only inference (no GPU dependency)
5. LLM usage limited to:
    - Episode summary
    - Q&A only when user explicitly asks

This keeps inference cost low and predictable.

---

## Human-in-the-Loop

Human validation is built into the UI:

1. Each topic can be marked as reviewed
2. Confidence score shown per topic (low / medium / high)
3. Warning banner indicating AI-generated content
4. Designed so humans can:
    - Validate summaries
    - Correct topic titles
    - Decide trustworthiness before reuse

This matches production-grade AI safety expectations.

---

## Limitations & Future Work

Current limitations:
- Topic boundaries are heuristic-based and may over-segment long discussions
- Confidence scoring is heuristic, not probabilistic
- No persistent database for long-term storage
- Toggling the dark-mode and light-mode while processing the file is still causing bugs and issues. (Please don't toggle while processing for now)

Future improvements:
- Vector database for semantic search
- Topic merging using hierarchical clustering
- Explicit feedback loop for improving summaries
- Role-based human review workflow
- Enhanced professional UI/UX
- controlled bugging of features in UI

---

## How to Run

1️⃣ Clone the repository
```bash
git clone <your-fork-url>
cd Intern_Submissions/"your directory name"
```   

2️⃣ Create & activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

4️⃣ Set environment variables
```bash
GEMINI_API_KEY="your_gemini_api_key_here"
```

5️⃣ Start backend
```bash
uvicorn backend.main:app --reload
```

6️⃣ Start frontend
```bash
streamlit run frontend/app.py
```

Frontend runs at:
http://localhost:8501

---

## Demo

This is the repo where my code exists.

![Repo-structure](images/PodC-infy-Repo-structure.png)

---

This is the project location, where the files including frontend, backend, pipeline, etc. are present.

![Project-location](images/PodC-infy-project-location.png)

---

## 1. Open a split terminal for running Backend and Frontend simultaneously

![Split-terminal](images/PodC-infy-split-terminal.png)

---

## 2. Run Backend and Frontend

Type the backend command first. After it starts successfully, run the frontend command.

![Backend-Frontend-commands](images/PodC-infy-frontend-backend-commands.png)

---

## 3. Verify Backend Root Endpoint

Click on the backend uvicorn URL `http://127.0.0.1:8000`.

![BE-root](images/PodC-infy-BE-root.png)

---

### Health & Docs Endpoints

![Health-endpoint](images/PodC-infy-health-endpoint.png)

![Docs-endpoint](images/PodC-infy-BE-docs.png)

---

## 4. Frontend UI (Dark & Light Mode)

![Dark-mode-display](images/PodC-infy-FE.png)

![Light-mode-display](images/PodC-infy-FE-light.png)

---

### Full Web App UI

![Dark-mode-full-UI](images/PodC-infy-Full-UI.png)

![Light-mode-full-UI](images/PodC-infy-Full-UI-light.png)

---

## 5. Load Audio File

![Audio-loaded](images/PodC-infy-audio-loaded.png)

---

## 6. Process Podcast

![Process-podcast](images/PodC-infy-processing.png)

---

## 7. Backend Processing Logs

![BE](images/PodC-infy-backend-process.png)

![BE-1](images/PodC-infy-backend-process1.png)

![BE-2](images/PodC-infy-backend-process2.png)

---

## 8. Processing Successful

![Processing-successful](images/PodC-infy-processing-success.png)

---

## 9. Episode Summary

![Episode-summary](images/PodC-infy-whole-summary.png)

---

## 10. Topic Segmentation with Timestamps

![Segments](images/PodC-infy-different-topics.png)

---

## 11. Human-in-the-loop Review

![Humanized-review](images/PodC-infy-humanized-review1.png)

---

## 12. Download Transcript as PDF

![Download-pdf](images/PodC-infy-download-pdf-option.png)

---

## 13. Click to Download PDF

![click-to-download](images/PodC-infy-download-pdf.png)

---

## 14. Downloaded PDF Preview

![downloaded-pdf](images/PodC-infy-downloaded-pdf.png)

---

## 15. Podcast Q&A Interface

![chat-box](images/PodC-infy-QnA.png)

---

## 16. Ask Question Flow

![ask](images/PodC-infy-ask-option.png)

---

## 17. Answer Generated

![answer-generated](images/PodC-infy-answer-generated.png)

---

## 18. Backend API Call for Question

![api-call-question](images/PodC-infy-BE-request.png)

---
