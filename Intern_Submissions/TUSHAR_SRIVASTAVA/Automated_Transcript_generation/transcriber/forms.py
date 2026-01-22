# transcriber/forms.py
from django import forms
from .models import Podcast
from django.contrib.auth.models import User

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))

class PodcastUploadForm(forms.ModelForm):
    class Meta:
        model = Podcast
        fields = ['title', 'audio_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'audio_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TranscriptEditForm(forms.ModelForm):
    class Meta:
        model = Podcast
        fields = ['transcript_final']
        widgets = {
            'transcript_final': forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
        }