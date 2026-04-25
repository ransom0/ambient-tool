from __future__ import annotations

from dataclasses import dataclass

from ambient_tool.query import get_recent_observations_for_columns
from ambient_tool.trend import compute_rolling_overnight_low


@dataclass(frozen=True)
class FrostRiskReport:
    hours: int
    risk: str
    reason: str
    meaning: str
    next_check: str
    overnight_low: float | None
    current_temp: float | None
    current_dew_point: float | None
    current_wind_mph: float | None
    spread: float | None

def _to_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def classify_frost_risk(
    *,
    overnight_low: float | None,
    current_temp: float | None,
    current_dew_point: float | None,
    current_wind_mph: float | None,
) -> tuple[str, str]:
    if overnight_low is None:
        return "Unknown", "Not enough temperature data to estimate overnight low."

    if overnight_low <= 32.0:
        return "Freeze Risk", "Overnight low is at or below freezing."

    if overnight_low <= 36.0:
        if current_wind_mph is not None and current_wind_mph <= 5.0:
            return "Frost Likely", "Overnight low is near freezing with light wind."
        return "Frost Watch", "Overnight low is near freezing."

    if overnight_low <= 40.0:
        if current_dew_point is not None and current_dew_point <= 36.0:
            return "Frost Watch", "Overnight low is chilly and dew point is low."
        return "Frost Watch", "Overnight low is within the frost-watch range."

    return "None", "Overnight low is above the frost-risk range."

def interpret_risk(risk: str) -> str:
    if risk == "Freeze Risk":
        return "Sensitive plants may need protection or covering."
    if risk == "Frost Likely":
        return "Surface frost is plausible in exposed areas."
    if risk == "Frost Watch":
        return "Conditions are borderline. Continue monitoring."
    if risk == "None":
        return "No significant frost concern indicated."
    return "Insufficient data for interpretation."


def next_check_advice(risk: str) -> str:
    if risk == "Freeze Risk":
        return "Recheck near sunset and before dawn."
    if risk == "Frost Likely":
        return "Recheck after midnight if winds stay light."
    if risk == "Frost Watch":
        return "Recheck late evening as temperatures fall."
    if risk == "None":
        return "Check again only if forecast trends colder."
    return "Wait for more observations."

def build_frost_risk_report(hours: int) -> FrostRiskReport:
    rows = get_recent_observations_for_columns(
        hours=hours,
        columns=[
            "observation_time_utc",
            "tempf",
            "dew_point",
            "windspeedmph",
        ],
    )

    if not rows:
        return FrostRiskReport(
            hours=hours,
            risk="Unknown",
            reason="No local observations found for the requested time range.",
            meaning="Insufficient data for interpretation.",
            next_check="Wait for more observations.",
            overnight_low=None,
            current_temp=None,
            current_dew_point=None,
            current_wind_mph=None,
            spread=None,
        )

    overnight_values = compute_rolling_overnight_low(rows)
    clean_overnight_values = [
        value for value in overnight_values if value is not None
    ]
    overnight_low = min(clean_overnight_values) if clean_overnight_values else None

    latest = rows[-1]
    current_temp = _to_float(latest["tempf"])
    current_dew_point = _to_float(latest["dew_point"])
    current_wind_mph = _to_float(latest["windspeedmph"])
    spread = None
    if current_temp is not None and current_dew_point is not None:
        spread = current_temp - current_dew_point

    risk, reason = classify_frost_risk(
        overnight_low=overnight_low,
        current_temp=current_temp,
        current_dew_point=current_dew_point,
        current_wind_mph=current_wind_mph,
    )

    return FrostRiskReport(
        hours=hours,
        risk=risk,
        reason=reason,
        meaning=interpret_risk(risk),
        next_check=next_check_advice(risk),
        overnight_low=overnight_low,
        current_temp=current_temp,
        current_dew_point=current_dew_point,
        current_wind_mph=current_wind_mph,
        spread=spread,
    )
