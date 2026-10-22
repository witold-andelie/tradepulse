import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def dates():
    return pd.bdate_range("2025-01-01", periods=300)


@pytest.fixture
def random_prices(dates):
    rng = np.random.default_rng(7)
    rets = rng.normal(0.0005, 0.02, size=(len(dates), 8))
    return pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=dates, columns=[f"S{i}" for i in range(8)])
