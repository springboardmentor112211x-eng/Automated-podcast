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
            podcast.save()
            
            # Step 1: Transcribe
            result = transcribe_audio(podcast.audio_file.path)
            
            if result:
                # Step 2: Pass BOTH raw text and timeline text
                processed_text = segment_and_summarize(
                    result['text'], 
                    result['timeline_text']
                )
                
                podcast.transcript_raw = result['text']
                podcast.transcript_final = processed_text
                podcast.detected_language = result['language']
                podcast.status = 'completed'
            else:
                podcast.status = 'failed'
            
            podcast.save()
            return redirect('dashboard')
    return render(request, 'transcriber/upload.html', {'form': PodcastUploadForm()})
import io
from django.shortcuts import render, get_object_or_404, redirect
from .models import Podcast
from .forms import TranscriptEditForm

def transcript_detail(request, pk):
    podcast = get_object_or_404(Podcast, pk=pk, user=request.user)
    
    # PARSING LOGIC: Split the stored string back into pieces for the UI
    raw_data = podcast.transcript_final or ""
    summary_text = ""
    topic_text = ""
    main_content = ""

    if "[[SUMMARY]]" in raw_data:
        parts = raw_data.split("[[SUMMARY]]")[1].split("[[TOPICS]]")
        summary_text = parts[0].strip()
        sub_parts = parts[1].split("[[CONTENT]]")
        topic_text = sub_parts[0].strip()
        main_content = sub_parts[1].strip()

    # Form handling
    if request.method == 'POST':
        form = TranscriptEditForm(request.POST, instance=podcast)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TranscriptEditForm(instance=podcast)

    context = {
        'podcast': podcast,
        'form': form,
        'summary_text': summary_text,
        'mathematical_topics': [topic_text], # List for the template loop
        'main_content': main_content,
    }
    return render(request, 'transcriber/transcript_detail.html', context)
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