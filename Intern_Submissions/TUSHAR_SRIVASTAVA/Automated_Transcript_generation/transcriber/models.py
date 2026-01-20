from django.db import models
from django.contrib.auth.models import User

class Podcast(models.Model):
    """
    Model to handle the end-to-end transcription flow including 
    audio ingestion, AI generation, and human review.
    """
    # Status choices for production-style pipeline monitoring
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Link to the user for personalized dashboard access
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Podcast Metadata
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='podcasts/')
    
    # Transcription Data
    # Stores the raw output from the Whisper ASR model
    transcript_raw = models.TextField(blank=True, null=True) 
    
    # Stores the edited version (Human-in-the-Loop supervision)
    transcript_final = models.TextField(blank=True, null=True) 
    
    # Metadata for semantic analysis and insights
    detected_language = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # Timestamps for history and sorting
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']