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

@dataclass(frozen=True)
class TemperatureClimateSummary:
    days: int
    average_temp: float | None
    average_high: float | None
    average_low: float | None
    warmest_day: str | None
    warmest_day_temp: float | None
    coolest_day: str | None
    coolest_day_temp: float | None
    hot_days: int
    cool_nights: int
    largest_range_day: str | None
    largest_range_temp: float | None

@dataclass(frozen=True)
class GrowingClimateSummary:
    days: int
    warm_days: int
    hot_stress_days: int
    cool_nights: int
    rain_total: float
    longest_dry_streak: int
    recent_frost_nights: int

@dataclass(frozen=True)
class MoistureClimateSummary:
    days: int
    average_dew_point: float | None
    muggy_days: int
    very_dry_days: int
    highest_dew_day: str | None
    highest_dew_point: float | None
    lowest_dew_day: str | None
    lowest_dew_point: float | None

def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)

def _to_optional_float(value) -> float | None:
    if value is None:
        return None
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

def build_temperature_climate_summary(days: int) -> TemperatureClimateSummary:
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    rows = get_observations_for_columns(
        columns=[
            "observation_time_utc",
            "tempf",
        ],
        since=since,
    )

    if not rows:
        return TemperatureClimateSummary(
            days=days,
            average_temp=None,
            average_high=None,
            average_low=None,
            warmest_day=None,
            warmest_day_temp=None,
            coolest_day=None,
            coolest_day_temp=None,
            hot_days=0,
            cool_nights=0,
            largest_range_day=None,
            largest_range_temp=None,
        )

    daily_values: dict[str, list[float]] = {}

    for row in rows:
        ts = row["observation_time_utc"]
        date_key = str(ts)[:10]
        temp = _to_optional_float(row["tempf"])

        if temp is None:
            continue

        daily_values.setdefault(date_key, []).append(temp)

    if not daily_values:
        return TemperatureClimateSummary(
            days=days,
            average_temp=None,
            average_high=None,
            average_low=None,
            warmest_day=None,
            warmest_day_temp=None,
            coolest_day=None,
            coolest_day_temp=None,
            hot_days=0,
            cool_nights=0,
            largest_range_day=None,
            largest_range_temp=None,
        )

    daily_highs = {
        day: max(values)
        for day, values in daily_values.items()
    }
    daily_lows = {
        day: min(values)
        for day, values in daily_values.items()
    }

    hot_days = sum(1 for value in daily_highs.values() if value >= 85.0)
    cool_nights = sum(1 for value in daily_lows.values() if value <= 45.0)
    daily_ranges = {
        day: daily_highs[day] - daily_lows[day]
        for day in daily_highs
    }

    largest_range_day, largest_range_temp = max(
        daily_ranges.items(),
        key=lambda item: item[1],
    )

    all_values = [
        value
        for values in daily_values.values()
        for value in values
    ]

    average_temp = round(sum(all_values) / len(all_values), 1)
    average_high = round(sum(daily_highs.values()) / len(daily_highs), 1)
    average_low = round(sum(daily_lows.values()) / len(daily_lows), 1)

    warmest_day, warmest_day_temp = max(
        daily_highs.items(),
        key=lambda item: item[1],
    )
    coolest_day, coolest_day_temp = min(
        daily_lows.items(),
        key=lambda item: item[1],
    )

    return TemperatureClimateSummary(
        days=days,
        average_temp=average_temp,
        average_high=average_high,
        average_low=average_low,
        warmest_day=warmest_day,
        warmest_day_temp=round(warmest_day_temp, 1),
        coolest_day=coolest_day,
        coolest_day_temp=round(coolest_day_temp, 1),
        hot_days=hot_days,
        cool_nights=cool_nights,
        largest_range_day=largest_range_day,
        largest_range_temp=round(largest_range_temp, 1),
    )

