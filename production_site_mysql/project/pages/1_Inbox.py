# pages/1_Inbox.py  (or wherever you render Inbox)
import os, requests, streamlit as st
from dotenv import load_dotenv
load_dotenv()

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Inbox", page_icon="📥")
st.title("📥 Incoming Emails")

unread_only = st.checkbox("Show unread only", value=True)

if st.button("Fetch Emails"):
    try:
        r = requests.get(f"{API}/inbox", params={"unread": str(unread_only).lower()}, timeout=20)
        data = r.json()
        emails = data.get("emails", [])
        if not emails:
            st.info("No emails found.")
        else:
            for mail in emails:
                sender = mail.get("from", "(unknown)")
                subject = mail.get("subject", "(no subject)")
                body = mail.get("body", "(empty)")
                tag = " (UNREAD)" if mail.get("unread") else ""
                with st.expander(f"{subject}{tag} — {sender}"):
                    st.write(f"**From:** {sender}")
                    st.write(f"**Subject:** {subject}")
                    st.write("---")
                    st.write(body)
    except Exception as e:
        st.error(str(e))
