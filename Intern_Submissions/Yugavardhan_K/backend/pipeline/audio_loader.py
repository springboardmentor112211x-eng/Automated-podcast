import os
import librosa
import noisereduce as nr
import numpy as np


def load_and_preprocess_audio(path, target_sr=16000):
    """
    Load and preprocess audio for ASR.

    Steps:
    - Load audio (any format)
    - Resample to 16kHz
    - Convert to mono
    - Normalize amplitude
    - Noise reduction (safe)
    - Trim leading/trailing silence

    Returns:
        audio (np.ndarray), sample_rate (int)
    """

    # ---------- VALIDATION ----------
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    # ---------- LOAD AUDIO ----------
    audio, sr = librosa.load(path, sr=None, mono=False)

    # Convert to mono (if stereo)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=0)

    # ---------- RESAMPLING ----------
    if sr != target_sr:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    # ---------- NORMALIZATION ----------
    audio = librosa.util.normalize(audio)

    # ---------- NOISE REDUCTION (SAFE) ----------
    try:
        audio = nr.reduce_noise(y=audio, sr=sr)
    except Exception:
        # Fail-safe: continue without noise reduction
        pass

    # ---------- SILENCE TRIMMING ----------
    try:
        audio, _ = librosa.effects.trim(audio, top_db=20)
    except Exception:
        pass

    # ---------- FINAL VALIDATION ----------
    if audio is None or len(audio) == 0:
        raise ValueError("Audio is empty after preprocessing")

    # Enforce float32 for ML models
    audio = audio.astype(np.float32)

    return audio, sr