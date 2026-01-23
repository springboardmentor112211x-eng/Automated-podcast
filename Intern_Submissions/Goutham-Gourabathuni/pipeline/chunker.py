import os
import subprocess

def chunk_audio(audio_path, chunk_duration=300):
    output_dir = "media/chunks"
    os.makedirs(output_dir, exist_ok=True)

    for f in os.listdir(output_dir):
        if f.endswith(".wav"):
            os.remove(os.path.join(output_dir, f))

    pattern = os.path.join(output_dir, "chunk_%03d.wav")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", audio_path,
        "-f", "segment",
        "-segment_time", str(chunk_duration),
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        pattern
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    chunks = sorted(
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.endswith(".wav")
    )

    return chunks if chunks else [audio_path]
