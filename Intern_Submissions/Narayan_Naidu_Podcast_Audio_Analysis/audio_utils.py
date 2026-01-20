
import os
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment

def load_and_preprocess_audio(file_path: str, target_sr: int = 16000) -> tuple[np.ndarray, str]:
    """
    Load, preprocess (convert to mono 16kHz, denoise, normalize), and store audio.
    Returns the audio data (numpy array) and the path to the processed file.
    """
    print(f"Loading and preprocessing audio: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Ensure output directory exists
    output_dir = "preprocessed-audio"
    os.makedirs(output_dir, exist_ok=True)

    # Create output filename
    base_filename = os.path.basename(file_path)
    filename_no_ext = os.path.splitext(base_filename)[0]
    processed_filename = f"processed_{filename_no_ext}.wav"
    processed_path = os.path.join(output_dir, processed_filename)
    
    # Convert to WAV 16kHz Mono using Pydub
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1).set_frame_rate(target_sr)
        # Export to the new location
        audio.export(processed_path, format="wav")
    except Exception as e:
            raise RuntimeError(f"Error processing audio with pydub: {e}")

    # Load with soundfile for robust WAV reading (avoids some librosa backend decoder issues)
    try:
        y, sr = sf.read(processed_path)
        # Handle multi-channel if pydub failed 
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        
        if sr != target_sr:
             y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
             sr = target_sr
             
    except Exception as e:
         print(f"Soundfile read failed, falling back to librosa: {e}")
         y, sr = librosa.load(processed_path, sr=target_sr)
    
    # Noise Reduction
    print("Applying noise reduction...")

    y_denoised = nr.reduce_noise(y=y, sr=sr, stationary=True, prop_decrease=0.75)

    # Volume Normalization (Librosa)
    print("Normalizing volume...")
    y_normalized = librosa.util.normalize(y_denoised)
    
    sf.write(processed_path, y_normalized, target_sr)
    
    return y_normalized, processed_path
