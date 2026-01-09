import os, time, requests
from dotenv import load_dotenv
from services.gmail_client import fetch_unseen

load_dotenv()
API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def process_email(email):
    payload = {"sender":email["sender"], "subject":email["subject"], "body":email["body"]}
    r = requests.post(f"{API}/process_email", json=payload, timeout=30)
    print("Processed:", r.status_code, r.json())

if __name__ == "__main__":
    print("Gmail poller started. Ctrl+C to stop.")
    while True:
        try:
            for em in fetch_unseen(limit=20):
                process_email(em)
        except Exception as e:
            print("Poller error:", e)
        time.sleep(60)
