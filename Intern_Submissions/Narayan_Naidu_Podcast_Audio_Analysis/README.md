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
3.  **Speaker Diarization** using Pyannote Audio (Automatic speaker count detection).
4.  **Speech-to-text transcription** using OpenAI Whisper (Large-v3 via Transformers) with **Safe Chunking** for stability.
5.  **Semantic topic segmentation** using Sentence-BERT and sliding window analysis.
6.  **Visualize final outputs** directly in the UI (Transcription, Topic List, Summaries).

---

## ⚙️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Interface** | Streamlit |
| **ASR** | OpenAI Whisper (Large-v3 driven by Hugging Face Transformers) |
| **Diarization** | Pyannote Audio 3.3.1 |
| **NLP** | Sentence Transformers (Embeddings), Facebook BART (Summarization) |
| **Audio Processing** | Librosa, SoundFile, Pydub, NoiseReduce, NumPy |
| **Memory Management** | Custom Lazy Loading & Garbage Collection |
| **Language** | Python 3.10+ |

---

## 🚀 Installation & Setup

### Prerequisites

1.  **Python**: Ensure you have Python installed (Python 3.10-3.12 recommended).
2.  **CUDA (Optional but Recommended)**: For faster processing on NVIDIA GPUs, ensure you have the appropriate CUDA toolkit installed.
3.  **FFmpeg**: **Required** for MP3 processing. Ensure it is installed and added to your system PATH.
4.  **Hugging Face Account**: You need to accept user agreements for the Pyannote models.

### Step-by-Step Installation

1.  **Clone or Download** this repository.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` ensures compatibility with `numpy<2.0.0` depending on your environment.*

3.  **Hugging Face Authentication**:
    The system requires access to gated models (`pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`).
    - Go to [Pyannote Speaker Diarization 3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) and accept the license.
    - Go to [Pyannote Segmentation 3.0](https://huggingface.co/pyannote/segmentation-3.0) and accept the license.
    - Create a generic "Read" Access Token in your Hugging Face settings.
    - Log in via terminal:
      ```bash
      huggingface-cli login (please use your HF token, its free of cost to create one)
      # hf_EhmNs*RpHgre*UFpiEGeLIlJVGkpklzFP
      ```

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
| `audio_utils.py` | Loads audio, converts to 16kHz mono (via Pydub), applies noise reduction (Noisereduce) and volume normalization. |
| `model_pipeline.py` | Orchestrates the process with **Lazy Loading**. Loads one model at a time to save GPU memory. |
| `diarization.py` | Wrapper for Pyannote speaker diarization. Includes fixes for PyTorch safe globals. |
| `transcription.py` | Wrapper for OpenAI Whisper using Hugging Face pipelines. Implements **Safe Chunking** (30s chunks) for reliable progress tracking. |
| `nlp_service.py` | Handles semantic segmentation (Sentence-BERT + Sliding Window Similarity) and summarization (BART). |

---

## 📊 Outputs / Results

The system generates the following insights:

-   **Full Transcription**: Complete text with timestamps and speaker labels (e.g., "Speaker 1"). (Downloadable as TXT file).
-   **Topic Segments**: A structured table of identified topics with start/end times. (Downloadable as TXT file)
-   **Topic Summaries**: AI-generated summaries for each distinct segment of the audio. (Downloadable as TXT file).
-   **Audio Visualizations**: Mel Spectrogram, Waveform statistics. (Downloadable as PDF file)

---

## 🔧 Troubleshooting
If you encounter issues while running the application, refer to the following common errors and solutions:
-   **RuntimeError: WeightsUnpickler...**: This is often due to PyTorch 2.6+ security changes. The code includes a fix (`torch.serialization.add_safe_globals`).
-   **No Diarization Output/Auth Error**: Ensure you have accepted the model licenses on Hugging Face and successfully logged in with `huggingface-cli login`.
-   **Out of Memory**: The app uses `memory_utils.py` to aggressively clear memory. If issues persist, ensure no other GPU-heavy apps are running. (I didn't pushed the `memory_utils.py` file to github)
-   **Audio Loading Errors**: If `librosa` or `pydub` fails to load mp3s, ensure **FFmpeg** is correctly installed and in your PATH.

---

## 🔒 Safety & Privacy

-   **Local-only processing**: No audio is sent to third-party cloud APIs (Whisper and Pyannote run locally).
-   **No external data leakage**: All computation happens on your machine.
-   **User data remains private**: Uploaded files are processed in temporary directories.
