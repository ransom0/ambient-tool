from __future__ import annotations

from ambient_tool.trend import (
    TREND_FIELDS,
    TrendStatBlock,
    normalize_show_fields,
    summarize_trends,
)


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

def test_summarize_trends_computes_stats_and_spread(monkeypatch) -> None:
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

    result_map = {field.name: stats for field, stats in results}

    temp_stats = result_map["temp"]
    assert temp_stats.latest == 68.0
    assert temp_stats.min_value == 68.0
    assert temp_stats.max_value == 72.0
    assert temp_stats.sample_count == 3

    spread_stats = result_map["spread"]
    assert spread_stats.latest == 9.0
    assert spread_stats.min_value == 9.0
    assert spread_stats.max_value == 11.0
    assert spread_stats.avg_value == 10.0

    pressure_stats = result_map["pressure"]
    assert pressure_stats.latest == 29.99
    assert pressure_stats.min_value == 29.99
    assert pressure_stats.max_value == 30.03
    assert pressure_stats.sample_count == 3
