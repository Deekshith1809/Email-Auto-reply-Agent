import os
import email
import imaplib
from email.header import decode_header, make_header
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def _connect():
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD):
        raise RuntimeError("GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set in .env")
    m = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    m.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    return m


def _decode(s):
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def _get_body(msg: email.message.Message) -> str:
    # prefer text/plain, fallback to text/html (stripped)
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                except Exception:
                    pass
        # fallback: first text/html
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/html":
                try:
                    html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                    # crude strip of tags
                    return email.utils.unquote(html).replace("<br>", "\n").replace("<br/>", "\n")
                except Exception:
                    pass
        return ""
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
        except Exception:
            return msg.get_payload() or ""


def fetch_latest_emails(limit: int = 25, unread_only: bool = False):
    """
    Returns a list of dicts: { id (UID str), from, subject, body, unread: bool }
    """
    m = _connect()
    try:
        m.select("INBOX")
        criteria = "UNSEEN" if unread_only else "ALL"
        status, data = m.uid("search", None, criteria)
        if status != "OK":
            return []

        uids = data[0].split()
        # newest first
        uids = list(reversed(uids))[:limit]

        out = []
        for uid in uids:
            status, msg_data = m.uid("fetch", uid, "(RFC822 FLAGS)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            flags_part = msg_data[-1][0].decode() if isinstance(msg_data[-1][0], (bytes, bytearray)) else str(msg_data[-1][0])

            from_ = _decode(msg.get("From", "")).strip()
            subject = _decode(msg.get("Subject", "")).strip()
            body = _get_body(msg)
            is_unread = "\\Seen" not in flags_part

            out.append({
                "id": uid.decode() if isinstance(uid, (bytes, bytearray)) else str(uid),
                "from": from_,
                "subject": subject,
                "body": body,
                "unread": is_unread,
            })
        return out
    finally:
        try:
            m.logout()
        except Exception:
            pass


def mark_seen(uids):
    """Mark a list of UID strings as \\Seen."""
    if not uids:
        return
    m = _connect()
    try:
        m.select("INBOX")
        for uid in uids:
            m.uid("store", uid, "+FLAGS", r"(\Seen)")
    finally:
        try:
            m.logout()
        except Exception:
            pass
