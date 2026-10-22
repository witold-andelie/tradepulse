import datetime as dt
import json

import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from tradepulse import contracts
from tradepulse.contracts import CONTRACTS_DIR, DTYPES, load_table_spec, table_names, validate_table


def test_every_table_spec_is_well_formed():
    assert set(table_names()) == {
        "universe_member", "price_bar", "pageview", "filing", "fundamental_fact", "filing_text", "macro_point",
    }
    for name in table_names():
        spec = load_table_spec(name)
        cols = [c["name"] for c in spec["columns"]]
        assert spec["name"] == name
        assert spec["path"] == f"data/lake/{name}.parquet"
        assert len(cols) == len(set(cols))
        assert set(spec["primary_key"]) <= set(cols)
        for c in spec["columns"]:
            assert c["dtype"] in DTYPES, (name, c)
            assert isinstance(c["nullable"], bool)
            assert c["description"]


def _price_frame() -> pd.DataFrame:
    now = pd.Timestamp("2026-10-21 22:00", tz="UTC")
    return pd.DataFrame({
        "pool": ["us_equity", "us_equity"],
        "symbol": ["AAA", "AAA"],
        "date": pd.to_datetime(["2026-10-20", "2026-10-21"]),
        "open": [10.0, 10.5], "high": [11.0, 11.0], "low": [9.5, 10.0],
        "close": [10.5, 10.8], "adj_close": [10.5, 10.8], "volume": [1e6, None],
        "currency": ["USD", "USD"], "source": ["yahoo", "yahoo"], "ingested_at": [now, now],
    })


def test_valid_price_frame_passes():
    assert validate_table(_price_frame(), "price_bar") == []


def test_python_dates_are_accepted_for_date_columns():
    df = _price_frame()
    df["date"] = [dt.date(2026, 10, 20), dt.date(2026, 10, 21)]
    assert validate_table(df, "price_bar") == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda d: d.drop(columns=["adj_close"]), "missing columns"),
    (lambda d: d.assign(extra=1), "unexpected columns"),
    (lambda d: d.assign(pool=["us_equity", "mars"]), "outside enum"),
    (lambda d: d.assign(date=pd.to_datetime(["2026-10-21", "2026-10-21"])), "primary key"),
    (lambda d: d.assign(close=[10.5, None]), "null values"),
    (lambda d: d.assign(high=[9.0, 11.0]), "violate check"),
    (lambda d: d.assign(ingested_at=pd.to_datetime(["2026-10-21", "2026-10-21"])), "expected dtype datetime"),
    (lambda d: d.assign(close=["10.5", "10.8"]), "expected dtype float"),
])
def test_violations_are_reported(mutate, fragment):
    errors = validate_table(mutate(_price_frame()), "price_bar")
    assert any(fragment in e for e in errors), errors


def test_as_of_rejects_future_rows():
    errors = validate_table(_price_frame(), "price_bar", as_of=dt.date(2026, 10, 20))
    assert any("after as_of" in e for e in errors)


def test_api_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(contracts.load_api_schema())


def test_fixture_run_output_satisfies_contract():
    payload = json.loads((CONTRACTS_DIR / "fixtures" / "run_output.fixture.json").read_text(encoding="utf-8"))
    assert payload["data_mode"] == "SYNTHETIC"
    assert contracts.validate_payload(payload) == []


def test_fixture_contributions_sum_to_score():
    payload = json.loads((CONTRACTS_DIR / "fixtures" / "run_output.fixture.json").read_text(encoding="utf-8"))
    for rec in payload["recommendations"]:
        total = sum(c["contribution"] for c in rec["contributions"])
        assert abs(total - rec["score"]) < 1e-4, rec["symbol"]


def test_fixture_trace_lines_satisfy_contract():
    lines = (CONTRACTS_DIR / "fixtures" / "trace.fixture.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        assert contracts.validate_payload(json.loads(line), "TraceEvent") == []


def test_invalid_payload_is_rejected():
    errors = contracts.validate_payload({"pools": ["moon"]}, "RunRequest")
    assert errors
