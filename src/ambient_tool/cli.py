from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from pprint import pprint
from zoneinfo import ZoneInfo

from ambient_tool.chart import build_chart
from ambient_tool.client import build_client
from ambient_tool.derived import (
    add_derived_fields,
    derived_field_names,
    is_derived_field,
    required_source_fields,
    split_requested_fields,
)
from ambient_tool.export_csv import write_rows_to_csv
from ambient_tool.export_json import write_rows_to_json
from ambient_tool.query import (
    get_grouped_fieldnames,
    get_grouped_observations_for_columns,
    get_observation_database_summary,
    get_observations_for_columns,
    normalize_observation_columns,
)
from ambient_tool.storage import (
    init_db,
    migrate_add_unique_index,
    save_historical_observations,
    save_observations,
)
from ambient_tool.trend import get_recent_trend_rows, normalize_show_fields, summarize_trends


def format_device_summary(device) -> str:
    info = device.get("info", {})
    data = device.get("lastData", {})

    name = info.get("name", "Unknown Device")
    tempf = data.get("tempf", "N/A")
    humidity = data.get("humidity", "N/A")
    windspeed = data.get("windspeedmph", "N/A")
    winddir = data.get("winddir", "N/A")
    pressure = data.get("baromrelin", "N/A")
    monthly_rain = data.get("monthlyrainin", "N/A")

    return (
        f"{name}\n"
        f"  Temp: {tempf}°F\n"
        f"  Humidity: {humidity}%\n"
        f"  Wind: {windspeed} mph @ {winddir}°\n"
        f"  Pressure: {pressure} inHg\n"
        f"  Rain (month): {monthly_rain} in\n"
    )


def format_observation_time(device) -> str:
    data = device.get("lastData", {})
    tz_name = data.get("tz", "America/Chicago")
    dateutc = data.get("dateutc")

    if not dateutc:
        return "Unknown"

    dt_utc = datetime.fromtimestamp(dateutc / 1000, tz=ZoneInfo("UTC"))
    dt_local = dt_utc.astimezone(ZoneInfo(tz_name))
    return dt_local.strftime("%Y-%m-%d %I:%M:%S %p %Z")


def format_current_conditions(device) -> str:
    info = device.get("info", {})
    data = device.get("lastData", {})

    name = info.get("name", "Unknown Device")
    observed = format_observation_time(device)
    tempf = data.get("tempf", "N/A")
    feels_like = data.get("feelsLike", "N/A")
    humidity = data.get("humidity", "N/A")
    dew_point = data.get("dewPoint", "N/A")
    windspeed = data.get("windspeedmph", "N/A")
    windgust = data.get("windgustmph", "N/A")
    winddir = data.get("winddir", "N/A")
    pressure = data.get("baromrelin", "N/A")
    daily_rain = data.get("dailyrainin", "N/A")

    return (
        f"{name}\n"
        f"  Observed: {observed}\n"
        f"  Temp: {tempf}°F\n"
        f"  Feels like: {feels_like}°F\n"
        f"  Humidity: {humidity}%\n"
        f"  Dew point: {dew_point}°F\n"
        f"  Wind: {windspeed} mph @ {winddir}°\n"
        f"  Gust: {windgust} mph\n"
        f"  Pressure: {pressure} inHg\n"
        f"  Rain today: {daily_rain} in\n"
    )


def get_device_name(device) -> str:
    return device.get("info", {}).get("name", "Unknown Device")


def select_devices(devices, device_selector):
    if not device_selector:
        return devices

    selector = device_selector.strip()

    if selector.isdigit():
        index = int(selector)
        if index < 1 or index > len(devices):
            raise ValueError(
                f"Device index out of range: {index}. Valid range is 1 to {len(devices)}."
            )
        return [devices[index - 1]]

    matches = []
    selector_lower = selector.lower()

    for device in devices:
        name = get_device_name(device)
        if name.lower() == selector_lower:
            matches.append(device)

    if not matches:
        available = ", ".join(get_device_name(device) for device in devices)
        raise ValueError(
            f'No device matched "{device_selector}". Available devices: {available}'
        )

    return matches


def print_summary(devices) -> None:
    print(f"\nDevices found: {len(devices)}\n")
    for device in devices:
        print(format_device_summary(device))