def build_growing_climate_summary(days: int) -> GrowingClimateSummary:
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    rows = get_observations_for_columns(
        columns=[
            "observation_time_utc",
            "tempf",
            "dailyrainin",
        ],
        since=since,
    )

    if not rows:
        return GrowingClimateSummary(
            days=days,
            warm_days=0,
            hot_stress_days=0,
            cool_nights=0,
            rain_total=0.0,
            longest_dry_streak=days,
            recent_frost_nights=0,
        )

    daily_temps: dict[str, list[float]] = {}
    daily_rain: dict[str, float] = {}

    for row in rows:
        date_key = str(row["observation_time_utc"])[:10]

        temp = _to_optional_float(row["tempf"])
        if temp is not None:
            daily_temps.setdefault(date_key, []).append(temp)

        rain = _to_float(row["dailyrainin"])
        previous_rain = daily_rain.get(date_key)
        if previous_rain is None or rain > previous_rain:
            daily_rain[date_key] = rain

    daily_highs = {
        day: max(values)
        for day, values in daily_temps.items()
    }
    daily_lows = {
        day: min(values)
        for day, values in daily_temps.items()
    }

    warm_days = sum(1 for value in daily_highs.values() if value >= 70.0)
    hot_stress_days = sum(1 for value in daily_highs.values() if value >= 90.0)
    cool_nights = sum(1 for value in daily_lows.values() if value < 50.0)
    recent_frost_nights = sum(1 for value in daily_lows.values() if value <= 36.0)

    return GrowingClimateSummary(
        days=days,
        warm_days=warm_days,
        hot_stress_days=hot_stress_days,
        cool_nights=cool_nights,
        rain_total=round(sum(daily_rain.values()), 2),
        longest_dry_streak=_longest_dry_streak(daily_rain),
        recent_frost_nights=recent_frost_nights,
    )

def build_moisture_climate_summary(days: int) -> MoistureClimateSummary:
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    rows = get_observations_for_columns(
        columns=[
            "observation_time_utc",
            "dew_point",
        ],
        since=since,
    )

    if not rows:
        return MoistureClimateSummary(
            days=days,
            average_dew_point=None,
            muggy_days=0,
            very_dry_days=0,
            highest_dew_day=None,
            highest_dew_point=None,
            lowest_dew_day=None,
            lowest_dew_point=None,
        )

    daily_values: dict[str, list[float]] = {}

    for row in rows:
        day = str(row["observation_time_utc"])[:10]
        dew = _to_optional_float(row["dew_point"])

        if dew is None:
            continue

        daily_values.setdefault(day, []).append(dew)

    if not daily_values:
        return MoistureClimateSummary(
            days=days,
            average_dew_point=None,
            muggy_days=0,
            very_dry_days=0,
            highest_dew_day=None,
            highest_dew_point=None,
            lowest_dew_day=None,
            lowest_dew_point=None,
        )

    daily_avg = {
        day: sum(values) / len(values)
        for day, values in daily_values.items()
    }

    all_values = [
        value
        for values in daily_values.values()
        for value in values
    ]

    average_dew_point = round(sum(all_values) / len(all_values), 1)
    muggy_days = sum(1 for value in daily_avg.values() if value >= 65.0)
    very_dry_days = sum(1 for value in daily_avg.values() if value <= 40.0)

    highest_dew_day, highest_dew_point = max(
        daily_avg.items(),
        key=lambda item: item[1],
    )

    lowest_dew_day, lowest_dew_point = min(
        daily_avg.items(),
        key=lambda item: item[1],
    )

    return MoistureClimateSummary(
        days=days,
        average_dew_point=average_dew_point,
        muggy_days=muggy_days,
        very_dry_days=very_dry_days,
        highest_dew_day=highest_dew_day,
        highest_dew_point=round(highest_dew_point, 1),
        lowest_dew_day=lowest_dew_day,
        lowest_dew_point=round(lowest_dew_point, 1),
    )
