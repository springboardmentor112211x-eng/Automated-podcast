import os
import uuid
import threading
import time
import traceback

from django.http import JsonResponse, FileResponse, StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
from django.http import Http404
from pipeline.pipeline import run_pipeline
from pipeline.exporter import export_pdf, export_docx


# ==========================
# In-memory job stores
# ==========================
PIPELINE_PROGRESS = {}
PIPELINE_RESULTS = {}


# ==========================
# SSE progress stream (optional)
# ==========================
def progress_stream():
    while True:
        yield b"data: ping\n\n"
        time.sleep(1)


def progress(request):
    return StreamingHttpResponse(
        progress_stream(),
        content_type="text/event-stream"
    )


# ==========================
# Upload + start pipeline
# ==========================
def upload_audio(request):
    if request.method == "POST":
        audio = request.FILES.get("audio")
        if not audio:
            return JsonResponse({"error": "No audio file"}, status=400)

        job_id = str(uuid.uuid4())

        input_dir = os.path.join(settings.MEDIA_ROOT, "input")
        os.makedirs(input_dir, exist_ok=True)
        safe_name = os.path.basename(audio.name)
        stored_name = f"{job_id}_{safe_name}" if safe_name else f"{job_id}_upload"
        path = os.path.join(input_dir, stored_name)

        with open(path, "wb+") as f:
            for chunk in audio.chunks():
                f.write(chunk)

        PIPELINE_PROGRESS[job_id] = {
            "step": "Queued",
            "percent": 0,
            "done": False,
        }

        def progress_cb(step, percent):
            PIPELINE_PROGRESS[job_id].update({
                "step": step,
                "percent": percent,
            })

        def task():
            try:
                result = run_pipeline(
                    path,
                    media_dir=settings.MEDIA_ROOT,
                    media_url=settings.MEDIA_URL,
                    progress_cb=progress_cb,
                    job_id=job_id,
                )

                PIPELINE_RESULTS[job_id] = result
                PIPELINE_PROGRESS[job_id]["done"] = True

            except Exception as e:
                traceback.print_exc()  # surface detailed error to server logs
                PIPELINE_RESULTS[job_id] = {"error": str(e)}
                PIPELINE_PROGRESS[job_id].update({
                    "step": f"Error: {str(e)}",
                    "percent": 100,
                    "done": True,
                })

        threading.Thread(target=task, daemon=True).start()

        return JsonResponse({"job_id": job_id})

    return render(request, "upload.html")


# ==========================
# Poll pipeline progress
# ==========================
def pipeline_progress(request, job_id):
    data = PIPELINE_PROGRESS.get(job_id)
    if not data:
        return JsonResponse({"error": "Invalid job ID"}, status=404)
    return JsonResponse(data)


# ==========================
# Render result page
# ==========================
# def pipeline_result(request, job_id):
#     progress = PIPELINE_PROGRESS.get(job_id)

#     if not progress:
#         return JsonResponse({"error": "Invalid job ID"}, status=404)

#     if not progress.get("done"):
#         return render(request, "processing.html", {
#             "job_id": job_id,
#             "step": progress.get("step", "Processing"),
#             "percent": progress.get("percent", 0),
#         })

#     if job_id not in PIPELINE_RESULTS:
#         return JsonResponse({"error": "Pipeline failed. Check server logs."}, status=500)

#     # ✅ THIS IS THE CRITICAL FIX
#     return render(request, "result.html", {
#         **PIPELINE_RESULTS[job_id],
#         "job_id": job_id
#     })

def pipeline_result(request, job_id):

    # Always render result page if job exists
    result = PIPELINE_RESULTS.get(job_id)

    if not result:
        return render(request, "result.html", {
            "transcript": [],
            "topics": [],
            "audio_url": None,
            "metrics": {},
            "job_id": job_id,
            "message": "No data available yet."
        })

    result = {**result}
    result.setdefault("metrics", {})
    return render(request, "result.html", {
        **result,
        "job_id": job_id
    })

# ==========================
# Export PDF
# ==========================
def download_pdf(request, job_id):
    result = PIPELINE_RESULTS.get(job_id)
    if not result:
        return JsonResponse({"error": "Result not found"}, status=404)

    out_dir = os.path.join(settings.MEDIA_ROOT, "outputs", str(job_id))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"report_{job_id}.pdf")

    export_pdf(result, path)
    return FileResponse(open(path, "rb"), as_attachment=True, filename=f"report_{job_id}.pdf")


# ==========================
# Export DOCX
# ==========================
def download_docx(request, job_id):
    result = PIPELINE_RESULTS.get(job_id)
    if not result:
        return JsonResponse({"error": "Result not found"}, status=404)

    out_dir = os.path.join(settings.MEDIA_ROOT, "outputs", str(job_id))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"report_{job_id}.docx")

    export_docx(result, path)
    return FileResponse(open(path, "rb"), as_attachment=True, filename=f"report_{job_id}.docx")


def download_text(request, job_id, filename):
    safe_name = os.path.basename(filename)
    if safe_name != filename or safe_name in {"", ".", ".."}:
        raise Http404("File not found")

    base_dir = os.path.join(settings.MEDIA_ROOT, "outputs", str(job_id))
    file_path = os.path.join(base_dir, safe_name)

    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=safe_name
    )
