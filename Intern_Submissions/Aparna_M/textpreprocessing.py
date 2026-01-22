import difflib
import nltk
nltk.download('punkt')

class TextProcessor:
    def __init__(self, dedupe_threshold=0.85): 
        self.dedupe_threshold = dedupe_threshold

    def deduplicate(self, sentence_objects):
        cleaned = []
        for obj in sentence_objects:
            if not cleaned:
                cleaned.append(obj)
                continue
            
            is_duplicate = False
            for prev in cleaned[-2:]:
                sim = difflib.SequenceMatcher(None, prev['text'], obj['text']).ratio()
                if sim >= self.dedupe_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                cleaned.append(obj)
                
        sentences = [obj['text'] for obj in cleaned]
        times = [obj['time'] for obj in cleaned]
        return sentences, times
