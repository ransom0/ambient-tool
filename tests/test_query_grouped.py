from __future__ import annotations

import pytest

from ambient_tool.query import (
    get_grouped_fieldnames,
    group_observations_by_hour,
    truncate_to_hour_iso,
)


def test_truncate_to_hour_iso_returns_hour_bucket() -> None:
    assert truncate_to_hour_iso("2026-04-11T12:37:45+00:00") == "2026-04-11T12:00:00+00:00"


def test_get_grouped_fieldnames_for_hour_uses_requested_fields() -> None:
    assert get_grouped_fieldnames("hour", fields=["tempf", "humidity"]) == [
        "bucket_start",
        "tempf_avg",
        "tempf_min",
        "tempf_max",
        "humidity_avg",
        "humidity_min",
        "humidity_max",
    ]


def test_get_grouped_fieldnames_for_hour_rejects_unsupported_field() -> None:
    with pytest.raises(ValueError, match="Unsupported grouped hourly field"):
        get_grouped_fieldnames("hour", fields=["tempf", "windspeedmph"])


def test_group_observations_by_hour_computes_only_requested_metric_stats() -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-11T12:05:00+00:00",
            "tempf": 70.0,
            "humidity": 80.0,
            "dew_point": 63.0,
            "baromrelin": 30.01,
        },
        {
            "observation_time_utc": "2026-04-11T12:40:00+00:00",
            "tempf": 72.0,
            "humidity": 84.0,
            "dew_point": 64.0,
            "baromrelin": 30.03,
        },
        {
            "observation_time_utc": "2026-04-11T13:10:00+00:00",
            "tempf": 68.0,
            "humidity": 78.0,
            "dew_point": 60.0,
            "baromrelin": 29.98,
        },
    ]

    grouped = group_observations_by_hour(rows, fields=["tempf", "humidity"])

    assert grouped == [
        {
            "bucket_start": "2026-04-11T12:00:00+00:00",
            "tempf_avg": 71.0,
            "tempf_min": 70.0,
            "tempf_max": 72.0,
            "humidity_avg": 82.0,
            "humidity_min": 80.0,
            "humidity_max": 84.0,
        },
        {
            "bucket_start": "2026-04-11T13:00:00+00:00",
            "tempf_avg": 68.0,
            "tempf_min": 68.0,
            "tempf_max": 68.0,
            "humidity_avg": 78.0,
            "humidity_min": 78.0,
            "humidity_max": 78.0,
        },
    ]


def test_group_observations_by_hour_keeps_bucket_and_uses_none_for_missing_metric_values() -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-11T12:05:00+00:00",
            "tempf": 72.0,
            "humidity": None,
            "dew_point": None,
            "baromrelin": 30.01,
        }
    ]

    grouped = group_observations_by_hour(rows, fields=["tempf", "humidity"])

    assert grouped == [
        {
            "bucket_start": "2026-04-11T12:00:00+00:00",
            "tempf_avg": 72.0,
            "tempf_min": 72.0,
            "tempf_max": 72.0,
            "humidity_avg": None,
            "humidity_min": None,
            "humidity_max": None,
        }
    ]
