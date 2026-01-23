from django.urls import path
from .views import transcribe_podcast

urlpatterns = [
    path("transcribe/", transcribe_podcast),
]
