from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os, tempfile, shutil

from .audio_preprocessing import preprocess_audio
from .asr_whisper import transcribe_chunks
from .post_processing import clean_transcript
from .topic_segmentation import segment_topics
from .topic_labeling import label_topics
from .final_output import save_final

@csrf_exempt
def transcribe_podcast(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, uploaded_file.name)

    try:
        # Save file
        with open(audio_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Preprocess & chunk
        chunk_dir = preprocess_audio(audio_path, temp_dir)

        # Transcribe
        transcriptions = transcribe_chunks(chunk_dir)

        # Clean
        cleaned_segments = transcriptions  # Already segment dicts
        # Segment topics
        topic_segments = segment_topics(cleaned_segments)

        # Label topics
        topics = label_topics(topic_segments)

        save_final(topics, os.path.join(temp_dir, "final_output.json"))

        return JsonResponse({
            "status": "success",
            "total_topics": len(topics),
            "topics": topics
        }, json_dumps_params={"indent": 2})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
