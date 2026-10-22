import datetime as dt
import re

import pytest

from integrations.zetaris.templates import TEMPLATE_DIR, TemplateError, declared_params, list_templates, render
from tradepulse.contracts import table_names

LAKE = lambda t: f"LAKE.{t}"  # noqa: E731
SAMPLE = {"symbol": "AAPL", "symbols": ["AAPL", "BRK-B"], "pool": "us_equity", "date": dt.date(2025, 1, 2),
          "int": 5, "tag": "EarningsPerShareDiluted", "series": "BAMLH0A0HYM2"}


def test_catalogue_present():
    assert {"price_symbol_window", "price_pool_window", "price_symbols_window", "universe_pool",
            "pageviews_symbol_window", "filings_symbol_window", "facts_symbol_tag",
            "filing_texts_symbol_window", "macro_window"} <= set(list_templates())


def test_declared_params():
    assert declared_params("price_symbol_window") == {"symbol": "symbol", "start": "date", "end": "date"}
    with pytest.raises(TemplateError):
        declared_params("no_such_template")


def test_render_valid():
    sql = render("price_symbol_window", {"symbol": "AAPL", "start": "2025-01-02", "end": dt.date(2025, 3, 31)}, LAKE)
    assert "LAKE.price_bar" in sql
    assert "'AAPL'" in sql
    assert "DATE '2025-01-02'" in sql and "DATE '2025-03-31'" in sql
    assert ";" not in sql and "{{" not in sql
    assert not re.search(r":[a-z_]+", sql)


def test_render_symbol_list():
    sql = render("price_symbols_window", {"symbols": ["AAPL", "BRK-B"], "start": "2025-01-02", "end": "2025-01-03"}, LAKE)
    assert "('AAPL', 'BRK-B')" in sql


@pytest.mark.parametrize("params", [
    {"symbol": "AAPL'; DROP TABLE x --", "start": "2025-01-02", "end": "2025-01-03"},
    {"symbol": "aapl", "start": "2025-01-02", "end": "2025-01-03"},
    {"symbol": "AAPL", "start": "2025-13-02", "end": "2025-01-03"},
    {"symbol": "AAPL", "start": "2025-01-02"},
    {"symbol": "AAPL", "start": "2025-01-02", "end": "2025-01-03", "extra": 1},
])
def test_render_rejects_bad_params(params):
    with pytest.raises(TemplateError):
        render("price_symbol_window", params, LAKE)


def test_render_rejects_bad_pool_and_empty_list():
    with pytest.raises(TemplateError):
        render("universe_pool", {"pool": "mars"}, LAKE)
    with pytest.raises(TemplateError):
        render("price_symbols_window", {"symbols": [], "start": "2025-01-02", "end": "2025-01-03"}, LAKE)


def test_unknown_template():
    with pytest.raises(TemplateError):
        render("drop_everything", {}, LAKE)


@pytest.mark.parametrize("name", sorted(p.stem for p in TEMPLATE_DIR.glob("*.sql")))
def test_every_template_renders_and_uses_contract_tables(name):
    params = {p: SAMPLE[t] for p, t in declared_params(name).items()}
    used = []
    sql = render(name, params, lambda t: used.append(t) or f"LAKE.{t}")
    assert used and set(used) <= set(table_names())
    assert sql.lstrip().upper().startswith("SELECT")
