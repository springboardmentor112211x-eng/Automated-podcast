# pipeline/topic_titles.py

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

nlp = spacy.load("en_core_web_sm")


def _extract_candidate_phrases(text):
    """Extract short noun phrases"""
    doc = nlp(text)
    phrases = []

    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        if 2 <= len(phrase.split()) <= 4:
            phrases.append(phrase)

    return phrases


def generate_titles(topics, min_score=0.15):
    """
    Generate confident titles.
    If confidence is low → create descriptive fallback title.
    """

    documents = []
    phrase_maps = []

    for topic in topics:
        phrases = _extract_candidate_phrases(topic["text"])
        phrase_maps.append(phrases)
        documents.append(" ".join(phrases) if phrases else "")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5
    )

    try:
        X = vectorizer.fit_transform(documents)
        terms = vectorizer.get_feature_names_out()
    except ValueError:
        # No meaningful phrases anywhere
        return _fallback_titles(topics)

    for i, topic in enumerate(topics):
        scores = X[i].toarray()[0]

        if scores.max() < min_score:
            topic["title"] = _descriptive_fallback(topic["text"], i)
            continue

        top_indices = scores.argsort()[-2:][::-1]
        keywords = [terms[j] for j in top_indices if scores[j] > min_score]

        if keywords:
            topic["title"] = " / ".join(keywords).title()
        else:
            topic["title"] = _descriptive_fallback(topic["text"], i)

    return topics


def _descriptive_fallback(text, index):
    """
    Intelligent fallback instead of 'Topic X'
    """
    sentences = text.split(".")
    if sentences:
        first = sentences[0].strip()
        words = first.split()
        return " ".join(words[:6]).title()
    return f"Discussion Segment {index + 1}"


def _fallback_titles(topics):
    for i, topic in enumerate(topics):
        topic["title"] = _descriptive_fallback(topic["text"], i)
    return topics
