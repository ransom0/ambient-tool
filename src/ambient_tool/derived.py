from __future__ import annotations

from collections.abc import Iterable, Mapping
import math
from typing import Any

DERIVED_FIELDS: tuple[str, ...] = (
    "spread",
    "gust_delta",
    "feels_like_delta",
    "pressure_tendency_3hr",
    "vpd",
    "heat_index_anomaly",
)

_REQUIRED_SOURCE_FIELDS: dict[str, tuple[str, ...]] = {
    "spread": ("tempf", "dew_point"),
    "gust_delta": ("windspeedmph", "windgustmph"),
    "feels_like_delta": ("tempf", "feels_like"),
    "pressure_tendency_3hr": ("baromrelin",),
    "vpd": ("tempf", "humidity"),
    "heat_index_anomaly": ("tempf", "feels_like"),
}


def is_derived_field(name: str) -> bool:
    return name in DERIVED_FIELDS


def derived_field_names() -> tuple[str, ...]:
    return DERIVED_FIELDS


def required_source_fields(name: str) -> tuple[str, ...]:
    try:
        return _REQUIRED_SOURCE_FIELDS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported derived field: {name}") from exc


def _safe_get(row: Mapping[str, Any], key: str) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None

def compute_derived_value(name: str, row: Mapping[str, Any]) -> float | None:
    if name == "spread":
        tempf = _safe_get(row, "tempf")
        dew_point = _safe_get(row, "dew_point")
        if tempf is None or dew_point is None:
            return None
        return float(tempf) - float(dew_point)

    if name == "gust_delta":
        windspeed = _safe_get(row, "windspeedmph")
        windgust = _safe_get(row, "windgustmph")
        if windspeed is None or windgust is None:
            return None
        return float(windgust) - float(windspeed)

    if name == "feels_like_delta":
        tempf = _safe_get(row, "tempf")
        feels_like = _safe_get(row, "feels_like")
        if tempf is None or feels_like is None:
            return None
        return float(tempf) - float(feels_like)

    if name == "heat_index_anomaly":
        tempf = _safe_get(row, "tempf")
        feels_like = _safe_get(row, "feels_like")
        if tempf is None or feels_like is None:
            return None
        heat_index_anomaly = float(feels_like) - float(tempf)
        return heat_index_anomaly

    if name == "vpd":
        tempf = _safe_get(row, "tempf")
        humidity = _safe_get(row, "humidity")
        if tempf is None or humidity is None:
            return None

        temp_c = (float(tempf) - 32.0) * 5.0 / 9.0
        relative_humidity = float(humidity)

        saturation_vapor_pressure = 0.6108 * math.exp(
            (17.27 * temp_c) / (temp_c + 237.3)
        )
        actual_vapor_pressure = saturation_vapor_pressure * (
            relative_humidity / 100.0
        )

        return saturation_vapor_pressure - actual_vapor_pressure

    raise ValueError(f"Unsupported derived field: {name}")

def add_derived_fields(
    rows: Iterable[Mapping[str, Any]],
    derived_fields: Iterable[str],
) -> list[dict[str, Any]]:
    derived_list = list(derived_fields)
    out: list[dict[str, Any]] = []

    for row in rows:
        enriched = dict(row)
        for field in derived_list:
            enriched[field] = compute_derived_value(field, enriched)
        out.append(enriched)

    return out


def split_requested_fields(fields: Iterable[str]) -> tuple[list[str], list[str]]:
    raw_fields: list[str] = []
    derived_fields: list[str] = []

    for field in fields:
        if is_derived_field(field):
            derived_fields.append(field)
        else:
            raw_fields.append(field)

    return raw_fields, derived_fields
