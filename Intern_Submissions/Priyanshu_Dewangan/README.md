# 🎙️ Podcast Insights AI

**A production-ready Streamlit application for intelligent podcast processing with transcription, hybrid summarization, and AI-powered Q&A.**

---

## 🎯 Problem

Traditional podcasts contain valuable information but are:
- **Time-consuming to consume** - Difficult to find specific topics
- **Hard to search** - No easy way to query content by topic
- **Lack structure** - No automatic segmentation or summaries
- **Difficult to validate** - AI answers need human verification

**Our Solution:** Automatically transcribe, segment, summarize podcasts, and enable intelligent Q&A with human validation for accuracy.

---

## 🏗️ Architecture

```
┌─────────────┐
│  Audio File │ (MP3, WAV, M4A, FLAC)
└──────┬──────┘
┌─────────────┐
│  Audio File │ (MP3, WAV, M4A, FLAC)
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│  Audio Preprocessing     │ ◄── Load, resample, normalize
│  - Format detection      │
│  - Resampling to 16kHz   │
│  - Silence trimming      │
│  - Volume normalization  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────┐
│    Whisper ASR   │ ◄── Automatic Speech Recognition
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Text Cleaning   │ ◄── Remove noise, normalize
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│  Semantic Segmentation   │ ◄── Topic-based chapters
│  (Embeddings + PageRank) │
└──────┬───────────────────┘
       │
       ├─────────────────────────┐
       ▼                         ▼
┌──────────────────┐    ┌─────────────────┐
│  TextRank Extractive │    │  BART Abstractive │
│  (40% sentences)    │    │  (Natural rewrite) │
└──────┬──────────────┘    └────────┬────────┘
       │                           │
       └───────────┬───────────────┘
                   ▼
        ┌────────────────────┐
        │ Hybrid Summary     │ ◄── 50% compression
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  ChromaDB Indexing     │ ◄── Vector database
        │  (MiniLM Embeddings)   │
        └────────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────────┐
   │ Q&A Tab │      │ History Tab  │
   │(Flan-T5)│      │(Audit Log)   │
   └─────────┘      └──────────────┘
        │
        ▼
   ┌──────────────────────┐
   │ Human Validation     │
   │ (If confidence <60%) │
   └──────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit 1.28 | Web UI with 4 tabs |
| **ASR** | Whisper (base 140MB) | Speech-to-text transcription |
| **NLP Cleaning** | NLTK 3.8 | Tokenization, stopword removal |
| **Segmentation** | MiniLM-L6-v2 (90MB) | Semantic embeddings |
| **Extractive Summary** | TextRank + NetworkX | Graph-based ranking |
| **Abstractive Summary** | BART (280MB) | Neural text rewriting |
| **Title Generation** | T5-headline (230MB) | Auto chapter titles |
| **LLM - Q&A** | Flan-T5 base (230MB) | Question answering |
| **Vector DB** | ChromaDB 0.4.24 | Semantic indexing & search |
| **Embeddings** | sentence-transformers 2.3 | Dense vector generation |
| **ML Backbone** | PyTorch 2.1.2 | Deep learning framework |
| **Model Hub** | Transformers 4.35.2 | Pre-trained models |
| **API Backend** | FastAPI + Uvicorn | REST API (optional) |
| **Audio Processing** | Librosa 0.10 | Audio loading & preprocessing |

**Total Model Size:** ~970MB (downloaded on first use)
**Total Dependencies:** 20 packages

---

## 📊 Pipeline

### Step 1: Audio Ingestion
```
Input: podcast.mp3 (any duration, any format)
Output: Audio array (16kHz mono, normalized)
- Format detection & conversion
- Resampling to 16kHz
- Silence trimming
- Volume normalization
```

### Step 2: Transcription (ASR)
```
Input: Audio array
Model: Whisper (base) - 140MB
Output: Full transcript + segment timestamps
- Automatic language detection
- Word-level timestamps
- ~5-10 min per hour of audio
```

### Step 3: Text Cleaning
```
Input: Raw transcript
Output: Cleaned transcript
- Lowercase conversion
- Remove special characters
- NLTK stopword filtering
- Grammar normalization
```

### Step 4: Topic Segmentation
```
Input: Cleaned transcript (sentences)
Algorithm: Semantic similarity + PageRank
- Encode sentences → embeddings (MiniLM)
- Calculate similarity matrix
- Apply PageRank to find boundaries
- Group into semantic chapters
Output: 10-20 chapters per 1-hour podcast
```

### Step 5: Hybrid Summarization
```
For each chapter:

