from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from ambient_tool.derived import compute_derived_value
from ambient_tool.query import get_recent_observations_for_columns


@dataclass(frozen=True)
class TrendStatBlock:
    latest: float | None
    min_value: float | None
    max_value: float | None
    avg_value: float | None
    sample_count: int


@dataclass(frozen=True)
class TrendField:
    name: str
    label: str
    unit: str
    required_columns: tuple[str, ...]
    value_getter: Callable[[dict], float | None]

@dataclass(frozen=True)
class TrendSummary:
    field: TrendField
    stats: TrendStatBlock
    tendency: str | None

@dataclass(frozen=True)
class TrendRecentRow:
    observation_time_utc: str
    values: dict[str, float | None]

@dataclass(frozen=True)
class TrendAnalysis:
    stats: TrendStatBlock
    tendency: str | None

def _get_single(column: str) -> Callable[[dict], float | None]:
    def getter(row: dict) -> float | None:
        value = row[column]
        if value is None:
            return None
        return float(value)

    return getter

def _get_derived(name: str) -> Callable[[dict], float | None]:
    def getter(row: dict) -> float | None:
        return compute_derived_value(name, row)

    return getter



TREND_FIELDS: dict[str, TrendField] = {
    "temp": TrendField(
        name="temp",
        label="Temperature",
        unit="°F",
        required_columns=("tempf",),
        value_getter=_get_single("tempf"),
    ),
    "dewpoint": TrendField(
        name="dewpoint",
        label="Dew Point",
        unit="°F",
        required_columns=("dew_point",),
        value_getter=_get_single("dew_point"),
    ),
    "pressure": TrendField(
        name="pressure",
        label="Pressure",
        unit="inHg",
        required_columns=("baromrelin",),
        value_getter=_get_single("baromrelin"),
    ),
    "pressure_tendency_3hr": TrendField(
        name="pressure_tendency_3hr",
        label="Pressure Tendency 3hr",
        unit="inHg/3hr",
        required_columns=("baromrelin",),
        value_getter=_get_single("baromrelin"),
    ),
    "humidity": TrendField(
        name="humidity",
        label="Humidity",
        unit="%",
        required_columns=("humidity",),
        value_getter=_get_single("humidity"),
    ),
    "spread": TrendField(
        name="spread",
        label="Spread",
        unit="°F",
        required_columns=("tempf", "dew_point"),
        value_getter=_get_derived("spread"),
    ),
    "gust_delta": TrendField(
        name="gust_delta",
        label="Gust Delta",
        unit="mph",
        required_columns=("windspeedmph", "windgustmph"),
        value_getter=_get_derived("gust_delta"),
    ),
    "feels_like_delta": TrendField(
        name="feels_like_delta",
        label="Feels-Like Delta",
        unit="°F",
        required_columns=("tempf", "feels_like"),
        value_getter=_get_derived("feels_like_delta"),
    ),
    "hourlyrain": TrendField(
        name="hourlyrain",
        label="Rain (Hourly)",
        unit="in",
        required_columns=("hourlyrainin",),
        value_getter=_get_single("hourlyrainin"),
    ),
    "dailyrain": TrendField(
        name="dailyrain",
        label="Rain (Daily)",
        unit="in",
        required_columns=("dailyrainin",),
        value_getter=_get_single("dailyrainin"),
    ),
    "weeklyrain": TrendField(
        name="weeklyrain",
        label="Rain (Weekly)",
        unit="in",
        required_columns=("weeklyrainin",),
        value_getter=_get_single("weeklyrainin"),
    ),
    "monthlyrain": TrendField(
        name="monthlyrain",
        label="Rain (Monthly)",
        unit="in",
        required_columns=("monthlyrainin",),
        value_getter=_get_single("monthlyrainin"),
    ),
    "yearlyrain": TrendField(
        name="yearlyrain",
        label="Rain (Yearly)",
        unit="in",
        required_columns=("yearlyrainin",),
        value_getter=_get_single("yearlyrainin"),
    ),
}


def normalize_show_fields(show_fields: list[str] | None) -> list[str]:
    if not show_fields:
        return ["temp"]

    normalized: list[str] = []
    seen: set[str] = set()

    for field_name in show_fields:
        key = field_name.strip().lower()

        if key not in TREND_FIELDS:
            valid = ", ".join(sorted(TREND_FIELDS))
            raise ValueError(f"Unknown trend field: {field_name}. Valid fields: {valid}")

        if key not in seen:
            seen.add(key)
            normalized.append(key)

    return normalized


