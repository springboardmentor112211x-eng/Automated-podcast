from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from .models import Podcast
from .forms import ContactForm, PodcastUploadForm, TranscriptEditForm
from .transcribers_utils import transcribe_audio, segment_and_summarize
from reportlab.pdfgen import canvas
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Contact message sent!")
            return redirect('index')
    else:
        form = ContactForm()
    return render(request, 'transcriber/index.html', {'form': form})

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
    podcasts = Podcast.objects.filter(user=request.user)
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
            
            # Step 1: ASR Transcription (Whisper)
            result = transcribe_audio(podcast.audio_file.path)
            
            if result:
                # Step 2: GenAI Topic Segmentation & Summary
                processed_text = segment_and_summarize(result['text'])
                
                podcast.transcript_raw = result['text']
                podcast.transcript_final = processed_text
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
        form = TranscriptEditForm(request.POST, instance=podcast)
        if form.is_valid():
            form.save()
            messages.success(request, "Transcript verified and saved!")
            return redirect('dashboard')
    else:
        form = TranscriptEditForm(instance=podcast)
    return render(request, 'transcriber/transcript_detail.html', {'podcast': podcast, 'form': form})

@login_required
def download_pdf(request, pk):
    podcast = get_object_or_404(Podcast, pk=pk, user=request.user)
    
    buffer = io.BytesIO()
    # Create a template that understands multiple pages
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Define styles for the document
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=10, leading=14))
    
    elements = []
    
    # 1. Add Title
    elements.append(Paragraph(f"<b>Podcast Transcript: {podcast.title}</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # 2. Add Metadata (Language)
    elements.append(Paragraph(f"<i>Detected Language: {podcast.detected_language.upper()}</i>", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # 3. Add the AI Transcript & Summary
    # We split by newlines and create a new Paragraph for each block of text
    content = podcast.transcript_final.split('\n')
    for line in content:
        if line.strip():
            # Check for headers to apply bold styling
            if line.startswith('###'):
                clean_line = line.replace('###', '').strip()
                elements.append(Paragraph(f"<b>{clean_line}</b>", styles['Heading3']))
            else:
                elements.append(Paragraph(line, styles['Justify']))
            elements.append(Spacer(1, 10))
            
    # Build the PDF - Platypus will automatically create new pages as needed
    doc.build(elements)
    
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')