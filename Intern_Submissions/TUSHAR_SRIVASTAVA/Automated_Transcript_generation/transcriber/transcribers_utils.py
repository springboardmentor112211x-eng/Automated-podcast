import whisper
import os

from transformers import pipeline

# Using the turbo model identified in your logs
MODEL_TYPE = "turbo" 

def transcribe_audio(file_path):
    """Processes whole podcast audio using the Whisper Turbo engine."""
    try:
        # load_model downloads weights to ~/.cache/whisper (~1.5GB)
        model = whisper.load_model(MODEL_TYPE)
        
        # .transcribe() handles long-form audio automatically
        result = model.transcribe(file_path)
        return {
            'text': result['text'],
            'language': result.get('language', 'unknown')
        }
    except Exception as e:
        print(f"ASR Error: {e}")
        return None



# Initialize the summarization pipeline once (it will download on first run)
# bart-large-cnn is excellent for abstractive summarization of long text
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def segment_and_summarize(text):
    """
    Fulfills GenAI Lab requirements using a real Transformer model.
    Based on the pipeline inference method in summarization.py.
    """
    try:
        # 1. Generate the Summary
        # We truncate the input to 1024 tokens (standard for many models) 
        # to prevent memory errors on very long podcasts.
        summary_result = summarizer(
            text[:3000],  # Use the first ~3000 characters for the executive summary
            max_length=150, 
            min_length=50, 
            do_sample=False
        )
        summary_text = summary_result[0]['summary_text']
        
        # 2. Format the Output
        header = "### AI EXECUTIVE SUMMARY\n"
        body = f"{summary_text}\n\n"
        segments_header = "### LOGICAL TOPIC SEGMENTS\n"
        
        # In a more advanced version, you could chunk the text 
        # and summarize each section for true "Topic Segmentation."
        return f"{header}{body}{segments_header}{text}"

    except Exception as e:
        print(f"Summarization error: {e}")
        return f"### AI SUMMARY ERROR\n{text}"