def print_current(devices) -> None:
    print(f"\nDevices found: {len(devices)}\n")
    for device in devices:
        print(format_current_conditions(device))


def print_device_names(devices) -> None:
    print(f"\nDevices found: {len(devices)}\n")
    for index, device in enumerate(devices, start=1):
        name = get_device_name(device)
        mac = device.get("macAddress", "Unknown MAC")
        print(f"{index}. {name} ({mac})")


def print_raw(devices) -> None:
    pprint(devices)

def print_recent_trend_rows(
    *,
    rows,
    show_fields: list[str],
) -> None:
    if not rows:
        print("\nNo recent rows available for that time range.")
        return

    headers = ["time", *show_fields]

    table_rows: list[list[str]] = []

    for row in rows:
        table_row = [row.observation_time_utc]

        for field_name in show_fields:
            value = row.values[field_name]
            table_row.append("N/A" if value is None else f"{value:.2f}")

        table_rows.append(table_row)

    widths = [
        max(len(str(value)) for value in [header, *(row[index] for row in table_rows)])
        for index, header in enumerate(headers)
    ]

    def format_row(values: list[str]) -> str:
        return " | ".join(
            str(value).ljust(width)
            for value, width in zip(values, widths, strict=True)
        )

    print("\nRecent trend rows\n")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))

    for row in table_rows:
        print(format_row(row))


def save_snapshot(devices) -> None:
    init_db()
    migrate_add_unique_index()

    fetched_at_utc = datetime.now(UTC).isoformat()
    saved_count = save_observations(devices, fetched_at_utc)

    print(f"\nSaved {saved_count} observation(s)")
    print("Database: ~/.ambient_tool/ambient_weather.db")


SUPPORTED_GROUPED_HOURLY_FIELDS = {
    "tempf",
    "humidity",
    "dew_point",
    "baromrelin",
}

SUPPORTED_ROW_EXPORT_RAW_FIELDS = {
    "observation_time_utc",
    "tempf",
    "humidity",
    "dew_point",
    "baromrelin",
    "feels_like",
    "windspeedmph",
    "windgustmph",
    "winddir",
    "hourlyrainin",
    "dailyrainin",
    "weeklyrainin",
    "monthlyrainin",
    "yearlyrainin",
}


def validate_row_export_fields(fields: list[str]) -> None:
    supported = SUPPORTED_ROW_EXPORT_RAW_FIELDS | set(derived_field_names())
    unsupported = [field for field in fields if field not in supported]
    if unsupported:
        joined = ", ".join(sorted(unsupported))
        raise ValueError(f"Unsupported export field(s): {joined}")


def validate_grouped_hourly_fields(fields: list[str]) -> None:
    derived = [field for field in fields if is_derived_field(field)]
    if derived:
        joined = ", ".join(derived)
        supported = ", ".join(sorted(SUPPORTED_GROUPED_HOURLY_FIELDS))
        raise ValueError(
            "Grouped export does not support derived fields yet: "
            f"{joined}. Supported grouped hourly fields: {supported}"
        )

    unsupported = [
        field for field in fields if field not in SUPPORTED_GROUPED_HOURLY_FIELDS
    ]
    if unsupported:
        joined = ", ".join(sorted(unsupported))
        supported = ", ".join(sorted(SUPPORTED_GROUPED_HOURLY_FIELDS))
        raise ValueError(
            f"Unsupported grouped hourly field(s): {joined}. "
            f"Supported grouped hourly fields: {supported}"
        )


