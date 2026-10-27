import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from integrations.environment import load_private_env
from integrations.live_acceptance import check_public_bytes, validate_case
from integrations.meterless.llm import Cassette
from tradepulse.contracts import REPO_ROOT


def test_env_loader_reads_only_integration_values_and_does_not_execute(monkeypatch, tmp_path):
    monkeypatch.delenv("ZETARIS_BASE_URL", raising=False)
    monkeypatch.setenv("METERLESS_MODEL", "meterless/local")
    monkeypatch.delenv("UNRELATED_TEST_VALUE", raising=False)
    path = tmp_path / ".env.local"
    path.write_text('ZETARIS_BASE_URL="http://localhost:3000"\n'
                    'METERLESS_MODEL=meterless/auto\nUNRELATED_TEST_VALUE=blocked\n',
                    encoding="utf-8")
    load_private_env(path)
    import os

    assert os.environ["ZETARIS_BASE_URL"] == "http://localhost:3000"
    assert os.environ["METERLESS_MODEL"] == "meterless/local"
    assert "UNRELATED_TEST_VALUE" not in os.environ


def test_private_values_cannot_be_published_as_evidence():
    with pytest.raises(ValueError, match="private value"):
        check_public_bytes(b'{"value": "test-runtime-token"}', ["test-runtime-token"])


def test_concurrent_cassette_writes_remain_valid_and_complete(tmp_path):
    path = tmp_path / "cassette.jsonl"
    cassette = Cassette(path)

    def save(index):
        cassette.put(str(index), {"text": "SYNTHETIC " * 2000, "provider": "test",
                                  "model": "test", "tokens_in": 1, "tokens_out": 1})

    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(save, range(40)))
    assert len(path.read_text(encoding="utf-8").splitlines()) == 40
    assert all(Cassette(path).get(str(index))["provider"] == "test" for index in range(40))


def test_offline_example_cannot_satisfy_live_acceptance():
    output = json.loads((REPO_ROOT / "examples" / "crypto" / "output.json")
                        .read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="REAL run"):
        validate_case(output, [])
