import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("WW_UPLOAD_DIR")
DB_NAME = os.getenv("WW_DB_NAME")
assert type(UPLOAD_DIR) == str
assert type(DB_NAME) == str
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_PATH = os.path.join(UPLOAD_DIR, DB_NAME)

uploaded = st.file_uploader("Your unencrypted Whatsapp DB", type="db", accept_multiple_files=False, max_upload_size=1000)
if uploaded is not None:
    with open(DB_PATH, "wb") as f:
        f.write(uploaded.read())
