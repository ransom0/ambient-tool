from pathlib import Path

import pytest

from ambient_tool.chart import build_chart, get_y_axis_bounds


def test_build_chart_writes_png(tmp_path, monkeypatch):
    def fake_rows(*, hours, columns):
        assert hours == 24
        assert columns == ["observation_time_utc", "tempf", "dew_point"]
        return [
            {
                "observation_time_utc": "2026-04-24T00:00:00+00:00",
                "tempf": 70.0,
                "dew_point": 60.0,
            },
            {
                "observation_time_utc": "2026-04-24T01:00:00+00:00",
                "tempf": 72.0,
                "dew_point": 61.0,
            },
        ]

    monkeypatch.setattr("ambient_tool.chart.get_recent_observations_for_columns", fake_rows)

    out = tmp_path / "chart.png"
    result = build_chart(hours=24, show=["temp", "dewpoint"], out=out)

    assert result == out
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")


def test_build_chart_rejects_unknown_field(tmp_path):
    with pytest.raises(ValueError, match="Unknown trend field"):
        build_chart(hours=24, show=["rain"], out=tmp_path / "chart.png")


def test_build_chart_rejects_empty_local_data(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ambient_tool.chart.get_recent_observations_for_columns",
        lambda *, hours, columns: [],
    )

    with pytest.raises(ValueError, match="No local observations"):
        build_chart(hours=24, show=["pressure"], out=tmp_path / "chart.png")

def test_build_chart_supports_bar_style(tmp_path, monkeypatch):
    def fake_rows(*, hours, columns):
        return [
            {
                "observation_time_utc": "2026-04-24T00:00:00+00:00",
                "hourlyrainin": 0.0,
            },
            {
                "observation_time_utc": "2026-04-24T01:00:00+00:00",
                "hourlyrainin": 0.12,
            },
        ]

    monkeypatch.setattr(
        "ambient_tool.chart.get_recent_observations_for_columns",
        fake_rows,
    )

    out = tmp_path / "rain_bar.png"

    result = build_chart(
        hours=24,
        show=["hourlyrain"],
        out=out,
        style="bar",
    )

    assert result == out
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")

def test_get_y_axis_bounds_uses_data_padding_for_pressure():
    y_min, y_max = get_y_axis_bounds(
        series_values=[[29.42, 29.45, 29.48]],
        units={"inHg"},
        style="line",
    )

    assert y_min is not None
    assert y_max is not None
    assert y_min > 29.0
    assert y_max < 30.0
    assert y_min < 29.42
    assert y_max > 29.48


def test_get_y_axis_bounds_keeps_rain_bar_baseline_at_zero():
    y_min, y_max = get_y_axis_bounds(
        series_values=[[0.0, 0.12, 0.3]],
        units={"in"},
        style="bar",
    )

    assert y_min == 0.0
    assert y_max is not None
    assert y_max > 0.3

def test_build_chart_supports_dual_axis(tmp_path, monkeypatch):
    def fake_rows(*, hours, columns):
        assert columns == ["observation_time_utc", "tempf", "baromrelin"]
        return [
            {
                "observation_time_utc": "2026-04-24T00:00:00+00:00",
                "tempf": 70.0,
                "baromrelin": 29.42,
            },
            {
                "observation_time_utc": "2026-04-24T01:00:00+00:00",
                "tempf": 72.0,
                "baromrelin": 29.45,
            },
        ]

    monkeypatch.setattr(
        "ambient_tool.chart.get_recent_observations_for_columns",
        fake_rows,
    )

    out = tmp_path / "dual_axis.png"

    result = build_chart(
        hours=24,
        show=["temp", "pressure"],
        out=out,
        dual_axis=True,
    )

    assert result == out
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")

def test_build_chart_rejects_dual_axis_with_more_than_two_fields(tmp_path):
    with pytest.raises(ValueError, match="requires exactly two fields"):
        build_chart(
            hours=24,
            show=["temp", "dewpoint", "pressure"],
            out=tmp_path / "bad.png",
            dual_axis=True,
        )


def test_build_chart_rejects_dual_axis_with_bar_style(tmp_path):
    with pytest.raises(ValueError, match="only supports line or step"):
        build_chart(
            hours=24,
            show=["temp", "pressure"],
            out=tmp_path / "bad.png",
            style="bar",
            dual_axis=True,
        )
