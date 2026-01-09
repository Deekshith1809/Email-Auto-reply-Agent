from __future__ import annotations
import os
from sqlalchemy.orm import Session
from .db_mysql import SessionLocal, OutboxRow
from .gmail_client import send_gmail

USE_REAL_GMAIL = os.getenv("USE_REAL_GMAIL", "false").lower() == "true"

def send_email_and_record(to: str, subject: str, body: str, auto: bool) -> dict:
    session: Session = SessionLocal()
    try:
        # DEFAULT STATUS
        status = "queued"

        # AUTO MODE → TRY REAL GMAIL
        if auto:
            if USE_REAL_GMAIL:
                try:
                    send_gmail(to, subject, body)
                    status = "sent(gmail)"
                except Exception as e:
                    status = f"send_error:{str(e)}"
            else:
                status = "queued(simulated)"  # auto, but simulation mode

        # WRITE TO DB
        row = OutboxRow(
            recipient=to,
            subject=subject,
            body=body,
            status=status,
            auto=auto
        )

        session.add(row)
        session.commit()
        session.refresh(row)

        return {"message_id": row.id, "status": row.status}

    finally:
        session.close()
