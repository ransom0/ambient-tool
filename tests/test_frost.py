from __future__ import annotations

from ambient_tool.frost import build_frost_risk_report, classify_frost_risk


def test_classify_frost_risk_freeze() -> None:
    risk, reason = classify_frost_risk(
        overnight_low=31.9,
        current_temp=34.0,
        current_dew_point=30.0,
        current_wind_mph=3.0,
    )

    assert risk == "Freeze Risk"
    assert "freezing" in reason


def test_classify_frost_risk_likely_with_light_wind() -> None:
    risk, reason = classify_frost_risk(
        overnight_low=35.0,
        current_temp=38.0,
        current_dew_point=33.0,
        current_wind_mph=2.0,
    )

    assert risk == "Frost Likely"
    assert "light wind" in reason


def test_classify_frost_risk_watch_near_40() -> None:
    risk, reason = classify_frost_risk(
        overnight_low=39.0,
        current_temp=42.0,
        current_dew_point=35.0,
        current_wind_mph=8.0,
    )

    assert risk == "Frost Watch"
    assert "dew point" in reason


def test_classify_frost_risk_none() -> None:
    risk, reason = classify_frost_risk(
        overnight_low=45.0,
        current_temp=48.0,
        current_dew_point=41.0,
        current_wind_mph=6.0,
    )

    assert risk == "None"
    assert "above" in reason


def test_build_frost_risk_report(monkeypatch) -> None:
    rows = [
        {
            "observation_time_utc": "2026-04-25T00:00:00+00:00",
            "tempf": 39.0,
            "dew_point": 34.0,
            "windspeedmph": 3.0,
        },
        {
            "observation_time_utc": "2026-04-25T09:00:00+00:00",
            "tempf": 35.0,
            "dew_point": 32.0,
            "windspeedmph": 2.0,
        },
    ]

    def fake_get_recent_observations_for_columns(*, hours, columns):
        assert hours == 24
        assert columns == [
            "observation_time_utc",
            "tempf",
            "dew_point",
            "windspeedmph",
        ]
        return rows

    monkeypatch.setattr(
        "ambient_tool.frost.get_recent_observations_for_columns",
        fake_get_recent_observations_for_columns,
    )

    report = build_frost_risk_report(hours=24)

    assert report.hours == 24
    assert report.risk == "Frost Likely"
    assert report.overnight_low == 35.0
    assert report.current_temp == 35.0
    assert report.current_dew_point == 32.0
    assert report.current_wind_mph == 2.0
