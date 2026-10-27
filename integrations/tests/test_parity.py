import json
import os

import pytest

from integrations.zetaris.adapter import DuckDBAdapter, ZetarisAdapter
from integrations.zetaris.client import ZetarisClient
from integrations.zetaris.parity import fixed_params
from integrations.zetaris.templates import list_templates, render
from tradepulse.contracts import REPO_ROOT


@pytest.mark.parametrize("template", list_templates())
def test_every_template_has_a_renderable_fixed_parity_case(template):
    assert render(template, fixed_params(template, "2026-10-23"), lambda table: table)


@pytest.mark.network
@pytest.mark.parametrize("template", list_templates())
def test_duckdb_and_zetaris_match_on_frozen_sample(template):
    if not os.environ.get("ZETARIS_API_KEY"):
        pytest.skip("Configure the live Zetaris service before running parity acceptance")
    root = REPO_ROOT / "data" / "sample"
    as_of = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["as_of"]
    params = fixed_params(template, as_of)
    expected = DuckDBAdapter(root).run(template, params)
    actual = ZetarisAdapter(ZetarisClient.from_env()).run(template, params)
    assert actual.rows_sha256 == expected.rows_sha256, template
