# services/processed_store.py
from sqlalchemy.orm import Session
from .db_mysql import SessionLocal, ProcessedEmail

def is_processed(msg_id: str) -> bool:
    with SessionLocal() as s:
        return s.get(ProcessedEmail, msg_id) is not None

def mark_processed(msg_id: str):
    with SessionLocal() as s:
        if s.get(ProcessedEmail, msg_id) is None:
            s.add(ProcessedEmail(msg_id=msg_id))
            s.commit()
