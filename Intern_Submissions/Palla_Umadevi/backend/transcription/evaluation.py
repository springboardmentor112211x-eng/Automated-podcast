from sentence_transformers import SentenceTransformer, util

def topic_coherence(topics):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    scores = []

    for t in topics:
        sents = t["text"].split(". ")
        if len(sents) < 2:
            scores.append(1.0)
            continue
        emb = model.encode(sents, convert_to_tensor=True)
        sim = util.pytorch_cos_sim(emb[:-1], emb[1:]).mean()
        scores.append(float(sim))

    return sum(scores)/len(scores)
