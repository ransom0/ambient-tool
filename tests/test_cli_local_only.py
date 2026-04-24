from __future__ import annotations

import sys

import pytest

from ambient_tool.cli import main


def test_main_export_csv_does_not_build_client(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "export.csv"
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ambient",
            "export",
            "csv",
            "--hours",
            "24",
            "--fields",
            "tempf",
            "--out",
            str(output_file),
        ],
    )

    def fail_build_client():
        raise AssertionError("build_client should not be called for export commands")

    def fake_run_export_csv(*, fields, output_path, hours=None, since=None, group_by=None):
        captured["fields"] = fields
        captured["output_path"] = output_path
        captured["hours"] = hours
        captured["since"] = since
        captured["group_by"] = group_by

    monkeypatch.setattr("ambient_tool.cli.build_client", fail_build_client)
    monkeypatch.setattr("ambient_tool.cli.run_export_csv", fake_run_export_csv)

    main()

    assert captured == {
        "fields": ["tempf"],
        "output_path": str(output_file),
        "hours": 24,
        "since": None,
        "group_by": None,
    }


def test_main_export_json_does_not_build_client(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "export.json"
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ambient",
            "export",
            "json",
            "--hours",
            "24",
            "--fields",
            "tempf",
            "--group-by",
            "hour",
            "--out",
            str(output_file),
        ],
    )

    def fail_build_client():
        raise AssertionError("build_client should not be called for export commands")

    def fake_run_export_json(*, fields, output_path, hours=None, since=None, group_by=None):
        captured["fields"] = fields
        captured["output_path"] = output_path
        captured["hours"] = hours
        captured["since"] = since
        captured["group_by"] = group_by

    monkeypatch.setattr("ambient_tool.cli.build_client", fail_build_client)
    monkeypatch.setattr("ambient_tool.cli.run_export_json", fake_run_export_json)

    main()

    assert captured == {
        "fields": ["tempf"],
        "output_path": str(output_file),
        "hours": 24,
        "since": None,
        "group_by": "hour",
    }


def test_main_trend_does_not_build_client(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ambient",
            "trend",
            "--hours",
            "12",
            "--format",
            "table",
            "--show",
            "temp",
            "pressure",
        ],
    )

    def fail_build_client():
        raise AssertionError("build_client should not be called for trend commands")

    def fake_run_trend(show_fields, hours, output_format, last=None):
        captured["show_fields"] = show_fields
        captured["hours"] = hours
        captured["output_format"] = output_format
        captured["last"] = last

    monkeypatch.setattr("ambient_tool.cli.build_client", fail_build_client)
    monkeypatch.setattr("ambient_tool.cli.run_trend", fake_run_trend)

    main()

    assert captured == {
        "show_fields": ["temp", "pressure"],
        "hours": 12,
        "output_format": "table",
        "last": None,
    }

def test_main_trend_table_shortcut_and_last(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ambient",
            "trend",
            "--hours",
            "6",
            "--table",
            "--last",
            "5",
            "--show",
            "temp",
            "dewpoint",
        ],
    )

    def fail_build_client():
        raise AssertionError("build_client should not be called for trend commands")

    def fake_run_trend(show_fields, hours, output_format, last=None):
        captured["show_fields"] = show_fields
        captured["hours"] = hours
        captured["output_format"] = output_format
        captured["last"] = last

    monkeypatch.setattr("ambient_tool.cli.build_client", fail_build_client)
    monkeypatch.setattr("ambient_tool.cli.run_trend", fake_run_trend)

    main()

    assert captured == {
        "show_fields": ["temp", "dewpoint"],
        "hours": 6,
        "output_format": "table",
        "last": 5,
    }

def test_main_summary_still_builds_client(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(sys, "argv", ["ambient", "summary"])

    class FakeClient:
        def get_devices(self):
            events.append("get_devices")
            return [{"info": {"name": "Test Device"}, "lastData": {}}]

    def fake_build_client():
        events.append("build_client")
        return FakeClient()

    def fake_print_summary(devices):
        events.append("print_summary")
        assert len(devices) == 1

    monkeypatch.setattr("ambient_tool.cli.build_client", fake_build_client)
    monkeypatch.setattr("ambient_tool.cli.print_summary", fake_print_summary)

    main()

    assert events == ["build_client", "get_devices", "print_summary"]
