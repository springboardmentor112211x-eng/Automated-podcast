import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def answer_question(question: str, context: str) -> str:
    """
    Answer question using Gemini with podcast context
    """

    # 🛡️ Safety guard (VERY IMPORTANT)
    if not context or len(context.split()) < 100:
        return "I’m not confident enough to answer based on the available transcript."

    prompt = f"""
You are an assistant answering questions about a podcast.

Use ONLY the context below.
If the answer is not present, say: "Not enough information in the podcast."

Context:
{context}

Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        return f"Gemini error: {str(e)}"
