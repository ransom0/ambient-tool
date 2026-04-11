from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, UTC

from ambient_tool.storage import get_connection


def get_recent_observations(hours: int):
    cutoff = datetime.now(UTC) - timedelta(hours=hours)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT observation_time_utc, tempf, humidity, baromrelin
            FROM observations
            WHERE observation_time_utc >= ?
            ORDER BY observation_time_utc ASC
            """,
            (cutoff.isoformat(),),
        ).fetchall()

    return rows


def compute_stats(values):
    values = [v for v in values if v is not None]

    if not values:
        return None

    return {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
    }
