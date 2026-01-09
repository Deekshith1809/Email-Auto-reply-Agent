import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Outbox", page_icon="📤", layout="wide")
st.title("📤 Outgoing Emails (MySQL Outbox)")

try:
    r = requests.get(f"{API}/outbox", timeout=20)
    if r.status_code == 200:
        st.dataframe(r.json(), use_container_width=True)
    else:
        st.error(r.text)
except Exception as e:
    st.error(str(e))