A) Extractive (TextRank)
   - Rank sentences by importance (graph-based)
   - Keep top 40% of sentences
   
B) Abstractive (BART)
   - Input: Extracted sentences
   - Output: Rewritten, natural summary
   - Max length: 150 tokens per chapter

Result: ~50% compression ratio, coherent summaries
```

### Step 6: Vector Indexing (ChromaDB)
```
Input: All chapter summaries
- Embed each summary (MiniLM)
- Store in ChromaDB vector DB
- Create semantic index

Purpose: Enable fast semantic search for Q&A
```

### Step 7: Q&A & Retrieval
```
User Question: "What is AI?"
    ↓
1. Embed question (MiniLM)
2. Semantic search in ChromaDB (cosine similarity)
3. Retrieve most relevant chapter(s)
4. Calculate confidence score (0-100%)
    ↓
If confidence >= 60%:
   → Auto-approved, logged
   
If confidence < 60%:
   → Request human validation
    ↓
5. Generate answer with Flan-T5 LLM
6. Log to audit trail with validation status
```

---

## 💬 Prompt Strategy

### 1. **Safe Prompt Formatting**
```python
prompt = f"""Based on this podcast content:
{context_text}

Question: {user_question}
Answer:"""
```

**Why this approach?**
- Simple, clear structure for T5 model
- Minimal instruction overhead
- Reduces hallucination risk

### 2. **Injection Detection**
```python
injection_patterns = [
    r"ignore previous instructions",
    r"system override",
    r"delete all data",
    r"you are not"
]
```

Blocks suspicious queries before processing.

### 3. **Context Grounding**
- Only use podcast content (no external knowledge)
- Limit context to 300 tokens
- Prevents model going "off-script"

### 4. **Token Limits**
```python
max_new_tokens = 200  # Prevent rambling
do_sample = False     # Deterministic answers
```

---

## 🛡️ Safety & Hallucination Control

### Problem: LLMs can generate plausible but false information

### Solution Stack:

| Layer | Method | Coverage |
|-------|--------|----------|
| **Input** | Prompt injection detection | Blocks malicious queries |
| **Context** | Semantic search filtering | Only relevant info fed to LLM |
| **Generation** | Confidence scoring | Flag low-reliability answers |
| **Validation** | Human-in-the-loop | <60% confidence → requires approval |
| **Storage** | Audit trail | Track corrections & confidence |

### Specific Controls:

1. **Semantic Grounding**
   - Answer only references retrieved context
   - No external knowledge injection

2. **Confidence Thresholds**
   ```
   0-20%:   Reject immediately
   20-60%:  Human review required
   60-100%: Auto-approve
   ```

3. **Human Validation Workflow**
   ```
   Low confidence answer
         ↓
   Display with red flag (🔴)
         ↓
   Ask: "Is this correct?"
         ↓
   If NO → Allow human correction
   If YES → Approve & log
   ```

4. **Audit Trail**
   - Every Q&A logged with confidence & status
   - Human corrections stored
   - Enables retraining on real feedback

---

## 💰 Cost Optimization

### Problem: Large LLMs are expensive (~$0.05-0.30 per query on cloud APIs)

### Solutions Implemented:

| Strategy | Savings |
|----------|---------|
| **Local Models** | 100% - No API calls |
| **Model Distillation** | 70% smaller models (base vs large) |
| **Hybrid Summarization** | 50% fewer tokens (extractive + abstractive) |
| **Vector Search** | Fast retrieval (no LLM needed for search) |
| **Batch Processing** | Process entire podcast in one go |
| **GPU Optional** | CPU inference viable (slower but free) |

### Cost Breakdown (per podcast):

| Component | Cost | Notes |
|-----------|------|-------|
| Whisper | Free | Local inference |
| TextRank | Free | Graph algorithm |
| BART + Flan-T5 | Free | Local inference |
| ChromaDB | Free | Local storage |
| **Total** | **$0** | 100% local, zero API costs |

### vs Cloud Alternative:
- OpenAI Whisper API: $0.02/min → $1.20/hour
- GPT-4 API: $0.03/query × 100 queries = $3.00
- **Cloud Total: ~$10-15 per podcast**
- **Our Solution: $0**

---

## 👥 Human-in-the-Loop Validation

### Design Philosophy
Trust but verify - AI generates, humans validate.

### Workflow:

```
1. HIGH CONFIDENCE (60%+)
   Question: "What is AI?"
   Answer: "[Auto-generated]"
   Status: ✅ AUTO_APPROVED
   → Logged immediately

