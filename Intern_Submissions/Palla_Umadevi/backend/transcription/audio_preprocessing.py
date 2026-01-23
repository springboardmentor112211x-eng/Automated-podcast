import os
import librosa
import soundfile as sf
from pydub import AudioSegment

def preprocess_audio(input_audio, base_dir):
    """
    Converts audio to 16kHz WAV and splits into 30s chunks.
    Returns directory containing chunk WAV files.
    """
    os.makedirs(base_dir, exist_ok=True)

    # Load and save clean audio
    audio, sr = librosa.load(input_audio, sr=16000)
    clean_path = os.path.join(base_dir, "clean.wav")
    sf.write(clean_path, audio, sr)

    # Split into 30s chunks
    chunk_dir = os.path.join(base_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)

    audio_seg = AudioSegment.from_wav(clean_path)
    chunk_ms = 30 * 1000

    for i in range(0, len(audio_seg), chunk_ms):
        audio_seg[i:i+chunk_ms].export(
            os.path.join(chunk_dir, f"chunk_{i//chunk_ms}.wav"),
            format="wav"
        )

    return chunk_dir
