from __future__ import annotations

import json
from pathlib import Path

import pytest

from ambient_tool.cli import build_parser, get_export_rows, run_export_csv, run_export_json


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
        "columns": ["observation_time_utc", "humidity", "tempf"],
        "hours": 24,
        "since": None,
    }


def test_get_export_rows_returns_grouped_fieldnames_and_rows(monkeypatch) -> None:
    fake_rows = [
        {
            "bucket_start": "2026-04-11T00:00:00+00:00",
            "tempf_avg": 70.5,
            "tempf_min": 70.0,
            "tempf_max": 71.0,
            "humidity_avg": 82.0,
            "humidity_min": 80.0,
            "humidity_max": 84.0,
        }
    ]

    captured: dict[str, object] = {}

    def fake_grouped_query(*, columns, group_by, hours=None, since=None):
        captured["columns"] = columns
        captured["group_by"] = group_by
        captured["hours"] = hours
        captured["since"] = since
        return fake_rows

    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_fieldnames",
        lambda group_by, *, fields: [
            "bucket_start",
            "tempf_avg",
            "tempf_min",
            "tempf_max",
            "humidity_avg",
            "humidity_min",
            "humidity_max",
        ],
    )
    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_observations_for_columns",
        fake_grouped_query,
    )

    fieldnames, rows = get_export_rows(
        fields=["tempf", "humidity"],
        hours=24,
        group_by="hour",
    )

    assert fieldnames == [
        "bucket_start",
        "tempf_avg",
        "tempf_min",
        "tempf_max",
        "humidity_avg",
        "humidity_min",
        "humidity_max",
    ]
    assert rows == fake_rows
    assert captured == {
        "columns": ["tempf", "humidity"],
        "group_by": "hour",
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


def test_run_export_csv_writes_grouped_rows_for_requested_fields_and_prints_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "bucket_start": "2026-04-11T00:00:00+00:00",
            "tempf_avg": 70.5,
            "tempf_min": 70.0,
            "tempf_max": 71.0,
            "humidity_avg": 82.0,
            "humidity_min": 80.0,
            "humidity_max": 84.0,
        },
        {
            "bucket_start": "2026-04-11T01:00:00+00:00",
            "tempf_avg": 71.5,
            "tempf_min": 71.0,
            "tempf_max": 72.0,
            "humidity_avg": 79.0,
            "humidity_min": 77.0,
            "humidity_max": 81.0,
        },
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_fieldnames",
        lambda group_by, *, fields: [
            "bucket_start",
            "tempf_avg",
            "tempf_min",
            "tempf_max",
            "humidity_avg",
            "humidity_min",
            "humidity_max",
        ],
    )
    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_observations_for_columns",
        lambda *, columns, group_by, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "grouped_export.csv"

    run_export_csv(
        hours=24,
        fields=["tempf", "humidity"],
        output_path=str(output_file),
        group_by="hour",
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    content = output_file.read_text(encoding="utf-8")
    assert content == (
        "bucket_start,tempf_avg,tempf_min,tempf_max,humidity_avg,humidity_min,humidity_max\n"
        "2026-04-11T00:00:00+00:00,70.5,70.0,71.0,82.0,80.0,84.0\n"
        "2026-04-11T01:00:00+00:00,71.5,71.0,72.0,79.0,77.0,81.0\n"
    )


def test_run_export_json_writes_grouped_rows_for_requested_fields_and_prints_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_rows = [
        {
            "bucket_start": "2026-04-11T00:00:00+00:00",
            "dew_point_avg": 61.5,
            "dew_point_min": 61.0,
            "dew_point_max": 62.0,
            "baromrelin_avg": 30.02,
            "baromrelin_min": 30.01,
            "baromrelin_max": 30.03,
        }
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_fieldnames",
        lambda group_by, *, fields: [
            "bucket_start",
            "dew_point_avg",
            "dew_point_min",
            "dew_point_max",
            "baromrelin_avg",
            "baromrelin_min",
            "baromrelin_max",
        ],
    )
    monkeypatch.setattr(
        "ambient_tool.cli.get_grouped_observations_for_columns",
        lambda *, columns, group_by, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "grouped_export.json"

    run_export_json(
        hours=24,
        fields=["dew_point", "baromrelin"],
        output_path=str(output_file),
        group_by="hour",
    )

    captured = capsys.readouterr()
    assert "Exported 1 row(s) to" in captured.out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "bucket_start": "2026-04-11T00:00:00+00:00",
            "dew_point_avg": 61.5,
            "dew_point_min": 61.0,
            "dew_point_max": 62.0,
            "baromrelin_avg": 30.02,
            "baromrelin_min": 30.01,
            "baromrelin_max": 30.03,
        }
    ]


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


