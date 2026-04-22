# WhatsWrapped

A Streamlit app for visualizing WhatsApp chat stats from an unencrypted exported SQLite database.

## Project structure

- `streamlit_app.py`: app entrypoint and page navigation.
- `upload.py`: upload page for placing the WhatsApp database into the configured storage directory.
- `stats.py`: stats page UI and state handling for chat selection + stat rendering.
- `stat_modules.py`: chart/stat definitions and registration list.
- `db_interface.py`: database access layer and query helpers.
- `config.py`: centralized environment/config loading (`WW_UPLOAD_DIR`, `WW_DB_NAME`).

## Environment variables

Create a `.env` file (or set variables in your environment):

```bash
WW_UPLOAD_DIR=/path/to/upload/dir
WW_DB_NAME=msgstore.db
```

## Run locally

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Start the app

```bash
streamlit run streamlit_app.py
```
