from __future__ import annotations

from ambient_tool.derived import (
    add_derived_fields,
    compute_derived_value,
    derived_field_names,
    is_derived_field,
    required_source_fields,
    split_requested_fields,
)


def test_derived_field_names_contains_expected_metrics() -> None:
    assert derived_field_names() == (
        "spread",
        "gust_delta",
        "feels_like_delta",
    )


def test_is_derived_field_identifies_supported_fields() -> None:
    assert is_derived_field("spread") is True
    assert is_derived_field("gust_delta") is True
    assert is_derived_field("feels_like_delta") is True
    assert is_derived_field("tempf") is False


def test_required_source_fields_for_spread() -> None:
    assert required_source_fields("spread") == ("tempf", "dew_point")


def test_required_source_fields_for_gust_delta() -> None:
    assert required_source_fields("gust_delta") == ("windspeedmph", "windgustmph")


def test_required_source_fields_for_feels_like_delta() -> None:
    assert required_source_fields("feels_like_delta") == ("tempf", "feels_like")


def test_compute_derived_value_spread() -> None:
    row = {"tempf": 72.0, "dew_point": 60.5}
    assert compute_derived_value("spread", row) == 11.5


def test_compute_derived_value_gust_delta() -> None:
    row = {"windspeedmph": 8.0, "windgustmph": 15.5}
    assert compute_derived_value("gust_delta", row) == 7.5


def test_compute_derived_value_feels_like_delta() -> None:
    row = {"tempf": 92.0, "feels_like": 98.0}
    assert compute_derived_value("feels_like_delta", row) == -6.0


def test_compute_derived_value_returns_none_when_inputs_missing() -> None:
    assert compute_derived_value("spread", {"dew_point": 60.0}) is None
    assert compute_derived_value("gust_delta", {"windgustmph": 15.0}) is None
    assert compute_derived_value("feels_like_delta", {"tempf": 90.0}) is None


def test_add_derived_fields_adds_multiple_metrics() -> None:
    rows = [
        {
            "tempf": 75.0,
            "dew_point": 63.0,
            "windspeedmph": 10.0,
            "windgustmph": 18.0,
            "feels_like": 79.0,
        }
    ]

    assert add_derived_fields(
        rows,
        ["spread", "gust_delta", "feels_like_delta"],
    ) == [
        {
            "tempf": 75.0,
            "dew_point": 63.0,
            "windspeedmph": 10.0,
            "windgustmph": 18.0,
            "feels_like": 79.0,
            "spread": 12.0,
            "gust_delta": 8.0,
            "feels_like_delta": -4.0,
        }
    ]


def test_split_requested_fields_separates_raw_and_derived() -> None:
    raw_fields, derived_fields = split_requested_fields(
        ["humidity", "gust_delta", "tempf", "spread"]
    )
    assert raw_fields == ["humidity", "tempf"]
    assert derived_fields == ["gust_delta", "spread"]
