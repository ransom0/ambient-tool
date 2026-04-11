from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, Sequence


class JsonRowLike(Protocol):
    def __getitem__(self, key: str) -> object: ...
    def keys(self) -> object: ...


def write_rows_to_json(
    output_path: str | Path,
    fieldnames: Sequence[str],
    rows: Sequence[JsonRowLike],
) -> Path:
    """
    Write row-like objects to a JSON file using the provided field order.

    Each row is serialized as a JSON object containing only the requested fields.
    Missing keys are written as null.
    """

    if not fieldnames:
        raise ValueError("fieldnames must not be empty")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: list[dict[str, object | None]] = []

    for row in rows:
        available_keys = set(row.keys())
        payload.append(
            {
                name: row[name] if name in available_keys else None
                for name in fieldnames
            }
        )

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return path