3. LOW CONFIDENCE (<60%)
   Question: "What specific algorithm?"
   Answer: "[Auto-generated]"
   Status: 🔴 HUMAN VALIDATION REQUIRED
   → Display with radio buttons
   → Wait for user input

   User selects "Yes ✅":
   → Status: HUMAN_VERIFIED
   → Logged with confidence score

   User selects "No ❌":
   → Allow correction input
   → Status: HUMAN_CORRECTED
   → Logged with correction

4. NO ANSWER FOUND
   → Status: NO_ANSWER_FOUND
   → Logged for analysis
```

### Statistics Tracked:
- Total queries
- Auto-approved (%)
- Human verified (%)
- Human corrected (%)
- Average confidence
- Correction patterns

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- 3GB free disk (for models)
- 10-15 minutes (first run model download)

### Step 1: Install Dependencies (One-time)

```bash
cd Intern_Submissions\Priyanshu_Dewangan

pip install -r requirements.txt
```

### Step 2: Download NLTK Resources (One-time)
Just skip this step and let the app download on first use Or manually run NLTK download:
```bash

python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Step 3: Run the Application

**Terminal 1 - Web UI:**
```bash
streamlit run app.py
```

Opens at: http://localhost:8501

**Terminal 2 (Optional) - REST API:**
```bash
python api_server.py
```

API at: http://localhost:8000/docs

### Step 4: Use the App

1. **Upload Tab**
   - Click "Browse files"
   - Select MP3/WAV/M4A/FLAC
   - Click "Process Audio"
   - Wait 5-15 minutes ⏳

2. **Transcript & Summary Tab**
   - View full transcript
   - Read AI summaries
   - Toggle to see original text

3. **Q&A Chat Tab**
   - Type question
   - Click "🚀 Search"
   - Review answer & confidence
   - Validate if needed (Yes/No)

4. **Query History Tab**
   - View all interactions
   - Filter by status
   - Export as CSV

---

## 📸 Demo

### Tab 1: Upload & Process

<img width="1543" height="895" alt="Screenshot 2026-01-22 at 18-35-13 Podcast Insights AI" src="https://github.com/user-attachments/assets/6389f906-e403-48c4-a081-f7a36259afd9" />



### Tab 2: Transcript & Summaries

<img width="1534" height="862" alt="Screenshot 2026-01-22 at 18-35-40 Podcast Insights AI" src="https://github.com/user-attachments/assets/fdaab38e-24f9-4de2-a2e5-c2f28c9abb06" />



### Tab 3: Q&A Chat

<img width="1210" height="766" alt="Screenshot 2026-01-22 at 18-36-21 Podcast Insights AI" src="https://github.com/user-attachments/assets/3104e4ec-716a-40d9-b7f6-f1b34ebc9809" />



### Tab 4: Query History

<img width="1443" height="672" alt="Screenshot 2026-01-22 at 18-43-56 Podcast Insights AI" src="https://github.com/user-attachments/assets/b11bbd0a-1faa-4d4e-93db-ba6b7a383529" />



---


## 👨‍💻 Author

**Priyanshu Dewangan**
Infosys Springboard Internship | Jan 2026

---

**Enjoy your podcast insights!** 🎙️

