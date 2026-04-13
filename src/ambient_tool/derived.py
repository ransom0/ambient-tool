from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

DERIVED_FIELDS: tuple[str, ...] = (
    "spread",
    "gust_delta",
    "feels_like_delta",
)

_REQUIRED_SOURCE_FIELDS: dict[str, tuple[str, ...]] = {
    "spread": ("tempf", "dew_point"),
    "gust_delta": ("windspeedmph", "windgustmph"),
    "feels_like_delta": ("tempf", "feels_like"),
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


def compute_derived_value(name: str, row: Mapping[str, Any]) -> float | None:
    if name == "spread":
        tempf = row.get("tempf")
        dew_point = row.get("dew_point")
        if tempf is None or dew_point is None:
            return None
        return float(tempf) - float(dew_point)

    if name == "gust_delta":
        windspeed = row.get("windspeedmph")
        windgust = row.get("windgustmph")
        if windspeed is None or windgust is None:
            return None
        return float(windgust) - float(windspeed)

    if name == "feels_like_delta":
        tempf = row.get("tempf")
        feels_like = row.get("feels_like")
        if tempf is None or feels_like is None:
            return None
        return float(tempf) - float(feels_like)

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
