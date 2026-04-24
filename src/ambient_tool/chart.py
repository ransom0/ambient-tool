from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from ambient_tool.query import get_recent_observations_for_columns
from ambient_tool.trend import TREND_FIELDS, normalize_show_fields

def build_chart(
    *,
    hours: int,
    show: list[str],
    out: Path,
    last: int | None = None,
) -> Path:
    requested_fields = normalize_show_fields(show)

    required_columns: list[str] = ["observation_time_utc"]

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        for column in field.required_columns:
            if column not in required_columns:
                required_columns.append(column)

    rows = get_recent_observations_for_columns(
        hours=hours,
        columns=required_columns,
    )

    if last is not None:
        rows = rows[-last:] if last > 0 else []

    if not rows:
        raise ValueError("No local observations found for the requested time range.")

    times = [
        datetime.fromisoformat(row["observation_time_utc"].replace("Z", "+00:00"))
        for row in rows
    ]

    plt.figure(figsize=(11, 5))

    units: set[str] = set()

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        values = [field.value_getter(row) for row in rows]

        plt.plot(
            times,
            values,
            label=field.label,
            linewidth=2,
        )

        units.add(field.unit)

    title = " / ".join(TREND_FIELDS[name].label for name in requested_fields)

    plt.title(f"{title} — Last {hours} Hour(s)")
    plt.xlabel("Observation Time (UTC)")

    if len(units) == 1:
        plt.ylabel(next(iter(units)))
    else:
        plt.ylabel("Mixed Units")

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))

    plt.xticks(rotation=0)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, format="png", dpi=140)
    plt.close()

    return out
