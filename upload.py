import streamlit as st

from config import load_config

try:
    cfg = load_config()
except ValueError as exc:
    st.error(str(exc))
else:
    uploaded = st.file_uploader(
        "Your unencrypted Whatsapp DB",
        type="db",
        accept_multiple_files=False,
        max_upload_size=1000,
    )
    if uploaded is not None:
        with open(cfg.db_path, "wb") as f:
            f.write(uploaded.read())
