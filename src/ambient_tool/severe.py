from __future__ import annotations


def describe_storm_setup(
    *,
    pressure_tendency_3hr: float | None,
    temp_dewpoint_spread: float | None,
    gust_delta: float | None,
    rainfall_rate: float | None,
) -> str:
    if (
        pressure_tendency_3hr is None
        and temp_dewpoint_spread is None
        and gust_delta is None
        and rainfall_rate is None
    ):
        return "Storm setup is unavailable."

    if rainfall_rate is not None and rainfall_rate >= 0.5:
        return "Rain-cooled or active rainfall pattern."

    falling_pressure = (
        pressure_tendency_3hr is not None
        and pressure_tendency_3hr <= -0.06
    )
    moist_air = (
        temp_dewpoint_spread is not None
        and temp_dewpoint_spread <= 8.0
    )
    gusty_wind = (
        gust_delta is not None
        and gust_delta >= 10.0
    )

    if falling_pressure and moist_air and gusty_wind:
        return "Monitor for storm development."

    if falling_pressure and (moist_air or gusty_wind):
        return "Potential unsettled pattern."

    return "Quiet / weak storm signal."
