from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path.home() / ".ambient_tool" / "ambient_weather.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at_utc TEXT NOT NULL,
                device_name TEXT,
                mac_address TEXT,
                observation_time_utc TEXT,
                tempf REAL,
                humidity REAL,
                feels_like REAL,
                dew_point REAL,
                windspeedmph REAL,
                windgustmph REAL,
                winddir REAL,
                baromrelin REAL,
                hourlyrainin REAL,
                dailyrainin REAL,
                weeklyrainin REAL,
                monthlyrainin REAL,
                yearlyrainin REAL,
                raw_json TEXT NOT NULL
            )
            """
        )


def save_observation(device: dict[str, Any], fetched_at_utc: str) -> None:
    info = device.get("info", {})
    data = device.get("lastData", {})

    device_name = info.get("name")
    mac_address = device.get("macAddress")
    observation_time_utc = data.get("date")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO observations (
                fetched_at_utc,
                device_name,
                mac_address,
                observation_time_utc,
                tempf,
                humidity,
                feels_like,
                dew_point,
                windspeedmph,
                windgustmph,
                winddir,
                baromrelin,
                hourlyrainin,
                dailyrainin,
                weeklyrainin,
                monthlyrainin,
                yearlyrainin,
                raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fetched_at_utc,
                device_name,
                mac_address,
                observation_time_utc,
                data.get("tempf"),
                data.get("humidity"),
                data.get("feelsLike"),
                data.get("dewPoint"),
                data.get("windspeedmph"),
                data.get("windgustmph"),
                data.get("winddir"),
                data.get("baromrelin"),
                data.get("hourlyrainin"),
                data.get("dailyrainin"),
                data.get("weeklyrainin"),
                data.get("monthlyrainin"),
                data.get("yearlyrainin"),
                json.dumps(device),
            ),
        )


def save_observations(devices: list[dict[str, Any]], fetched_at_utc: str) -> int:
    count = 0
    for device in devices:
        save_observation(device, fetched_at_utc)
        count += 1
    return count
