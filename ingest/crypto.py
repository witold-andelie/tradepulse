"""Source-backed crypto curation; unsupported assets remain explicit exceptions."""

from __future__ import annotations

import json
from urllib.parse import quote

import pandas as pd

from ingest.common import environment, report
from ingest.net import RateLimiter, build_session, get_with_retries
from tradepulse.contracts import REPO_ROOT

# Research categories are curated metadata, not fabricated prices or ranking results.
CATEGORIES = {
    "bitcoin": "layer-1",
    "ethereum": "layer-1",
    "binancecoin": "exchange-token",
    "ripple": "payments",
    "solana": "layer-1",
    "tron": "layer-1",
    "zcash": "privacy",
    "hyperliquid": "defi",
    "dogecoin": "meme",
    "monero": "privacy",
    "whitebit": "exchange-token",
    "chainlink": "oracle",
    "leo-token": "exchange-token",
    "cardano": "layer-1",
    "stellar": "payments",
    "near": "layer-1",
    "bitcoin-cash": "payments",
    "litecoin": "payments",
    "uniswap": "defi",
    "avalanche-2": "layer-1",
    "sui": "layer-1",
    "the-open-network": "layer-1",
    "hedera-hashgraph": "layer-1",
    "shiba-inu": "meme",
    "bittensor": "ai",
    "crypto-com-chain": "exchange-token",
    "quant-network": "interoperability",
    "ethena": "defi",
    "okb": "exchange-token",
    "aave": "defi",
    "ondo-finance": "defi",
    "pepe": "meme",
    "polkadot": "layer-1",
    "worldcoin-wld": "identity",
    "mantle": "layer-2",
    "sky": "defi",
    "morpho": "defi",
    "internet-computer": "layer-1",
    "bitget-token": "exchange-token",
    "ethereum-classic": "layer-1",
    "arbitrum": "layer-2",
    "just": "defi",
    "kucoin-shares": "exchange-token",
    "kaspa": "layer-1",
    "jupiter-exchange-solana": "defi",
    "polygon-ecosystem-token": "layer-2",
    "algorand": "layer-1",
    "cosmos": "layer-1",
    "render-token": "ai",
    "pi-network": "layer-1",
    "filecoin": "storage",
    "aptos": "layer-1",
    "nexo": "defi",
    "gatechain-token": "exchange-token",
}


def fetch_crypto_research(as_of):
    cache = REPO_ROOT / "data/cache/crypto"
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(1)
        markets_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false"
        response = get_with_retries(session, markets_url, limiter)
        if response.status_code != 200:
            raise ValueError(f"CoinGecko market response HTTP {response.status_code}")
        markets = response.json()
        (cache / "markets.json").write_text(json.dumps(markets), encoding="utf-8")
        candidates = [c for c in markets if c["id"] in CATEGORIES]
        for asset in candidates:
            ident = asset["id"]
            record = {
                "id": ident,
                "name": asset["name"],
                "market_cap_rank": asset["market_cap_rank"],
                "market_cap": asset["market_cap"],
                "category": CATEGORIES[ident],
                "coingecko_symbol": asset["symbol"],
                "yahoo_candidates": "",
                "wiki_candidates": "",
            }
            for source in ["yahoo", "wiki"]:
                path = cache / f"{ident}-{source}.json"
                if path.exists():
                    payload = json.loads(path.read_text())
                else:
                    name = asset["name"] if ident != "the-open-network" else "Toncoin"
                    if source == "yahoo":
                        url = (
                            "https://query1.finance.yahoo.com/v1/finance/search?q="
                            + quote(name)
                            + "&quotesCount=8&newsCount=0"
                        )
                    else:
                        url = (
                            "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=4&srsearch="
                            + quote(name + " cryptocurrency")
                        )
                    response = get_with_retries(session, url, limiter)
                    if response.status_code != 200:
                        record[source + "_error"] = response.status_code
                        continue
                    payload = response.json()
                    path.write_text(json.dumps(payload), encoding="utf-8")
                if source == "yahoo":
                    options = [
                        {"symbol": q.get("symbol"), "name": q.get("shortname", q.get("longname"))}
                        for q in payload.get("quotes", [])
                        if q.get("quoteType") == "CRYPTOCURRENCY"
                    ]
                else:
                    options = [q["title"] for q in payload.get("query", {}).get("search", [])]
                record[source + "_candidates"] = json.dumps(options, ensure_ascii=True)
            rows.append(record)
            report(pd.DataFrame(rows), "crypto_candidates.csv")
            print(f"Crypto candidate {len(rows)}/{len(candidates)}: {ident}", flush=True)
    return pd.DataFrame(rows)


