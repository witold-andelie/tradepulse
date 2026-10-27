"""Sanitized Nightshift provider smoke test.

Run on the machine hosting Nightshift. The command prints provider/model metadata and a response
hash, never the bearer token or full model answer.
"""

from __future__ import annotations

import hashlib
import json
import os

import requests

from .llm import ChainClient, build_routes_from_env, normalise_meterless_base_url, read_token


def main() -> None:
    token_path = os.environ.get("METERLESS_TOKEN_FILE")
    if not token_path:
        raise SystemExit("Set METERLESS_TOKEN_FILE to Nightshift's proxy-token path.")
    token = read_token(token_path)
    base = normalise_meterless_base_url(
        os.environ.get("METERLESS_BASE_URL") or "http://127.0.0.1:8088/v1"
    )
    app = os.environ.get("METERLESS_APP") or "tradepulse"
    headers = {"Authorization": f"Bearer {token}", "meterless-app": app}
    try:
        models_response = requests.get(f"{base}/models", headers=headers, timeout=30)
    except requests.RequestException as error:
        raise SystemExit(f"Nightshift model discovery failed ({type(error).__name__}).") from None
    if models_response.status_code in {401, 403}:
        raise SystemExit("Nightshift rejected the configured token.")
    if models_response.status_code != 200:
        raise SystemExit(f"Nightshift model discovery returned HTTP {models_response.status_code}.")
    try:
        payload = models_response.json()
        models = payload.get("data", []) if isinstance(payload, dict) else []
        valid = isinstance(models, list) and any(
            isinstance(item, dict) and str(item.get("id", "")).startswith("meterless/")
            for item in models
        )
    except ValueError:
        valid = False
    if not valid:
        raise SystemExit("The configured endpoint did not advertise Meterless routing IDs.")

    messages = [{
        "role": "user",
        "content": "Return one JSON object with the key status and the value ready.",
    }]
    routes = {role: [route for route in values if route[0] == "meterless"]
              for role, values in build_routes_from_env().items()}
    response = ChainClient(routes, None, mode="live").complete(
        "analyst", messages
    )
    print(json.dumps({
        "status": "ok",
        "provider": response.provider,
        "model": response.model,
        "response_chars": len(response.text),
        "response_sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
