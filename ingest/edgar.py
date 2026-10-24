"""SEC filings, point-in-time facts, and grounded document text."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from ingest.common import before_cutoff, environment, frame, report, showcase
from ingest.lake import read_table, write_table
from ingest.net import IngestHTTPError, RateLimiter, build_session, fetch_response
from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT, load_table_spec

ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
FACT_TAGS = (
    ("us-gaap", "EarningsPerShareDiluted"),
    ("us-gaap", "Revenues"),
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("dei", "EntityCommonStockSharesOutstanding"),
)
FORMS = ("8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A")


def cik10(cik: int | str) -> str:
    text = str(cik).strip()
    if not text.isdigit() or not 0 < int(text) < 10**10:
        raise ValueError("CIK must be a positive integer of at most 10 digits")
    return str(int(text)).zfill(10)


def acceptance_to_utc(raw: str) -> pd.Timestamp:
    # Required repository interpretation; live collection verifies it before persisting filings.
    timestamp = pd.Timestamp(raw)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.tz_localize("America/New_York").tz_convert("UTC")


def parse_submissions(payload: dict, symbol: str) -> pd.DataFrame:
    recent = payload.get("filings", {}).get("recent", {})
    rows = []
    cik = cik10(payload["cik"])
    for i, form in enumerate(recent.get("form", [])):
        if form not in FORMS:
            continue
        accession = recent["accessionNumber"][i]
        doc = recent["primaryDocument"][i]
        rows.append(
            {
                "cik": cik,
                "symbol": symbol,
                "accession_number": accession,
                "form": form,
                "items": recent["items"][i] or None,
                "filing_date": recent["filingDate"][i],
                "acceptance_datetime": acceptance_to_utc(recent["acceptanceDateTime"][i]),
                "report_date": recent["reportDate"][i] or None,
                "primary_document": doc,
                "primary_doc_url": f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/{doc}",
            }
        )
    return frame(rows, "filing").sort_values("acceptance_datetime").reset_index(drop=True)


def parse_companyfacts(payload: dict, symbol: str) -> pd.DataFrame:
    rows = []
    for taxonomy, tag in FACT_TAGS:
        units = payload.get("facts", {}).get(taxonomy, {}).get(tag, {}).get("units", {})
        for unit, records in units.items():
            for fact in records:
                rows.append(
                    {
                        "cik": cik10(payload["cik"]),
                        "symbol": symbol,
                        "taxonomy": taxonomy,
                        "tag": tag,
                        "unit": unit,
                        "value": fact["val"],
                        "period_start": fact.get("start"),
                        "period_end": fact["end"],
                        "fiscal_year": fact.get("fy"),
                        "fiscal_period": fact.get("fp"),
                        "form": fact["form"],
                        "filed": fact["filed"],
                        "accession_number": fact["accn"],
                        "frame": fact.get("frame"),
                    }
                )
    result = frame(rows, "fundamental_fact")
    pk = load_table_spec("fundamental_fact")["primary_key"]
    # EDGAR may repeat a fact with and without a frame. Conflicting values must never be hidden.
    if not result.empty and (result.groupby(pk, dropna=False).value.nunique() > 1).any():
        raise ValueError("Conflicting values for a fundamental_fact primary key")
    return result.drop_duplicates(pk).sort_values(["period_end", "filed"]).reset_index(drop=True)


def find_exhibit_url(index_html: str, exhibit_type: str = "EX-99.1") -> str | None:
    for table in BeautifulSoup(index_html, "lxml").find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if "Type" not in headers or "Document" not in headers:
            continue
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            if (
                len(cells) != len(headers)
                or cells[headers.index("Type")].get_text(strip=True) != exhibit_type
            ):
                continue
            link = cells[headers.index("Document")].find("a", href=True)
            if not link:
                continue
            href = link["href"]
            href = parse_qs(urlsplit(href).query).get("doc", [href])[0]
            url = urljoin("https://www.sec.gov", href)
            if urlsplit(url).hostname != "www.sec.gov" or not urlsplit(url).path.startswith(
                "/Archives/"
            ):
                raise ValueError("Exhibit URL must remain in SEC Archives")
            return url
    return None


def html_to_text(html: str, max_chars: int = 200_000) -> str:
    if max_chars < 0:
        raise ValueError("max_chars must be nonnegative")
    soup = BeautifulSoup(html, "lxml")
    for node in soup(["script", "style"]):
        node.decompose()
    return " ".join(soup.get_text(" ").split())[:max_chars]


def fetch_sec(session, limiter, url):
    import requests

    cache = REPO_ROOT / "data/cache/sec" / dt.datetime.now(dt.UTC).date().isoformat()
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + ".body")
    if path.exists():
        response = requests.Response()
        response.status_code, response.url, response.encoding = 200, url, "utf-8"
        response._content = path.read_bytes()
        response.ingest_fetched_at = pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC")
        return response
    response = fetch_response(session, url, limiter)
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    response.ingest_fetched_at = pd.Timestamp.now(tz="UTC")
    return response


def fetch_optional_sec(session, limiter, url):
    """Only a genuine 404 is optional; provider blocking and retry exhaustion are fatal."""
    try:
        return fetch_sec(session, limiter, url)
    except IngestHTTPError as exc:
        if exc.status_code == 404:
            return None
        raise


def _index_url(cik, accession):
    return f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/{accession}-index.htm"


def fetch_timezone_checks(session, limiter, payload, root=None):
    """Compare three accepted clocks against index pages; fail closed on a contradiction."""
    import re

    recent = payload["filings"]["recent"]
    checks = []
    for i in range(min(3, len(recent["accessionNumber"]))):
        accession = recent["accessionNumber"][i]
        html = fetch_sec(session, limiter, _index_url(payload["cik"], accession)).text
        text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
        match = re.search(r"Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", text)
        if not match:
            raise ValueError("Cannot verify SEC Accepted time on index page")
        raw = recent["acceptanceDateTime"][i]
        accepted = pd.Timestamp(match.group(1)).tz_localize("America/New_York").tz_convert("UTC")
        checks.append(
            {
                "accession_number": accession,
                "raw": raw,
                "index_accepted": match.group(1),
                "interpreted_utc": acceptance_to_utc(raw).isoformat(),
                "matches": accepted == acceptance_to_utc(raw),
            }
        )
    report(pd.DataFrame(checks), "edgar_timezone.csv", root)
    if len(checks) != 3 or not all(c["matches"] for c in checks):
        raise ValueError("SEC timezone hypothesis not confirmed; team-lead decision required")


def _accepted_from_index(html):
    """Canonical source approved by the user after the three real comparisons failed."""
    import re

    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    match = re.search(r"Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", text)
    if not match:
        raise ValueError("SEC Accepted timestamp missing from index")
    return pd.Timestamp(match.group(1)).tz_localize("America/New_York").tz_convert("UTC")


def run_filings(as_of: dt.date, root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    from concurrent.futures import ThreadPoolExecutor

    members = read_table("universe_member", root)
    groups = list(members[members.pool == "us_equity"].groupby("cik", dropna=False))
    if any(pd.isna(cik) for cik, _ in groups):
        raise ValueError("US member is missing CIK")
    user_agent = environment("SEC_USER_AGENT")
    limiter = RateLimiter(8)
    start = pd.Timestamp(as_of) - pd.Timedelta(days=load_config()["backtest"]["window_days"])
    showcase_names = set(showcase())

    def collect(item):
        cik, group = item
        filing_parts, fact_parts, missing, checks = [], [], [], []
        with build_session(user_agent) as session:
            response = fetch_optional_sec(
                session, limiter, f"https://data.sec.gov/submissions/CIK{cik10(cik)}.json"
            )
            if response is None:
                return [], [], [{"cik": cik, "reason": "submissions_HTTP_404"}], []
            payload = response.json()
            first_symbol = group.symbol.iloc[0]
            base = parse_submissions(payload, first_symbol)
            base = base[base.filing_date <= pd.Timestamp(as_of)].copy()
            selected = base.filing_date >= start
            if showcase_names.intersection(group.symbol):
                latest = base[base.form == "10-K"].sort_values("filing_date").tail(1)
                selected |= base.accession_number.isin(latest.accession_number)
            base = base[selected].copy()
            recent = payload["filings"]["recent"]
            raw_times = dict(zip(recent["accessionNumber"], recent["acceptanceDateTime"]))
            for index, filing in base.iterrows():
                response = fetch_optional_sec(
                    session, limiter, _index_url(cik, filing.accession_number)
                )
                if response is None:
                    missing.append(
                        {"cik": cik, "reason": "index_HTTP_404:" + filing.accession_number}
                    )
                    base = base.drop(index)
                    continue
                accepted = _accepted_from_index(response.text)
                base.loc[index, "acceptance_datetime"] = accepted
                checks.append(
                    {
                        "accession_number": filing.accession_number,
                        "cik": cik,
                        "raw": raw_times[filing.accession_number],
                        "index_accepted": accepted.tz_convert("America/New_York").isoformat(),
                        "interpreted_utc": filing.acceptance_datetime.isoformat(),
                        "raw_interpretation_matches": accepted == filing.acceptance_datetime,
                        "applied_utc": accepted.isoformat(),
                        "applied_policy": "index_accepted_approved",
                        "matches": base.loc[index, "acceptance_datetime"] == accepted,
                    }
                )
            response = fetch_optional_sec(
                session, limiter, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10(cik)}.json"
            )
            facts_payload = response.json() if response is not None else None
            if facts_payload is None:
                missing.append({"cik": cik, "reason": "companyfacts_HTTP_404"})
            for symbol in group.symbol:
                filing_parts.append(base.assign(symbol=symbol))
                if facts_payload is not None:
                    fact_parts.append(parse_companyfacts(facts_payload, symbol))
        return filing_parts, fact_parts, missing, checks

    filings, facts, missing, checks = [], [], [], []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for number, result in enumerate(executor.map(collect, groups), 1):
            fp, xp, errors, times = result
            filings.extend(fp)
            facts.extend(xp)
            missing.extend(errors)
            checks.extend(times)
            if number % 20 == 0 or number == len(groups):
                print(f"SEC companies {number}/{len(groups)}", flush=True)
    report(pd.DataFrame(missing, columns=["cik", "reason"]), "edgar_missing.csv", root)
    report(pd.DataFrame(checks), "edgar_timezone.csv", root)
    output = []
    for name, parts in [("filing", filings), ("fundamental_fact", facts)]:
        result = before_cutoff(
            frame(pd.concat(parts).to_dict("records") if parts else [], name), name, as_of
        )
        write_table(result, name, root, as_of)
        output.append(result)
    return tuple(output)


def _earnings_evidence(text: str) -> str:
    """Conservative body evidence required for the explicitly approved exhibit aliases."""
    lower = text.lower()
    groups = (
        ("earnings", "revenue", "net income", "financial results", "net sales"),
        ("quarter", "fiscal", "year ended", "three months", "six months", "nine months"),
        ("reports", "announces", "press release", "results"),
    )
    matches = [next((word for word in group if word in lower), "") for group in groups]
    return " | ".join(matches) if all(matches) and len(text) > 500 else ""


def run_texts(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    filings = before_cutoff(read_table("filing", root), "filing", as_of)
    start = pd.Timestamp(as_of) - pd.Timedelta(days=load_config()["backtest"]["window_days"])
    is_earnings = (
        filings["items"]
        .fillna("")
        .str.split(",")
        .map(lambda values: "2.02" in [v.strip() for v in values])
    )
    earnings = filings[
        (filings.form == "8-K") & is_earnings & (filings.filing_date >= start)
    ].assign(document_type="EX-99.1")
    annual = (
        filings[(filings.form == "10-K") & filings.symbol.isin(showcase())]
        .sort_values("acceptance_datetime")
        .groupby("symbol")
        .tail(1)
        .assign(document_type="10-K")
    )
    from concurrent.futures import ThreadPoolExecutor

    work = list(pd.concat([earnings, annual]).groupby(["cik", "accession_number", "document_type"]))
    user_agent = environment("SEC_USER_AGENT")
    limiter = RateLimiter(8)
    # Resume validated documents without downloading or reparsing their cached bodies.
    existing = {}
    prior_sources = []
    try:
        saved = before_cutoff(read_table("filing_text", root), "filing_text", as_of)
        for key, group in saved.groupby(["cik", "accession_number", "document_type"]):
            existing[key] = group
        provenance_path = (
            Path(root or REPO_ROOT) / "data/lake/_reports/filing_text_normalization.csv"
        )
        if provenance_path.exists() and provenance_path.stat().st_size > 1:
            prior_sources = pd.read_csv(provenance_path).to_dict("records")
    except FileNotFoundError:
        pass

    def collect(item):
        key, group = item
        first = group.iloc[0]
        if key in existing:
            saved = existing[key]
            if set(group.symbol) <= set(saved.symbol):
                selected = saved[saved.symbol.isin(group.symbol)].copy()
                selected["available_at"] = first.acceptance_datetime
                provenance = [
                    r
                    for r in prior_sources
                    if r.get("accession") == first.accession_number
                    and r.get("symbol") in set(group.symbol)
                ]
                return selected.to_dict("records"), [], provenance
        rows, missing, sources = [], [], []
        reason = None
        original_type = first.document_type
        index_url = _index_url(first.cik, first.accession_number)
        verified_index = False
        url = first.primary_doc_url
        with build_session(user_agent) as session:
            if first.document_type == "EX-99.1":
                response = fetch_optional_sec(session, limiter, index_url)
                verified_index = response is not None
                url = find_exhibit_url(response.text) if verified_index else None
                if url is None and verified_index:
                    for alias in ("EX-99.01", "EX-99"):
                        url = find_exhibit_url(response.text, alias)
                        if url is not None:
                            original_type = alias
                            break
            if url is None:
                reason = "missing_exhibit"
            else:
                response = fetch_optional_sec(session, limiter, url)
                if response is None:
                    reason = "document_HTTP_404"
                elif urlsplit(url).path.lower().endswith(".pdf") or getattr(
                    response, "content", b""
                ).startswith(b"%PDF"):
                    reason = "unsupported_pdf_exhibit"
                else:
                    text = html_to_text(response.text)
                    if not text or (first.document_type == "EX-99.1" and len(text) <= 500):
                        reason = "short_exhibit"
                    elif original_type in ("EX-99.01", "EX-99") and not _earnings_evidence(text):
                        reason = "alias_body_not_verified_as_earnings"
                    else:
                        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        if original_type in ("EX-99.01", "EX-99"):
                            sources.extend(
                                {
                                    "symbol": f.symbol,
                                    "accession": f.accession_number,
                                    "original_type": original_type,
                                    "canonical_type": "EX-99.1",
                                    "index_url": index_url,
                                    "url": url,
                                    "evidence": _earnings_evidence(text),
                                    "policy": "approved_index_and_body_normalization",
                                }
                                for f in group.itertuples()
                            )
                        fetched_at = getattr(
                            response, "ingest_fetched_at", pd.Timestamp.now(tz="UTC")
                        )
                        for filing in group.itertuples():
                            rows.append(
                                {
                                    "accession_number": filing.accession_number,
                                    "cik": filing.cik,
                                    "symbol": filing.symbol,
                                    "document_name": Path(urlsplit(url).path).name,
                                    "document_type": filing.document_type,
                                    "url": url,
                                    "sha256": digest,
                                    "text": text,
                                    "char_count": len(text),
                                    "available_at": filing.acceptance_datetime,
                                    "fetched_at": fetched_at,
                                }
                            )
            if reason:
                missing.extend(
                    {
                        "symbol": filing.symbol,
                        "accession": filing.accession_number,
                        "reason": reason,
                        "index_url": index_url,
                        "index_verified": verified_index,
                        "original_type": original_type,
                        "policy": "approved_source_exception"
                        if verified_index and reason == "missing_exhibit"
                        else "unresolved",
                    }
                    for filing in group.itertuples()
                )
        return rows, missing, sources

    rows, missing, sources = [], [], []
    executor = ThreadPoolExecutor(max_workers=6)
    try:
        for number, (parts, errors, provenance) in enumerate(executor.map(collect, work), 1):
            rows.extend(parts)
            missing.extend(errors)
            sources.extend(provenance)
            if number % 100 == 0 or number == len(work):
                print(f"SEC documents {number}/{len(work)}", flush=True)
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    report(
        pd.DataFrame(
            missing,
            columns=[
                "symbol",
                "accession",
                "reason",
                "index_url",
                "index_verified",
                "original_type",
                "policy",
            ],
        ),
        "filing_text_missing.csv",
        root,
    )
    report(pd.DataFrame(sources), "filing_text_normalization.csv", root)
    result = frame(rows, "filing_text")
    write_table(result, "filing_text", root, as_of)
    return result


def verify_saved_timestamps(as_of, root=None):
    """Check three persisted filings against index pages under the approved policy."""
    filings = read_table("filing", root)
    selected = (
        filings.sort_values("acceptance_datetime", ascending=False).drop_duplicates("cik").head(3)
    )
    checks = []
    with build_session(environment("SEC_USER_AGENT")) as session:
        limiter = RateLimiter(2)
        for row in selected.itertuples():
            url = _index_url(row.cik, row.accession_number)
            accepted = _accepted_from_index(fetch_sec(session, limiter, url).text)
            checks.append(
                {
                    "symbol": row.symbol,
                    "accession_number": row.accession_number,
                    "index_url": url,
                    "acceptance_datetime": row.acceptance_datetime.isoformat(),
                    "acceptance_eastern": row.acceptance_datetime.tz_convert(
                        "America/New_York"
                    ).isoformat(),
                    "index_accepted_eastern": accepted.tz_convert("America/New_York").isoformat(),
                    "matches": row.acceptance_datetime == accepted,
                    "policy": "index_accepted_approved",
                }
            )
    result = pd.DataFrame(checks)
    report(result, "edgar_timezone_verification.csv", root)
    if len(result) != 3 or not result.matches.all():
        raise ValueError("Persisted filing timestamps do not match index pages")
    return result


def showcase_symbols(root: Path | None = None) -> tuple[str, ...]:
    """Preserve the upstream showcase helper and its root-local graph lookup."""
    edges = pd.read_csv(Path(root or REPO_ROOT) / "config/graph/seed_edges.csv")
    return tuple(dict.fromkeys([*edges.src_symbol.dropna(), *edges.dst_symbol.dropna()]))
