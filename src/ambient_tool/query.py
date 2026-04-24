from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from sqlite3 import Row
from statistics import fmean
from typing import Any, Final

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

ALLOWED_GROUP_BY: Final[set[str]] = {"hour"}

GROUPABLE_HOURLY_FIELDS: Final[list[str]] = [
    "tempf",
    "humidity",
    "dew_point",
    "baromrelin",
]


def _supported_grouped_hourly_fields_text() -> str:
    return ", ".join(GROUPABLE_HOURLY_FIELDS)


def normalize_group_by(group_by: str) -> str:
    if group_by not in ALLOWED_GROUP_BY:
        raise ValueError(f"Unsupported group_by: {group_by}")
    return group_by


def normalize_grouped_hourly_fields(fields: list[str]) -> list[str]:
    requested: list[str] = []
    seen: set[str] = set()

    for field in fields:
        if field == "observation_time_utc":
            continue

        if field not in GROUPABLE_HOURLY_FIELDS:
            raise ValueError(
                f"Unsupported grouped hourly field: {field}. "
                f"Supported fields: {_supported_grouped_hourly_fields_text()}"
            )

        if field not in seen:
            seen.add(field)
            requested.append(field)

    if not requested:
        raise ValueError(
            "Grouped hourly export requires at least one supported field. "
            f"Supported fields: {_supported_grouped_hourly_fields_text()}"
        )

    return requested


def get_grouped_fieldnames(group_by: str, *, fields: list[str]) -> list[str]:
    normalized = normalize_group_by(group_by)

    if normalized == "hour":
        grouped_fields = normalize_grouped_hourly_fields(fields)
        fieldnames = ["bucket_start"]

        for field in grouped_fields:
            fieldnames.extend(
                [
                    f"{field}_avg",
                    f"{field}_min",
                    f"{field}_max",
                ]
            )

        return fieldnames

    raise ValueError(f"Unsupported group_by: {group_by}")


def truncate_to_hour_iso(observation_time_utc: str) -> str:
    dt = datetime.fromisoformat(observation_time_utc)
    dt = dt.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    return dt.isoformat()


def _append_if_numeric(bucket: dict[str, list[float]], key: str, value: Any) -> None:
    if value is None:
        return
    bucket[key].append(float(value))


def group_observations_by_hour(rows: list[Row], *, fields: list[str]) -> list[dict]:
    grouped_fields = normalize_grouped_hourly_fields(fields)

    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {field: [] for field in grouped_fields}
    )

    for row in rows:
        observation_time = row["observation_time_utc"]
        if observation_time is None:
            continue

        bucket_start = truncate_to_hour_iso(observation_time)
        bucket = buckets[bucket_start]

        for field in grouped_fields:
            _append_if_numeric(bucket, field, row[field])

    grouped_rows: list[dict] = []

    for bucket_start in sorted(buckets):
        bucket = buckets[bucket_start]

        if not any(bucket.values()):
            continue

        grouped_row: dict[str, object] = {"bucket_start": bucket_start}

        for field in grouped_fields:
            values = bucket[field]
            grouped_row[f"{field}_avg"] = fmean(values) if values else None
            grouped_row[f"{field}_min"] = min(values) if values else None
            grouped_row[f"{field}_max"] = max(values) if values else None

        grouped_rows.append(grouped_row)

    return grouped_rows


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


def get_grouped_observations_for_columns(
    *,
    columns: list[str],
    group_by: str,
    hours: int | None = None,
    since: str | None = None,
) -> list[dict]:
    normalized_group_by = normalize_group_by(group_by)

    if normalized_group_by == "hour":
        grouped_fields = normalize_grouped_hourly_fields(columns)
        required_columns = ["observation_time_utc", *grouped_fields]
        raw_rows = get_observations_for_columns(
            columns=required_columns,
            hours=hours,
            since=since,
        )
        return group_observations_by_hour(raw_rows, fields=grouped_fields)

    raise ValueError(f"Unsupported group_by: {group_by}")


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

def get_observation_database_summary() -> dict[str, object]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT mac_address) AS device_count,
                MIN(observation_time_utc) AS oldest_observation_time_utc,
                MAX(observation_time_utc) AS newest_observation_time_utc
            FROM observations
            """
        ).fetchone()

    return {
        "row_count": row["row_count"],
        "device_count": row["device_count"],
        "oldest_observation_time_utc": row["oldest_observation_time_utc"],
        "newest_observation_time_utc": row["newest_observation_time_utc"],
    }