def backfill_history(client, devices, days: int | None = None) -> None:
    if days is not None and days < 1:
        raise ValueError("--days must be at least 1")

    init_db()
    migrate_add_unique_index()

    fetched_at_utc = datetime.now(UTC).isoformat()
    cutoff = None if days is None else datetime.now(UTC) - timedelta(days=days)

    total_saved = 0

    for device in devices:
        mac = device.get("macAddress")
        name = get_device_name(device)

        if not mac:
            print(f"Skipping {name}: missing macAddress")
            continue

        if days is None:
            print(
                f"\nBackfilling {name} ({mac}) until existing data overlap is reached..."
            )
        else:
            print(f"\nBackfilling {name} ({mac}) for the last {days} day(s)...")

        end_date = None
        device_saved = 0
        page_count = 0

        while True:
            page_count += 1
            rows = client.get_device_history(
                mac,
                end_date=end_date,
                limit=288,
            )

            if not rows:
                break

            kept_rows = []
            oldest_dt = None

            for row in rows:
                row_date = row.get("date")
                if not row_date:
                    continue

                row_dt = datetime.fromisoformat(row_date.replace("Z", "+00:00"))

                if oldest_dt is None or row_dt < oldest_dt:
                    oldest_dt = row_dt

                if cutoff is None or row_dt >= cutoff:
                    kept_rows.append(row)

            saved_now = save_historical_observations(
                mac_address=mac,
                device_name=name,
                history_rows=kept_rows,
                fetched_at_utc=fetched_at_utc,
            )
            device_saved += saved_now
            total_saved += saved_now

            print(
                f"  Page {page_count}: fetched {len(rows)} row(s), "
                f"saved {saved_now}, total saved for device {device_saved}"
            )

            if oldest_dt is None:
                break

            if cutoff is not None and oldest_dt < cutoff:
                break

            if cutoff is None and saved_now == 0:
                print("  Reached existing data overlap; stopping.")
                break

            oldest_ms = rows[-1].get("dateutc")
            if not oldest_ms:
                break

            end_date = oldest_ms - 1
            time.sleep(2.0)

        print(f"Finished {name}: saved {device_saved} row(s)")

    print(f"\nBackfill complete. Total new rows saved: {total_saved}")


def format_trend_value(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def print_trend_block(results, hours: int) -> None:
    print(f"\nTrend summary: last {hours} hour(s)\n")

    for result in results:
        field = result.field
        stats = result.stats
        tendency = result.tendency

        print(f"{field.label} ({field.name})")
        print(f" Latest:  {format_trend_value(stats.latest)} {field.unit}")
        print(f" Min:     {format_trend_value(stats.min_value)} {field.unit}")
        print(f" Max:     {format_trend_value(stats.max_value)} {field.unit}")
        print(f" Avg:     {format_trend_value(stats.avg_value)} {field.unit}")
        print(f" Samples: {stats.sample_count}")

        if tendency:
            print(f" Trend:   {tendency}")

        print()


def print_trend_table(results, hours: int) -> None:
    headers = ["Field", "Latest", "Min", "Max", "Avg", "Samples", "Trend"]
    rows: list[list[str]] = []

    for result in results:
        field = result.field
        stats = result.stats
        tendency = result.tendency

        rows.append(
            [
                f"{field.label} ({field.unit})",
                format_trend_value(stats.latest),
                format_trend_value(stats.min_value),
                format_trend_value(stats.max_value),
                format_trend_value(stats.avg_value),
                str(stats.sample_count),
                tendency or "-",
            ]
        )

    widths = [len(header) for header in headers]

    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def format_row(values: list[str]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        )

    print(f"\nTrend summary: last {hours} hour(s)\n")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))

    for row in rows:
        print(format_row(row))

    print()

def run_inspect() -> None:
    summary = get_observation_database_summary()

    print("\nAmbient local data inspection\n")
    print("Database: ~/.ambient_tool/ambient_weather.db")
    print(f"Rows:     {summary['row_count']}")
    print(f"Devices:  {summary['device_count']}")
    print(f"Oldest:   {summary['oldest_observation_time_utc'] or 'N/A'}")
    print(f"Newest:   {summary['newest_observation_time_utc'] or 'N/A'}")


def run_trend(
    show_fields: list[str] | None,
    hours: int,
    output_format: str,
    last: int | None = None,
) -> None:
    try:
        normalized_fields = normalize_show_fields(show_fields)
    except ValueError as exc:
        print(str(exc))
        return

    results = summarize_trends(hours=hours, show_fields=normalized_fields)

    if not results:
        print("No data available for that time range.")
        return

    if output_format == "table":
        print_trend_table(results, hours)
    else:
        print_trend_block(results, hours)

    if last is not None:
        if last <= 0:
            print("\n--last must be greater than 0.")
            return

        recent_rows = get_recent_trend_rows(
            hours=hours,
            show_fields=normalized_fields,
            limit=last,
        )
        print_recent_trend_rows(rows=recent_rows, show_fields=normalized_fields)

