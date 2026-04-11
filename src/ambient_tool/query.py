from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Final

from ambient_tool.storage import get_connection


ALLOWED_OBSERVATION_COLUMNS: Final[set[str]] = {
    "observation_time_utc",
    "tempf",
    "humidity",
    "baromrelin",
    "dew_point",
    "feels_like",
    "windspeedmph",
    "windgustmph",
    "winddir",
    "hourlyrainin",
    "dailyrainin",
    "weeklyrainin",
    "monthlyrainin",
    "yearlyrainin",
}


def normalize_observation_columns(columns: list[str]) -> list[str]:
    requested: list[str] = []
    seen: set[str] = set()

    for column in columns:
        if column not in ALLOWED_OBSERVATION_COLUMNS:
            raise ValueError(f"Unsupported observation column: {column}")
        if column not in seen:
            seen.add(column)
            requested.append(column)

    if "observation_time_utc" not in seen:
        requested.insert(0, "observation_time_utc")

    return requested


def parse_since_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "--since must be a valid ISO-8601 timestamp, e.g. 2026-04-10T15:00:00+00:00"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            "--since must include a timezone offset, e.g. 2026-04-10T15:00:00+00:00"
        )

    return parsed.astimezone(UTC)


def get_observations_since(
    *,
    since_utc: datetime,
    columns: list[str],
) -> list:
    normalized_columns = normalize_observation_columns(columns)
    select_clause = ", ".join(normalized_columns)

    with get_connection() as conn:
        rows: list = conn.execute(
            f"""
            SELECT {select_clause}
            FROM observations
            WHERE observation_time_utc >= ?
            ORDER BY observation_time_utc ASC
            """,
            (since_utc.isoformat(),),
        ).fetchall()

    return rows


def get_recent_observations_for_columns(
    hours: int,
    columns: list[str],
) -> list:
    if hours < 1:
        raise ValueError("hours must be at least 1")

    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    return get_observations_since(
        since_utc=cutoff,
        columns=columns,
    )


def get_observations_for_columns(
    *,
    columns: list[str],
    hours: int | None = None,
    since: str | None = None,
) -> list:
    if (hours is None and since is None) or (hours is not None and since is not None):
        raise ValueError("Provide exactly one of hours or since")

    if hours is not None:
        return get_recent_observations_for_columns(
            hours=hours,
            columns=columns,
        )

    assert since is not None
    since_utc = parse_since_utc(since)
    return get_observations_since(
        since_utc=since_utc,
        columns=columns,
    )


def get_recent_observations(hours: int):
    return get_recent_observations_for_columns(
        hours=hours,
        columns=["observation_time_utc", "tempf", "humidity", "baromrelin"],
    )
