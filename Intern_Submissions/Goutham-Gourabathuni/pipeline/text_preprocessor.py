from nltk.tokenize import sent_tokenize
import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


def segment_into_sentences(transcript):
    """
    Accepts Whisper transcript output and extracts sentences safely
    """

    sentences = []

    for seg in transcript:
        # ✅ handle both dict and string
        if isinstance(seg, dict):
            text = seg.get("text", "")
        elif isinstance(seg, str):
            text = seg
        else:
            continue

        text = text.strip()
        if not text:
            continue

        for sent in sent_tokenize(text):
            cleaned = sent.strip()
            if cleaned:
                sentences.append(cleaned)

    return sentences
