from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from ambient_tool.client import AmbientWeatherClient, RetryConfig


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload=None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def test_get_devices_retries_on_429_then_succeeds(monkeypatch) -> None:
    responses = [
        FakeResponse(status_code=429),
        FakeResponse(status_code=200, payload=[{"macAddress": "abc"}]),
    ]
    calls: list[dict] = []
    sleeps: list[float] = []

    def fake_get(url, *, params, timeout):
        calls.append(
            {
                "url": url,
                "params": params,
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr("ambient_tool.client.requests.get", fake_get)
    monkeypatch.setattr("ambient_tool.client.time.sleep", lambda seconds: sleeps.append(seconds))

    client = AmbientWeatherClient(
        "api-key",
        "app-key",
        retry_config=RetryConfig(
            max_attempts=4,
            initial_backoff_seconds=1.0,
            backoff_multiplier=2.0,
            request_timeout_seconds=30.0,
        ),
    )

    result = client.get_devices()

    assert result == [{"macAddress": "abc"}]
    assert len(calls) == 2
    assert sleeps == [1.0]


def test_get_devices_uses_retry_after_header_when_present(monkeypatch) -> None:
    responses = [
        FakeResponse(status_code=429, headers={"Retry-After": "3"}),
        FakeResponse(status_code=200, payload=[{"macAddress": "abc"}]),
    ]
    sleeps: list[float] = []

    def fake_get(url, *, params, timeout):
        return responses.pop(0)

    monkeypatch.setattr("ambient_tool.client.requests.get", fake_get)
    monkeypatch.setattr("ambient_tool.client.time.sleep", lambda seconds: sleeps.append(seconds))

    client = AmbientWeatherClient(
        "api-key",
        "app-key",
        retry_config=RetryConfig(),
    )

    result = client.get_devices()

    assert result == [{"macAddress": "abc"}]
    assert sleeps == [3.0]


def test_get_devices_raises_after_max_429_attempts(monkeypatch) -> None:
    responses = [
        FakeResponse(status_code=429),
        FakeResponse(status_code=429),
        FakeResponse(status_code=429),
    ]
    sleeps: list[float] = []

    def fake_get(url, *, params, timeout):
        return responses.pop(0)

    monkeypatch.setattr("ambient_tool.client.requests.get", fake_get)
    monkeypatch.setattr("ambient_tool.client.time.sleep", lambda seconds: sleeps.append(seconds))

    client = AmbientWeatherClient(
        "api-key",
        "app-key",
        retry_config=RetryConfig(
            max_attempts=3,
            initial_backoff_seconds=1.0,
            backoff_multiplier=2.0,
            request_timeout_seconds=30.0,
        ),
    )

    with pytest.raises(requests.HTTPError, match="429 error"):
        client.get_devices()

    assert sleeps == [1.0, 2.0]


def test_get_device_history_retries_on_429_then_succeeds(monkeypatch) -> None:
    responses = [
        FakeResponse(status_code=429),
        FakeResponse(status_code=200, payload=[{"dateutc": 1234567890}]),
    ]
    calls: list[dict] = []
    sleeps: list[float] = []

    def fake_get(url, *, params, timeout):
        calls.append(
            {
                "url": url,
                "params": params,
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr("ambient_tool.client.requests.get", fake_get)
    monkeypatch.setattr("ambient_tool.client.time.sleep", lambda seconds: sleeps.append(seconds))

    client = AmbientWeatherClient(
        "api-key",
        "app-key",
        retry_config=RetryConfig(),
    )

    result = client.get_device_history("00:11:22:33", end_date=12345, limit=100)

    assert result == [{"dateutc": 1234567890}]
    assert sleeps == [1.0]
    assert calls[-1]["url"].endswith("/devices/00:11:22:33")
    assert calls[-1]["params"] == {
        "apiKey": "api-key",
        "applicationKey": "app-key",
        "limit": 100,
        "endDate": 12345,
    }


def test_non_429_http_errors_are_not_retried(monkeypatch) -> None:
    sleeps: list[float] = []
    call_count = {"count": 0}

    def fake_get(url, *, params, timeout):
        call_count["count"] += 1
        return FakeResponse(status_code=500)

    monkeypatch.setattr("ambient_tool.client.requests.get", fake_get)
    monkeypatch.setattr("ambient_tool.client.time.sleep", lambda seconds: sleeps.append(seconds))

    client = AmbientWeatherClient(
        "api-key",
        "app-key",
        retry_config=RetryConfig(),
    )

    with pytest.raises(requests.HTTPError, match="500 error"):
        client.get_devices()

    assert call_count["count"] == 1
    assert sleeps == []
