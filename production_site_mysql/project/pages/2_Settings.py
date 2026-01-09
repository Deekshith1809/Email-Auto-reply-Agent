import os, streamlit as st
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title="Settings", page_icon="⚙️")
st.title("⚙️ Settings")
st.caption("These are read from your .env")
st.code(f"""BACKEND_URL={os.getenv('BACKEND_URL')}
AUTO_MODE={os.getenv('AUTO_MODE')}
GMAIL_ADDRESS={os.getenv('GMAIL_ADDRESS')}
IMAP_HOST={os.getenv('IMAP_HOST')}
SMTP_HOST={os.getenv('SMTP_HOST')}
DATABASE_URL={os.getenv('DATABASE_URL')}
""")
