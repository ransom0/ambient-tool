from __future__ import annotations

from ambient_tool.severe import build_storm_setup_report, describe_storm_setup


def test_describe_storm_setup_unavailable() -> None:
    result = describe_storm_setup(
        pressure_tendency_3hr=None,
        temp_dewpoint_spread=None,
        gust_delta=None,
        rainfall_rate=None,
    )

    assert result == "Storm setup is unavailable."


def test_describe_storm_setup_rain_cooled() -> None:
    result = describe_storm_setup(
        pressure_tendency_3hr=-0.02,
        temp_dewpoint_spread=3.0,
        gust_delta=4.0,
        rainfall_rate=0.75,
    )

    assert result == "Rain-cooled or active rainfall pattern."


def test_describe_storm_setup_monitor_for_development() -> None:
    result = describe_storm_setup(
        pressure_tendency_3hr=-0.08,
        temp_dewpoint_spread=5.0,
        gust_delta=12.0,
        rainfall_rate=0.0,
    )

    assert result == "Monitor for storm development."


def test_describe_storm_setup_potential_unsettled() -> None:
    result = describe_storm_setup(
        pressure_tendency_3hr=-0.08,
        temp_dewpoint_spread=6.0,
        gust_delta=3.0,
        rainfall_rate=0.0,
    )

    assert result == "Potential unsettled pattern."


def test_describe_storm_setup_quiet() -> None:
    result = describe_storm_setup(
        pressure_tendency_3hr=0.01,
        temp_dewpoint_spread=18.0,
        gust_delta=2.0,
        rainfall_rate=0.0,
    )

    assert result == "Quiet / weak storm signal."

def test_build_storm_setup_report_includes_signals() -> None:
    report = build_storm_setup_report(
        pressure_tendency_3hr=-0.08,
        temp_dewpoint_spread=5.0,
        gust_delta=12.0,
        rainfall_rate=0.0,
    )

    assert report.headline == "Monitor for storm development."
    assert "falling pressure" in report.signals
    assert "moist air" in report.signals
    assert "gusty wind signal" in report.signals
    assert "no recent rainfall" in report.signals
