from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from pprint import pprint

from ambient_tool.client import build_client


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
        name = device.get("info", {}).get("name", "Unknown Device")
        mac = device.get("macAddress", "Unknown MAC")
        print(f"{index}. {name} ({mac})")


def print_raw(devices) -> None:
    pprint(devices)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ambient",
        description="CLI for Ambient Weather data",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("summary", help="Show summarized weather data")
    subparsers.add_parser("current", help="Show current conditions")
    subparsers.add_parser("devices", help="List device names and MAC addresses")
    subparsers.add_parser("raw", help="Show raw API response")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "summary"

    client = build_client()
    devices = client.get_devices()

    if command == "summary":
        print_summary(devices)
    elif command == "current":
        print_current(devices)
    elif command == "devices":
        print_device_names(devices)
    elif command == "raw":
        print_raw(devices)
    else:
        parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
