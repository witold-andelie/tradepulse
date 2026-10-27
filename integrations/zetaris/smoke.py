"""Run credential-safe live client and template checks using the configured Zetaris service."""

import json

from .adapter import ZetarisAdapter
from .client import ZetarisClient


def main() -> None:
    client = ZetarisClient.from_env()
    result = client.execute("SELECT 1 AS one")
    if len(result) != 1 or str(result.iloc[0, 0]) != "1":
        raise RuntimeError("Zetaris SELECT 1 did not return its expected result")
    print(json.dumps({"status": "ok", "check": "SELECT 1"}))
    adapter = ZetarisAdapter(client)
    for pool in ("us_equity", "eu_equity", "crypto"):
        rows = adapter.run("universe_pool", {"pool": pool})
        if rows.df.empty:
            raise RuntimeError(f"No registered universe members for {pool}")
        print(json.dumps({"status": "ok", "template": rows.template, "pool": pool,
                          "rows": len(rows.df), "rows_sha256": rows.rows_sha256}))


if __name__ == "__main__":
    main()
