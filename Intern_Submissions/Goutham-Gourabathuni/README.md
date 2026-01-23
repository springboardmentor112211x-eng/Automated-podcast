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

![Repo-structure](Intern_Submissions/Goutham-Gourabathuni/images/PodC-infy-Repo-structure.png)

---

This is the project location, where are the files including frontend, backend, pipeline, etc are present. In which the main code is present.

![Project-location](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-project-location.png)

---

1. Open a split terminal for running Backend and Frontend simultaneously.

![Split-terminal](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-split-terminal.png)

---

2. Type the backend command first to initiate the backend. After it returns successful, Type the frontend command to initiate the frontend.

![Backend-Frontend-commands](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-frontend-backend-commands.png)

---

3. Click on the backend uvicorn URL http://127.0.0.1:8000 to verify the json format output.

![BE-root](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-BE-root.png)

---

Heath endpoint and Docs endpoint of backend

![Health-endpoint](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-health-endpoint.png)

![Docs-endpoint](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-BE-docs.png)

---

4. Frontend website display of dark-mode and light-mode

![Dark-mode-display](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-FE.png)

![Light-mode-display](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-FE-light.png)

---

Frontend Full WebAPP UI of dark-mode and light-mode

![Dark-mode-full-UI](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-Full-UI.png)

![Light-mode-full-UI](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-Full-UI-light.png)

---

5. Load Audio file

![Audio-loaded](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-audio-loaded.png)

---

6. Click on process podcast, to process the audio podcast file.

![Process-podcast](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-processing.png)

---

7. Come back to the code editor to witness the backend calls running in the terminal.

![BE](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-backend-process.png)

![BE-1](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-backend-process1.png)

![BE-2](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-backend-process2.png)

---

8. Once you receive the POST call in backend ("POST /process HTTP/1.1" 200 OK). You can go to the minimized WebAPP and see that the file got processed successfully.

![Processing-successful](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-processing-success.png)

---

9. You can see the Whole Summary of the podcast audio file in Episode-summary section.

![Episode-summary](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-whole-summary.png)

---

10. You can also read the segmented topics, which also have timestamps of the topics segmented.

![Segments](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-different-topics.png)

---

11. You can give your review on the segmented topic by ticking on the checkboxes below topics. The model will learn from it and tries to perform in a better way next time.

![Humanized-review](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-humanized-review1.png)

---

12. If you want to download the transcripted pdf, you can click on the "Download Summary as Pdf" button.

![Download-pdf](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-download-pdf-option.png)

---

13. After clicking on download button, you will receive another button "Click to download Pdf". Once you click on that, your pdf will be downloaded.

![click-to-download](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-download-pdf.png)

---

14. This is how the downloaded pdf looks.

![downloaded-pdf](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-downloaded-pdf.png)

---

15. You can ask any question about the podcast which you have processed in the below dialogue-box.

![chat-box](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-QnA.png)

---

16. Once you type and click on enter, you will get a button named "ask" below it. you can proceed by clicking on it.

![ask](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-ask-option.png)

---

17. The answer for your question regarding the processed podcast will be generated.

![answer-generated](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-answer-generated.png)

---

18. You can see the question which was asked, went to the backend.

![api-call-question](Intern_Submissions\Goutham-Gourabathuni\images\PodC-infy-BE-request.png)

---

## Website Link



---