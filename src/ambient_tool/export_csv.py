from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Sequence


def write_rows_to_csv(
    output_path: str | Path,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, object]],
) -> Path:
    """
    Write row dictionaries to a CSV file using the provided field order.

    Missing keys are written as empty strings.
    Extra keys in rows are ignored.
    """

    if not fieldnames:
        raise ValueError("fieldnames must not be empty")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in rows:
            normalized_row = {name: row[name] if name in row.keys() else "" for name in fieldnames}
            writer.writerow(normalized_row)

    return path
