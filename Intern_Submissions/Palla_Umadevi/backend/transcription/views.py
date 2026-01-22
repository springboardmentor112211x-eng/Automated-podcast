from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import tempfile
import shutil

from transcription.audio_preprocessing import preprocess_audio
from transcription.asr_whisper import transcribe_chunks
from transcription.post_processing import clean_transcript
from transcription.topic_segmentation import segment_topics
from transcription.topic_labeling import label_topics
from transcription.final_output import save_final


@csrf_exempt
def transcribe_podcast(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, uploaded_file.name)

    try:
        # Save uploaded audio
        with open(audio_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Preprocess audio and create chunks
        chunk_dir = preprocess_audio(audio_path, temp_dir)

        # Transcribe chunks
        transcriptions = transcribe_chunks(chunk_dir)

        # Segment topics (preserves timestamps)
        topics = segment_topics(transcriptions)

        # Label topics with keywords & summaries
        topics = label_topics(topics)

        # Save final output (optional)
        save_final(topics)

        # Return JSON
        return JsonResponse({
            "status": "success",
            "total_topics": len(topics),
            "topics": [
                {
                    "topic_id": t["topic_id"],
                    "start_time": t["start_time"],
                    "end_time": t["end_time"],
                    "title": t["title"],
                    "keywords": t["keywords"],
                    "summary": t["summary"],
                    "text": t["text"]
                }
                for t in topics
            ]
        }, json_dumps_params={"indent": 2})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
