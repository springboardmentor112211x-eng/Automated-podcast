from django.shortcuts import render

# Create your views here.
# transcriber/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from .forms import ContactForm, PodcastUploadForm, TranscriptEditForm
from .models import Podcast
from .transcribers_utils import transcribe_audio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm

def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a production system, you would send an email here
            # For this lab, we will simulate success with a message
            messages.success(request, "Your message has been sent successfully!")
            return redirect('index')
    else:
        form = ContactForm()
    
    # Project details for the landing page as per internship requirements
    project_flow = [
        "Audio Ingestion: Secure upload of MP3/WAV podcast files.",
        "ASR Engine: Processing via OpenAI Whisper Turbo model.",
        "Human-in-the-Loop: Interface for manual transcript verification.",
        "Export: Generation of structured PDF reports."
    ]
    
    return render(request, 'transcriber/index.html', {
        'form': form,
        'project_flow': project_flow
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'transcriber/register.html', {'form': form})

@login_required
def dashboard(request):
    podcasts = Podcast.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transcriber/dashboard.html', {'podcasts': podcasts})

@login_required
def upload_podcast(request):
    if request.method == 'POST':
        form = PodcastUploadForm(request.POST, request.FILES)
        if form.is_valid():
            podcast = form.save(commit=False)
            podcast.user = request.user
            podcast.status = 'processing'
            podcast.save()
            
            # Run transcription (Ideally this should be a background task like Celery)
            result = transcribe_audio(podcast.audio_file.path)
            
            if result:
                podcast.transcript_raw = result['text']
                podcast.transcript_final = result['text'] # Initialize final with raw
                podcast.detected_language = result['language']
                podcast.status = 'completed'
            else:
                podcast.status = 'failed'
            
            podcast.save()
            return redirect('dashboard')
    else:
        form = PodcastUploadForm()
    return render(request, 'transcriber/upload.html', {'form': form})

@login_required
def transcript_detail(request, pk):
    podcast = get_object_or_404(Podcast, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Human in the loop: Editing the transcript
        form = TranscriptEditForm(request.POST, instance=podcast)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TranscriptEditForm(instance=podcast)
    
    return render(request, 'transcriber/transcript_detail.html', {
        'podcast': podcast, 
        'form': form
    })

@login_required
def download_pdf(request, pk):
    podcast = get_object_or_404(Podcast, pk=pk, user=request.user)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Simple PDF generation
    text = podcast.transcript_final if podcast.transcript_final else "No transcript available."
    
    p.drawString(100, 750, f"Transcript: {podcast.title}")
    p.drawString(100, 730, f"Language: {podcast.detected_language}")
    p.line(100, 720, 500, 720)
    
    # Text wrapping logic would be needed for long texts, keeping it simple here
    text_object = p.beginText(40, 700)
    text_object.setFont("Helvetica", 10)
    
    # Basic wrapping for demo
    words = text.split()
    line_len = 0
    line = ""
    for word in words:
        if line_len + len(word) > 100:
            text_object.textLine(line)
            line = ""
            line_len = 0
        line += word + " "
        line_len += len(word)
    text_object.textLine(line)
    
    p.drawText(text_object)
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')