from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    ambient_api_key: str
    ambient_app_key: str


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("AMBIENT_API_KEY", "").strip()
    app_key = os.getenv("AMBIENT_APPLICATION_KEY", "").strip()

    if not api_key:
        raise RuntimeError("Missing AMBIENT_API_KEY in .env or environment")
    if not app_key:
        raise RuntimeError("Missing AMBIENT_APPLICATION_KEY in .env or environment")

    return Settings(
        ambient_api_key=api_key,
        ambient_app_key=app_key,
    )
