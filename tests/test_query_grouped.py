from __future__ import annotations

from ambient_tool.query import group_observations_by_hour


def test_group_observations_by_hour_computes_tempf_stats() -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-11T12:05:00+00:00",
            "tempf": 70.0,
        },
        {
            "observation_time_utc": "2026-04-11T12:40:00+00:00",
            "tempf": 72.0,
        },
        {
            "observation_time_utc": "2026-04-11T13:10:00+00:00",
            "tempf": 68.0,
        },
    ]

    grouped = group_observations_by_hour(rows)

    assert grouped == [
        {
            "bucket_start": "2026-04-11T12:00:00+00:00",
            "tempf_avg": 71.0,
            "tempf_min": 70.0,
            "tempf_max": 72.0,
        },
        {
            "bucket_start": "2026-04-11T13:00:00+00:00",
            "tempf_avg": 68.0,
            "tempf_min": 68.0,
            "tempf_max": 68.0,
        },
    ]


def test_group_observations_by_hour_skips_rows_without_tempf() -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-11T12:05:00+00:00",
            "tempf": None,
        },
        {
            "observation_time_utc": "2026-04-11T12:40:00+00:00",
            "tempf": 72.0,
        },
    ]

    grouped = group_observations_by_hour(rows)

    assert grouped == [
        {
            "bucket_start": "2026-04-11T12:00:00+00:00",
            "tempf_avg": 72.0,
            "tempf_min": 72.0,
            "tempf_max": 72.0,
        }
    ]
