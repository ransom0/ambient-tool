from __future__ import annotations
import pytest

from ambient_tool.trend import TREND_FIELDS, normalize_show_fields, summarize_trends


def test_normalize_show_fields_defaults_to_temp() -> None:
    assert normalize_show_fields(None) == ["temp"]
    assert normalize_show_fields([]) == ["temp"]


def test_normalize_show_fields_dedupes_and_lowercases() -> None:
    assert normalize_show_fields(["Temp", "dewpoint", "TEMP", "spread"]) == [
        "temp",
        "dewpoint",
        "spread",
    ]


def test_normalize_show_fields_rejects_unknown() -> None:
    try:
        normalize_show_fields(["temp", "banana"])
    except ValueError as exc:
        assert "Unknown trend field" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown trend field")


def test_spread_field_definition_exists() -> None:
    field = TREND_FIELDS["spread"]
    assert field.required_columns == ("tempf", "dew_point")


def test_rain_field_definitions_exist() -> None:
    assert TREND_FIELDS["hourlyrain"].required_columns == ("hourlyrainin",)
    assert TREND_FIELDS["dailyrain"].required_columns == ("dailyrainin",)
    assert TREND_FIELDS["weeklyrain"].required_columns == ("weeklyrainin",)
    assert TREND_FIELDS["monthlyrain"].required_columns == ("monthlyrainin",)
    assert TREND_FIELDS["yearlyrain"].required_columns == ("yearlyrainin",)


def test_summarize_trends_computes_stats_spread_and_tendency(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
            "baromrelin": 30.01,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "tempf": 72.0,
            "dew_point": 61.0,
            "baromrelin": 30.03,
        },
        {
            "observation_time_utc": "2026-04-11T02:00:00+00:00",
            "tempf": 68.0,
            "dew_point": 59.0,
            "baromrelin": 29.99,
        },
    ]

    def fake_get_recent_observations_for_columns(hours: int, columns: list[str]):
        assert hours == 24
        assert "tempf" in columns
        assert "dew_point" in columns
        assert "baromrelin" in columns
        return fake_rows

    monkeypatch.setattr(
        "ambient_tool.trend.get_recent_observations_for_columns",
        fake_get_recent_observations_for_columns,
    )

    results = summarize_trends(
        hours=24,
        show_fields=["temp", "dewpoint", "spread", "pressure"],
    )

    result_map = {result.field.name: result for result in results}

    temp_result = result_map["temp"]
    assert temp_result.stats.latest == 68.0
    assert temp_result.stats.min_value == 68.0
    assert temp_result.stats.max_value == 72.0
    assert temp_result.stats.sample_count == 3
    assert temp_result.tendency == "falling ↓"

    dewpoint_result = result_map["dewpoint"]
    assert dewpoint_result.stats.latest == 59.0
    assert dewpoint_result.stats.min_value == 59.0
    assert dewpoint_result.stats.max_value == 61.0
    assert dewpoint_result.stats.avg_value == 60.0
    assert dewpoint_result.stats.sample_count == 3
    assert dewpoint_result.tendency == "steady →"

    spread_result = result_map["spread"]
    assert spread_result.stats.latest == 9.0
    assert spread_result.stats.min_value == 9.0
    assert spread_result.stats.max_value == 11.0
    assert spread_result.stats.avg_value == 10.0
    assert spread_result.stats.sample_count == 3
    assert spread_result.tendency is None

    pressure_result = result_map["pressure"]
    assert pressure_result.stats.latest == 29.99
    assert pressure_result.stats.min_value == 29.99
    assert pressure_result.stats.max_value == 30.03
    assert pressure_result.stats.avg_value == 30.01
    assert pressure_result.stats.sample_count == 3
    assert pressure_result.tendency == "falling ↓"

def test_gust_delta_field_definition_exists() -> None:
    field = TREND_FIELDS["gust_delta"]
    assert field.required_columns == ("windspeedmph", "windgustmph")


def test_feels_like_delta_field_definition_exists() -> None:
    field = TREND_FIELDS["feels_like_delta"]
    assert field.required_columns == ("tempf", "feels_like")

