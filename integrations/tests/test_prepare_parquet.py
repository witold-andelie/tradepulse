import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from integrations.zetaris.prepare_parquet import convert_file, spark_compatible_schema


def test_schema_converts_nanoseconds_and_preserves_timezone_and_metadata():
    schema = pa.schema([
        pa.field("plain", pa.timestamp("ns"), metadata={b"kind": b"plain"}),
        pa.field("utc", pa.timestamp("ns", tz="UTC")),
        pa.field("value", pa.float64()),
    ], metadata={b"table": b"test"})
    converted = spark_compatible_schema(schema)
    assert converted.field("plain").type == pa.timestamp("us")
    assert converted.field("plain").metadata == {b"kind": b"plain"}
    assert converted.field("utc").type == pa.timestamp("us", tz="UTC")
    assert converted.field("value").type == pa.float64()
    assert converted.metadata == {b"table": b"test"}


def test_convert_file_is_exact_and_never_overwrites_source(tmp_path):
    source = tmp_path / "source.parquet"
    output = tmp_path / "upload" / "copy.parquet"
    table = pa.table({
        "timestamp": pa.array([1_700_000_000_123_456_000, None], type=pa.timestamp("ns")),
        "value": [1.5, 2.5],
    })
    pq.write_table(table, source)
    result = convert_file(source, output)
    assert result["rows"] == 2
    assert result["timestamp_units"] == {"timestamp": "us"}
    assert len(result["sha256"]) == 64
    assert pq.read_table(source).schema.field("timestamp").type == pa.timestamp("ns")
    assert pq.read_table(output).schema.field("timestamp").type == pa.timestamp("us")
    with pytest.raises(ValueError, match="must not overwrite"):
        convert_file(source, source)


def test_convert_file_rejects_lossy_nanoseconds(tmp_path):
    source = tmp_path / "source.parquet"
    table = pa.table({"timestamp": pa.array([1_700_000_000_123_456_789],
                                             type=pa.timestamp("ns"))})
    pq.write_table(table, source)
    with pytest.raises(pa.ArrowInvalid):
        convert_file(source, tmp_path / "copy.parquet")
