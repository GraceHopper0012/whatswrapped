import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    upload_dir: str
    db_name: str

    @property
    def db_path(self) -> str:
        return os.path.join(self.upload_dir, self.db_name)


def load_config() -> AppConfig:
    load_dotenv()

    upload_dir = os.getenv("WW_UPLOAD_DIR")
    db_name = os.getenv("WW_DB_NAME")
    if not upload_dir or not db_name:
        raise ValueError("Environment variables WW_UPLOAD_DIR and WW_DB_NAME must be defined.")

    os.makedirs(upload_dir, exist_ok=True)
    return AppConfig(upload_dir=upload_dir, db_name=db_name)
