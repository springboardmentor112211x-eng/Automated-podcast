# Automated Podcast Transcription and Topic Segmentation

## 🧩 Problem Statement

Podcasts are increasingly popular, but long audio episodes are difficult to navigate. Manual transcription and topic-wise timestamp creation is time-consuming and inefficient.
This project builds an **automated system that converts podcast audio into structured, searchable, topic-wise knowledge using GenAI.**

---

## 🎯 Project Objective

To design and implement an **end-to-end automated pipeline** that transforms podcast audio into:

- Accurate text transcription
- Speaker diarization (distinguishing who is speaking)
- Semantically segmented topics with timestamps
- Human-like chapter titles for easy navigation

---

## 🛠️ Solution Overview

The system is a **Streamlit-based interactive application** that provides a one-click automated pipeline. It performs audio preprocessing, speech-to-text transcription, speaker identification, and semantic topic segmentation, all executed **locally**.

**User Workflow:**

1.  **Upload podcast audio** (MP3/WAV format supported).
2.  **Audio preprocessing** (loading, resample to 16kHz, noise reduction, normalization).
3.  **Speaker Diarization** using Pyannote Audio.
4.  **Speech-to-text transcription** using OpenAI Whisper (Large-v3).
5.  **Semantic topic segmentation** with AI-generated titles using Sentence Transformers and BART.
6.  **Visualize final outputs** directly in the UI (Transcription, Topic List, Summaries).

---

## ⚙️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Interface** | Streamlit |
| **ASR** | OpenAI Whisper (Large-v3 driven by Hugging Face Transformers) |
| **Diarization** | Pyannote Audio 3.3.1 |
| **NLP** | Sentence Transformers, Facebook BART (Summarization) |
| **Audio Processing** | Librosa, SoundFile, Pydub, NoiseReduce |
| **Language** | Python 3.10+ |

---

## 🚀 Installation & Setup

### Prerequisites

1.  **Python**: Ensure you have Python installed (Python 3.10-3.12 recommended).
2.  **CUDA (Optional but Recommended)**: For faster processing on NVIDIA GPUs, ensure you have the appropriate CUDA toolkit installed.
3.  **Hugging Face Account**: You need to accept user agreements for the Pyannote models.

### Step-by-Step Installation

1.  **Clone or Download** this repository.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` restricts `numpy<2.0.0` for compatibility.*

3.  **Hugging Face Authentication**:
    The system requires access to gated models (`pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`).
    - Go to [Pyannote Speaker Diarization 3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) and accept the license.
    - Go to [Pyannote Segmentation 3.0](https://huggingface.co/pyannote/segmentation-3.0) and accept the license.
    - Create a generic "Read" Access Token in your Hugging Face settings.
    - Log in via terminal:
      ```bash
      huggingface-cli login (please use your HF token, it's free of cost)
      # hf_EhmNs*RpHgre*UFpiEGeLIlJVGkpklzFP
      ```

4.  **FFmpeg**: 
    Ensure FFmpeg is installed and added to your system PATH (required by Pydub for MP3 processing).

### Running the Application

```bash
streamlit run app.py
```
The application will open in your default browser at `http://localhost:8501`.

---

## 🧩 Core Modules

| Module | Responsibility |
| :--- | :--- |
| `app.py` | Main Streamlit application entry point. Handles UI, file upload, and visualization. |
| `audio_utils.py` | Loads audio, converts to 16kHz mono, applies noise reduction and volume normalization. |
| `model_pipeline.py` | Orchestrates the entire process: Load -> Diarize -> Transcribe -> Segment -> Summarize. |
| `diarization.py` | Wrapper for Pyannote speaker diarization. Includes fixes for PyTorch safe globals. |
| `transcription.py` | Wrapper for OpenAI Whisper using Hugging Face pipelines with chunking support. |
| `nlp_service.py` | Handles semantic segmentation (Sentence-BERT), clustering (K-Means), and summarization (BART). |

---

## 📊 Outputs / Results

The system generates the following insights:

-   **Full Transcription**: Complete text with timestamps and speaker labels (e.g., "Speaker 1", "Speaker 2"). (Downloadable as TXT file).
-   **Topic Segments**: A structured table of identified topics with start/end times. (Downloadable as TXT file)
-   **Topic Summaries**: AI-generated summaries for each distinct segment of the audio. (Downloadable as TXT file).
-   **Audio Visualizations**: Mel Spectrogram, Waveform statistics. (Downloadable as PDF file)

---

## 🔧 Troubleshooting
I added this section because I faced these issues a lot while building this project
-   **RuntimeError: WeightsUnpickler...**: This is often due to PyTorch 2.6+ security changes. The code includes a fix (`torch.serialization.add_safe_globals`), but ensure you are using compatible versions if issues persist.
-   **No Diarization Output**: Ensure you have accepted the model licenses on Hugging Face and successfully logged in with `huggingface-cli login`.
-   **Out of Memory**: `whisper-large-v3` is heavy. If you run out of VRAM, try switching to `openai/whisper-medium` or `small` in the code or sidebar configuration.
-   **Audio Loading Errors**: If `librosa` fails to load mp3s, ensure FFmpeg is correctly installed.

---

## 🔒 Safety & Privacy

-   **Local-only processing**: No audio is sent to third-party cloud APIs (Whisper and Pyannote run locally).
-   **No external data leakage**: All computation happens on your machine.
-   **User data remains private**: Uploaded files are processed in temporary directories.
