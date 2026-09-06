import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)


def translate(text):
    prompt = f"""
Translate this citizen complaint into English.

Keep the meaning exactly the same.
Return only the English translation.

Complaint:
{text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()


def ask(question):
    prompt = f"""
You are the JanDwaar citizen assistant.

Answer the citizen's question in simple language.
Help with complaints, public services and using JanDwaar.

Do not pretend to be a government official.
Do not make up complaint information.

Question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()


def transcribe(audio_path):
    audio = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            audio,
            """
Listen to this audio and write down exactly what the person says.
Keep the original language.
Return only the transcription.
"""
        ]
    )

    return response.text.strip()