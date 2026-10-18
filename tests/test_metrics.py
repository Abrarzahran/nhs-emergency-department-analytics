"""Rate maths: small hand-checkable examples."""
import math

import pandas as pd
import pytest

from nhs_ed.metrics import add_rates, pct_within_4h


def test_pct_within_4h_basic():
    assert pct_within_4h(100, 25) == pytest.approx(75.0)
    assert pct_within_4h(100, 0) == pytest.approx(100.0)
    assert pct_within_4h(100, 100) == pytest.approx(0.0)


def test_zero_attendances_gives_nan_not_an_error_or_100():
    assert math.isnan(pct_within_4h(0, 0))


def test_aggregate_counts_not_average_percentages():
    # Small unit: 10 attendances, 5 over 4h -> 50%. Big unit: 1000 attendances, 100 over -> 90%.
    df = pd.DataFrame({"attendances": [10, 1000], "over_4hrs": [5, 100]})
    mean_of_percentages = pct_within_4h(df.attendances, df.over_4hrs).mean()  # 70.0 - misleading
    correct = pct_within_4h(df.attendances.sum(), df.over_4hrs.sum())  # 89.6 - weighted by volume
    assert mean_of_percentages == pytest.approx(70.0)
    assert correct == pytest.approx(100 * (1 - 105 / 1010))
    assert correct > mean_of_percentages


def _frame():
    return pd.DataFrame({"attendances": [100], "over_4hrs": [20], "booked_attendances": [50], "booked_over_4hrs": [5],
                         "emergency_admissions": [30], "days_in_month": [30]})


def test_add_rates_includes_booked_by_default():
    """Default matches NHS England's published basis (see tests/test_official_reconciliation.py)."""
    r = add_rates(_frame()).iloc[0]
    assert r.attendances_used == 150 and r.pct_within_4h == pytest.approx(100 * (1 - 25 / 150))
    assert r.admission_ratio_pct == pytest.approx(100 * 30 / 150)
    assert r.attendances_per_day == pytest.approx(150 / 30)


def test_add_rates_can_exclude_booked():
    r = add_rates(_frame(), include_booked=False).iloc[0]
    assert r.attendances_used == 100 and r.pct_within_4h == pytest.approx(80.0) and r.admission_ratio_pct == pytest.approx(30.0)
