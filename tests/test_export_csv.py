from __future__ import annotations

from pathlib import Path

import pytest

from ambient_tool.export_csv import write_rows_to_csv


def test_write_rows_to_csv_writes_header_and_rows(tmp_path: Path) -> None:
    output_file = tmp_path / "exports" / "observations.csv"

    result = write_rows_to_csv(
        output_path=output_file,
        fieldnames=["observation_time_utc", "tempf", "dew_point"],
        rows=[
            {
                "observation_time_utc": "2026-04-11T00:00:00+00:00",
                "tempf": 70.5,
                "dew_point": 61.2,
            },
            {
                "observation_time_utc": "2026-04-11T01:00:00+00:00",
                "tempf": 71.0,
                "dew_point": 60.8,
            },
        ],
    )

    assert result == output_file
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert (
        content
        == "observation_time_utc,tempf,dew_point\n"
        "2026-04-11T00:00:00+00:00,70.5,61.2\n"
        "2026-04-11T01:00:00+00:00,71.0,60.8\n"
    )


def test_write_rows_to_csv_fills_missing_keys_with_blank(tmp_path: Path) -> None:
    output_file = tmp_path / "observations.csv"

    write_rows_to_csv(
        output_path=output_file,
        fieldnames=["observation_time_utc", "tempf", "dew_point"],
        rows=[
            {
                "observation_time_utc": "2026-04-11T00:00:00+00:00",
                "tempf": 70.5,
            }
        ],
    )

    content = output_file.read_text(encoding="utf-8")
    assert (
        content
        == "observation_time_utc,tempf,dew_point\n"
        "2026-04-11T00:00:00+00:00,70.5,\n"
    )


def test_write_rows_to_csv_ignores_extra_keys(tmp_path: Path) -> None:
    output_file = tmp_path / "observations.csv"

    write_rows_to_csv(
        output_path=output_file,
        fieldnames=["observation_time_utc", "tempf"],
        rows=[
            {
                "observation_time_utc": "2026-04-11T00:00:00+00:00",
                "tempf": 70.5,
                "humidity": 82,
            }
        ],
    )

    content = output_file.read_text(encoding="utf-8")
    assert content == "observation_time_utc,tempf\n2026-04-11T00:00:00+00:00,70.5\n"


def test_write_rows_to_csv_requires_fieldnames(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fieldnames must not be empty"):
        write_rows_to_csv(
            output_path=tmp_path / "observations.csv",
            fieldnames=[],
            rows=[],
        )


def test_write_rows_to_csv_supports_sqlite_row_like_objects(tmp_path: Path) -> None:
    class FakeRow:
        def __init__(self, data: dict[str, object]) -> None:
            self._data = data

        def __getitem__(self, key: str) -> object:
            return self._data[key]

        def keys(self):
            return self._data.keys()

    output_file = tmp_path / "observations.csv"

    write_rows_to_csv(
        output_path=output_file,
        fieldnames=["observation_time_utc", "tempf", "dew_point"],
        rows=[
            FakeRow(
                {
                    "observation_time_utc": "2026-04-11T00:00:00+00:00",
                    "tempf": 70.5,
                    "dew_point": 61.2,
                }
            )
        ],
    )

    content = output_file.read_text(encoding="utf-8")
    assert (
        content
        == "observation_time_utc,tempf,dew_point\n"
        "2026-04-11T00:00:00+00:00,70.5,61.2\n"
    )
