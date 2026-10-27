"""SYNTHETIC transport fixtures reproducing capped results and naive DuckDB timestamps."""

import datetime as dt
import math
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from integrations.zetaris.adapter import DuckDBAdapter, ZetarisAdapter, rows_sha256
from integrations.zetaris.client import ZetarisError, ZetarisClient
from integrations.zetaris.templates import list_templates
from tradepulse.contracts import table_names, table_path


def universe_frame(size=23):
    return pd.DataFrame({
        "pool": ["us_equity"] * size,
        "symbol": [f"SYN{index:04d}" for index in range(size)],
        "name": ["SYNTHETIC transport fixture"] * size,
        "sector": ["SYNTHETIC"] * size,
        "country": [None] * size, "currency": ["USD"] * size,
        "cik": [None] * size, "wikipedia_title": [None] * size,
        "index_membership": ["SYNTHETIC"] * size,
    })


class CappedClient:
    def __init__(self, frame, cap=7):
        self.cap, self.calls = cap, []
        self.connection = duckdb.connect(":memory:")
        self.connection.execute("CREATE SCHEMA TRADEPULSE_LAKE")
        self.connection.register("synthetic_rows", frame)
        self.connection.execute("CREATE VIEW TRADEPULSE_LAKE.universe_member AS "
                                "SELECT * FROM synthetic_rows")

    def execute(self, sql):
        self.calls.append(sql)
        # Simulate the observed API cap independently of request size or reported total.
        return self.connection.execute(sql).fetchdf().head(self.cap).copy()


def test_adapter_does_not_accept_a_capped_result_as_complete():
    source = universe_frame()
    client = CappedClient(source)
    result = ZetarisAdapter(client).run("universe_pool", {"pool": "us_equity"})
    assert len(result.df) == len(source)
    assert set(result.df["symbol"]) == set(source["symbol"])
    assert result.rows_sha256 == rows_sha256(source)
    assert len(client.calls) >= math.ceil(len(source) / client.cap)
    assert not any(column.startswith("__tp_") for column in result.df.columns)


@pytest.mark.parametrize("failure", ["gap", "changed_total", "empty", "budget"])
def test_paging_fails_closed_on_incomplete_or_changed_results(failure):
    class BrokenClient(CappedClient):
        def execute(self, sql):
            frame = super().execute(sql)
            if failure == "gap":
                frame.loc[frame.index[0], "__tp_row"] = 999
            if len(self.calls) > 1 and failure == "changed_total":
                frame["__tp_total"] += 1
            if len(self.calls) > 1 and failure == "empty":
                return frame.iloc[:0]
            return frame

    client = BrokenClient(universe_frame())
    if failure == "budget":
        client._max_pages = 1
    with pytest.raises(ZetarisError):
        ZetarisAdapter(client).run("universe_pool", {"pool": "us_equity"})


def test_empty_template_is_verified_by_a_server_count():
    client = CappedClient(universe_frame(0))
    assert ZetarisAdapter(client).run("universe_pool", {"pool": "us_equity"}).df.empty
    assert len(client.calls) == 2
    assert "COUNT(*) AS __tp_total" in client.calls[1]


class NaiveConnection:
    """Delegate real SQL but simulate a DuckDB release returning UTC instants without tzinfo."""

    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        parent = self

        class Cursor:
            def __enter__(self):
                self.inner = parent.connection.cursor()
                return self

            def __exit__(self, *args):
                self.inner.close()

            def execute(self, sql):
                self.inner.execute(sql)
                return self

            def fetchdf(self):
                frame = self.inner.fetchdf()
                for name in frame:
                    if isinstance(frame[name].dtype, pd.DatetimeTZDtype):
                        frame[name] = frame[name].dt.tz_convert("UTC").dt.tz_localize(None)
                return frame

        return Cursor()


