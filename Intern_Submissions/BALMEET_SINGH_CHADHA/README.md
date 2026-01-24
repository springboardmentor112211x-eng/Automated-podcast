# Podcast Transcription & Segmentation Tool

A Python-based tool for transcribing audio files using OpenAI's Whisper model, with support for audio analysis and segmentation.

## Features

- 🎙️ Audio transcription using Whisper AI
- ⏱️ Timestamp support
- 📊 Audio analysis (duration, format, channels)
- ✂️ Audio segmentation by time chunks
- 🌍 Multi-language support with translation

## Requirements

- Python 3.8+
- FFmpeg (required for audio processing)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/podcast-transcription-segmentation.git
cd podcast-transcription-segmentation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Transcribe Audio
```bash
# Basic transcription
python cli.py transcribe AUDIO.ogg

# Save to file with timestamps
python cli.py transcribe AUDIO.ogg -t -o transcript.txt

# Use different model sizes (tiny, base, small, medium, large)
python cli.py transcribe AUDIO.ogg -m small -o output.txt
```

### Segment Audio
```bash
# Segment audio into chunks
python cli.py segment AUDIO.ogg -d 60 -o segments.txt
```

### Analyze Audio
```bash
# Get audio information
python cli.py analyze AUDIO.ogg

# Detect silence
python cli.py analyze AUDIO.ogg -s
```

### Extract Audio Clip
```bash
# Extract portion of audio
python cli.py extract AUDIO.ogg --start 10 --end 30 -o clip.ogg
```

## Technologies Used

- **Whisper**: OpenAI's speech recognition model
- **PyTorch**: Deep learning framework
- **NumPy**: Numerical computing
- **FFmpeg**: Audio/video processing

## Project Structure

```
podcast-transcription-segmentation/
├── cli.py              # Main CLI interface
├── src/                # Source code modules
├── tests/              # Test files
├── requirements.txt    # Python dependencies
└── README.md          # Documentation
```

## Author

Created as part of INFOSYS Internship project

## License

MIT License

##SAVE FILE IN C:\Users\navpr\podcast-transcription-segmentation AS IT IS THE PLACE STORED HERE FOR WORK 


# Keep original language (Urdu)  TO ENGLISH   
>> python cli.py transcribe allrounder.OGG -o urdu_transcript.txt
>>
>> # Translate to English
>> python cli.py transcribe allrounder.OGG --translate -o english_translation.txt
>>
>> # Display in terminal directly (English)
>> python cli.py transcribe allrounder.OGG --translate
