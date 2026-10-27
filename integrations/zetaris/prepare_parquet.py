"""Create Spark-compatible copies of the contract lake for Zetaris registration.

Spark rejects Parquet timestamp nanoseconds. TradePulse values are microsecond-aligned, so this
tool performs a safe ns-to-us cast, verifies exact round-trip equality and never overwrites the
source lake.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from tradepulse.contracts import table_names, table_path


def spark_compatible_schema(schema: pa.Schema) -> pa.Schema:
    """Return the same schema with top-level timestamp[ns] fields represented as timestamp[us]."""
    fields = []
    for field in schema:
        kind = field.type
        if pa.types.is_timestamp(kind) and kind.unit == "ns":
            kind = pa.timestamp("us", tz=kind.tz)
        fields.append(pa.field(field.name, kind, field.nullable, field.metadata))
    return pa.schema(fields, metadata=schema.metadata)


def convert_file(source: Path, destination: Path) -> dict:
    """Convert one Parquet file and verify row count, precision and exact logical values."""
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Output must not overwrite the source Parquet file")
    if not source.is_file():
        raise FileNotFoundError(source)

    original = pq.read_table(source)
    target_schema = spark_compatible_schema(original.schema)
    converted = original.cast(target_schema, safe=True)
    if converted.num_rows != original.num_rows:
        raise ValueError("Row count changed during timestamp conversion")
    if any(pa.types.is_timestamp(field.type) and field.type.unit == "ns"
           for field in converted.schema):
        raise ValueError("Nanosecond timestamp remained after conversion")
    if not converted.cast(original.schema, safe=True).equals(original):
        raise ValueError("Timestamp conversion did not preserve exact logical values")

    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(converted, destination, compression="snappy")
    written = pq.read_table(destination)
    if not written.equals(converted):
        raise ValueError("Written Parquet copy failed read-back verification")
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "source": str(source),
        "output": str(destination),
        "rows": written.num_rows,
        "sha256": digest,
        "timestamp_units": {
            field.name: field.type.unit
            for field in written.schema
            if pa.types.is_timestamp(field.type)
        },
    }


def prepare_lake(source_root: Path, output_dir: Path, *, replace: bool = False) -> list[dict]:
    """Convert every contract table into one flat upload directory."""
    output_dir = output_dir.resolve()
    results = []
    for name in table_names():
        source = table_path(name, root=source_root)
        destination = output_dir / f"{name}.parquet"
        if destination.exists() and not replace:
            raise FileExistsError(f"Output exists; pass --replace to regenerate: {destination}")
        results.append({"table": name, **convert_file(source, destination)})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path.cwd(),
                        help="repository root containing data/lake (default: current directory)")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="separate directory for Zetaris-compatible copies")
    parser.add_argument("--replace", action="store_true",
                        help="replace existing files in the output directory only")
    args = parser.parse_args(argv)
    results = prepare_lake(args.source_root, args.output_dir, replace=args.replace)
    for result in results:
        print(json.dumps(result, sort_keys=True))
    print(json.dumps({"status": "ok", "tables": len(results),
                      "rows": sum(item["rows"] for item in results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
