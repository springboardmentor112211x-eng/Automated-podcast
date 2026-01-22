from keybert import KeyBERT
from transformers import pipeline

kw_model = KeyBERT("all-MiniLM-L6-v2")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def label_topics(topics):
    for t in topics:
        keywords = kw_model.extract_keywords(t["text"], top_n=3)
        t["keywords"] = ", ".join([k[0] for k in keywords])
        t["title"] = t["keywords"]

        if len(t["text"].split()) < 40:
            t["summary"] = t["text"]
        else:
            t["summary"] = summarizer(
                t["text"], max_length=60, min_length=30
            )[0]["summary_text"]

    return topics
