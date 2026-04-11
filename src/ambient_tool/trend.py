from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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


def _get_single(column: str) -> Callable[[dict], float | None]:
    def getter(row: dict) -> float | None:
        value = row[column]
        if value is None:
            return None
        return float(value)

    return getter


def _get_spread(row: dict) -> float | None:
    temp = row["tempf"]
    dew_point = row["dew_point"]

    if temp is None or dew_point is None:
        return None

    return float(temp) - float(dew_point)


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
        value_getter=_get_spread,
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


def summarize_trends(
    hours: int,
    show_fields: list[str] | None,
) -> list[tuple[TrendField, TrendStatBlock]]:
    requested_fields = normalize_show_fields(show_fields)

    required_columns: list[str] = ["observation_time_utc"]

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        for column in field.required_columns:
            if column not in required_columns:
                required_columns.append(column)

    rows = get_recent_observations_for_columns(hours=hours, columns=required_columns)

    results: list[tuple[TrendField, TrendStatBlock]] = []

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        values = [field.value_getter(row) for row in rows]
        stats = _compute_stats(values)
        results.append((field, stats))

    return results
