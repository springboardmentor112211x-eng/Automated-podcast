from pathlib import Path
import csv
import librosa
import soundfile as sf
import uuid

from backend.services.asr import transcribe_audio


DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_DIR = DATA_DIR / "metadata"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def chunk_audio(audio_path, chunk_duration=30):
    y, sr = librosa.load(audio_path, sr=16000)

    audio_id = Path(audio_path).stem
    out_dir = PROCESSED_DIR / audio_id
    out_dir.mkdir(parents=True, exist_ok=True)

    durations = []
    chunk_index = 1

    for i in range(0, len(y), chunk_duration * sr):
        chunk = y[i : i + chunk_duration * sr]
        if len(chunk) == 0:
            continue

        chunk_name = f"{audio_id}_{chunk_index:04d}.wav"
        chunk_path = out_dir / chunk_name

        sf.write(chunk_path, chunk, sr)
        durations.append(round(len(chunk) / sr, 2))

        chunk_index += 1

    return out_dir, durations


def create_metadata_csv(audio_path, chunk_dir, durations):
    audio_id = Path(audio_path).stem
    csv_path = METADATA_DIR / f"{audio_id}_metadata.csv"

    chunk_files = sorted(chunk_dir.glob("*.wav"))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["audio_id", "source", "audio_path", "duration_sec", "transcript"]
        )

        for chunk_file, dur in zip(chunk_files, durations):
            writer.writerow(
                [
                    chunk_file.stem,
                    "user_upload",
                    str(chunk_file),
                    dur,
                    "",
                ]
            )

    return csv_path


def transcribe_chunks(metadata_csv_path):
    rows = []
    audio_paths = []

    with open(metadata_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_paths.append(row["audio_path"])
            rows.append(row)

    if not rows:
        print("No chunks found in metadata; nothing to transcribe.")
        return

    print(f"Starting transcription of {len(audio_paths)} chunks in a worker process...")
    from concurrent.futures import ProcessPoolExecutor

    try:
        # Use a single worker process to avoid multiple large model loads
        with ProcessPoolExecutor(max_workers=1) as ex:
            transcripts = list(ex.map(transcribe_audio, audio_paths))
    except Exception as e:
        print("Transcription worker failed:", e)
        transcripts = ["" for _ in audio_paths]

    for row, transcript in zip(rows, transcripts):
        row["transcript"] = transcript

    with open(metadata_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
