import os
from dataclasses import dataclass


@dataclass
class Settings:
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8888"))

    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "memory")  # memory | filesystem
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./data")

    FRONTEND_DIR: str = os.getenv("FRONTEND_DIR", "./frontend/build")

    # When set, admin "Open" links will use this origin
    # e.g., https://chart.example.com (no trailing slash)
    PUBLIC_ORIGIN: str | None = os.getenv("PUBLIC_ORIGIN")


settings = Settings()
