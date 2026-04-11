from __future__ import annotations

import json
from pathlib import Path

import pytest

from ambient_tool.export_json import write_rows_to_json


def test_write_rows_to_json_writes_rows_in_requested_field_order(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "exports" / "observations.json"

    result = write_rows_to_json(
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

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
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
    ]


def test_write_rows_to_json_writes_missing_keys_as_null(tmp_path: Path) -> None:
    output_file = tmp_path / "observations.json"

    write_rows_to_json(
        output_path=output_file,
        fieldnames=["observation_time_utc", "tempf", "dew_point"],
        rows=[
            {
                "observation_time_utc": "2026-04-11T00:00:00+00:00",
                "tempf": 70.5,
            }
        ],
    )

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.5,
            "dew_point": None,
        }
    ]


def test_write_rows_to_json_supports_row_like_objects(tmp_path: Path) -> None:
    class FakeRow:
        def __init__(self, data: dict[str, object]) -> None:
            self._data = data

        def __getitem__(self, key: str) -> object:
            return self._data[key]

        def keys(self):
            return self._data.keys()

    output_file = tmp_path / "observations.json"

    write_rows_to_json(
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

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == [
        {
            "observation_time_utc": "2026-04-11T00:00:00+00:00",
            "tempf": 70.5,
            "dew_point": 61.2,
        }
    ]


def test_write_rows_to_json_requires_fieldnames(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fieldnames must not be empty"):
        write_rows_to_json(
            output_path=tmp_path / "observations.json",
            fieldnames=[],
            rows=[],
        )