def test_build_parser_parses_export_csv_group_by_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "csv",
            "--hours",
            "12",
            "--fields",
            "tempf",
            "humidity",
            "--group-by",
            "hour",
            "--out",
            "sample.csv",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "csv"
    assert args.hours == 12
    assert args.group_by == "hour"
    assert args.fields == ["tempf", "humidity"]
    assert args.out == "sample.csv"


def test_build_parser_parses_export_json_group_by_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "export",
            "json",
            "--hours",
            "12",
            "--fields",
            "dew_point",
            "baromrelin",
            "--group-by",
            "hour",
            "--out",
            "sample.json",
        ]
    )

    assert args.command == "export"
    assert args.export_format == "json"
    assert args.hours == 12
    assert args.group_by == "hour"
    assert args.fields == ["dew_point", "baromrelin"]
    assert args.out == "sample.json"


def test_get_export_rows_grouped_rejects_unsupported_field(monkeypatch) -> None:
    with pytest.raises(ValueError, match="Unsupported grouped hourly field"):
        get_export_rows(
            fields=["tempf", "windspeedmph"],
            hours=24,
            group_by="hour",
        )

def test_get_export_rows_row_mode_supports_derived_spread(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
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
        fields=["spread", "tempf"],
        hours=24,
    )

    assert fieldnames == ["observation_time_utc", "spread", "tempf"]
    assert rows == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.0,
            "dew_point": 60.0,
            "spread": 10.0,
        }
    ]
    assert captured == {
        "columns": ["observation_time_utc", "tempf", "dew_point"],
        "hours": 24,
        "since": None,
    }


def test_run_export_csv_writes_derived_spread(
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
            "dew_point": 61.5,
        },
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    output_file = tmp_path / "spread.csv"

    run_export_csv(
        hours=24,
        fields=["tempf", "spread"],
        output_path=str(output_file),
    )

    captured = capsys.readouterr()
    assert "Exported 2 row(s) to" in captured.out

    content = output_file.read_text(encoding="utf-8")
    assert content == (
        "observation_time_utc,tempf,spread\n"
        "2026-04-11T00:00:00+00:00,70.0,10.0\n"
        "2026-04-11T01:00:00+00:00,71.0,9.5\n"
    )


def test_get_export_rows_grouped_rejects_derived_field() -> None:
    with pytest.raises(
        ValueError,
        match="Grouped export does not support derived fields yet: spread",
    ):
        get_export_rows(
            fields=["spread"],
            hours=24,
            group_by="hour",
        )

def test_get_export_rows_row_mode_supports_gust_delta(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "windspeedmph": 8.0,
            "windgustmph": 15.0,
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
        fields=["gust_delta"],
        hours=24,
    )

    assert fieldnames == ["observation_time_utc", "gust_delta"]
    assert rows == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "windspeedmph": 8.0,
            "windgustmph": 15.0,
            "gust_delta": 7.0,
        }
    ]
    assert captured == {
        "columns": ["observation_time_utc", "windspeedmph", "windgustmph"],
        "hours": 24,
        "since": None,
    }


def test_get_export_rows_row_mode_supports_feels_like_delta(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 90.0,
            "feels_like": 95.0,
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
        fields=["feels_like_delta", "tempf"],
        hours=24,
    )

    assert fieldnames == ["observation_time_utc", "feels_like_delta", "tempf"]
    assert rows == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 90.0,
            "feels_like": 95.0,
            "feels_like_delta": -5.0,
        }
    ]
    assert captured == {
        "columns": ["observation_time_utc", "tempf", "feels_like"],
        "hours": 24,
        "since": None,
    }


def test_get_export_rows_row_mode_supports_multiple_derived_fields(monkeypatch) -> None:
    fake_rows = [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 80.0,
            "dew_point": 62.0,
            "windspeedmph": 7.0,
            "windgustmph": 12.0,
            "feels_like": 83.0,
        }
    ]

    monkeypatch.setattr(
        "ambient_tool.cli.get_observations_for_columns",
        lambda *, columns, hours=None, since=None: fake_rows,
    )

    fieldnames, rows = get_export_rows(
        fields=["spread", "gust_delta", "feels_like_delta"],
        hours=24,
    )

    assert fieldnames == [
        "observation_time_utc",
        "spread",
        "gust_delta",
        "feels_like_delta",
    ]
    assert rows == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 80.0,
            "dew_point": 62.0,
            "windspeedmph": 7.0,
            "windgustmph": 12.0,
            "feels_like": 83.0,
            "spread": 18.0,
            "gust_delta": 5.0,
            "feels_like_delta": -3.0,
        }
    ]
