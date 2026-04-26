from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ambient_tool.query import get_observations_for_columns


@dataclass(frozen=True)
class RainClimateSummary:
    days: int
    total_rain: float
    rain_days: int
    dry_days: int
    average_per_rain_day: float
    longest_dry_streak: int
    wettest_day: str | None
    wettest_day_rain: float


def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)

def _longest_dry_streak(daily_rain: dict[str, float]) -> int:
    longest = 0
    current = 0

    for day in sorted(daily_rain):
        if daily_rain[day] <= 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest

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
            dry_days=days,
            average_per_rain_day=0.0,
            longest_dry_streak=days,
            wettest_day=None,
            wettest_day_rain=0.0,
        )

    daily_max: dict[str, float] = {}

    for row in rows:
        ts = row["observation_time_utc"]
        date_key = str(ts)[:10]

        rain = _to_float(row["dailyrainin"])

        previous = daily_max.get(date_key)

        if previous is None:
            daily_max[date_key] = rain
        elif rain > previous:
            daily_max[date_key] = rain

    total_rain = round(sum(daily_max.values()), 2)
    rain_days = sum(1 for value in daily_max.values() if value > 0)
    dry_days = max(days - rain_days, 0)
    average_per_rain_day = round(total_rain / rain_days, 2) if rain_days else 0.0
    longest_dry_streak = _longest_dry_streak(daily_max)
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
        dry_days=dry_days,
        average_per_rain_day=average_per_rain_day,
        longest_dry_streak=longest_dry_streak,
        wettest_day=wettest_day,
        wettest_day_rain=round(wettest_day_rain, 2),
    )
