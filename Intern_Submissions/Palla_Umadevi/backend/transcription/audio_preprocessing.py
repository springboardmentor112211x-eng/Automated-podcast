import os
import librosa
import noisereduce as nr
import soundfile as sf
from pydub import AudioSegment


def preprocess_audio(input_wav, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Load audio
    audio, sr = librosa.load(input_wav, sr=16000)

    # Noise reduction
    reduced_audio = nr.reduce_noise(
        y=audio,
        sr=sr,
        prop_decrease=1.0
    )

    # Silence trimming
    trimmed_audio, _ = librosa.effects.trim(
        reduced_audio,
        top_db=25
    )

    clean_path = os.path.join(output_dir, "clean.wav")
    sf.write(clean_path, trimmed_audio, sr)

    # Chunking
    audio_seg = AudioSegment.from_wav(clean_path)
    chunk_ms = 30 * 1000  # 30 seconds

    chunk_dir = os.path.join(output_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)

    for i in range(0, len(audio_seg), chunk_ms):
        chunk_path = os.path.join(chunk_dir, f"chunk_{i//chunk_ms}.wav")
        audio_seg[i:i + chunk_ms].export(chunk_path, format="wav")

    return chunk_dir
