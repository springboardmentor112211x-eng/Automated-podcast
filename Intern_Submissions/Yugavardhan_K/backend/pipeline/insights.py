from typing import Any, Optional
from transformers import pipeline

_qa: Optional[Any] = None

def load_qa() -> Any:
    global _qa
    if _qa is None:
        _qa = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            device=-1
        )
    return _qa

def ask_insight(question, transcript, topics):
    qa = load_qa()
    if qa is None:
        raise RuntimeError("Failed to initialize QA pipeline")

    context = (
        "TRANSCRIPT:\n" +
        " ".join(s["text"] for s in transcript)[:3500] +
        "\n\nTOPICS:\n" +
        " ".join(t["summary"] for t in topics)[:3500]
    )

    prompt = f"""
Answer the question strictly based on the context.

Context:
{context}

Question:
{question}
"""

    out = qa(prompt, max_new_tokens=128, do_sample=False)
    return out[0]["generated_text"]