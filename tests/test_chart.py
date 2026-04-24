from pathlib import Path

import pytest

from ambient_tool.chart import build_chart


def test_build_chart_writes_png(tmp_path, monkeypatch):
    def fake_rows(*, hours, columns):
        assert hours == 24
        assert columns == ["tempf", "dew_point"]
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
    with pytest.raises(ValueError, match="Unknown chart field"):
        build_chart(hours=24, show=["rain"], out=tmp_path / "chart.png")


def test_build_chart_rejects_empty_local_data(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ambient_tool.chart.get_recent_observations_for_columns",
        lambda *, hours, columns: [],
    )

    with pytest.raises(ValueError, match="No local observations"):
        build_chart(hours=24, show=["pressure"], out=tmp_path / "chart.png")
