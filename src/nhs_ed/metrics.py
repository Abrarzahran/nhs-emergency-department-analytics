"""Rate calculations. This is the only place where percentages are computed in Python.

Golden rule: add up the counts first, divide afterwards.
Never average percentages (a tiny department would count as much as a huge one).
"""
import numpy as np
import pandas as pd


def pct_within_4h(attendances, over_4hrs):
    """% of attendances dealt with (admitted, transferred or discharged) within 4 hours.

    = (1 - waits over 4h / attendances) * 100. Works on numbers or arrays; NaN where attendances == 0.
    """
    att = np.asarray(attendances, dtype="float64")
    over = np.asarray(over_4hrs, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(att > 0, (1 - over / att) * 100, np.nan)
    return result if result.ndim else float(result)


def add_rates(df: pd.DataFrame, include_booked: bool = True) -> pd.DataFrame:
    """Add rate columns to a frame of SUMMED counts.

    Needs: attendances, over_4hrs, booked_attendances, booked_over_4hrs, emergency_admissions.
    include_booked=True (default) adds booked-appointment attendances to both numerator and denominator. This is the
    basis on which NHS England's published headline figures reconcile (docs/OFFICIAL_RECONCILIATION.md).
    include_booked=False gives a "walk-in / unbooked only" view.
    """
    out = df.copy()
    att = out["attendances"] + (out["booked_attendances"] if include_booked else 0)
    over = out["over_4hrs"] + (out["booked_over_4hrs"] if include_booked else 0)
    out["attendances_used"] = att
    out["over_4hrs_used"] = over
    out["pct_within_4h"] = pct_within_4h(att, over)
    out["admission_ratio_pct"] = np.where(att > 0, out["emergency_admissions"] / att.where(att > 0) * 100, np.nan)
    if "days_in_month" in out.columns:
        out["attendances_per_day"] = att / out["days_in_month"]
    return out
