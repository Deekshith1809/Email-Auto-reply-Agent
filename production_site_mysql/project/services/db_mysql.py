import os
from sqlalchemy import (
    create_engine, Integer, String, DateTime, Boolean, Text
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set. Use: mysql+pymysql://user:pass@host:3306/email_agent"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ✅ TABLE 1: Outbox (sent or queued replies)
class OutboxRow(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500))

    # ✅ Large body text
    body: Mapped[str] = mapped_column(Text)

    # ✅ Fixed: Use TEXT instead of VARCHAR(50)
    status: Mapped[str] = mapped_column(Text)

    auto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ✅ TABLE 2: Processed emails (Gmail auto-processing history)
# Prevents double replies
class ProcessedEmail(Base):
    __tablename__ = "processed_emails"

    msg_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    processed_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
