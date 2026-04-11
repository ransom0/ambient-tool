from __future__ import annotations

from pathlib import Path

from ambient_tool.cli import build_parser, get_export_rows, run_export_csv


def test_get_export_rows_normalizes_fields_and_returns_rows(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "humidity": 80.0,
        }
    ]

    captured: dict[str, object] = {}

    def fake_query(*, columns, hours=None, since=None):
        captured["columns"] = columns
        captured["hours"] = hours
        captured["since"] = since
        return fake_rows

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        fake_query,
    )

    fieldnames, rows = get_export_rows(
        fields=["humidity", "tempf"],
        hours=24,
    )

    assert fieldnames == ["observation_time_utc", "humidity", "tempf"]
    assert rows == fake_rows
    assert captured == {
        "columns": ["humidity", "tempf"],
        "hours": 24,
        "since": None,
    }


def test_run_export_csv_writes_rows_and_prints_summary(
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

    output_file = tmp_path / "export.csv"

    run_export_csv(
        hours=24,
        fields=["tempf", "dew_point"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    content = output_file.read_text(encoding="utf-8")
    assert (
        content
        == "observation_time_utc,tempf,dew_point\n"
        "2026-04-11T00:00:00+00:00,70.0,60.0\n"
        "2026-04-11T01:00:00+00:00,71.0,61.0\n"
    )


def test_run_export_csv_prints_message_when_no_rows(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: [],
    )

    run_export_csv(
        hours=24,
        fields=["tempf"],
        output_path="ignored.csv",
    )

    captured = capsys.readouterr()
    assert captured.out.strip() == "No data available for that time range."


def test_run_export_csv_preserves_requested_field_order(
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

    output_file = tmp_path / "export.csv"

    run_export_csv(
        hours=24,
        fields=["humidity", "tempf"],
        output_path=str(output_file),
    )

    content = output_file.read_text(encoding="utf-8")
    assert content == (
        "observation_time_utc,humidity,tempf\n"
        "2026-04-11T00:00:00+00:00,80.0,70.0\n"
    )


def test_build_parser_parses_export_csv_hours_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "csv",
            "--hours",
            "12",
            "--fields",
            "tempf",
            "dew_point",
            "--out",
            "sample.csv",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "csv"
    assert args.hours == 12
    assert args.since is None
    assert args.fields == ["tempf", "dew_point"]
    assert args.out == "sample.csv"


def test_build_parser_parses_export_csv_since_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "csv",
            "--since",
            "2026-04-10T15:00:00+00:00",
            "--fields",
            "tempf",
            "dew_point",
            "--out",
            "sample.csv",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "csv"
    assert args.hours is None
    assert args.since == "2026-04-10T15:00:00+00:00"
    assert args.fields == ["tempf", "dew_point"]
    assert args.out == "sample.csv"
