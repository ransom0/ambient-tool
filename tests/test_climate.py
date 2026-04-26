from __future__ import annotations

from ambient_tool.climate import (
    build_growing_climate_summary,
    build_rain_climate_summary,
    build_temperature_climate_summary,
)


def test_build_rain_climate_summary(monkeypatch) -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-20T01:00:00+00:00",
            "dailyrainin": 0.10,
        },
        {
            "observation_time_utc": "2026-04-20T18:00:00+00:00",
            "dailyrainin": 0.45,
        },
        {
            "observation_time_utc": "2026-04-21T12:00:00+00:00",
        "dailyrainin": 1.20,
        },
        {
            "observation_time_utc": "2026-04-22T09:00:00+00:00",
            "dailyrainin": 0.00,
        },
        {
            "observation_time_utc": "2026-04-23T09:00:00+00:00",
            "dailyrainin": 0.00,
        },
    ]

    def fake_get_observations_for_columns(*, columns, since):
        assert columns == [
            "observation_time_utc",
            "dailyrainin",
        ]
        assert since
        return rows

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_rain_climate_summary(days=30)

    assert summary.days == 30
    assert summary.total_rain == 1.65
    assert summary.rain_days == 2
    assert summary.dry_days == 28
    assert summary.longest_dry_streak == 2
    assert summary.average_per_rain_day == 0.82
    assert summary.wettest_day == "2026-04-21"
    assert summary.wettest_day_rain == 1.20

def test_build_growing_climate_summary(monkeypatch) -> None:
    rows = [
        {"observation_time_utc": "2026-04-20T06:00:00+00:00", "tempf": 48.0, "dailyrainin": 0.0},
        {"observation_time_utc": "2026-04-20T18:00:00+00:00", "tempf": 72.0, "dailyrainin": 0.0},
        {"observation_time_utc": "2026-04-21T06:00:00+00:00", "tempf": 55.0, "dailyrainin": 0.4},
        {"observation_time_utc": "2026-04-21T18:00:00+00:00", "tempf": 91.0, "dailyrainin": 0.6},
        {"observation_time_utc": "2026-04-22T06:00:00+00:00", "tempf": 35.0, "dailyrainin": 0.0},
        {"observation_time_utc": "2026-04-22T18:00:00+00:00", "tempf": 65.0, "dailyrainin": 0.0},
    ]

    def fake_get_observations_for_columns(*, columns, since):
        assert columns == ["observation_time_utc", "tempf", "dailyrainin"]
        assert since
        return rows

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_growing_climate_summary(days=30)

    assert summary.days == 30
    assert summary.warm_days == 2
    assert summary.hot_stress_days == 1
    assert summary.cool_nights == 2
    assert summary.rain_total == 0.6
    assert summary.longest_dry_streak == 1
    assert summary.recent_frost_nights == 1


def test_build_growing_climate_summary_no_rows(monkeypatch) -> None:
    def fake_get_observations_for_columns(*, columns, since):
        return []

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_growing_climate_summary(days=30)

    assert summary.warm_days == 0
    assert summary.hot_stress_days == 0
    assert summary.cool_nights == 0
    assert summary.rain_total == 0.0
    assert summary.longest_dry_streak == 30
    assert summary.recent_frost_nights == 0


def test_build_rain_climate_summary_no_rows(monkeypatch) -> None:
    def fake_get_observations_for_columns(*, columns, since):
        return []

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_rain_climate_summary(days=30)

    assert summary.total_rain == 0.0
    assert summary.rain_days == 0
    assert summary.dry_days == 30
    assert summary.average_per_rain_day == 0.0
    assert summary.longest_dry_streak == 30
    assert summary.wettest_day is None
    assert summary.wettest_day_rain == 0.0

def test_build_temperature_climate_summary(monkeypatch) -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-20T06:00:00+00:00",
            "tempf": 50.0,
        },
        {
            "observation_time_utc": "2026-04-20T18:00:00+00:00",
            "tempf": 80.0,
        },
        {
            "observation_time_utc": "2026-04-21T06:00:00+00:00",
            "tempf": 60.0,
        },
        {
            "observation_time_utc": "2026-04-21T18:00:00+00:00",
            "tempf": 90.0,
        },
    ]

    def fake_get_observations_for_columns(*, columns, since):
        assert columns == [
            "observation_time_utc",
            "tempf",
        ]
        assert since
        return rows

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_temperature_climate_summary(days=30)

    assert summary.days == 30
    assert summary.average_temp == 70.0
    assert summary.average_high == 85.0
    assert summary.average_low == 55.0
    assert summary.warmest_day == "2026-04-21"
    assert summary.warmest_day_temp == 90.0
    assert summary.coolest_day == "2026-04-20"
    assert summary.coolest_day_temp == 50.0
    assert summary.hot_days == 1
    assert summary.cool_nights == 0
    assert summary.largest_range_day == "2026-04-20"
    assert summary.largest_range_temp == 30.0


def test_build_temperature_climate_summary_no_rows(monkeypatch) -> None:
    def fake_get_observations_for_columns(*, columns, since):
        return []

    monkeypatch.setattr(
        "ambient_tool.climate.get_observations_for_columns",
        fake_get_observations_for_columns,
    )

    summary = build_temperature_climate_summary(days=30)

    assert summary.days == 30
    assert summary.average_temp is None
    assert summary.average_high is None
    assert summary.average_low is None
    assert summary.warmest_day is None
    assert summary.warmest_day_temp is None
    assert summary.coolest_day is None
    assert summary.coolest_day_temp is None
    assert summary.hot_days == 0
    assert summary.cool_nights == 0
    assert summary.largest_range_day is None
    assert summary.largest_range_temp is None
