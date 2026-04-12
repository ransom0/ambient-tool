from __future__ import annotations

from ambient_tool.derived import (
    add_derived_fields,
    compute_derived_value,
    derived_field_names,
    is_derived_field,
    required_source_fields,
    split_requested_fields,
)


def test_derived_field_names_contains_spread() -> None:
    assert derived_field_names() == ("spread",)


def test_is_derived_field_identifies_spread() -> None:
    assert is_derived_field("spread") is True
    assert is_derived_field("tempf") is False


def test_required_source_fields_for_spread() -> None:
    assert required_source_fields("spread") == ("tempf", "dew_point")


def test_compute_derived_value_spread() -> None:
    row = {"tempf": 72.0, "dew_point": 60.5}
    assert compute_derived_value("spread", row) == 11.5


def test_compute_derived_value_spread_returns_none_when_missing() -> None:
    assert compute_derived_value("spread", {"dew_point": 60.0}) is None
    assert compute_derived_value("spread", {"tempf": 72.0}) is None


def test_add_derived_fields_adds_spread() -> None:
    rows = [{"tempf": 75.0, "dew_point": 63.0}]
    assert add_derived_fields(rows, ["spread"]) == [
        {"tempf": 75.0, "dew_point": 63.0, "spread": 12.0}
    ]


def test_split_requested_fields_separates_raw_and_derived() -> None:
    raw_fields, derived_fields = split_requested_fields(
        ["humidity", "spread", "tempf"]
    )
    assert raw_fields == ["humidity", "tempf"]
    assert derived_fields == ["spread"]
