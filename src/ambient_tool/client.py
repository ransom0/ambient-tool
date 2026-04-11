from __future__ import annotations

from typing import Any

import requests

from ambient_tool.config import load_settings

BASE_URL = "https://api.ambientweather.net/v1"


class AmbientWeatherClient:
    def __init__(self, api_key: str, application_key: str) -> None:
        if not api_key or not application_key:
            raise ValueError("Missing Ambient Weather API credentials.")
        self.api_key = api_key
        self.application_key = application_key

    def get_devices(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{BASE_URL}/devices",
            params={
                "apiKey": self.api_key,
                "applicationKey": self.application_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list of devices, got: {type(data).__name__}")
        return data

def build_client():
    settings = load_settings()
    return AmbientWeatherClient(
        settings.ambient_api_key,
        settings.ambient_app_key,
    )
