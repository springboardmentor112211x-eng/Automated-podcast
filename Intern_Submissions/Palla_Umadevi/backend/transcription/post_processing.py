import re
import contractions

# Fillers to remove
fillers = ["uh", "um", "you know", "like", "hmm", "ah", "er"]
pattern = r"\b(" + "|".join(fillers) + r")\b"

def clean_transcript(transcriptions):
    """
    Returns the full text cleaned from fillers and extra spaces.
    """
    full_text = ""

    for t in transcriptions:
        text = re.sub(pattern, "", t["text"], flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        full_text += " " + text

    full_text = contractions.fix(full_text.strip())
    return full_text
