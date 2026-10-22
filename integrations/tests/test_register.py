import pytest

from integrations.zetaris.register import run_files, split_statements, substitute

SQL = """-- create things
CREATE LIGHTNING DATABASE X DESCRIBE BY "a; b";

-- second
CREATE LIGHTNING FILESTORE TABLE t FROM X FORMAT PARQUET OPTIONS (PATH "${LAKE_PATH}/t.parquet");
SELECT ';' AS semi;
"""


def test_split_statements():
    out = split_statements(SQL)
    assert len(out) == 3
    assert out[0] == 'CREATE LIGHTNING DATABASE X DESCRIBE BY "a; b"'
    assert out[2] == "SELECT ';' AS semi"
    assert all(not s.startswith("--") for s in out)


def test_substitute():
    s = split_statements(SQL)[1]
    assert "s3a://bucket/lake/t.parquet" in substitute(s, {"LAKE_PATH": "s3a://bucket/lake"})
    with pytest.raises(KeyError):
        substitute(s, {})


class FakeClient:
    def __init__(self):
        self.sent = []

    def execute(self, sql):
        self.sent.append(sql)
        if "DATABASE" in sql:
            raise RuntimeError("Database X already exists")
        if "boom" in sql:
            raise RuntimeError("syntax error")


def test_run_files(tmp_path):
    f = tmp_path / "01.sql"
    f.write_text(SQL, encoding="utf-8")
    client = FakeClient()
    result = run_files(client, [f], {"LAKE_PATH": "s3a://b/l"})
    assert [status for _, status in result] == ["exists", "ok", "ok"]
    assert len(client.sent) == 3
    bad = tmp_path / "02.sql"
    bad.write_text("SELECT boom;", encoding="utf-8")
    with pytest.raises(Exception):
        run_files(client, [bad], {})
