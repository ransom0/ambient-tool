from __future__ import annotations

from ambient_tool.analyze import (
    build_local_weather_analysis,
    describe_moisture,
    describe_pressure_tendency,
    describe_rainfall_rate,
)
from ambient_tool.frost import FrostRiskReport


def test_describe_pressure_tendency_falling() -> None:
    result = describe_pressure_tendency(-0.08)

    assert "falling" in result
    assert "-0.08" in result


def test_describe_pressure_tendency_rising() -> None:
    result = describe_pressure_tendency(0.08)

    assert "rising" in result
    assert "0.08" in result


def test_describe_pressure_tendency_steady() -> None:
    result = describe_pressure_tendency(0.01)

    assert "steady" in result


def test_describe_moisture_very_moist() -> None:
    result = describe_moisture(current_temp=70.0, current_dew_point=68.0)

    assert "very moist" in result
    assert "2.0" in result


def test_describe_moisture_relatively_dry() -> None:
    result = describe_moisture(current_temp=80.0, current_dew_point=60.0)

    assert "relatively dry" in result
    assert "20.0" in result


def test_describe_rainfall_rate_none() -> None:
    result = describe_rainfall_rate(0.0)

    assert "No recent rainfall" in result


def test_describe_rainfall_rate_heavy() -> None:
    result = describe_rainfall_rate(0.75)

    assert "Heavy" in result
    assert "0.75" in result


def test_build_local_weather_analysis() -> None:
    frost_report = FrostRiskReport(
        hours=24,
        risk="Frost Watch",
        reason="Overnight low is within the frost-watch range.",
        meaning="Conditions are borderline. Continue monitoring.",
        next_check="Recheck late evening as temperatures fall.",
        overnight_low=39.0,
        current_temp=42.0,
        current_dew_point=38.0,
        current_wind_mph=4.0,
        spread=4.0,
    )

    analysis = build_local_weather_analysis(
        hours=24,
        pressure_tendency_3hr=-0.07,
        rainfall_rate=0.12,
        gust_delta=11.0,
        frost_report=frost_report,
    )

    assert analysis.hours == 24
    assert "falling" in analysis.pressure
    assert "moderately moist" in analysis.moisture
    assert "Moderate" in analysis.rain
    assert "Frost Watch" in analysis.frost
    assert "Monitor" in analysis.storm_setup.headline
    assert "falling pressure" in analysis.storm_setup.signals
