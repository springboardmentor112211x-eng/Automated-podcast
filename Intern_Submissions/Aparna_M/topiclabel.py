
from keybert import KeyBERT
from transformers import pipeline
import re
class TopicLabeller:
    def __init__(self):
        self.kw_model = KeyBERT()
        self.labeler = pipeline("text2text-generation", model="google/flan-t5-base")

    def get_keywords(self, text):
        
        return [kw[0] for kw in self.kw_model.extract_keywords(text, top_n=3, keyphrase_ngram_range=(1,2))]

    def label_topic(self, text):
        kws = self.get_keywords(text)
        
        prompt = (
            "Instruction: Transform the following keywords into a professional 3-word chapter title.\n"
            
            f"Context: {text[:300]}\n"
            "Style: Noun phrase, declarative, no verbs.\n"
            "Keywords: solar, energy, power | Title: Solar Power Systems\n"
            "Keywords: cooking, pasta, sauce | Title: Pasta Cooking Methods\n"
            f"Keywords: {', '.join(kws)} | Title:"

        )
        
        output = self.labeler(
            prompt, 
            max_new_tokens=10, 
            repetition_penalty=4.5, 
            num_beams=4,
            do_sample=False
        )
        
        title = output[0]['generated_text'].strip().title()
        title = title.replace("Title:", "").strip()

        title = title.replace(":", " ")
        title = re.sub(r"\s+", " ", title).strip()
        
        words = title.split()
        if len(words) < 2 or len(words) > 4: 
            main_topic = kws[0].title()
            sub_topic = kws[1].title() if len(kws) > 1 else "Analysis"
            title = f"{main_topic}: {sub_topic}"
            
        return title, kws