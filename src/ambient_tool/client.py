from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from ambient_tool.config import load_settings

BASE_URL = "https://api.ambientweather.net/v1"


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 4
    initial_backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    request_timeout_seconds: float = 30.0


class AmbientWeatherClient:
    def __init__(
        self,
        api_key: str,
        application_key: str,
        *,
        retry_config: RetryConfig | None = None,
    ) -> None:
        if not api_key or not application_key:
            raise ValueError("Missing Ambient Weather API credentials.")

        self.api_key = api_key
        self.application_key = application_key
        self.retry_config = retry_config or RetryConfig()

    def _request_json(self, path: str, *, params: dict) -> list | dict:
        url = f"{BASE_URL}{path}"
        attempts = 0
        backoff = self.retry_config.initial_backoff_seconds

        while True:
            attempts += 1
            response = requests.get(
                url,
                params=params,
                timeout=self.retry_config.request_timeout_seconds,
            )

            if response.status_code != 429:
                response.raise_for_status()
                return response.json()

            if attempts >= self.retry_config.max_attempts:
                response.raise_for_status()

            retry_after = response.headers.get("Retry-After")
            sleep_seconds = backoff

            if retry_after is not None:
                try:
                    parsed_retry_after = float(retry_after)
                    if parsed_retry_after > 0:
                        sleep_seconds = parsed_retry_after
                except ValueError:
                    pass

            time.sleep(sleep_seconds)
            backoff *= self.retry_config.backoff_multiplier

    def get_devices(self):
        return self._request_json(
            "/devices",
            params={
                "apiKey": self.api_key,
                "applicationKey": self.application_key,
            },
        )

    def get_device_history(
        self,
        mac_address: str,
        *,
        end_date: int | None = None,
        limit: int = 288,
    ):
        params = {
            "apiKey": self.api_key,
            "applicationKey": self.application_key,
            "limit": limit,
        }

        if end_date is not None:
            params["endDate"] = end_date

        return self._request_json(
            f"/devices/{mac_address}",
            params=params,
        )


def build_client() -> AmbientWeatherClient:
    settings = load_settings()
    return AmbientWeatherClient(
        settings.ambient_api_key,
        settings.ambient_app_key,
    )
