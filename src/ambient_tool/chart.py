from __future__ import annotations

from pathlib import Path

import matplotlib

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
    ax,
    times: list[datetime],
    values: list[float | None],
    label: str,
    style: str,
    fill_baseline: float | None = None,
    color: str | None = None,
) -> None:
    if style == "line":
        ax.plot(times, values, label=label, linewidth=2, color=color)
        return

    if style == "step":
        ax.step(times, values, label=label, linewidth=2, where="post", color=color)
        return

    if style == "area":
        ax.plot(times, values, label=label, linewidth=2, color=color)
        baseline = 0.0 if fill_baseline is None else fill_baseline
        ax.fill_between(times, values, baseline, alpha=0.25, color=color)
        return

    if style == "bar":
        ax.bar(times, values, label=label, width=0.02, color=color)
        return

    raise ValueError(f"Unsupported chart style: {style}")

def build_chart(
    *,
    hours: int,
    show: list[str],
    out: Path,
    last: int | None = None,
    style: str = "line",
    dual_axis: bool = False,
) -> Path:
    requested_fields = normalize_show_fields(show)
    if dual_axis:
        if len(requested_fields) != 2:
            raise ValueError("--dual-axis requires exactly two fields")
        if style not in {"line", "step"}:
            raise ValueError("--dual-axis only supports line or step charts")
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
    series_to_plot: list[tuple[str, list[float | None]]] = []

    for field_name in requested_fields:
        field = TREND_FIELDS[field_name]
        values = [field.value_getter(row) for row in rows]

        series_to_plot.append((field.label, values))
        units.add(field.unit)

    fig, ax = plt.subplots(figsize=(11, 5))

    if dual_axis:
        left_field_name = requested_fields[0]
        right_field_name = requested_fields[1]
        left_field = TREND_FIELDS[left_field_name]
        right_field = TREND_FIELDS[right_field_name]

        left_label, left_values = series_to_plot[0]
        right_label, right_values = series_to_plot[1]

        left_y_min, left_y_max = get_y_axis_bounds(
            series_values=[left_values],
            units={left_field.unit},
            style=style,
        )
        right_y_min, right_y_max = get_y_axis_bounds(
            series_values=[right_values],
            units={right_field.unit},
            style=style,
        )

        plot_series(
            ax=ax,
            times=times,
            values=left_values,
            label=left_label,
            style=style,
            color="tab:blue",
        )

        ax_right = ax.twinx()

        plot_series(
            ax=ax_right,
            times=times,
            values=right_values,
            label=right_label,
            style=style,
            color="tab:orange",
        )

        if left_y_min is not None and left_y_max is not None:
            ax.set_ylim(left_y_min, left_y_max)

        if right_y_min is not None and right_y_max is not None:
            ax_right.set_ylim(right_y_min, right_y_max)

        ax.set_ylabel(left_field.unit, color="tab:blue")
        ax_right.set_ylabel(right_field.unit, color="tab:orange")

        ax.tick_params(axis="y", colors="tab:blue")
        ax_right.tick_params(axis="y", colors="tab:orange")

        left_handles, left_labels = ax.get_legend_handles_labels()
        right_handles, right_labels = ax_right.get_legend_handles_labels()
        ax.legend(
            left_handles + right_handles,
            left_labels + right_labels,
            loc="best",
        )
    else:
        y_min, y_max = get_y_axis_bounds(
            series_values=[values for _, values in series_to_plot],
            units=units,
            style=style,
        )

        for label, values in series_to_plot:
            plot_series(
                ax=ax,
                times=times,
                values=values,
                label=label,
                style=style,
                fill_baseline=y_min,
            )

        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)

        if len(units) == 1:
            ax.set_ylabel(next(iter(units)))
        else:
            ax.set_ylabel("Mixed Units")

        ax.legend()

    title = " / ".join(TREND_FIELDS[name].label for name in requested_fields)
    axis_note = " Dual Axis" if dual_axis else ""

    ax.set_title(f"{title} — Last {hours} Hour(s) — {style.title()}{axis_note} Chart")
    ax.set_xlabel("Observation Time (UTC)")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))

    ax.tick_params(axis="x", rotation=0)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png", dpi=140)
    plt.close(fig)

    return out
