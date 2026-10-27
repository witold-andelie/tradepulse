import os

import pytest
import requests

from integrations.meterless.llm import (ChainClient, build_routes_from_env,
                                        normalise_meterless_base_url, read_token,
                                        require_advertised_model)


@pytest.mark.network
def test_nightshift_is_a_working_ai_provider():
    token_path = os.environ.get("METERLESS_TOKEN_FILE")
    if not token_path:
        pytest.skip("METERLESS_TOKEN_FILE is not configured on this machine")
    token = read_token(token_path)
    base = normalise_meterless_base_url(os.environ.get("METERLESS_BASE_URL", "127.0.0.1:8088"))
    app = os.environ.get("METERLESS_APP") or "tradepulse"
    common = {"meterless-app": app}

    denied = requests.get(
        f"{base}/models",
        headers={**common, "Authorization": "Bearer deliberately-invalid"},
        timeout=30,
    )
    assert denied.status_code in {401, 403}
    accepted = requests.get(
        f"{base}/models",
        headers={**common, "Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert accepted.status_code == 200
    selected = os.environ.get("METERLESS_MODEL") or "meterless/auto"
    require_advertised_model(accepted.json(), selected)

    routes = {role: [route for route in values if route[0] == "meterless"]
              for role, values in build_routes_from_env().items()}
    reply = ChainClient(routes, None, mode="live").complete(
        "analyst",
        [{"role": "user", "content": "Reply with one short sentence confirming readiness."}],
    )
    assert reply.provider == "meterless"
    assert reply.model == selected
    assert reply.text.strip()
