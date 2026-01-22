from django.urls import path
from transcription.views import transcribe_podcast

urlpatterns = [
    path("api/transcribe/", transcribe_podcast),
]
