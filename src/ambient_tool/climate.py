from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ambient_tool.query import get_observations_for_columns


@dataclass(frozen=True)
class RainClimateSummary:
    days: int
    total_rain: float
    rain_days: int
    wettest_day: str | None
    wettest_day_rain: float


def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_rain_climate_summary(days: int) -> RainClimateSummary:
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    rows = get_observations_for_columns(
        columns=[
            "observation_time_utc",
            "dailyrainin",
        ],
        since=since,
    )

    if not rows:
        return RainClimateSummary(
            days=days,
            total_rain=0.0,
            rain_days=0,
            wettest_day=None,
            wettest_day_rain=0.0,
        )

    daily_max: dict[str, float] = {}

    for row in rows:
        ts = row["observation_time_utc"]
        date_key = str(ts)[:10]

        rain = _to_float(row["dailyrainin"])

        previous = daily_max.get(date_key, 0.0)
        if rain > previous:
            daily_max[date_key] = rain

    total_rain = round(sum(daily_max.values()), 2)
    rain_days = sum(1 for value in daily_max.values() if value > 0)

    wettest_day = None
    wettest_day_rain = 0.0

    for day, value in daily_max.items():
        if value > wettest_day_rain:
            wettest_day = day
            wettest_day_rain = value

    return RainClimateSummary(
        days=days,
        total_rain=total_rain,
        rain_days=rain_days,
        wettest_day=wettest_day,
        wettest_day_rain=round(wettest_day_rain, 2),
    )
