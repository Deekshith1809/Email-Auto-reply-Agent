from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
from typing import Optional, Literal, List
from dotenv import load_dotenv
import os
import atexit

# Services
from services.classification import classify
from services.sentiment import polarity
from services.reply_templates import render
from services.email_sender import send_email_and_record
from services.gemini_reply import generate_llm_reply
from services.db_mysql import Base, engine, get_session, OutboxRow
from services.gmail_reader import fetch_latest_emails, mark_seen

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = FastAPI(title="B2B Email Intent & Auto-Reply Agent (Prod)")

# DB tables
Base.metadata.create_all(bind=engine)

AUTO_MODE = os.getenv("AUTO_MODE", "manual").lower()

# Senders to ignore for auto-reply
AUTO_SKIP = ["no-reply", "noreply", "notification", "alert", "mailer-daemon", "postmaster", "bounce", "failure"]


@app.get("/")
def home():
    return {"message": "Backend running", "mode": AUTO_MODE}


# --- Models ---
class EmailIn(BaseModel):
    sender: str
    subject: str
    body: str


class ClassifyOut(BaseModel):
    intent: Literal["invoice", "complaint", "inquiry", "purchase_order", "quotation"]
    confidence: float
    sentiment: str
    sentiment_score: float


class ReplyOut(BaseModel):
    intent: str
    reply_draft: str
    auto_send: bool
    send_result: Optional[dict] = None


class ModeIn(BaseModel):
    mode: Literal["manual", "auto"]


class OutboxDTO(BaseModel):
    id: int
    recipient: str
    subject: str
    status: str
    auto: bool
    created_at: str


@app.get("/health")
def health():
    return {"status": "ok", "mode": AUTO_MODE}


# --- APIs ---
@app.post("/classify", response_model=ClassifyOut)
async def classify_email(payload: EmailIn):
    res = classify(payload.subject, payload.body)
    sent = polarity(payload.subject + "\n" + payload.body)
    return {
        "intent": res["label"],
        "confidence": res.get("confidence", 0.0),
        "sentiment": sent["label"],
        "sentiment_score": sent["score"],
    }


@app.post("/generate_reply", response_model=ReplyOut)
async def generate_reply(payload: EmailIn):
    clf = classify(payload.subject, payload.body)
    intent = clf["label"]
    try:
        draft = generate_llm_reply(payload.subject, payload.body, intent)
    except Exception:
        draft = render(intent, payload.sender, payload.subject, payload.body)
    auto = AUTO_MODE == "auto"
    result = send_email_and_record(payload.sender, f"Re: {payload.subject}", draft, auto=auto)
    return {"intent": intent, "reply_draft": draft, "auto_send": auto, "send_result": result}


@app.post("/send_manual")
async def send_manual(payload: EmailIn):
    result = send_email_and_record(payload.sender, f"Re: {payload.subject}", payload.body, auto=False)
    return {"status": "sent", "result": result}


@app.post("/set_mode")
async def set_mode(data: ModeIn):
    global AUTO_MODE
    AUTO_MODE = data.mode
    # Persist to .env so refresh keeps it
    try:
        if os.path.exists(".env"):
            lines = []
            with open(".env", "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(".env", "w", encoding="utf-8") as f:
                wrote = False
                for line in lines:
                    if line.startswith("AUTO_MODE"):
                        f.write(f"AUTO_MODE={AUTO_MODE}\n")
                        wrote = True
                    else:
                        f.write(line)
                if not wrote:
                    f.write(f"AUTO_MODE={AUTO_MODE}\n")
    except Exception as e:
        print("Could not persist AUTO_MODE:", e)
    return {"mode": AUTO_MODE}


@app.post("/process_email", response_model=ReplyOut)
async def process_email(payload: EmailIn):
    clf = classify(payload.subject, payload.body)
    intent = clf["label"]
    try:
        draft = generate_llm_reply(payload.subject, payload.body, intent)
    except Exception:
        draft = render(intent, payload.sender, payload.subject, payload.body)
    auto = AUTO_MODE == "auto"
    result = send_email_and_record(payload.sender, f"Re: {payload.subject}", draft, auto=auto)
    return {"intent": intent, "reply_draft": draft, "auto_send": auto, "send_result": result}


@app.get("/inbox")
async def inbox(unread: bool = Query(False, description="Return only unread emails if true")):
    try:
        return {"emails": fetch_latest_emails(unread_only=unread)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/outbox", response_model=List[OutboxDTO])
def list_outbox(session=Depends(get_session)):
    rows = session.query(OutboxRow).order_by(OutboxRow.id.desc()).limit(200).all()
    return [
        OutboxDTO(
            id=r.id,
            recipient=r.recipient,
            subject=r.subject,
            status=r.status,
            auto=bool(r.auto),
            created_at=str(r.created_at),
        )
        for r in rows
    ]


# --- Auto processor: reply ONLY to UNREAD messages ---
processed_uids = set()


def _is_automated(sender: str) -> bool:
    s = (sender or "").lower()
    return any(key in s for key in AUTO_SKIP)


def auto_process_inbox():
    try:
        # Pull only UNREAD messages
        emails = fetch_latest_emails(unread_only=True)

        to_mark_seen = []

        for mail in emails:
            uid = str(mail["id"])
            sender = mail.get("from", "")
            subject = mail.get("subject", "")
            body = mail.get("body", "")

            # already did this run
            if uid in processed_uids:
                continue

            # skip known automated/bounce senders
            if _is_automated(sender):
                processed_uids.add(uid)
                continue

            print(f"[AUTO] Processing: {subject}")

            # classify + draft
            clf = classify(subject, body)
            intent = clf["label"]
            try:
                draft = generate_llm_reply(subject, body, intent)
            except Exception:
                draft = render(intent, sender, subject, body)

            auto = AUTO_MODE == "auto"
            send_email_and_record(sender, f"Re: {subject}", draft, auto)

            # mark as processed this cycle
            processed_uids.add(uid)

            # if we auto-sent (or even queued), mark thread as read so we don’t reprocess
            if auto:
                to_mark_seen.append(uid)

        if to_mark_seen:
            mark_seen(to_mark_seen)

    except Exception as e:
        print("AUTO PROCESS ERROR:", e)


# schedule every 30s
scheduler = BackgroundScheduler()
scheduler.add_job(auto_process_inbox, "interval", seconds=30, max_instances=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