def test_vpd_field_definition_exists() -> None:
    field = TREND_FIELDS["vpd"]
    assert field.required_columns == ("tempf", "humidity")
    assert field.unit == "kPa"

def test_summarize_trends_computes_gust_delta_and_feels_like_delta(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 90.0,
            "feels_like": 94.0,
            "windspeedmph": 8.0,
            "windgustmph": 14.0,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "tempf": 92.0,
            "feels_like": 97.0,
            "windspeedmph": 10.0,
            "windgustmph": 16.5,
        },
        {
            "observation_time_utc": "2026-04-11T02:00:00+00:00",
            "tempf": 89.0,
            "feels_like": 91.0,
            "windspeedmph": 7.0,
            "windgustmph": 11.0,
        },
    ]

    def fake_get_recent_observations_for_columns(hours: int, columns: list[str]):
        assert hours == 24
        assert "tempf" in columns
        assert "feels_like" in columns
        assert "windspeedmph" in columns
        assert "windgustmph" in columns
        return fake_rows

    monkeypatch.setattr(
        "ambient_tool.trend.get_recent_observations_for_columns",
        fake_get_recent_observations_for_columns,
    )

    results = summarize_trends(
        hours=24,
        show_fields=["gust_delta", "feels_like_delta"],
    )

    result_map = {result.field.name: result for result in results}

    gust_delta_result = result_map["gust_delta"]
    assert gust_delta_result.stats.latest == 4.0
    assert gust_delta_result.stats.min_value == 4.0
    assert gust_delta_result.stats.max_value == 6.5
    assert gust_delta_result.stats.avg_value == 5.5
    assert gust_delta_result.stats.sample_count == 3
    assert gust_delta_result.tendency is None

    feels_like_delta_result = result_map["feels_like_delta"]
    assert feels_like_delta_result.stats.latest == -2.0
    assert feels_like_delta_result.stats.min_value == -5.0
    assert feels_like_delta_result.stats.max_value == -2.0
    assert feels_like_delta_result.stats.avg_value == -11.0 / 3.0
    assert feels_like_delta_result.stats.sample_count == 3
    assert feels_like_delta_result.tendency is None

from ambient_tool.trend import (
    compute_pressure_tendency_3hr,
    compute_rolling_pressure_tendency_3hr,
    compute_rolling_rainfall_rate,
)

def test_compute_pressure_tendency_3hr():
    rows = [
        {
            "observation_time_utc": "2026-04-24T00:00:00+00:00",
            "baromrelin": 29.80,
        },
        {
            "observation_time_utc": "2026-04-24T01:00:00+00:00",
            "baromrelin": 29.78,
        },
        {
            "observation_time_utc": "2026-04-24T03:00:00+00:00",
            "baromrelin": 29.70,
        },
    ]

    assert compute_pressure_tendency_3hr(rows) == pytest.approx(-0.10)

def test_compute_rolling_pressure_tendency_3hr():
    rows = [
        {
            "observation_time_utc": "2026-04-24T00:00:00+00:00",
            "baromrelin": 29.80,
        },
        {
            "observation_time_utc": "2026-04-24T01:00:00+00:00",
            "baromrelin": 29.78,
        },
        {
            "observation_time_utc": "2026-04-24T03:00:00+00:00",
            "baromrelin": 29.70,
        },
        {
            "observation_time_utc": "2026-04-24T04:00:00+00:00",
            "baromrelin": 29.74,
        },
    ]

    assert compute_rolling_pressure_tendency_3hr(rows) == [
        None,
        None,
        pytest.approx(-0.10),
        pytest.approx(-0.04),
    ]

def test_compute_rolling_rainfall_rate():
    rows = [
        {
            "observation_time_utc": "2026-04-24T00:00:00+00:00",
            "hourlyrainin": 0.00,
        },
        {
            "observation_time_utc": "2026-04-24T00:10:00+00:00",
            "hourlyrainin": 0.05,
        },
        {
            "observation_time_utc": "2026-04-24T00:20:00+00:00",
            "hourlyrainin": 0.10,
        },
    ]

    values = compute_rolling_rainfall_rate(rows)

    assert values[0] is None
    assert values[1] == pytest.approx(0.30)
    assert values[2] == pytest.approx(0.30)
