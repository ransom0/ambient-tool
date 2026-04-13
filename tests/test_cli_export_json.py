from __future__ import annotations

import json
from pathlib import Path

from ambient_tool.cli import build_parser, run_export_json


def test_run_export_json_writes_rows_and_prints_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "tempf": 71.0,
            "dew_point": 61.0,
        },
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "export.json"

    run_export_json(
        hours=24,
        fields=["tempf", "dew_point"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "tempf": 71.0,
            "dew_point": 61.0,
        },
    ]


def test_run_export_json_prints_message_when_no_rows(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: [],
    )

    run_export_json(
        hours=24,
        fields=["tempf"],
        output_path="ignored.json",
    )

    captured = capsys.readouterr()
    assert captured.out.strip() == "No data available for that time range."


def test_run_export_json_preserves_requested_field_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "humidity": 80.0,
        }
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "export.json"

    run_export_json(
        hours=24,
        fields=["humidity", "tempf"],
        output_path=str(output_file),
    )

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "humidity": 80.0,
            "tempf": 70.0,
        }
    ]


def test_build_parser_parses_export_json_hours_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "json",
            "--hours",
            "12",
            "--fields",
            "tempf",
            "dew_point",
            "--out",
            "sample.json",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "json"
    assert args.hours == 12
    assert args.since is None
    assert args.fields == ["tempf", "dew_point"]
    assert args.out == "sample.json"


def test_build_parser_parses_export_json_since_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "json",
            "--since",
            "2026-04-10T15:00:00+00:00",
            "--fields",
            "tempf",
            "dew_point",
            "--out",
            "sample.json",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "json"
    assert args.hours is None
    assert args.since == "2026-04-10T15:00:00+00:00"
    assert args.fields == ["tempf", "dew_point"]
    assert args.out == "sample.json"

def test_run_export_json_writes_derived_spread(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "tempf": 68.0,
            "dew_point": None,
        },
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "spread.json"

    run_export_json(
        hours=24,
        fields=["spread"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "spread": 10.0,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "spread": None,
        },
    ]

def test_run_export_json_writes_gust_delta(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "windspeedmph": 10.0,
            "windgustmph": 14.5,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "windspeedmph": 8.0,
            "windgustmph": None,
        },
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "gust_delta.json"

    run_export_json(
        hours=24,
        fields=["gust_delta"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "gust_delta": 4.5,
        },
        {
            "observation_time_utc": "2026-04-11T01:00:00+00:00",
            "gust_delta": None,
        },
    ]


def test_run_export_json_writes_feels_like_delta(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 88.0,
            "feels_like": 92.0,
        }
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "feels_like_delta.json"

    run_export_json(
        hours=24,
        fields=["tempf", "feels_like_delta"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 1 row(s) to" in captured.out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 88.0,
            "feels_like_delta": -4.0,
        }
    ]
