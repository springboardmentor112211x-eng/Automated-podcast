import nltk

nltk.download("punkt", quiet=True)

def preprocess_transcript(segments, min_words=8):
    """
    Combine transcript segments into sentences with minimum word count.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        min_words: Minimum words per sentence (default: 8)
    
    Returns:
        List of sentence dicts with timing and text
    """
    print("🧹 Preprocessing transcript text")
    
    if not segments:
        return []
    
    sentences = []
    buffer = []
    start_time = None
    
    for seg in segments:
        if not start_time:
            start_time = seg["start"]
        
        buffer.append(seg["text"])
        combined_text = " ".join(buffer)
        word_count = len(combined_text.split())
        
        if word_count >= min_words:
            sentences.append({
                "start": start_time,
                "end": seg["end"],
                "text": combined_text
            })
            buffer = []
            start_time = None
    
    # Handle remaining buffer
    if buffer:
        sentences.append({
            "start": start_time,
            "end": segments[-1]["end"],
            "text": " ".join(buffer)
        })
    
    print(f"   Sentences generated: {len(sentences)}")
    return sentences