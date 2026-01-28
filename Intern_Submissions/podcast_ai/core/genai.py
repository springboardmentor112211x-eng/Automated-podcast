import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def segment_topics(text):
    prompt = f"Split transcript into topic-wise sections:\n{text}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def summarize(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":f"Summarize:\n{text}"}]
    )
    return response.choices[0].message.content
