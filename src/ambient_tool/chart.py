from __future__ import annotations

from pathlib import Path

import matplotlib
from matplotlib import units

matplotlib.use("Agg")

from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from ambient_tool.query import get_recent_observations_for_columns
from ambient_tool.trend import TREND_FIELDS, normalize_show_fields

def clean_numeric_values(values: list[float | None]) -> list[float]:
    return [value for value in values if value is not None]


def get_y_axis_bounds(
    *,
    series_values: list[list[float | None]],
    units: set[str],
    style: str,
) -> tuple[float | None, float | None]:
    all_values: list[float] = []

    for values in series_values:
        all_values.extend(clean_numeric_values(values))

    if not all_values:
        return None, None

    min_value = min(all_values)
    max_value = max(all_values)

    if style == "bar" or units == {"in"}:
        upper = max_value * 1.15 if max_value > 0 else 1.0
        return 0.0, upper

    if min_value == max_value:
        padding = abs(min_value) * 0.05 if min_value else 1.0
        return min_value - padding, max_value + padding

    data_range = max_value - min_value
    padding = data_range * 0.10

    return min_value - padding, max_value + padding

def plot_series(
    *,
    times: list[datetime],
    values: list[float | None],
    label: str,
    style: str,
    fill_baseline: float | None = None,
) -> None:
    if style == "line":
        plt.plot(times, values, label=label, linewidth=2)
        return

    if style == "step":
        plt.step(times, values, label=label, linewidth=2, where="post")
        return

    if style == "area":
        plt.plot(times, values, label=label, linewidth=2)
        baseline = 0.0 if fill_baseline is None else fill_baseline
        plt.fill_between(times, values, baseline, alpha=0.25)
        return

    if style == "bar":
        plt.bar(times, values, label=label, width=0.02)
        return

    raise ValueError(f"Unsupported chart style: {style}")

def build_chart(
    *,
    hours: int,
    show: list[str],
    out: Path,
    last: int | None = None,
    style: str = "line",
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

    units: set[str] = set()
    series_to_plot: list[tuple[str, list[float | None]]] = []

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        values = [field.value_getter(row) for row in rows]

        series_to_plot.append((field.label, values))
        units.add(field.unit)

    y_min, y_max = get_y_axis_bounds(
        series_values=[values for _, values in series_to_plot],
        units=units,
        style=style,
    )

    for label, values in series_to_plot:
        plot_series(
            times=times,
            values=values,
            label=label,
            style=style,
            fill_baseline=y_min,
    )

    title = " / ".join(TREND_FIELDS[name].label for name in requested_fields)

    plt.title(f"{title} — Last {hours} Hour(s) — {style.title()} Chart")
    plt.xlabel("Observation Time (UTC)")

    if len(units) == 1:
        plt.ylabel(next(iter(units)))
    else:
        plt.ylabel("Mixed Units")

    ax = plt.gca()

    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)

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
