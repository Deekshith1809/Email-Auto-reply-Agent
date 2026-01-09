# B2B Email Intent & Auto‑Reply Agent — Production (MySQL + Gmail)

- FastAPI backend with Gemini drafting (fallback templates)
- Streamlit frontend (multi-page: Compose, Inbox, Settings)
- Gmail IMAP poller + SMTP sender
- MySQL via SQLAlchemy (Outbox table) — single-tenant
- Ready to deploy (Render/EC2 for backend & worker, Streamlit Cloud or Render for UI)

## Run locally
```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env             # fill values (GEMINI_API_KEY, DATABASE_URL, Gmail)
uvicorn main:app --reload          # backend
# new terminal, same venv:
streamlit run app.py               # frontend
# optional worker (poll Gmail):
python scripts/worker_gmail_poll.py
```

## MySQL
Create database then set DATABASE_URL, e.g.:
```
CREATE DATABASE email_agent CHARACTER SET utf8mb4;
```
