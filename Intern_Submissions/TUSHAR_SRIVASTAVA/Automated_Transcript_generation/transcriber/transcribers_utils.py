import whisper
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD

# Using the pipeline method for abstractive summarization
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def transcribe_audio(file_path):
    """
    Returns the raw text for the AI and a 'Timeline String' for the UI.
    """
    try:
        model = whisper.load_model("turbo")
        result = model.transcribe(file_path)
        
        # 1. Create a formatted timeline string: [00:05] Text here...
        timeline_lines = []
        for s in result['segments']:
            minutes = int(s['start'] // 60)
            seconds = int(s['start'] % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            timeline_lines.append(f"{timestamp} {s['text'].strip()}")
            
        timeline_string = "\n".join(timeline_lines)
            
        return {
            'text': result['text'], # Raw text for AI logic
            'timeline_text': timeline_string, # Text with timestamps for display
            'language': result.get('language', 'en'),
        }
    except Exception as e:
        print(f"ASR Error: {e}")
        return None

def segment_and_summarize(raw_text, timeline_text):
    """
    Now takes both raw text (for AI) and timeline text (for UI display).
    """
    # 1. LLM Abstractive Summary
    try:
        # Use raw text for better summarization quality
        summary = summarizer(raw_text[:3000], max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    except:
        summary = "Summary generation failed."

    # 2. Topic Modeling (NMF, LDA, LSA)
    topics = _run_all_topic_models(raw_text)

    # 3. Combine using markers. We store the 'timeline_text' in the CONTENT section.
    return f"[[SUMMARY]]\n{summary}\n\n[[TOPICS]]\n{topics}\n\n[[CONTENT]]\n{timeline_text}"

def _run_all_topic_models(text):
    # (Keep your existing NMF/LDA/LSA logic here)
    try:
        tfidf_vect = TfidfVectorizer(stop_words='english')
        tfidf = tfidf_vect.fit_transform([text])
        words = tfidf_vect.get_feature_names_out()
        nmf = NMF(n_components=1, random_state=1).fit(tfidf)
        nmf_words = [words[i] for i in nmf.components_[0].argsort()[-3:]]
        return f"NMF: {', '.join(nmf_words)}"
    except:
        return "No topics detected."