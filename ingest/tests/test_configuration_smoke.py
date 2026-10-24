"""SYNTHETIC offline checks: local configuration never appears in smoke reports."""

import datetime as dt

import pandas as pd
import pytest

from ingest import common, preflight
from ingest.net import IngestHTTPError


def test_local_edits_are_reloaded_without_mutating_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    path = tmp_path / ".env"
    path.write_text('SEC_USER_AGENT=""\n')
    assert common._local_setting("SEC_USER_AGENT") == ""
    path.write_text('SEC_USER_AGENT="SYNTHETIC_LOCAL_VALUE"\n')
    assert common._local_setting("SEC_USER_AGENT") == "SYNTHETIC_LOCAL_VALUE"
    assert "SEC_USER_AGENT" not in common.os.environ
    monkeypatch.setenv("SEC_USER_AGENT", "SYNTHETIC_ENVIRONMENT_VALUE")
    assert common._local_setting("SEC_USER_AGENT") == "SYNTHETIC_ENVIRONMENT_VALUE"


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "SYNTHETIC_NO_CONTACT",
        "app " + "contact" + chr(64) + "example.com",
        "app " + "contact" + chr(64) + "EXAMPLE.ORG",
        "app " + "contact" + chr(64) + "unit.invalid",
    ],
)
def test_invalid_contacts_are_rejected_without_echoing_values(value, monkeypatch, tmp_path):
    monkeypatch.setattr(common, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("SEC_USER_AGENT", value)
    with pytest.raises(common.ConfigurationError) as error:
        common.environment("SEC_USER_AGENT")
    if value.strip():
        assert value not in str(error.value)


def test_missing_configuration_never_calls_providers(tmp_path, monkeypatch):
    def missing(name):
        raise common.ConfigurationError("SYNTHETIC missing configuration")

    def forbidden(*args):
        pytest.fail("Provider called without configuration")

    monkeypatch.setattr(preflight, "environment", missing)
    for name in ("wikipedia", "sec", "pageviews", "yahoo", "fred"):
        monkeypatch.setattr(preflight, "fetch_" + name + "_probe", forbidden)
    result = preflight.smoke(dt.date(2026, 10, 21), tmp_path)
    assert len(result) == 5
    assert result.status.eq("BLOCKED").all()
    assert result.rows.eq(0).all()


def test_smoke_continues_after_failure_and_redacts_details(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight, "environment", lambda name: "SYNTHETIC")

    def failed(*args):
        raise IngestHTTPError("SYNTHETIC_PRIVATE_HEADER", 403)

    monkeypatch.setattr(preflight, "fetch_sec_probe", failed)
    for name in ("wikipedia", "pageviews", "yahoo", "fred"):
        monkeypatch.setattr(preflight, "fetch_" + name + "_probe", lambda as_of: 3)
    result = preflight.smoke(dt.date(2026, 10, 21), tmp_path)
    assert result.status.eq("PASS").sum() == 4
    assert result.status.eq("FAIL").sum() == 1
    path = tmp_path / "data/lake/_reports/provider_smoke.csv"
    assert "SYNTHETIC_PRIVATE_HEADER" not in path.read_text()
    assert "HTTP_403" in path.read_text()
    pd.testing.assert_frame_equal(pd.read_csv(path), result, check_dtype=False)