def get_export_rows(
    *,
    fields: list[str],
    hours: int | None = None,
    since: str | None = None,
    group_by: str | None = None,
):
    if group_by is None:
        validate_row_export_fields(fields)

        raw_fields, derived_fields = split_requested_fields(fields)

        required_columns = list(raw_fields)
        for derived in derived_fields:
            for dep in required_source_fields(derived):
                if dep not in required_columns:
                    required_columns.append(dep)

        query_columns = normalize_observation_columns(required_columns)
        rows = get_observations_for_columns(
            columns=query_columns,
            hours=hours,
            since=since,
        )

        enriched_rows = add_derived_fields(rows, derived_fields)

        fieldnames = list(fields)
        if "observation_time_utc" not in fieldnames:
            fieldnames.insert(0, "observation_time_utc")

        return fieldnames, enriched_rows

    validate_grouped_hourly_fields(fields)

    fieldnames = get_grouped_fieldnames(group_by, fields=fields)
    rows = get_grouped_observations_for_columns(
        columns=fields,
        group_by=group_by,
        hours=hours,
        since=since,
    )
    return fieldnames, rows


def run_export_csv(
    *,
    fields: list[str],
    output_path: str,
    hours: int | None = None,
    since: str | None = None,
    group_by: str | None = None,
) -> None:
    fieldnames, rows = get_export_rows(
        fields=fields,
        hours=hours,
        since=since,
        group_by=group_by,
    )

    if not rows:
        print("No data available for that time range.")
        return

    write_rows_to_csv(
        output_path=output_path,
        fieldnames=fieldnames,
        rows=rows,
    )

    print(f"Exported {len(rows)} row(s) to {output_path}")

def run_chart(args: argparse.Namespace) -> None:
    out = build_chart(
        hours=args.hours,
        show=args.show,
        out=args.out,
        last=args.last,
        style=args.style,
    )

    print(f"Chart written to {out}")

