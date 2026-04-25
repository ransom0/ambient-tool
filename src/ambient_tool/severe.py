from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StormSetupReport:
    headline: str
    signals: list[str]


def build_storm_setup_report(
    *,
    pressure_tendency_3hr: float | None,
    temp_dewpoint_spread: float | None,
    gust_delta: float | None,
    rainfall_rate: float | None,
) -> StormSetupReport:
    signals: list[str] = []

    if pressure_tendency_3hr is None:
        signals.append("pressure unavailable")
    elif pressure_tendency_3hr <= -0.06:
        signals.append("falling pressure")
    elif pressure_tendency_3hr >= 0.06:
        signals.append("rising pressure")
    else:
        signals.append("steady pressure")

    if temp_dewpoint_spread is None:
        signals.append("moisture unavailable")
    elif temp_dewpoint_spread <= 8.0:
        signals.append("moist air")
    else:
        signals.append("dry air")

    if gust_delta is None:
        signals.append("gust signal unavailable")
    elif gust_delta >= 10.0:
        signals.append("gusty wind signal")
    else:
        signals.append("weak gust signal")

    if rainfall_rate is None:
        signals.append("rainfall rate unavailable")
    elif rainfall_rate >= 0.5:
        signals.append("active rainfall")
    elif rainfall_rate > 0:
        signals.append("light/moderate rainfall")
    else:
        signals.append("no recent rainfall")

    if (
        pressure_tendency_3hr is None
        and temp_dewpoint_spread is None
        and gust_delta is None
        and rainfall_rate is None
    ):
        return StormSetupReport(
            headline="Storm setup is unavailable.",
            signals=signals,
        )

    if rainfall_rate is not None and rainfall_rate >= 0.5:
        return StormSetupReport(
            headline="Rain-cooled or active rainfall pattern.",
            signals=signals,
        )

    falling_pressure = pressure_tendency_3hr is not None and pressure_tendency_3hr <= -0.06
    moist_air = temp_dewpoint_spread is not None and temp_dewpoint_spread <= 8.0
    gusty_wind = gust_delta is not None and gust_delta >= 10.0

    if falling_pressure and moist_air and gusty_wind:
        return StormSetupReport(
            headline="Monitor for storm development.",
            signals=signals,
        )

    if falling_pressure and (moist_air or gusty_wind):
        return StormSetupReport(
            headline="Potential unsettled pattern.",
            signals=signals,
        )

    return StormSetupReport(
        headline="Quiet / weak storm signal.",
        signals=signals,
    )


def describe_storm_setup(
    *,
    pressure_tendency_3hr: float | None,
    temp_dewpoint_spread: float | None,
    gust_delta: float | None,
    rainfall_rate: float | None,
) -> str:
    return build_storm_setup_report(
        pressure_tendency_3hr=pressure_tendency_3hr,
        temp_dewpoint_spread=temp_dewpoint_spread,
        gust_delta=gust_delta,
        rainfall_rate=rainfall_rate,
    ).headline
