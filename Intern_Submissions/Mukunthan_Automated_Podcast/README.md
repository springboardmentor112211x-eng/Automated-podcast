# Automated Podcast Transcription & Topic Segmentation

## Intern Details
- Name: Mukunthan S
- Internship: GenAI Internship Lab (Infosys Springboard)

## Project Overview
This project is a web-based application that automates podcast transcription and topic segmentation.  
Users can upload audio files or provide a YouTube podcast link to generate accurate transcripts and topic-wise segments.

## Features
- Audio upload and transcription
- Topic segmentation from transcript
- Clickable segments with timestamps
- Audio player integration
- Downloadable transcript and segments files

## Tech Stack
- Python
- Flask
- OpenAI Whisper (ASR)
- HTML, CSS, JavaScript

## How It Works
1. User uploads an audio file or YouTube link
2. Audio is processed using Whisper for transcription
3. Transcript is segmented into meaningful topics
4. Results are displayed with playback support

## Output Files
- transcript.txt → Full transcription
- segments.json → Topic-wise segmentation

## How to Run
```bash
pip install -r requirements.txt
python app.py
