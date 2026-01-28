from django.shortcuts import render, redirect
from .models import Podcast
from .transcriber import transcribe_audio
from .genai import segment_topics, summarize
from .safety import safety_check

def upload(request):
    if request.method == "POST":
        audio = request.FILES['audio']
        podcast = Podcast.objects.create(audio_file=audio)

        transcript = transcribe_audio(podcast.audio_file.path)

        if safety_check(transcript):
            podcast.transcript = transcript
            podcast.topics = segment_topics(transcript)
            podcast.summary = summarize(transcript)
        else:
            podcast.transcript = transcript
            podcast.topics = "Blocked due to unsafe content"
            podcast.summary = "Blocked"

        podcast.save()
        return redirect('result', podcast.id)

    return render(request, "upload.html")

def result(request, id):
    podcast = Podcast.objects.get(id=id)
    return render(request, "result.html", {"podcast": podcast})

def review(request):
    podcasts = Podcast.objects.filter(status="PENDING")
    if request.method == "POST":
        pid = request.POST['id']
        p = Podcast.objects.get(id=pid)
        p.status = "APPROVED"
        p.save()
    return render(request, "review.html", {"podcasts": podcasts})
