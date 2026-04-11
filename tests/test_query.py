from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ambient_tool import query


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.executed_sql = None
        self.executed_params = None

    def execute(self, sql, params):
        self.executed_sql = sql
        self.executed_params = params
        return FakeCursor(self.rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_normalize_observation_columns_adds_timestamp_and_deduplicates() -> None:
    result = query.normalize_observation_columns(
        ["tempf", "humidity", "tempf", "baromrelin"]
    )

    assert result == ["observation_time_utc", "tempf", "humidity", "baromrelin"]


def test_normalize_observation_columns_preserves_existing_timestamp_position() -> None:
    result = query.normalize_observation_columns(
        ["observation_time_utc", "tempf", "humidity"]
    )

    assert result == ["observation_time_utc", "tempf", "humidity"]


def test_normalize_observation_columns_rejects_unknown_column() -> None:
    with pytest.raises(ValueError, match="Unsupported observation column: bogus"):
        query.normalize_observation_columns(["tempf", "bogus"])


def test_get_observations_since_uses_normalized_columns_and_cutoff(monkeypatch) -> None:
    fake_rows = [{"observation_time_utc": "2026-04-11T00:00:00+00:00", "tempf": 70.0}]
    fake_conn = FakeConnection(fake_rows)

    monkeypatch.setattr(query, "get_connection", lambda: fake_conn)

    since_utc = datetime(2026, 4, 11, 0, 0, tzinfo=UTC)
    result = query.get_observations_since(
        since_utc=since_utc,
        columns=["tempf", "tempf", "humidity"],
    )

    assert result == fake_rows
    assert fake_conn.executed_params == (since_utc.isoformat(),)
    assert fake_conn.executed_sql is not None
    assert "SELECT observation_time_utc, tempf, humidity" in fake_conn.executed_sql
    assert "FROM observations" in fake_conn.executed_sql
    assert "WHERE observation_time_utc >= ?" in fake_conn.executed_sql
    assert "ORDER BY observation_time_utc ASC" in fake_conn.executed_sql


def test_get_recent_observations_for_columns_requires_hours_at_least_one() -> None:
    with pytest.raises(ValueError, match="hours must be at least 1"):
        query.get_recent_observations_for_columns(
            hours=0,
            columns=["tempf"],
        )

def test_parse_since_utc_accepts_timezone_aware_iso_string() -> None:
    result = query.parse_since_utc("2026-04-11T00:00:00+00:00")
    assert result == datetime(2026, 4, 11, 0, 0, tzinfo=UTC)


def test_parse_since_utc_rejects_invalid_string() -> None:
    with pytest.raises(ValueError, match="valid ISO-8601 timestamp"):
        query.parse_since_utc("not-a-date")


def test_parse_since_utc_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="must include a timezone offset"):
        query.parse_since_utc("2026-04-11T00:00:00")


def test_get_observations_for_columns_requires_exactly_one_time_filter() -> None:
    with pytest.raises(ValueError, match="Provide exactly one of hours or since"):
        query.get_observations_for_columns(
            columns=["tempf"],
        )

    with pytest.raises(ValueError, match="Provide exactly one of hours or since"):
        query.get_observations_for_columns(
            columns=["tempf"],
            hours=24,
            since="2026-04-11T00:00:00+00:00",
        )


def test_get_observations_for_columns_uses_hours_path(monkeypatch) -> None:
    fake_rows = [{"observation_time_utc": "2026-04-11T00:00:00+00:00", "tempf": 70.0}]

    monkeypatch.setattr(
        query,
        "get_recent_observations_for_columns",
        lambda hours, columns: fake_rows,
    )

    result = query.get_observations_for_columns(
        columns=["tempf"],
        hours=24,
    )

    assert result == fake_rows


def test_get_observations_for_columns_uses_since_path(monkeypatch) -> None:
    fake_rows = [{"observation_time_utc": "2026-04-11T00:00:00+00:00", "tempf": 70.0}]
    captured: dict[str, object] = {}

    def fake_get_observations_since(*, since_utc: datetime, columns: list[str]):
        captured["since_utc"] = since_utc
        captured["columns"] = columns
        return fake_rows

    monkeypatch.setattr(query, "get_observations_since", fake_get_observations_since)

    result = query.get_observations_for_columns(
        columns=["tempf"],
        since="2026-04-11T00:00:00+00:00",
    )

    assert result == fake_rows
    assert captured["since_utc"] == datetime(2026, 4, 11, 0, 0, tzinfo=UTC)
    assert captured["columns"] == ["tempf"]
