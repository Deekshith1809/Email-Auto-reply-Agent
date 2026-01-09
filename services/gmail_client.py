import os, ssl, imaplib, smtplib, email
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS   = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASS  = os.getenv("GMAIL_APP_PASSWORD")
IMAP_HOST       = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT       = int(os.getenv("IMAP_PORT", "993"))
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))

def _decode(s):
    if not s: return ""
    try: return str(make_header(decode_header(s)))
    except: return s

def fetch_unseen(limit=25):
    res = []
    ctx = ssl.create_default_context()
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx) as M:
        M.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        M.select("INBOX")
        typ, data = M.search(None, '(UNSEEN)')
        if typ != "OK": return res
        ids = data[0].split()
        ids = ids[-limit:] if limit else ids
        for i in ids:
            typ, msg_data = M.fetch(i, "(RFC822)")
            if typ != "OK": continue
            msg = email.message_from_bytes(msg_data[0][1])
            sender  = _decode(msg.get("From", ""))
            subject = _decode(msg.get("Subject", ""))
            msg_id  = msg.get("Message-ID", str(i))
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                        charset = part.get_content_charset() or "utf-8"
                        body += part.get_payload(decode=True).decode(charset, errors="ignore")
                        break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
                else:
                    body = msg.get_payload()

            res.append({
                "sender": sender.split("<")[-1].strip(" >") if "<" in sender else sender,
                "subject": subject,
                "body": body.strip(),
                "msg_id": msg_id
            })
    return res

def send_gmail(to_addr: str, subject: str, body: str):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_addr
    msg["Subject"] = subject
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        s.send_message(msg)
    return {"status":"sent","provider":"gmail"}
