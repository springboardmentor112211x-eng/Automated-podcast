import re
import contractions

def clean_transcript(segments):
    """
    Takes a list of segments and returns cleaned full text.
    """
    full = " ".join(s["text"] for s in segments)
    full = contractions.fix(full)
    full = re.sub(r"\s+", " ", full)
    return full.strip()
