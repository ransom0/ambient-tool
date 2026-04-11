from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime, timedelta
from pprint import pprint
from zoneinfo import ZoneInfo

from ambient_tool.client import build_client
from ambient_tool.storage import (
    init_db,
    migrate_add_unique_index,
    save_historical_observations,
    save_observations,
)


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


def save_snapshot(devices) -> None:
    init_db()
    migrate_add_unique_index()

    fetched_at_utc = datetime.now(UTC).isoformat()
    saved_count = save_observations(devices, fetched_at_utc)

    print(f"\nSaved {saved_count} observation(s)")
    print("Database: ~/.ambient_tool/ambient_weather.db")


def backfill_history(client, devices, days: int) -> None:
    if days < 1:
        raise ValueError("--days must be at least 1")

    init_db()
    migrate_add_unique_index()

    fetched_at_utc = datetime.now(UTC).isoformat()
    cutoff = datetime.now(UTC) - timedelta(days=days)

    total_saved = 0

    for device in devices:
        mac = device.get("macAddress")
        name = get_device_name(device)

        if not mac:
            print(f"Skipping {name}: missing macAddress")
            continue

        print(f"\nBackfilling {name} ({mac}) for the last {days} day(s)...")

        end_date = None
        device_saved = 0
        page_count = 0

        while True:
            page_count += 1
            rows = client.get_device_history(mac, end_date=end_date, limit=288)

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

                if row_dt >= cutoff:
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

            if oldest_dt < cutoff:
                break

            oldest_ms = rows[-1].get("dateutc")
            if not oldest_ms:
                break

            end_date = oldest_ms - 1
            time.sleep(2.0)

        print(f"Finished {name}: saved {device_saved} row(s)")

    print(f"\nBackfill complete. Total new rows saved: {total_saved}")


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

    devices_parser = subparsers.add_parser("devices", help="List device names and MAC addresses")
    devices_parser.add_argument("--device", help="Device index or exact device name")

    raw_parser = subparsers.add_parser("raw", help="Show raw API response")
    raw_parser.add_argument("--device", help="Device index or exact device name")

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Fetch current data and save it to the local database",
    )
    snapshot_parser.add_argument("--device", help="Device index or exact device name")

    backfill_parser = subparsers.add_parser(
        "backfill",
        help="Fetch historical data from Ambient and save it to the local database",
    )
    backfill_parser.add_argument("--device", help="Device index or exact device name")
    backfill_parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Number of days of history to backfill",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "summary"
    device_selector = getattr(args, "device", None)

    client = build_client()
    devices = client.get_devices()

    try:
        selected_devices = select_devices(devices, device_selector)
    except ValueError as exc:
        parser.error(str(exc))

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
    else:
        parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