# Candidate article names are verified by Wikipedia before they can enter configuration.
ARTICLE_CANDIDATES = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "binancecoin": "BNB Smart Chain (blockchain platform)",
    "ripple": "XRP Ledger",
    "solana": "Solana (blockchain platform)",
    "tron": "Tron (blockchain)",
    "zcash": "Zcash",
    "hyperliquid": "Hyperliquid",
    "dogecoin": "Dogecoin",
    "monero": "Monero",
    "whitebit": "WhiteBIT",
    "chainlink": "Chainlink (blockchain oracle)",
    "leo-token": "UNUS SED LEO",
    "cardano": "Cardano (blockchain platform)",
    "stellar": "Stellar (payment network)",
    "near": "NEAR (blockchain platform)",
    "bitcoin-cash": "Bitcoin Cash",
    "litecoin": "Litecoin",
    "uniswap": "Uniswap",
    "avalanche-2": "Avalanche (blockchain platform)",
    "sui": "Sui (blockchain platform)",
    "the-open-network": "TON (blockchain)",
    "hedera-hashgraph": "Hedera (distributed ledger)",
    "shiba-inu": "Shiba Inu (cryptocurrency)",
    "bittensor": "Bittensor",
    "crypto-com-chain": "Crypto.com",
    "quant-network": "Quant Network",
    "ethena": "Ethena",
    "okb": "OKX",
    "aave": "Aave",
    "ondo-finance": "Ondo Finance",
    "pepe": "Pepe (cryptocurrency)",
    "polkadot": "Polkadot (blockchain platform)",
    "worldcoin-wld": "World (blockchain)",
    "mantle": "Mantle (blockchain)",
    "sky": "Sky (cryptocurrency)",
    "morpho": "Morpho (cryptocurrency)",
    "internet-computer": "Dfinity",
    "bitget-token": "Bitget",
    "ethereum-classic": "Ethereum Classic",
    "arbitrum": "Arbitrum",
    "just": "JUST (cryptocurrency)",
    "kucoin-shares": "KuCoin",
    "kaspa": "Kaspa",
    "jupiter-exchange-solana": "Jupiter (cryptocurrency)",
    "polygon-ecosystem-token": "Polygon (blockchain)",
    "algorand": "Algorand",
    "cosmos": "Cosmos (network)",
    "render-token": "Render Network",
    "pi-network": "Pi Network",
    "nexo": "Nexo (company)",
    "filecoin": "Filecoin",
    "aptos": "Aptos Labs",
}


