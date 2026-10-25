"""Build and verify a private, credential-free handoff without uploading anything."""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from ingest.privacy import CONTACT_ADDRESS
from ingest.quality import audit
from tradepulse.contracts import REPO_ROOT, table_names, table_path

FORMAT = "tradepulse-private-lake/v1"
MAX_BYTES = 512 * 1024 * 1024
PROVENANCE = (
    "acceptance.csv",
    "crypto_review.json",
    "edgar_timezone_verification.csv",
    "filing_text_normalization.csv",
    "gdelt_probe.csv",
    "source_exception_verification.csv",
)


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _metadata(path, payload):
    return {"path": path, "bytes": len(payload), "sha256": _digest(payload)}


def verify_package(path: Path) -> dict:
    """Verify exact membership, payload hashes and contracts without extracting the archive."""
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Private handoff exceeds the bounded verification size")
    with ZipFile(path) as archive:
        files = archive.infolist()
        if len(files) > 32 or sum(item.file_size for item in files) > MAX_BYTES:
            raise ValueError("Private handoff exceeds the bounded verification size")
        names = [item.filename for item in files]
        if len(names) != len(set(names)):
            raise ValueError("Private handoff contains duplicate paths")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != FORMAT or set(manifest.get("tables", {})) != set(table_names()):
            raise ValueError("Private handoff format or table membership is invalid")
        expected_provenance = set(PROVENANCE) | {"sample-reference-manifest.json"}
        if set(manifest.get("provenance", {})) != expected_provenance:
            raise ValueError("Private handoff provenance membership is invalid")
        failed = manifest.get("failed_checks", [])
        if (
            failed not in ([], ["texts.earnings_complete"])
            or manifest.get("strict_acceptance_passed") is not (not failed)
            or manifest.get("source_exception_release") is not bool(failed)
        ):
            raise ValueError("Private handoff acceptance flags are inconsistent")
        as_of = dt.date.fromisoformat(manifest["as_of"])
        records = list(manifest["tables"].values()) + list(manifest["provenance"].values())
        allowed = {"manifest.json"} | {item["path"] for item in records}
        if set(names) != allowed:
            raise ValueError("Private handoff has missing or unexpected files")
        for item in records:
            payload = archive.read(item["path"])
            if len(payload) != item["bytes"] or _digest(payload) != item["sha256"]:
                raise ValueError("Private handoff payload hash or size does not match")
        from tradepulse.contracts import validate_table

        for name, item in manifest["tables"].items():
            if item["path"] != f"data/lake/{name}.parquet":
                raise ValueError("Private handoff contains an invalid table path")
            data = pd.read_parquet(io.BytesIO(archive.read(item["path"])))
            if len(data) != item["rows"] or data.empty or validate_table(data, name, as_of):
                raise ValueError("Private handoff table rows or contract do not match")
        for item in manifest["provenance"].values():
            if item["path"] not in {f"provenance/{name}" for name in PROVENANCE} | {
                "provenance/sample-reference-manifest.json"
            }:
                raise ValueError("Private handoff contains an invalid provenance path")
    return {
        "archive_path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _digest(path.read_bytes()),
        "as_of": manifest["as_of"],
        "tables": len(manifest["tables"]),
        "strict_acceptance_passed": manifest["strict_acceptance_passed"],
        "source_exception_release": manifest["source_exception_release"],
        "verified": True,
        "uploaded": False,
    }


def package_lake(
    as_of: dt.date,
    output: Path,
    root: Path | None = None,
    *,
    allow_source_exceptions=False,
):
    """Audit and package the seven full lake tables; require an explicit source-exception opt-in."""
    root, output = Path(root or REPO_ROOT), Path(output)
    if output.exists():
        raise FileExistsError("Private handoff destination exists; choose a new file")
    if output.resolve().is_relative_to((root / "data/sample").resolve()):
        raise ValueError("Private full-lake archives must stay outside the public sample")
    checks = audit(as_of, root)
    failed = checks.loc[~checks.passed, "check"].tolist()
    if failed and (not allow_source_exceptions or failed != ["texts.earnings_complete"]):
        raise ValueError("Lake audit failed; only the verified earnings-source exception can be opted in")
    reports = root / "data/lake/_reports"
    audit_manifest = json.loads((reports / "handoff_manifest.json").read_text(encoding="utf-8"))
    source = json.loads((root / "data/sample/manifest.json").read_text(encoding="utf-8"))
    if source["as_of"] != as_of.isoformat():
        raise ValueError("Private handoff date does not match the frozen sample")
    manifest = {
        "format": FORMAT,
        "as_of": as_of.isoformat(),
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "strict_acceptance_passed": not failed,
        "source_exception_release": bool(failed),
        "failed_checks": failed,
        "tables": {},
        "provenance": {},
        "uploaded": False,
    }
    payloads = {}
    for item in audit_manifest["tables"]:
        name = item["table"]
        payload = table_path(name, root).read_bytes()
        if _digest(payload) != item["sha256"]:
            raise ValueError("Source lake changed during the audit; retry a stable snapshot")
        data = pd.read_parquet(io.BytesIO(payload))
        for column in data.select_dtypes(include=["object", "string"]):
            if data[column].dropna().astype(str).str.contains(CONTACT_ADDRESS).any():
                raise ValueError("Private handoff contains a contact address; sanitize before sharing")
        if name != "filing_text" and source["tables"][name]["sha256"] != item["sha256"]:
            raise ValueError("Source lake differs from the frozen sample; review the snapshot first")
        member = f"data/lake/{name}.parquet"
        payloads[member] = payload
        manifest["tables"][name] = {**_metadata(member, payload), "rows": item["rows"]}
    for name in PROVENANCE:
        payload = (reports / name).read_bytes()
        if CONTACT_ADDRESS.search(payload.decode("utf-8")):
            raise ValueError("Private handoff provenance contains a contact address")
        member = f"provenance/{name}"
        payloads[member] = payload
        manifest["provenance"][name] = _metadata(member, payload)
    member = "provenance/sample-reference-manifest.json"
    payload = json.dumps(source, indent=2).encode("utf-8")
    if CONTACT_ADDRESS.search(payload.decode("utf-8")):
        raise ValueError("Sample reference manifest contains a contact address")
    payloads[member] = payload
    manifest["provenance"]["sample-reference-manifest.json"] = _metadata(member, payload)
    if sum(map(len, payloads.values())) > MAX_BYTES:
        raise ValueError("Private handoff exceeds the bounded verification size")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as target, ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for name, payload in payloads.items():
            archive.writestr(name, payload)
    return verify_package(output)
