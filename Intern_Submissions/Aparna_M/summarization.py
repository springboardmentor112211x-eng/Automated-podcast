
from transformers import pipeline

class Summarizer:
    def __init__(self):
        self.labeler = pipeline("text2text-generation", model="google/flan-t5-base")

    def summarize(self, text):
        summary = self.labeler(f"Summarize this in one brief sentence: {text}",
                               max_new_tokens=45,
                               repetition_penalty=3.0,
                               length_penalty=1.0)[0]['generated_text']
        return summary.strip()
