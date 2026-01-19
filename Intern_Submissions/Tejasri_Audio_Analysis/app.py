from flask import Flask, request, jsonify, render_template, send_file
import whisper
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

model = whisper.load_model("small")


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- UPLOAD & ANALYZE (API ONLY) ----------
@app.route("/upload", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # File validation
    if not file.filename.lower().endswith((".wav", ".mp3", ".flac", ".m4a")):
        return jsonify({"error": "Invalid file format"}), 400

    audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(audio_path)

    result = model.transcribe(audio_path)
    segments = result["segments"]
    language = result.get("language", "unknown")

    # Save transcript
    transcript_text = result["text"]
    with open(os.path.join(OUTPUT_FOLDER, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write(transcript_text)

    # Save segments
    with open(os.path.join(OUTPUT_FOLDER, "segments.txt"), "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"{seg['start']} - {seg['end']}: {seg['text']}\n")

    # Preview (first 300 chars)
    preview = transcript_text[:300] + "..."

    return jsonify({
        "status": "success",
        "language": language,
        "preview": preview
    })



# ---------- VIEW PAGE ----------
@app.route("/view")
def view_results():
    transcript = ""
    segments = []

    if os.path.exists("outputs/transcript.txt"):
        transcript = open("outputs/transcript.txt", "r", encoding="utf-8").read()

    if os.path.exists("outputs/segments.txt"):
        segments = open("outputs/segments.txt", "r", encoding="utf-8").readlines()

    return render_template("view.html", transcript=transcript, segments=segments)


# ---------- DOWNLOADS ----------
@app.route("/download/transcript")
def download_transcript():
    return send_file("outputs/transcript.txt", as_attachment=True)


@app.route("/download/segments")
def download_segments():
    return send_file("outputs/segments.txt", as_attachment=True)


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
