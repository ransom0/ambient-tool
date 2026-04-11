from __future__ import annotations

import time
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

    def get_device_history(
        self,
        mac_address: str,
        *,
        end_date: str | int | None = None,
        limit: int = 288,
        max_retries: int = 5,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 288:
            raise ValueError("limit must be between 1 and 288")

        params: dict[str, Any] = {
            "apiKey": self.api_key,
            "applicationKey": self.application_key,
            "limit": limit,
        }

        if end_date is not None:
            params["endDate"] = end_date

        backoff_seconds = 2.0

        for attempt in range(1, max_retries + 1):
            response = requests.get(
                f"{BASE_URL}/devices/{mac_address}",
                params=params,
                timeout=30,
            )

            if response.status_code == 429:
                if attempt == max_retries:
                    response.raise_for_status()

                print(
                    f"  Rate limited by Ambient (429). "
                    f"Retrying in {backoff_seconds:.1f}s "
                    f"(attempt {attempt}/{max_retries})..."
                )
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise RuntimeError(
                    f"Expected list of historical observations, got: {type(data).__name__}"
                )

            return data

        return []


def build_client() -> AmbientWeatherClient:
    settings = load_settings()
    return AmbientWeatherClient(
        api_key=settings.ambient_api_key,
        application_key=settings.ambient_app_key,
    )
