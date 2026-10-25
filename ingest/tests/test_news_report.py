"""SYNTHETIC blocked-provider evidence is reportable without invented observations."""

import datetime as dt
import json
import warnings

import pandas as pd

from ingest import __main__ as cli
from ingest import news_probe


def test_blocked_news_probe_without_cached_points_is_reported(tmp_path, monkeypatch, capsys):
    reports = tmp_path / "data/lake/_reports"
    reports.mkdir(parents=True)
    pd.DataFrame(
        [{"symbol": "SYNTHETIC", "status": "BLOCKED", "rows": 0,
          "first": None, "last": None, "detail": "HTTP_429"}]
    ).to_csv(reports / "gdelt_probe.csv", index=False)
    monkeypatch.setattr(news_probe, "REPO_ROOT", tmp_path)

    assert cli.main(["news-report", "--as-of", "2026-10-23"]) == 1

    result = pd.read_csv(reports / "gdelt_probe.csv")
    assert result.status.iloc[0] == "BLOCKED"
    assert result.rows.iloc[0] == 0
    assert pd.isna(result.calendar_day_coverage.iloc[0])
    assert pd.isna(result.missing_calendar_days.iloc[0])
    assert "SYNTHETIC" in capsys.readouterr().out


def test_news_summary_can_update_optional_columns_loaded_as_missing_floats(tmp_path, monkeypatch):
    reports = tmp_path / "data/lake/_reports"
    cache = tmp_path / "data/cache/gdelt"
    reports.mkdir(parents=True)
    cache.mkdir(parents=True)
    pd.DataFrame(
        [{"symbol": "SYNTHETIC", "status": "BLOCKED", "rows": 0,
          "daily_observations": None, "calendar_day_coverage": None,
          "missing_calendar_days": None, "detail": "SYNTHETIC"}]
    ).to_csv(reports / "gdelt_probe.csv", index=False)
    source = {"timeline": [{"series": "Average Tone", "data": [
        {"date": "20251023T000000Z", "value": 1.0},
        {"date": "20261022T000000Z", "value": 2.0},
    ]}]}
    (cache / "SYNTHETIC.json").write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setattr(news_probe, "REPO_ROOT", tmp_path)

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        result = news_probe.summarize_news_probe(dt.date(2026, 10, 23))

    assert bool(result.daily_observations.iloc[0])
    assert result.missing_calendar_days.iloc[0] == 363
