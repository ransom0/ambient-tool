from __future__ import annotations

from pathlib import Path

from ambient_tool.cli import build_parser, run_export_csv


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
        "ambient_tool.cli.get_recent_observations_for_columns",
        lambda hours, columns: fake_rows,
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
        "ambient_tool.cli.get_recent_observations_for_columns",
        lambda hours, columns: [],
    )

    run_export_csv(
        hours=24,
        fields=["tempf"],
        output_path="ignored.csv",
    )

    captured = capsys.readouterr()
    assert captured.out.strip() == "No data available for that time range."


def test_build_parser_parses_export_csv_arguments() -> None:
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
    assert args.fields == ["tempf", "dew_point"]
    assert args.out == "sample.csv"

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
        "ambient_tool.cli.get_recent_observations_for_columns",
        lambda hours, columns: fake_rows,
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
