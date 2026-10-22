import pytest

from integrations.meterless.engines_client import EnginesClient, EnginesError

EDGE = {"edge_id": "e1", "src_symbol": "NVDA", "dst_symbol": "TSM", "relation": "supplier_of", "weight": 0.6,
        "source": "seed", "evidence_ref": None, "status": "validated", "lead_lag_t": 2.4,
        "valid_from": "2026-10-21"}


class Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, status=200, body=None):
        self.calls = []
        self.status, self.body = status, body if body is not None else {"status": "ok"}

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        return Resp(self.status, self.body)

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        return Resp(self.status, self.body)


def test_health_and_snapshot_urls():
    s = FakeSession(body={"status": "ok", "engines": {}})
    c = EnginesClient("http://127.0.0.1:8790", session=s)
    assert c.health()["status"] == "ok"
    c.snapshot("2026-10-21")
    assert s.calls[0][:2] == ("GET", "http://127.0.0.1:8790/health")
    assert s.calls[1][1] == "http://127.0.0.1:8790/world-model/snapshot"
    assert s.calls[1][2] == {"as_of": "2026-10-21"}


def test_upsert_edges_validates_before_sending():
    s = FakeSession(body={"upserted": 1})
    c = EnginesClient("http://127.0.0.1:8790", session=s)
    assert c.upsert_edges([EDGE]) == {"upserted": 1}
    assert s.calls[0] == ("POST", "http://127.0.0.1:8790/world-model/edges", {"edges": [EDGE]})
    with pytest.raises(ValueError):
        c.upsert_edges([dict(EDGE, relation="friend_of")])
    assert len(s.calls) == 1  # the invalid edge never left the process


def test_http_errors_raise():
    c = EnginesClient("http://127.0.0.1:8790", session=FakeSession(status=500, body={"error": "boom"}))
    with pytest.raises(EnginesError):
        c.health()
