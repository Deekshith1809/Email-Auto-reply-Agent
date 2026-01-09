from google import genai
from dotenv import load_dotenv
import os
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_llm_reply(subject, body, intent):
    prompt = f"""You are a B2B operations assistant.
Intent: {intent}
Subject: {subject}
Body: {body}

Write a short, professional reply. Acknowledge the request and set clear next steps. No placeholders."""
    r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return r.text
