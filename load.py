"""
FRED Loader — Public API
=========================

Single entry point for pulling, resampling, and scoring FRED macro data.

Quick start::

    from load import pull_fred

    # Full ~80-series macro dataset with scores
    df = pull_fred("fred_master.csv", output_path="./data")

Cherry-pick series categories::

    from load import pull_fred, INFLATION, LABOR, RATES

    df = pull_fred(
        "policy_inputs.csv",
        output_path="./data",
        series={**INFLATION, **LABOR, **RATES},
    )

Available categories::

    INFLATION  — CPI, PCE, breakevens, inflation expectations
    OUTPUT     — GDP (nominal/real), industrial production, vehicle sales
    LABOR      — unemployment, payrolls, claims, earnings, JOLTS, LFPR
    RATES      — fed funds, Treasury curve, yield spreads, credit spreads, mortgage
    MONEY      — M2, reserves, commercial loans, consumer credit
    HOUSING    — Case-Shiller, starts, permits, existing sales, months of supply
    CONSUMER   — Michigan sentiment, retail sales, PCE, savings rate
    TRADE      — trade balance, trade-weighted dollar
    FINANCIAL  — VIX, S&P 500, NFCI, St. Louis financial stress
    FISCAL     — federal debt, surplus/deficit, monthly Treasury statement
    INEQUALITY — Gini index
    SEP        — FOMC dot-plot medians (fed funds, GDP, unemployment, PCE)
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from loader import Config, load_fred_master
from macro_scores import score

# Re-export every category so users only need `from load import ...`
from series import (  # noqa: F401
    INFLATION,
    OUTPUT,
    LABOR,
    RATES,
    MONEY,
    HOUSING,
    CONSUMER,
    TRADE,
    FINANCIAL,
    FISCAL,
    INEQUALITY,
    SEP,
    ALL_SERIES,
    CATEGORIES,
)


def pull_fred(config: Config, apply_scores: bool = True) -> pd.DataFrame | None:
    """
    Pull FRED data, resample to a uniform frequency, and optionally score.

    Parameters
    ----------
    filename : str
        Name of the output CSV (e.g. ``"fred_master.csv"``).

    output_path : str or Path, default ``"./data"``
        Directory where the CSV will be written.

    start : str, default ``"1990-01-01"``
        Earliest observation date to request from FRED (``'YYYY-MM-DD'``).

    resample_rule : str, default ``"W-FRI"``
        Pandas offset alias that controls output frequency.
        ``"W-FRI"`` = weekly ending Friday.  Other useful values:
        ``"MS"`` (month start), ``"ME"`` (month end), ``"QE"`` (quarter end).

    mean_freqs : set of str, optional
        Native-frequency codes whose series are averaged when resampling
        (e.g. ``{"D"}`` averages daily series into weekly buckets).
        All other frequencies take the last observation per period.
        Defaults to ``{"D"}``.

    series : dict, optional
        Custom series catalog.  Keys are FRED series IDs, values are
        ``(friendly_name, native_frequency)`` tuples.  Build one by
        merging category dicts::

            from load import INFLATION, LABOR, RATES
            series = {**INFLATION, **LABOR, **RATES}

        When ``None`` (default), the full built-in catalog is used.

    apply_scores : bool, default ``True``
        When ``True``, run the macro scoring layer (derived series,
        regime flags, continuous scores, and lead/lag signals).
        Set ``False`` to get only the raw FRED data.

    inflation_target : float, default ``2.0``
        Fed inflation target (percent) used in Taylor rule, mandate
        tension, and expectations-anchoring scores.

    nairu : float, default ``4.0``
        Natural rate of unemployment (percent) used in Taylor rule
        and employment-pressure scores.

    Returns
    -------
    pd.DataFrame
        Wide DataFrame with one column per series (plus scored columns
        if ``apply_scores=True``), indexed by date.
    """
    cfg = config if isinstance(config, Config) else None
    if cfg is None:
        print("Incorrect Configuration Format.")
        return None

    raw = load_fred_master(config=config)

    if apply_scores:
        output = score(
            raw,
            pi_star=config.INFLATION_TARGET,
            u_star=config.NATURAL_RATE_UNEMPLOYMENT,
        )
    else:
        output = raw
    # ── Save ──────────────────────────────────────────────────────────────
    config.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    out_file = config.OUTPUT_PATH / config.FILENAME
    output.to_csv(out_file)

    print(f"\nSaved → {out_file}")
    return output