def run_export_json(
    *,
    fields: list[str],
    output_path: str,
    hours: int | None = None,
    since: str | None = None,
    group_by: str | None = None,
) -> None:
    fieldnames, rows = get_export_rows(
        fields=fields,
        hours=hours,
        since=since,
        group_by=group_by,
    )

    if not rows:
        print("No data available for that time range.")
        return

    write_rows_to_json(
        output_path=output_path,
        fieldnames=fieldnames,
        rows=rows,
    )

    print(f"Exported {len(rows)} row(s) to {output_path}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ambient",
        description="CLI for Ambient Weather data",
    )

    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser("summary", help="Show summarized weather data")
    summary_parser.add_argument("--device", help="Device index or exact device name")

    current_parser = subparsers.add_parser("current", help="Show current conditions")
    current_parser.add_argument("--device", help="Device index or exact device name")

    devices_parser = subparsers.add_parser(
        "devices", help="List device names and MAC addresses"
    )
    devices_parser.add_argument("--device", help="Device index or exact device name")

    raw_parser = subparsers.add_parser("raw", help="Show raw API response")
    raw_parser.add_argument("--device", help="Device index or exact device name")

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Fetch current data and save it to the local database",
    )
    snapshot_parser.add_argument("--device", help="Device index or exact device name")

    chart_parser = subparsers.add_parser(
        "chart",
        help="Create PNG chart from local weather data",
    )

    chart_parser.add_argument(
        "--hours",
        type=int,
        default=24,
    )

    chart_parser.add_argument(
        "--show",
        nargs="+",
        required=True,
    )

    chart_parser.add_argument(
        "--out",
        type=Path,
        default=Path("ambient_chart.png"),
    )

    chart_parser.add_argument(
        "--last",
        type=int,
        default=None,
        help="Use last N observations after filtering",
    )

    chart_parser.add_argument(
        "--style",
        choices=["line", "step", "area", "bar"],
        default="line",
        help="Chart style to render",
    )

    trend_parser = subparsers.add_parser(
        "trend",
        help="Show trend statistics from local data",
    )
    trend_parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to look back",
    )
    trend_parser.add_argument(
        "--format",
        dest="output_format",
        choices=["block", "table"],
        default="block",
        help="Output format for trend summaries",
    )
    trend_parser.add_argument(
        "--table",
        action="store_true",
        help="Shortcut for --format table",
    )
    trend_parser.add_argument(
        "--last",
        type=int,
        help="Show the last N timestamped rows for the requested fields",
    )
    trend_parser.add_argument(
        "--show",
        nargs="+",
        default=["temp"],
        metavar="FIELD",
        help="Fields to analyze, e.g. --show temp dewpoint pressure spread",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Export local observation data",
    )
    export_subparsers = export_parser.add_subparsers(dest="export_format")

    export_csv_parser = export_subparsers.add_parser(
        "csv",
        help="Export local observation data to CSV",
    )
    export_csv_time_group = export_csv_parser.add_mutually_exclusive_group(required=True)
    export_csv_time_group.add_argument(
        "--hours",
        type=int,
        help="Number of hours to look back",
    )
    export_csv_time_group.add_argument(
        "--since",
        help="ISO-8601 timestamp with timezone, e.g. 2026-04-10T15:00:00+00:00",
    )
    export_csv_parser.add_argument(
        "--fields",
        nargs="+",
        required=True,
        metavar="COLUMN",
        help=(
            "Observation columns to export in row mode, including derived fields like "
            "spread, gust_delta, and feels_like_delta. When using --group-by hour, "
            "supported grouped hourly fields are: tempf humidity dew_point baromrelin"
        ),
    )
    export_csv_parser.add_argument(
        "--group-by",
        choices=["hour"],
        help="Group exported rows by time bucket",
    )
    export_csv_parser.add_argument(
        "--out",
        required=True,
        help="Path to the output CSV file",
    )

    export_json_parser = export_subparsers.add_parser(
        "json",
        help="Export local observation data to JSON",
    )
    subparsers.add_parser(
        "inspect",
        help="Inspect local Ambient Weather database coverage",
    )
    export_json_time_group = export_json_parser.add_mutually_exclusive_group(required=True)
    export_json_time_group.add_argument(
        "--hours",
        type=int,
        help="Number of hours to look back",
    )
    export_json_time_group.add_argument(
        "--since",
        help="ISO-8601 timestamp with timezone, e.g. 2026-04-10T15:00:00+00:00",
    )
    export_json_parser.add_argument(
        "--fields",
        nargs="+",
        required=True,
        metavar="COLUMN",
        help=(
            "Observation columns to export in row mode, including derived fields like "
            "spread, gust_delta, and feels_like_delta. When using --group-by hour, "
            "supported grouped hourly fields are: tempf humidity dew_point baromrelin"
        ),
    )
    export_json_parser.add_argument(
        "--group-by",
        choices=["hour"],
        help="Group exported rows by time bucket",
    )
    export_json_parser.add_argument(
        "--out",
        required=True,
        help="Path to the output JSON file",
    )

    backfill_parser = subparsers.add_parser(
        "backfill",
        help="Fetch historical data from Ambient and save it to the local database",
    )
    backfill_parser.add_argument("--device", help="Device index or exact device name")
    backfill_parser.add_argument(
        "--days",
        type=int,
        help=(
            "Number of days of history to backfill. If omitted, backfill until "
            "existing data overlap is reached."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "summary"

    try:
        if command in {"summary", "current", "devices", "raw", "snapshot", "backfill"}:
            device_selector = getattr(args, "device", None)
            client = build_client()
            devices = client.get_devices()
            selected_devices = select_devices(devices, device_selector)

            if command == "summary":
                print_summary(selected_devices)
            elif command == "current":
                print_current(selected_devices)
            elif command == "devices":
                print_device_names(selected_devices)
            elif command == "raw":
                print_raw(selected_devices)
            elif command == "snapshot":
                save_snapshot(selected_devices)
            elif command == "backfill":
                backfill_history(client, selected_devices, args.days)

        elif command == "trend":
            output_format = "table" if args.table else args.output_format
            run_trend(args.show, args.hours, output_format, args.last)

        elif command == "chart":
            run_chart(args)

        elif command == "inspect":
            run_inspect()

        elif command == "export":
            if args.export_format == "csv":
                run_export_csv(
                    hours=args.hours,
                    since=args.since,
                    fields=args.fields,
                    output_path=args.out,
                    group_by=args.group_by,
                )
            elif args.export_format == "json":
                run_export_json(
                    hours=args.hours,
                    since=args.since,
                    fields=args.fields,
                    output_path=args.out,
                    group_by=args.group_by,
                )
            else:
                parser.error("Missing export format. Try: ambient export csv ...")
        else:
            parser.error(f"Unknown command: {command}")

    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