def test_duckdb_contract_restores_datetime_timezone_before_hashing(tmp_path):
    frame = pd.DataFrame({
        "series_id": ["BAMLH0A0HYM2"], "date": pd.to_datetime(["2026-10-20"]),
        "value": [3.5], "source": ["fred"],
        "available_at": pd.to_datetime(["2026-10-21T12:34:56Z"], utc=True),
    })
    location = table_path("macro_point", tmp_path)
    location.parent.mkdir(parents=True)
    frame.to_parquet(location, index=False)
    adapter = DuckDBAdapter(tmp_path)
    adapter._connection = NaiveConnection(adapter._connection)
    result = adapter.run("macro_window", {"series": "BAMLH0A0HYM2",
                                          "start": "2026-10-01", "end": "2026-10-23"})
    assert str(result.df["available_at"].dt.tz) == "UTC"
    assert result.df["available_at"].iloc[0].hour == 12
    assert result.rows_sha256 == rows_sha256(frame.drop(columns="source"))


@pytest.mark.parametrize(("template", "naive_hash", "utc_hash"), [
    ("filing_texts_window", "2b11c3d7000d3fddff3030af7b7bd327d9717aef36fa4df3f244f1bb983300ba",
     "c0939318385dea043d07d663f3835cddeb163fe8cce90c80e6aa15bab9a66fb1"),
    ("macro_window", "acfba7a258140b61278c3136e7f070ef975cf06fd1223c5ea5d897d7176de0ef",
     "fa0ce55c2c06ab3ce0c428d799664304e3d684ce7e74d4bfa334aeffc9d630f7"),
    ("pageviews_symbol_window", "27909a70ff54bd1796711c0f3c5d75fe851918d4aaf372e892f6f3b7be63f7cb",
     "bee9e7242411f4175b2b22d3f09480358d41ce5edd59fb0b1f75bc788a56e113"),
])
def test_recorded_mac_hash_pattern_is_exactly_reproduced(template, naive_hash, utc_hash):
    from integrations.zetaris.parity import fixed_params

    source = DuckDBAdapter(Path(__file__).resolve().parents[2] / "data" / "sample")
    result = source.run(template, fixed_params(template, "2026-10-23"))
    assert result.rows_sha256 == utc_hash
    frame = result.df.copy()
    for name in frame:
        if isinstance(frame[name].dtype, pd.DatetimeTZDtype):
            frame[name] = frame[name].dt.tz_convert(dt.UTC).dt.tz_localize(None)
    assert rows_sha256(frame) == naive_hash


@pytest.mark.parametrize("template", list_templates())
def test_every_template_matches_real_snapshot_through_capped_string_api(template):
    """Real frozen data, explicitly simulated API transport: no live Zetaris claim."""
    from integrations.zetaris.parity import fixed_params

    root = Path(__file__).resolve().parents[2] / "data" / "sample"
    offline = DuckDBAdapter(root)
    connection = offline._connection
    connection.execute("CREATE SCHEMA TRADEPULSE_LAKE")
    for table in table_names():
        connection.execute(f"CREATE VIEW TRADEPULSE_LAKE.{table} AS SELECT * FROM main.{table}")

    class Response:
        status_code, text, content = 200, "", b"{}"

        def __init__(self, frame):
            def wire(value):
                if pd.isna(value):
                    return None
                if isinstance(value, dt.datetime):
                    return value.isoformat()
                return str(value)

            self.payload = {"headers": list(frame.columns), "total": len(frame),
                            "data": [[wire(value) for value in row]
                                     for row in frame.itertuples(index=False, name=None)]}

        def json(self):
            return self.payload

    class Session:
        def post(self, _url, **kwargs):
            result = connection.execute(kwargs["json"]["sql"]).fetchdf().head(1000)
            return Response(result)

    client = ZetarisClient("http://synthetic.invalid", "synthetic-test-key", "1",
                           session=Session())
    params = fixed_params(template, "2026-10-23")
    expected = offline.run(template, params)
    actual = ZetarisAdapter(client).run(template, params)
    assert len(actual.df) == len(expected.df)
    assert actual.rows_sha256 == expected.rows_sha256
