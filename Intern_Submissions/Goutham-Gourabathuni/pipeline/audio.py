import os
import subprocess

def normalize_audio(input_path):
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}_normalized.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        output_path
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    return output_path
