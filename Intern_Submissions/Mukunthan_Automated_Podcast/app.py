from flask import Flask, render_template, request, send_from_directory
import whisper
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

model = whisper.load_model("base")

@app.route("/", methods=["GET", "POST"])
def index():
    segments = None

    if request.method == "POST":
        audio = request.files["audio"]
        audio_path = os.path.join(UPLOAD_FOLDER, audio.filename)
        audio.save(audio_path)

        result = model.transcribe(audio_path)

        transcript_path = os.path.join(OUTPUT_FOLDER, "transcript.txt")
        segments_path = os.path.join(OUTPUT_FOLDER, "segments.txt")

        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(result["text"])

        segments = result["segments"]
        with open(segments_path, "w", encoding="utf-8") as f:
            for seg in segments:
                f.write(f"{seg['start']:.2f} - {seg['end']:.2f}: {seg['text']}\n")

    return render_template("index.html", segments=segments)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
