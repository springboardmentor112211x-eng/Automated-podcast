from django.db import models
from django.contrib.auth.models import User

class Podcast(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='podcasts/')
    
    # Transcription fields for human-in-the-loop validation
    transcript_raw = models.TextField(blank=True, null=True) 
    transcript_final = models.TextField(blank=True, null=True) 
    
    # Metadata for semantic intelligence
    detected_language = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_human_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title