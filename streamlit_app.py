import streamlit as st
import sqlite3
import os

st.title("WhatsWrapped")
st.markdown("---")
upload_page = st.Page("upload.py", title="Upload database", icon=":material/upload:")
stats_page = st.Page("stats.py", title="Stats", icon=":material/area_chart:")
pg = st.navigation([upload_page,stats_page])

pg.run()