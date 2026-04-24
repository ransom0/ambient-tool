from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from ambient_tool.query import get_recent_observations_for_columns


CHART_FIELDS: dict[str, str] = {
    "temp": "tempf",
    "dewpoint": "dew_point",
    "pressure": "baromrelin",
}


def build_chart(
    *,
    hours: int,
    show: list[str],
    out: Path,
) -> Path:
    if not show:
        raise ValueError("At least one field is required.")

    unknown = [field for field in show if field not in CHART_FIELDS]
    if unknown:
        valid = ", ".join(sorted(CHART_FIELDS))
        raise ValueError(f"Unknown chart field(s): {', '.join(unknown)}. Valid fields: {valid}")

    columns = [CHART_FIELDS[field] for field in show]
    rows = get_recent_observations_for_columns(hours=hours, columns=columns)

    if not rows:
        raise ValueError("No local observations found for the requested time range.")

    times = [row["observation_time_utc"] for row in rows]

    plt.figure(figsize=(10, 5))

    for field in show:
        column = CHART_FIELDS[field]
        values = [row[column] for row in rows]
        plt.plot(times, values, label=field)

    plt.xlabel("Observation time UTC")
    plt.ylabel("Value")
    plt.title(f"Ambient Weather chart - last {hours} hours")
    plt.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, format="png")
    plt.close()

    return out
