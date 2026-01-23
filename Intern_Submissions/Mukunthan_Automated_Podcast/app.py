from flask import Flask, render_template, request, redirect, send_file
import whisper
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load Whisper model
model = whisper.load_model("base")

@app.route("/")
def home():
    return redirect("/upload")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("index.html")

    # POST
    if "audio" not in request.files:
        return "No file uploaded"

    file = request.files["audio"]
    if file.filename == "":
        return "No selected file"

    audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(audio_path)

    # Transcribe with segments
    result = model.transcribe(audio_path)

    full_text = result["text"]
    segments = result["segments"]

    # Save full transcript
    transcript_path = os.path.join(OUTPUT_FOLDER, "transcript.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    # Save segmented transcript
    segments_path = os.path.join(OUTPUT_FOLDER, "segments.txt")
    with open(segments_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(
                f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}\n"
            )

    return render_template(
        "index.html",
        transcript=full_text,
        segments=segments
    )

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
