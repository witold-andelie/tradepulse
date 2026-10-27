import json
from pathlib import Path

import pandas as pd
import pytest

from integrations.zetaris.adapter import ZetarisAdapter
from integrations.zetaris.client import ZetarisClient, ZetarisError


FIXTURE = Path(__file__).parent / "fixtures" / "zetaris_query_response.json"


class FakeResponse:
    def __init__(self, payload=None, status=200, text=""):
        self._payload = payload
        self.status_code = status
        self.text = text
        self.content = b"x" if payload is not None else b""

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_parse_recorded_real_response_shape():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    frame = ZetarisClient.parse_response(payload)
    assert frame.to_dict("records") == [
        {"pool": "crypto", "members": "38"},
        {"pool": "eu_equity", "members": "55"},
        {"pool": "us_equity", "members": "523"},
    ]


def test_execute_uses_official_contract_and_bounded_expansion():
    first = {"headers": ["value"], "data": [["1"], ["2"]], "total": 3}
    second = {"headers": ["value"], "data": [["1"], ["2"], ["3"]], "total": 3}
    session = FakeSession([FakeResponse(first), FakeResponse(second)])
    client = ZetarisClient("http://localhost:8888/api/v1.0", "private-key", "1",
                           session=session)
    client._query_limit = 2
    client._max_rows = 10

    frame = client.execute("SELECT value FROM example")

    assert list(frame["value"]) == ["1", "2", "3"]
    assert len(session.calls) == 2
    assert [call[1]["json"]["limit"] for call in session.calls] == [2, 4]
    assert all(call[0].endswith("/api/v1.0/sql-editor/sqls/run") for call in session.calls)
    assert all(call[1]["json"]["source"] == "SqlEditor" for call in session.calls)
    assert len({call[1]["headers"]["X-Request-ID"] for call in session.calls}) == 2
    assert len({call[1]["json"]["queryId"] for call in session.calls}) == 2
    assert all(call[1]["timeout"] == 120.0 for call in session.calls)


def test_execute_never_leaks_key_in_http_error():
    session = FakeSession([FakeResponse(status=500, text="failed private-key")])
    client = ZetarisClient("http://localhost:8888/api/v1.0", "private-key", "1",
                           session=session)
    with pytest.raises(ZetarisError) as caught:
        client.execute("SELECT 1")
    assert "private-key" not in str(caught.value)
    assert "[REDACTED]" in str(caught.value)


def test_from_env_requires_named_configuration(monkeypatch):
    for name in ("ZETARIS_REST_URL", "ZETARIS_API_KEY", "ZETARIS_ORG_ID"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ZetarisError, match="ZETARIS_REST_URL"):
        ZetarisClient.from_env()


def test_proxy_mode_matches_the_official_working_helper(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_MODE", "proxy")
    monkeypatch.setenv("ZETARIS_BASE_URL", "http://localhost:3000")
    monkeypatch.setenv("ZETARIS_API_KEY", "private-key")
    monkeypatch.setenv("ZETARIS_ORG_ID", "1")
    monkeypatch.delenv("ZETARIS_ENGINE_ID", raising=False)
    client = ZetarisClient.from_env()
    client._session = FakeSession([
        FakeResponse({"headers": ["one"], "data": [["1"]], "total": 1}),
    ])
    assert client.execute("SELECT 1 AS one").iloc[0, 0] == "1"
    url, kwargs = client._session.calls[0]
    assert url == "http://localhost:3000/api/proxy/sql-editor/sqls/run-query"
    assert kwargs["json"] == {"sql": "SELECT 1 AS one", "limit": 50000}
    assert kwargs["allow_redirects"] is False


@pytest.mark.parametrize("total", [False, 1.5, -1, "1.5", None])
def test_client_rejects_invalid_result_totals(total):
    client = ZetarisClient("http://localhost:8888/api/v1.0", "private-key", "1",
                           session=FakeSession([FakeResponse({
                               "headers": ["x"], "data": [[1]], "total": total,
                           })]))
    with pytest.raises(ZetarisError, match="total"):
        client.execute("SELECT 1 AS x")


def test_client_fails_if_bounded_requests_cannot_prove_completeness():
    payload = {"headers": ["x"], "data": [[1], [2]], "total": 3}
    client = ZetarisClient("http://localhost:8888/api/v1.0", "private-key", "1",
                           session=FakeSession([FakeResponse(payload)]))
    client._max_requests = 1
    with pytest.raises(ZetarisError, match="bounded request"):
        client.execute("SELECT x FROM example")


def test_query_errors_with_data_are_never_reported_as_success():
    with pytest.raises(ZetarisError, match="reported an error"):
        ZetarisClient.parse_response({"error": "query failed", "data": []})


class AdapterClient:
    def execute(self, sql):
        assert "TRADEPULSE_LAKE.universe_member" in sql
        return pd.DataFrame({"pool": ["crypto"], "symbol": ["BTC-USD"],
                             "name": ["Bitcoin"], "sector": ["layer-1"],
                             "country": [None], "currency": ["USD"], "cik": [None],
                             "wikipedia_title": ["Bitcoin"],
                             "index_membership": ["CRYPTO_TOP"],
                             "__tp_row": ["1"], "__tp_total": ["1"]})


def test_adapter_renders_allow_listed_template_and_coerces_contract_columns():
    result = ZetarisAdapter(AdapterClient()).run("universe_pool", {"pool": "crypto"})
    assert result.backend == "zetaris"
    assert result.df["pool"].dtype.name == "string"
    assert result.df.iloc[0]["symbol"] == "BTC-USD"
    assert len(result.rows_sha256) == 64
