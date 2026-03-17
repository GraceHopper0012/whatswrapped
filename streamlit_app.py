import streamlit as st
import sqlite3
import os

UPLOAD_DIR = "upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_PATH = os.path.join(UPLOAD_DIR, "messages.db")

st.title("WhatsWrapped")

uploaded = st.file_uploader("Your unencrypted Wahtsapp DB", type="db", accept_multiple_files=False)
if uploaded is not None:
    with open(db_path, "wb") as f:
        f.write(uploaded.read())

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
