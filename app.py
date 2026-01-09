import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="B2B Email Agent", layout="wide")


# ✅ Helper: read backend mode
def get_backend_mode():
    try:
        r = requests.get(f"{API}/health")
        return r.json().get("mode", "manual")
    except:
        return "manual"


with st.sidebar:
    page = st.radio("Navigation", ["App", "Inbox", "Outbox", "Settings"])
    st.write("Backend URL:")
    st.code(API)


# ✅ ✅ SETTINGS PAGE
if page == "Settings":
    st.header("⚙️ Settings")

    current_mode = get_backend_mode()

    mode = st.radio(
        "Select Mode",
        ["manual", "auto"],
        index=0 if current_mode == "manual" else 1
    )

    if st.button("Apply Mode"):
        r = requests.post(f"{API}/set_mode", json={"mode": mode})
        st.success(f"Mode updated → {r.json()['mode']}")


# ✅ ✅ INBOX PAGE
elif page == "Inbox":
    st.header("📥 Incoming Emails")

    if st.button("Fetch Emails"):
        r = requests.get(f"{API}/inbox")
        data = r.json()

        emails = data.get("emails", [])

        if not emails:
            st.info("No emails found.")
        else:
            for mail in emails:
                sender = mail.get("from", "(unknown)")
                subject = mail.get("subject", "(no subject)")
                body = mail.get("body", "(empty)")

                with st.expander(f"{subject} — {sender}"):
                    st.write(f"**From:** {sender}")
                    st.write(f"**Subject:** {subject}")
                    st.write("---")
                    st.write(body)


# ✅ ✅ OUTBOX PAGE
elif page == "Outbox":
    st.header("📤 Sent Emails Log")

    r = requests.get(f"{API}/outbox")
    st.dataframe(r.json(), use_container_width=True)


# ✅ ✅ MAIN APP
elif page == "App":
    st.title("✉️ B2B Email Intent & Auto-Reply Agent")

    c1, c2 = st.columns(2)
    with c1:
        sender = st.text_input("Sender Email")
        subject = st.text_input("Subject")

    with c2:
        body = st.text_area("Email Body", height=200)

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Classify"):
        r = requests.post(f"{API}/classify", json={"sender": sender, "subject": subject, "body": body})
        st.json(r.json())

    if col2.button("Generate Reply"):
        r = requests.post(f"{API}/generate_reply", json={"sender": sender, "subject": subject, "body": body})
        st.json(r.json())

    if col3.button("Full Pipeline"):
        r = requests.post(f"{API}/process_email", json={"sender": sender, "subject": subject, "body": body})
        st.json(r.json())

    if col4.button("Send Now (Manual Mode)"):
        r = requests.post(f"{API}/send_manual", json={"sender": sender, "subject": subject, "body": body})
        st.json(r.json())