def _compute_stats(values: list[float | None]) -> TrendStatBlock:
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return TrendStatBlock(
            latest=None,
            min_value=None,
            max_value=None,
            avg_value=None,
            sample_count=0,
        )

    return TrendStatBlock(
        latest=clean_values[-1],
        min_value=min(clean_values),
        max_value=max(clean_values),
        avg_value=sum(clean_values) / len(clean_values),
        sample_count=len(clean_values),
    )

def compute_tendency(
    values: list[float | None],
    field_name: str,
) -> str | None:
    clean_values = [value for value in values if value is not None]

    if len(clean_values) < 2:
        return None

    delta = clean_values[-1] - clean_values[0]

    thresholds = {
        "temp": 1.0,
        "dewpoint": 1.0,
        "pressure": 0.02,
        "humidity": 3.0,
    }

    threshold = thresholds.get(field_name)

    if threshold is None:
        return None

    if delta > threshold:
        return "rising ↑"
    if delta < -threshold:
        return "falling ↓"
    return "steady →"

def compute_rolling_pressure_tendency_3hr(rows) -> list[float | None]:
    results: list[float | None] = []

    for index, row in enumerate(rows):
        current_pressure = row["baromrelin"]

        if current_pressure is None:
            results.append(None)
            continue

        current_dt = datetime.fromisoformat(
            row["observation_time_utc"].replace("Z", "+00:00")
        )
        target_dt = current_dt - timedelta(hours=3)

        prior_pressure = None

        for prior_row in reversed(rows[:index]):
            prior_dt = datetime.fromisoformat(
                prior_row["observation_time_utc"].replace("Z", "+00:00")
            )

            if prior_dt <= target_dt:
                prior_pressure = prior_row["baromrelin"]
                break

        if prior_pressure is None:
            results.append(None)
        else:
            results.append(float(current_pressure) - float(prior_pressure))

    return results


def compute_pressure_tendency_3hr(rows) -> float | None:
    values = compute_rolling_pressure_tendency_3hr(rows)
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return None

    return clean_values[-1]

def summarize_trends(
    hours: int,
    show_fields: list[str] | None,
) -> list[TrendSummary]:
    requested_fields = normalize_show_fields(show_fields)

    required_columns: list[str] = ["observation_time_utc"]

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        for column in field.required_columns:
            if column not in required_columns:
                required_columns.append(column)

    rows = get_recent_observations_for_columns(hours=hours, columns=required_columns)

    results: list[TrendSummary] = []

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]

        if field_name == "pressure_tendency_3hr":
            values = compute_rolling_pressure_tendency_3hr(rows)
            stats = _compute_stats(values)
            tendency = None
        else:
            values = [field.value_getter(row) for row in rows]
            stats = _compute_stats(values)
            tendency = compute_tendency(values, field.name)

        results.append(
            TrendSummary(
                field=field,
                stats=stats,
                tendency=tendency,
            )
        )

    return results

def get_recent_trend_rows(
    *,
    hours: int,
    show_fields: list[str] | None,
    limit: int,
) -> list[TrendRecentRow]:
    requested_fields = normalize_show_fields(show_fields)

    required_columns: list[str] = ["observation_time_utc"]

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        for column in field.required_columns:
            if column not in required_columns:
                required_columns.append(column)

    rows = get_recent_observations_for_columns(hours=hours, columns=required_columns)

    if limit <= 0:
        return []

    precomputed_values: dict[str, list[float | None]] = {}

    for field_name in requested_fields:
        if field_name == "pressure_tendency_3hr":
            precomputed_values[field_name] = compute_rolling_pressure_tendency_3hr(rows)

    start_index = max(len(rows) - limit, 0)
    recent_rows = rows[start_index:]

    results: list[TrendRecentRow] = []

    for offset, row in enumerate(recent_rows):
        row_index = start_index + offset
        values: dict[str, float | None] = {}

        for field_name in requested_fields:
            field = TREND_FIELDS[field_name]

            if field_name in precomputed_values:
                values[field_name] = precomputed_values[field_name][row_index]
            else:
                values[field_name] = field.value_getter(row)

        results.append(
            TrendRecentRow(
                observation_time_utc=row["observation_time_utc"],
                values=values,
            )
        )

    return results
