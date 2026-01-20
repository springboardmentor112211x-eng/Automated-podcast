import whisper
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD

# Using the pipeline method for abstractive summarization
# Load BART model for high-quality summary generation
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def transcribe_audio(file_path):
    """
    Transcribes audio and structures the output into paragraphs based on audio segments.
    """
    try:
        model = whisper.load_model("turbo")
        result = model.transcribe(file_path)
        
        timeline_lines = []
        paragraph_list = []
        current_para = []

        for i, s in enumerate(result['segments']):
            # 1. Build Timeline Entry
            minutes = int(s['start'] // 60)
            seconds = int(s['start'] % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            text_segment = s['text'].strip()
            timeline_lines.append(f"{timestamp} {text_segment}")

            # 2. Build Paragraphs: Group every 4 segments into a logical paragraph
            current_para.append(text_segment)
            if (i + 1) % 4 == 0:
                paragraph_list.append(" ".join(current_para))
                current_para = []
        
        # Add remaining text as the last paragraph
        if current_para:
            paragraph_list.append(" ".join(current_para))
            
        return {
            'raw_text': result['text'], 
            'formatted_transcript': "\n\n".join(paragraph_list), # Text divided by paragraphs
            'timeline_text': "\n".join(timeline_lines),        # One line per segment with timestamp
            'language': result.get('language', 'en'),
        }
    except Exception as e:
        print(f"ASR Error: {e}")
        return None

def segment_and_summarize(raw_text, formatted_transcript, timeline_text):
    """
    Fulfills GenAI Lab requirements by combining formatting, summarization, 
    and topic modeling.
    """
    # 1. LLM Abstractive Summary
    try:
        # Generate summary from the first 3000 chars of raw text
        summary_res = summarizer(raw_text[:3000], max_length=130, min_length=30, do_sample=False)
        summary = summary_res[0]['summary_text']
    except:
        summary = "Summary generation failed."

    # 2. Topic Modeling (NMF, LDA, LSA)
    topics = _run_all_topic_models(raw_text)

    # 3. Combine into the final storage string using markers
    # We use formatted_transcript here to ensure the UI shows paragraphs
    return (
        f"[[SUMMARY]]\n{summary}\n\n"
        f"[[TOPICS]]\n{topics}\n\n"
        f"[[CONTENT]]\n{formatted_transcript}\n\n"
        f"[[TIMELINE]]\n{timeline_text}"
    )

def _run_all_topic_models(text):
    """Detects thematic patterns using NMF and LSA."""
    try:
        tfidf_vect = TfidfVectorizer(stop_words='english')
        tfidf = tfidf_vect.fit_transform([text])
        words = tfidf_vect.get_feature_names_out()

        # NMF: Non-Negative Matrix Factorization
        nmf = NMF(n_components=1, random_state=1).fit(tfidf)
        nmf_words = [words[i] for i in nmf.components_[0].argsort()[-3:]]

        # LSA: Latent Semantic Analysis
        lsa = TruncatedSVD(n_components=1, random_state=1).fit(tfidf)
        lsa_words = [words[i] for i in lsa.components_[0].argsort()[-3:]]

        return f"NMF: {', '.join(nmf_words)} | LSA: {', '.join(lsa_words)}"
    except:
        return "General Discussion"