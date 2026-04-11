from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path.home() / ".ambient_tool" / "ambient_weather.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at_utc TEXT NOT NULL,
                device_name TEXT,
                mac_address TEXT NOT NULL,
                observation_time_utc TEXT NOT NULL,
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
                raw_json TEXT NOT NULL,
                UNIQUE(mac_address, observation_time_utc)
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_observations_mac_time
            ON observations(mac_address, observation_time_utc)
            """
        )


def migrate_add_unique_index() -> None:
    with get_connection() as conn:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(observations)")]

        if not columns:
            init_db()
            return

        index_rows = list(conn.execute("PRAGMA index_list(observations)"))
        has_unique = any(row["unique"] == 1 for row in index_rows)
        if has_unique:
            return

        conn.execute(
            """
            CREATE TABLE observations_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at_utc TEXT NOT NULL,
                device_name TEXT,
                mac_address TEXT NOT NULL,
                observation_time_utc TEXT NOT NULL,
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
                raw_json TEXT NOT NULL,
                UNIQUE(mac_address, observation_time_utc)
            )
            """
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO observations_new (
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
            SELECT
                COALESCE(fetched_at_utc, ''),
                device_name,
                COALESCE(mac_address, ''),
                COALESCE(observation_time_utc, ''),
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
            FROM observations
            WHERE mac_address IS NOT NULL
              AND observation_time_utc IS NOT NULL
            """
        )

        conn.execute("DROP TABLE observations")
        conn.execute("ALTER TABLE observations_new RENAME TO observations")
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_observations_mac_time
            ON observations(mac_address, observation_time_utc)
            """
        )


def save_observation(
    device: dict[str, Any],
    fetched_at_utc: str,
    *,
    raw_json_override: dict[str, Any] | None = None,
) -> bool:
    info = device.get("info", {})
    data = device.get("lastData", {})

    device_name = info.get("name")
    mac_address = device.get("macAddress")
    observation_time_utc = data.get("date")

    if not mac_address or not observation_time_utc:
        return False

    raw_payload = raw_json_override if raw_json_override is not None else device

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO observations (
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
                json.dumps(raw_payload),
            ),
        )
        return cursor.rowcount == 1


def save_observations(devices: list[dict[str, Any]], fetched_at_utc: str) -> int:
    count = 0
    for device in devices:
        if save_observation(device, fetched_at_utc):
            count += 1
    return count


def save_historical_observations(
    mac_address: str,
    device_name: str,
    history_rows: list[dict[str, Any]],
    fetched_at_utc: str,
) -> int:
    count = 0

    for row in history_rows:
        observation_time_utc = row.get("date")
        if not observation_time_utc:
            continue

        wrapped_device = {
            "macAddress": mac_address,
            "info": {"name": device_name},
            "lastData": row,
        }

        if save_observation(
            wrapped_device,
            fetched_at_utc,
            raw_json_override=row,
        ):
            count += 1

    return count
