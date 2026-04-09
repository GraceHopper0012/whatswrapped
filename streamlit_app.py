import streamlit as st
import sqlite3
import os

st.title("WhatsWrapped")
st.markdown("---")
upload_page = st.Page("upload.py", title="Upload database", icon=":material/upload:")
stats_page = st.Page("stats.py", title="Stats", icon=":material/area_chart:")
pg = st.navigation([upload_page,stats_page])

st.sidebar.selectbox("Group", ["A", "B", "C"], key="group")
st.sidebar.slider("Size", 1, 5, key="size")
pg.run()