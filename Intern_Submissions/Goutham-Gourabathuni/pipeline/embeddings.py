from sentence_transformers import SentenceTransformer

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        print("🔄 Loading MiniLM embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded")
    return _model


def embed_sentences(sentences):
    """
    Convert list of sentences to embeddings
    """
    if not sentences:
        return []

    model = get_embedding_model()
    embeddings = model.encode(sentences)

    return embeddings