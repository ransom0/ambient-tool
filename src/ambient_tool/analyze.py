from __future__ import annotations

from dataclasses import dataclass

from ambient_tool.frost import FrostRiskReport
from ambient_tool.severe import describe_storm_setup


@dataclass(frozen=True)
class LocalWeatherAnalysis:
    hours: int
    pressure: str
    moisture: str
    rain: str
    storm_setup: str
    frost: str


def describe_pressure_tendency(value: float | None) -> str:
    if value is None:
        return "Pressure tendency is unavailable."

    if value <= -0.06:
        return f"Pressure is falling ({value:.2f} inHg/3hr)."
    if value >= 0.06:
        return f"Pressure is rising ({value:.2f} inHg/3hr)."
    return f"Pressure is mostly steady ({value:.2f} inHg/3hr)."


def describe_moisture(*, current_temp: float | None, current_dew_point: float | None) -> str:
    if current_temp is None or current_dew_point is None:
        return "Moisture information is unavailable."

    spread = current_temp - current_dew_point

    if spread <= 3.0:
        return f"Air is very moist; temp/dew point spread is {spread:.1f} °F."
    if spread <= 8.0:
        return f"Air is moderately moist; temp/dew point spread is {spread:.1f} °F."
    return f"Air is relatively dry; temp/dew point spread is {spread:.1f} °F."


def describe_rainfall_rate(value: float | None) -> str:
    if value is None:
        return "Rainfall rate is unavailable."

    if value <= 0:
        return "No recent rainfall rate indicated."
    if value < 0.10:
        return f"Light recent rainfall rate indicated ({value:.2f} in/hr)."
    if value < 0.50:
        return f"Moderate recent rainfall rate indicated ({value:.2f} in/hr)."
    return f"Heavy recent rainfall rate indicated ({value:.2f} in/hr)."


def describe_frost(report: FrostRiskReport) -> str:
    return f"{report.risk}: {report.meaning}"


def build_local_weather_analysis(
    *,
    hours: int,
    pressure_tendency_3hr: float | None,
    rainfall_rate: float | None,
    gust_delta: float | None = None,
    frost_report: FrostRiskReport,
) -> LocalWeatherAnalysis:
    return LocalWeatherAnalysis(
        hours=hours,
        pressure=describe_pressure_tendency(pressure_tendency_3hr),
        moisture=describe_moisture(
            current_temp=frost_report.current_temp,
            current_dew_point=frost_report.current_dew_point,
        ),
        rain=describe_rainfall_rate(rainfall_rate),
        storm_setup=describe_storm_setup(
            pressure_tendency_3hr=pressure_tendency_3hr,
            temp_dewpoint_spread=frost_report.spread,
            gust_delta=gust_delta,
            rainfall_rate=rainfall_rate,
        ),
        frost=describe_frost(frost_report),
    )