def fetch_crypto_verification(as_of):
    """Verify candidate articles and real five-day Yahoo bars before publishing configuration."""
    from ingest.prices import fetch_prices

    cache = REPO_ROOT / "data/cache/crypto"
    candidates = pd.read_csv(REPO_ROOT / "data/lake/_reports/crypto_candidates.csv")
    verified = {}
    article_names = list(ARTICLE_CANDIDATES.values())
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(1)
        for offset in range(0, len(article_names), 25):
            response = get_with_retries(
                session,
                "https://en.wikipedia.org/w/api.php",
                limiter,
                params={
                    "action": "query",
                    "format": "json",
                    "redirects": 1,
                    "prop": "info",
                    "inprop": "url",
                    "titles": "|".join(article_names[offset : offset + 25]),
                },
            )
            if response.status_code != 200:
                raise ValueError("Wikipedia article validation failed")
            payload = response.json()
            (cache / f"article-validation-{offset}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
            aliases = {r["from"]: r["to"] for r in payload.get("query", {}).get("redirects", [])}
            pages = {p["title"]: p for p in payload.get("query", {}).get("pages", {}).values()}
            for title in article_names[offset : offset + 25]:
                canonical = aliases.get(title, title)
                page = pages.get(canonical, {})
                if page and "missing" not in page:
                    verified[title] = canonical.replace(" ", "_")
        # Refine empty search results using the asset's source ticker, not a guessed Yahoo code.
        for index, row in candidates.iterrows():
            if json.loads(row.yahoo_candidates or "[]"):
                continue
            response = get_with_retries(
                session,
                "https://query1.finance.yahoo.com/v1/finance/search",
                limiter,
                params={
                    "q": row.coingecko_symbol.upper() + "-USD",
                    "quotesCount": 8,
                    "newsCount": 0,
                },
            )
            if response.status_code == 200:
                options = [
                    {"symbol": q.get("symbol"), "name": q.get("shortname", q.get("longname"))}
                    for q in response.json().get("quotes", [])
                    if q.get("quoteType") == "CRYPTOCURRENCY"
                ]
                candidates.loc[index, "yahoo_candidates"] = json.dumps(options)
    proposed = []
    for row in candidates.itertuples():
        options = json.loads(row.yahoo_candidates or "[]")
        target = row.name.lower() + " usd"
        option = next((q for q in options if (q.get("name") or "").lower() == target), None)
        aliases = {
            "kucoin-shares": {"kucoin token usd"},
            "cosmos": {"cosmos usd"},
            "polygon-ecosystem-token": {
                "polygon ecosystem token usd",
                "pol (ex-matic) usd",
                "polygon usd",
            },
            "gatechain-token": {"gate usd", "gate token usd"},
        }
        if option is None:
            option = next(
                (q for q in options if (q.get("name") or "").lower() in aliases.get(row.id, set())),
                None,
            )
        if option is None and row.id == "the-open-network":
            option = next(
                (q for q in options if (q.get("name") or "").lower() == "toncoin usd"), None
            )
        if option is None:
            continue
        article_candidate = ARTICLE_CANDIDATES.get(row.id)
        article = verified.get(article_candidate)
        proposed.append(
            {
                "symbol": option["symbol"],
                "name": row.name,
                "category": row.category,
                "wikipedia_title": article,
                "notes": f"CoinGecko id={row.id}; market-cap rank={int(row.market_cap_rank)}; decision as_of={as_of}",
                "id": row.id,
                "market_cap_rank": int(row.market_cap_rank),
            }
        )
    # Preserve the original named task assets, then add the largest supported candidates.
    required = {
        "bitcoin",
        "ethereum",
        "ripple",
        "binancecoin",
        "solana",
        "dogecoin",
        "cardano",
        "tron",
        "avalanche-2",
        "chainlink",
        "stellar",
        "bitcoin-cash",
        "litecoin",
        "polkadot",
        "hedera-hashgraph",
        "shiba-inu",
        "near",
        "internet-computer",
        "ethereum-classic",
        "aave",
        "the-open-network",
        "sui",
        "uniswap",
        "aptos",
        "pepe",
    }
    selected = [r for r in proposed if r["id"] in required]
    additions = [r for r in proposed if r["id"] not in required]
    # Prefer verifiable article coverage; missing titles are retained explicitly for required assets.
    additions.sort(key=lambda r: (r["wikipedia_title"] is None, r["market_cap_rank"]))
    selected += additions[: max(0, 40 - len(selected))]
    # The specification permits 35-45 assets. Preserve named task assets and avoid inventing
    # articles: remove optional low-ranked assets lacking articles until coverage reaches 90%.
    removed = []
    while (
        len(selected) > 35
        and sum(r["wikipedia_title"] is not None for r in selected) / len(selected) < 0.9
    ):
        optional = [r for r in selected if r["id"] not in required and r["wikipedia_title"] is None]
        if not optional:
            break
        remove = max(optional, key=lambda r: r["market_cap_rank"])
        selected.remove(remove)
        removed.append(
            {"id": remove["id"], "reason": "No verifiable English article; optional candidate"}
        )
    report(pd.DataFrame(removed, columns=["id", "reason"]), "crypto_selection_exceptions.csv")
    selected.sort(key=lambda r: r["market_cap_rank"])
    result = pd.DataFrame(selected)
    result.to_csv(cache / "proposed.csv", index=False)
    print(f"Verifying real Yahoo histories for {len(result)} selected assets", flush=True)
    prior_path = cache / "verified.csv"
    available = set()
    if prior_path.exists():
        prior = pd.read_csv(prior_path)
        same_date = prior.notes.str.contains(
            f"decision as_of={as_of}", regex=False
        ) | prior.notes.str.endswith(str(as_of))
        available = set(prior.loc[same_date & prior.yahoo_verified.eq(True), "symbol"])
    needed = [symbol for symbol in result.symbol if symbol not in available]
    if needed:
        bars = fetch_prices(needed, as_of - __import__("datetime").timedelta(days=7), as_of)
        available.update(bars.dropna(subset=["Close", "Adj Close"]).symbol)
    result["yahoo_verified"] = result.symbol.isin(available)
    result.to_csv(cache / "verified.csv", index=False)
    if (
        not 35 <= len(result) <= 45
        or not result.yahoo_verified.all()
        or not required <= set(result.id)
        or result.wikipedia_title.notna().mean() < 0.9
    ):
        raise ValueError(
            "Crypto proposal incomplete or contains failed Yahoo symbols; see verified.csv"
        )
    result[["symbol", "name", "category", "wikipedia_title", "notes"]].to_csv(
        REPO_ROOT / "config/universe/crypto.csv", index=False
    )
    review = {
        "source_url": "https://api.coingecko.com/api/v3/coins/markets",
        "reviewed_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "selection": "Original task assets plus largest Yahoo-supported candidates with verifiable articles; not an exact top-40 market-cap index",
        "assets": [
            {
                "symbol": r["symbol"],
                "id": r["id"],
                "market_cap_rank": r["market_cap_rank"],
                "excluded_type": False,
                "yahoo_verified": bool(r["yahoo_verified"]),
            }
            for r in result.to_dict("records")
        ],
    }
    path = REPO_ROOT / "data/lake/_reports/crypto_review.json"
    path.write_text(json.dumps(review, indent=2), encoding="utf-8")
    return result
