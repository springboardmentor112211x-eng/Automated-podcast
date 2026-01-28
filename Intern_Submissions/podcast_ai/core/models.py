from django.db import models

class Podcast(models.Model):
    audio_file = models.FileField(upload_to='audio/')
    transcript = models.TextField(blank=True)
    topics = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(default="PENDING", max_length=20)

    def __str__(self):
        return f"Podcast {self.id} - {self.status}"
