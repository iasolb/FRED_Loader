"""
Macro Scoring Module
====================

Registry-based scoring layer.  Each score declares its input dependencies
and output columns upfront.  At runtime the resolver figures out which
scores can be computed from the columns actually present, runs them in
dependency order, and skips the rest.

Adding a new score:
    1. Write a function that takes a DataFrame and returns it with new columns.
    2. Decorate it with @_register(...) or use a helper like _reg_yoy().
    3. That's it — resolution, ordering, and catalog are automatic.

Usage:
    from macro_scores import score, available_scores, list_scored_columns

    scored = score(df)                      # compute everything possible
    preview = available_scores(df)          # dry run — what WOULD be computed
    catalog = list_scored_columns()         # full catalog grouped by category
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Callable, Optional, Any


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

_W52 = 52
_W26 = 26
_W13 = 13
_W78 = 78

_PI_STAR = 2.0
_U_STAR = 4.0
_R_STAR_DEFAULT = 0.5
_SAHM_THRESHOLD = 0.50
_TAYLOR_ALPHA = 0.5
_TAYLOR_BETA = 0.5
_DEANCHOR_MILD = 1.0
_DEANCHOR_SEVERE = 2.0
_M2_NORMAL_LOW = 2.0
_M2_NORMAL_HIGH = 8.0


def blank(df: Any) -> Any:
    """Helper for specs that produce columns but have no actual logic."""
    return df


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRY INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class _ScoreSpec:
    """
    A single registered scoring block.

    Attributes
    ----------
    name : str
        Short identifier (used in logs and available_scores output).
    category : str
        One of 'derived', 'flags', 'continuous', 'leads_lags'.
    requires : set[str]
        Column names that MUST exist before this block can run.
        Can include raw series names OR columns produced by other specs.
    produces : list[str]
        Column names this block adds to the DataFrame.
    fn : callable
        fn(df) -> df — mutates and returns the DataFrame.
    """

    name: str
    category: str
    requires: set = field(default_factory=set)
    produces: list = field(default_factory=list)
    fn: Callable = field(default=blank)


_REGISTRY: list[_ScoreSpec] = []


def _register(name: str, category: str, requires: set, produces: list):
    """Decorator that registers a scoring function."""

    def decorator(fn):
        _REGISTRY.append(
            _ScoreSpec(
                name=name,
                category=category,
                requires=set(requires),
                produces=list(produces),
                fn=fn,
            )
        )
        return fn

    return decorator


def _resolve(columns: set[str]) -> list[_ScoreSpec]:
    """
    Topological dependency resolution.

    Starting from the columns present in the DataFrame, iteratively
    find specs whose requirements are met, add their outputs to the
    available set, and repeat until no new specs can be resolved.

    Returns specs in a valid execution order.
    """
    available = set(columns)
    resolved = []
    remaining = list(_REGISTRY)

    changed = True
    while changed:
        changed = False
        still_remaining = []
        for spec in remaining:
            if spec.requires.issubset(available):
                resolved.append(spec)
                available.update(spec.produces)
                changed = True
            else:
                still_remaining.append(spec)
        remaining = still_remaining

    return resolved


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _reg_yoy(src: str, dst: str, window: int = _W52):
    """Register a simple year-over-year pct_change score."""

    def fn(df, _s=src, _d=dst, _w=window):
        df[_d] = df[_s].pct_change(_w) * 100
        return df

    _REGISTRY.append(
        _ScoreSpec(
            name=dst,
            category="derived",
            requires={src},
            produces=[dst],
            fn=fn,
        )
    )


def _reg_annualized(src: str, dst: str, window: int = _W13):
    """Register an annualized short-window growth rate."""

    def fn(df, _s=src, _d=dst, _w=window):
        df[_d] = df[_s].pct_change(_w) * (52 / _w) * 100
        return df

    _REGISTRY.append(
        _ScoreSpec(
            name=dst,
            category="derived",
            requires={src},
            produces=[dst],
            fn=fn,
        )
    )


def _reg_diff(src: str, dst: str, periods: int, category: str = "derived"):
    """Register a simple first-difference."""

    def fn(df, _s=src, _d=dst, _p=periods):
        df[_d] = df[_s].diff(_p)
        return df

    _REGISTRY.append(
        _ScoreSpec(
            name=dst,
            category=category,
            requires={src},
            produces=[dst],
            fn=fn,
        )
    )


def _reg_shift(src: str, dst: str, periods: int, category: str = "leads_lags"):
    """Register a lag (positive) or lead (negative)."""

    def fn(df, _s=src, _d=dst, _p=periods):
        df[_d] = df[_s].shift(_p)
        return df

    _REGISTRY.append(
        _ScoreSpec(
            name=dst,
            category=category,
            requires={src},
            produces=[dst],
            fn=fn,
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. DERIVED SERIES
# ═══════════════════════════════════════════════════════════════════════════

# ── YoY inflation rates (each independent) ────────────────────────────
_reg_yoy("Headline_CPI", "CPI_YoY")
_reg_yoy("Core_CPI", "Core_CPI_YoY")
_reg_yoy("Core_PCE", "Core_PCE_YoY")
_reg_yoy("PCE_Price_Index", "PCE_YoY")
_reg_yoy("CPI_Food", "CPI_Food_YoY")
_reg_yoy("CPI_Energy", "CPI_Energy_YoY")

# ── Inflation momentum ────────────────────────────────────────────────
_reg_annualized("Core_PCE", "Core_PCE_3m_ann", _W13)


@_register(
    "inflation_momentum",
    "derived",
    requires={"Core_PCE_3m_ann", "Core_PCE_YoY"},
    produces=["Inflation_Momentum"],
)
def _inflation_momentum(df):
    df["Inflation_Momentum"] = df["Core_PCE_3m_ann"] - df["Core_PCE_YoY"]
    return df


# ── Money supply growth ───────────────────────────────────────────────
_reg_yoy("M2_Money_Stock", "M2_YoY")
_reg_annualized("M2_Money_Stock", "M2_6m_ann", _W26)


# ── Real rates ────────────────────────────────────────────────────────
@_register(
    "real_ffr_cpi",
    "derived",
    requires={"FedFunds_Rate", "CPI_YoY"},
    produces=["Real_FFR_CPI"],
)
def _real_ffr_cpi(df):
    df["Real_FFR_CPI"] = df["FedFunds_Rate"] - df["CPI_YoY"]
    return df


@_register(
    "real_ffr_pce",
    "derived",
    requires={"FedFunds_Rate", "Core_PCE_YoY"},
    produces=["Real_FFR_PCE"],
)
def _real_ffr_pce(df):
    df["Real_FFR_PCE"] = df["FedFunds_Rate"] - df["Core_PCE_YoY"]
    return df


@_register(
    "real_10y_cpi",
    "derived",
    requires={"Treasury_10Y", "CPI_YoY"},
    produces=["Real_10Y_CPI"],
)
def _real_10y_cpi(df):
    df["Real_10Y_CPI"] = df["Treasury_10Y"] - df["CPI_YoY"]
    return df


# ── Labor market derived ──────────────────────────────────────────────
_reg_diff("Nonfarm_Payrolls", "Payroll_Change_4w", 4)


@_register(
    "sahm_components",
    "derived",
    requires={"Unemployment_Rate"},
    produces=["UE_3m_avg", "UE_12m_min", "Sahm_Indicator"],
)
def _sahm_components(df):
    df["UE_3m_avg"] = df["Unemployment_Rate"].rolling(_W13, min_periods=8).mean()
    df["UE_12m_min"] = df["Unemployment_Rate"].rolling(_W52, min_periods=26).min()
    df["Sahm_Indicator"] = df["UE_3m_avg"] - df["UE_12m_min"]
    return df


@_register(
    "jolts_ue_ratio",
    "derived",
    requires={"JOLTS_Job_Openings", "Unemployment_Rate"},
    produces=["Unemployed_Approx", "JOLTS_UE_Ratio"],
)
def _jolts_ue_ratio(df):
    _labor_force = 160_000
    df["Unemployed_Approx"] = df["Unemployment_Rate"] / 100 * _labor_force
    df["JOLTS_UE_Ratio"] = df["JOLTS_Job_Openings"] / df["Unemployed_Approx"]
    return df


# ── Fiscal derived ────────────────────────────────────────────────────
@_register(
    "debt_to_gdp",
    "derived",
    requires={"Federal_Debt_Total", "Nominal_GDP"},
    produces=["Debt_to_GDP"],
)
def _debt_to_gdp(df):
    df["Debt_to_GDP"] = (df["Federal_Debt_Total"] / 1000) / df["Nominal_GDP"] * 100
    return df


@_register(
    "deficit_gdp_pct",
    "derived",
    requires={"Monthly_Treasury_Statement_Deficit", "Nominal_GDP"},
    produces=["Deficit_GDP_Pct"],
)
def _deficit_gdp_pct(df):
    df["Deficit_GDP_Pct"] = (
        (df["Monthly_Treasury_Statement_Deficit"] * 12 / 1000) / df["Nominal_GDP"] * 100
    )
    return df


# ── SEP-based derived ─────────────────────────────────────────────────
@_register(
    "sep_r_star",
    "derived",
    requires={"SEP_FedFunds_Median_LongerRun"},
    produces=["SEP_LR_FFR", "SEP_r_star"],
)
def _sep_r_star(df):
    df["SEP_LR_FFR"] = df["SEP_FedFunds_Median_LongerRun"].ffill()
    df["SEP_r_star"] = df["SEP_LR_FFR"] - _PI_STAR
    return df


@_register(
    "policy_stance_sep",
    "derived",
    requires={"FedFunds_Rate", "SEP_LR_FFR"},
    produces=["Policy_Stance_SEP"],
)
def _policy_stance_sep(df):
    df["Policy_Stance_SEP"] = df["FedFunds_Rate"] - df["SEP_LR_FFR"]
    return df


@_register(
    "sep_ffr_med", "derived", requires={"SEP_FedFunds_Median"}, produces=["SEP_FFR_Med"]
)
def _sep_ffr_med(df):
    df["SEP_FFR_Med"] = df["SEP_FedFunds_Median"].ffill()
    return df


@_register(
    "term_premium_proxy",
    "derived",
    requires={"Treasury_10Y", "SEP_FFR_Med"},
    produces=["Term_Premium_Proxy"],
)
def _term_premium_proxy(df):
    df["Term_Premium_Proxy"] = df["Treasury_10Y"] - df["SEP_FFR_Med"]
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 2. REGIME & ANOMALY FLAGS
# ═══════════════════════════════════════════════════════════════════════════


@_register(
    "curve_inversion_10y2y",
    "flags",
    requires={"Yield_Curve_10Y_2Y"},
    produces=["Flag_Curve_Inverted_10Y2Y"],
)
def _curve_inv_10y2y(df):
    df["Flag_Curve_Inverted_10Y2Y"] = (df["Yield_Curve_10Y_2Y"] < 0).astype(int)
    return df


@_register(
    "curve_inversion_10y3m",
    "flags",
    requires={"Yield_Curve_10Y_3M"},
    produces=["Flag_Curve_Inverted_10Y3M"],
)
def _curve_inv_10y3m(df):
    df["Flag_Curve_Inverted_10Y3M"] = (df["Yield_Curve_10Y_3M"] < 0).astype(int)
    return df


@_register(
    "sahm_flag", "flags", requires={"Sahm_Indicator"}, produces=["Flag_Sahm_Triggered"]
)
def _sahm_flag(df):
    df["Flag_Sahm_Triggered"] = (df["Sahm_Indicator"] >= _SAHM_THRESHOLD).astype(int)
    return df


@_register(
    "fci_contradiction_flag",
    "flags",
    requires={"Chicago_Fed_Financial_Conditions", "Policy_Stance_SEP"},
    produces=["Flag_FCI_Contradiction"],
)
def _fci_contradiction_flag(df):
    df["Flag_FCI_Contradiction"] = (
        (df["Chicago_Fed_Financial_Conditions"] < -0.2)
        & (df["Policy_Stance_SEP"] > 0.5)
    ).astype(int)
    return df


@_register(
    "deanchor_flags",
    "flags",
    requires={"UMich_Inflation_Expectations", "CPI_YoY"},
    produces=[
        "Expect_Gap_UMich",
        "Flag_Deanchor_Mild",
        "Flag_Deanchor_Severe",
        "Flag_Deanchor_Hot",
        "Flag_Deanchor_Cold",
    ],
)
def _deanchor_flags(df):
    df["Expect_Gap_UMich"] = df["UMich_Inflation_Expectations"] - df["CPI_YoY"]
    df["Flag_Deanchor_Mild"] = (df["Expect_Gap_UMich"].abs() > _DEANCHOR_MILD).astype(
        int
    )
    df["Flag_Deanchor_Severe"] = (
        df["Expect_Gap_UMich"].abs() > _DEANCHOR_SEVERE
    ).astype(int)
    df["Flag_Deanchor_Hot"] = (df["Expect_Gap_UMich"] > _DEANCHOR_MILD).astype(int)
    df["Flag_Deanchor_Cold"] = (df["Expect_Gap_UMich"] < -_DEANCHOR_MILD).astype(int)
    return df


@_register(
    "m2_anomaly_flags",
    "flags",
    requires={"M2_YoY"},
    produces=["Flag_M2_Excess", "Flag_M2_Contraction"],
)
def _m2_anomaly_flags(df):
    df["Flag_M2_Excess"] = (df["M2_YoY"] > _M2_NORMAL_HIGH).astype(int)
    df["Flag_M2_Contraction"] = (df["M2_YoY"] < _M2_NORMAL_LOW).astype(int)
    return df


@_register(
    "labor_divergence_flag",
    "flags",
    requires={"JOLTS_UE_Ratio", "Unemployment_Rate"},
    produces=["JOLTS_UE_Ratio_chg", "UE_chg_13w", "Flag_Labor_Divergence"],
)
def _labor_divergence_flag(df):
    df["JOLTS_UE_Ratio_chg"] = df["JOLTS_UE_Ratio"].diff(_W13)
    df["UE_chg_13w"] = df["Unemployment_Rate"].diff(_W13)
    df["Flag_Labor_Divergence"] = (
        (df["UE_chg_13w"] > 0.2) & (df["JOLTS_UE_Ratio_chg"] < -0.1)
        | (df["UE_chg_13w"] < -0.2) & (df["JOLTS_UE_Ratio_chg"] > 0.1)
    ).astype(int)
    return df


@_register(
    "neg_real_rate_flag",
    "flags",
    requires={"Real_FFR_PCE", "Core_PCE_YoY"},
    produces=["Flag_Neg_Real_Rate_HighInflation"],
)
def _neg_real_rate_flag(df):
    df["Flag_Neg_Real_Rate_HighInflation"] = (
        (df["Real_FFR_PCE"] < 0) & (df["Core_PCE_YoY"] > _PI_STAR)
    ).astype(int)
    return df


@_register(
    "hy_stress_flag", "flags", requires={"HY_OAS_Spread"}, produces=["Flag_HY_Stress"]
)
def _hy_stress_flag(df):
    df["Flag_HY_Stress"] = (df["HY_OAS_Spread"] > 5.0).astype(int)
    return df


@_register(
    "fiscal_dominance_flag",
    "flags",
    requires={"Debt_to_GDP", "FedFunds_Rate", "Core_PCE_YoY"},
    produces=["Debt_GDP_chg_26w", "FFR_chg_26w", "Flag_Fiscal_Dominance_Risk"],
)
def _fiscal_dominance_flag(df):
    df["Debt_GDP_chg_26w"] = df["Debt_to_GDP"].diff(_W26)
    df["FFR_chg_26w"] = df["FedFunds_Rate"].diff(_W26)
    df["Flag_Fiscal_Dominance_Risk"] = (
        (df["Debt_GDP_chg_26w"] > 0)
        & (df["FFR_chg_26w"] < -0.25)
        & (df["Core_PCE_YoY"] > _PI_STAR)
    ).astype(int)
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 3. CONTINUOUS SCORES
# ═══════════════════════════════════════════════════════════════════════════


@_register(
    "taylor_rule",
    "continuous",
    requires={"Core_PCE_YoY", "Unemployment_Rate", "SEP_r_star", "FedFunds_Rate"},
    produces=[
        "Taylor_Prescribed",
        "Taylor_Gap",
        "Flag_Taylor_Below_100bp",
        "Flag_Taylor_Above_100bp",
    ],
)
def _taylor_rule(df):
    r_star = df["SEP_r_star"].fillna(_R_STAR_DEFAULT)
    pi = df["Core_PCE_YoY"]
    u_gap = _U_STAR - df["Unemployment_Rate"]
    df["Taylor_Prescribed"] = (
        r_star + pi + _TAYLOR_ALPHA * (pi - _PI_STAR) + _TAYLOR_BETA * u_gap
    )
    df["Taylor_Gap"] = df["Taylor_Prescribed"] - df["FedFunds_Rate"]
    df["Flag_Taylor_Below_100bp"] = (df["Taylor_Gap"] > 1.0).astype(int)
    df["Flag_Taylor_Above_100bp"] = (df["Taylor_Gap"] < -1.0).astype(int)
    return df


@_register(
    "mandate_tension",
    "continuous",
    requires={"Core_PCE_YoY", "Unemployment_Rate"},
    produces=[
        "Inflation_Pressure",
        "Employment_Pressure",
        "Mandate_Tension",
        "Mandate_Regime",
    ],
)
def _mandate_tension(df):
    ip = df["Core_PCE_YoY"] - _PI_STAR
    ep = df["Unemployment_Rate"] - _U_STAR
    df["Inflation_Pressure"] = ip
    df["Employment_Pressure"] = ep
    df["Mandate_Tension"] = ip * ep

    def _classify(row):
        i, e = row["Inflation_Pressure"], row["Employment_Pressure"]
        if pd.isna(i) or pd.isna(e):
            return np.nan
        if i > 0.3 and e > 0.3:
            return 3
        elif i < -0.3 and e < -0.3:
            return -3
        elif i > 0.3 and e < -0.3:
            return 1
        elif i < -0.3 and e > 0.3:
            return -1
        return 0

    df["Mandate_Regime"] = df.apply(_classify, axis=1)
    return df


@_register(
    "fiscal_monetary_conflict",
    "continuous",
    requires={"Policy_Stance_SEP", "Deficit_GDP_Pct"},
    produces=["Fiscal_Monetary_Conflict"],
)
def _fiscal_monetary_conflict(df):
    df["Fiscal_Monetary_Conflict"] = df["Policy_Stance_SEP"] * df["Deficit_GDP_Pct"]
    return df


@_register(
    "expectations_anchoring",
    "continuous",
    requires=set(),
    produces=["Expect_Anchor_Score", "Expect_Anchor_Signed"],
)
def _expectations_anchoring(df):
    abs_devs, signed_devs = [], []
    for col in [
        "UMich_Inflation_Expectations",
        "Breakeven_Inflation_5Y",
        "Breakeven_Inflation_10Y",
    ]:
        if col in df.columns:
            abs_devs.append((df[col] - _PI_STAR).abs())
            signed_devs.append(df[col] - _PI_STAR)
    if not abs_devs:
        return df
    df["Expect_Anchor_Score"] = pd.concat(abs_devs, axis=1).mean(axis=1)
    df["Expect_Anchor_Signed"] = pd.concat(signed_devs, axis=1).mean(axis=1)
    return df


@_register(
    "fci_transmission",
    "continuous",
    requires={"Policy_Stance_SEP", "Chicago_Fed_Financial_Conditions"},
    produces=["FCI_Transmission"],
)
def _fci_transmission(df):
    df["FCI_Transmission"] = df["Policy_Stance_SEP"] * (
        -df["Chicago_Fed_Financial_Conditions"]
    )
    return df


@_register(
    "credit_impulse",
    "continuous",
    requires={"Consumer_Credit_Total"},
    produces=["Credit_Impulse"],
)
def _credit_impulse(df):
    cg = df["Consumer_Credit_Total"].pct_change(_W13) * (52 / 13) * 100
    df["Credit_Impulse"] = cg.diff(_W13)
    return df


@_register(
    "housing_pressure",
    "continuous",
    requires={"Case_Shiller_Home_Price", "Mortgage_Rate_30Y"},
    produces=["Home_Price_YoY", "Housing_Pressure"],
)
def _housing_pressure(df):
    hp = df["Case_Shiller_Home_Price"].pct_change(_W52) * 100
    df["Home_Price_YoY"] = hp
    df["Housing_Pressure"] = (
        df["Mortgage_Rate_30Y"]
        - df["Mortgage_Rate_30Y"].rolling(_W52 * 5, min_periods=52).mean()
    ) + (hp - hp.rolling(_W52 * 5, min_periods=52).mean())
    return df


@_register(
    "activity_momentum", "continuous", requires=set(), produces=["Activity_Momentum"]
)
def _activity_momentum(df):
    def _trailing_z(s, window=_W52 * 3):
        mu = s.rolling(window, min_periods=_W52).mean()
        sigma = s.rolling(window, min_periods=_W52).std()
        return (s - mu) / sigma.replace(0, np.nan)

    components = []
    for col in [
        "Industrial_Production",
        "Retail_Sales",
        "Personal_Consumption_Expenditures",
        "Nonfarm_Payrolls",
    ]:
        if col in df.columns:
            components.append(_trailing_z(df[col]))
    if not components:
        return df
    df["Activity_Momentum"] = pd.concat(components, axis=1).mean(axis=1)
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 4. LEAD / LAG PREDICTIVE SIGNALS
# ═══════════════════════════════════════════════════════════════════════════

# M2 → Inflation
_reg_shift("M2_YoY", "M2_YoY_Lag_78w", _W78)
_reg_shift("CPI_YoY", "CPI_YoY_Lead_78w", -_W78)
_reg_shift("Core_PCE_YoY", "Core_PCE_YoY_Lead_52w", -_W52)

# Claims → Unemployment
_reg_shift("Initial_Jobless_Claims", "Claims_Lag_13w", _W13)
_reg_shift("Initial_Jobless_Claims", "Claims_Lag_26w", _W26)
_reg_shift("Unemployment_Rate", "UE_Lead_26w", -_W26)

# Yield Curve → Recession
_reg_shift("Yield_Curve_10Y_2Y", "Curve_10Y2Y_Lag_52w", _W52)
_reg_shift("Yield_Curve_10Y_3M", "Curve_10Y3M_Lag_52w", _W52)

# Breakeven → Realized Inflation
_reg_shift("Breakeven_Inflation_5Y", "Breakeven_5Y_Lag_26w", _W26)
_reg_shift("Breakeven_Inflation_5Y", "Breakeven_5Y_Lag_52w", _W52)

# Housing → CPI Shelter
_reg_shift("Home_Price_YoY", "Home_Price_YoY_Lag_78w", _W78)

# Credit → Consumption
_reg_shift("Credit_Impulse", "Credit_Impulse_Lag_13w", _W13)
_reg_shift("Credit_Impulse", "Credit_Impulse_Lag_26w", _W26)

# FFR → Unemployment
_reg_diff("FedFunds_Rate", "FFR_Chg_52w", _W52, category="leads_lags")
_reg_shift("FFR_Chg_52w", "FFR_Chg_52w_Lag_52w", _W52)

# Sentiment → Activity
_reg_shift("UMich_Consumer_Sentiment", "Sentiment_Lag_13w", _W13)


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════


def score(
    df: pd.DataFrame,
    *,
    pi_star: float = 2.0,
    u_star: float = 4.0,
    copy: bool = True,
) -> pd.DataFrame:
    """
    Apply the scoring layer to a FRED DataFrame.

    Only scores whose input dependencies are satisfied will run.
    If no scores can be computed, returns the DataFrame unchanged
    with a warning.

    Args:
        df:       DataFrame from loader.py (any subset of series).
        pi_star:  inflation target override (default 2.0).
        u_star:   NAIRU override (default 4.0).
        copy:     if True, operate on a copy (default).

    Returns:
        DataFrame with original columns plus all computable scored columns.
    """
    global _PI_STAR, _U_STAR
    _PI_STAR = pi_star
    _U_STAR = u_star

    if copy:
        df = df.copy()

    if df.index.name == "date":
        pass
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    resolved = _resolve(set(df.columns))
    meaningful = [s for s in resolved if s.requires]
    if not meaningful:
        print(
            "\n⚠  No scores can be computed from the columns present.\n"
            "   Scoring requires series from categories like INFLATION, LABOR,\n"
            "   RATES, or SEP.  Returning raw data unchanged."
        )
        df = df.reset_index()
        return df

    cols_before = set(df.columns)
    for spec in resolved:
        df = spec.fn(df)
    cols_added = set(df.columns) - cols_before

    skipped = len(_REGISTRY) - len(resolved)
    print(
        f"\nScoring: {len(resolved)}/{len(_REGISTRY)} blocks resolved  |  "
        f"{len(cols_added)} columns added  |  {skipped} skipped (missing deps)"
    )

    df = df.reset_index()
    return df


def available_scores(df: pd.DataFrame) -> dict:
    """
    Dry-run: show which scores WOULD be computed for a given DataFrame.

    Returns:
        dict with 'resolved', 'skipped', 'columns_added',
        'resolved_count', 'skipped_count'.
    """
    columns = set(df.columns)
    if df.index.name:
        columns.add(str(df.index.name))

    resolved = _resolve(columns)
    resolved_names = {s.name for s in resolved}
    skipped = [s.name for s in _REGISTRY if s.name not in resolved_names]

    columns_added = []
    for s in resolved:
        columns_added.extend(s.produces)

    return {
        "resolved": [s.name for s in resolved],
        "skipped": skipped,
        "columns_added": columns_added,
        "resolved_count": len(resolved),
        "skipped_count": len(skipped),
    }


def list_scored_columns() -> dict[str, list[str]]:
    """Full catalog of all registered scored columns, grouped by category."""
    catalog: dict[str, list[str]] = {}
    for spec in _REGISTRY:
        if spec.category not in catalog:
            catalog[spec.category] = []
        catalog[spec.category].extend(spec.produces)
    return catalog
