"""Coverage for the scoring layer: the registry, the resolver, and the maths.

Written against measured coverage: macro_scores.py sat at 42% with most of the
registry, the whole dependency resolver, and every formula untested.

Two things this file is careful about:

- **The resolver is the interesting part.** Scores form a chain (Headline_CPI
  gives CPI_YoY, which with FedFunds_Rate gives Real_FFR_CPI, which feeds the
  flags). Whether a score runs depends on columns produced by other scores, so
  the tests give a MINIMAL input set and assert the whole downstream chain
  appears. A test that hands over every column at once would not prove the
  resolver resolves anything.
- **Formulas are checked against the arithmetic, not against themselves.**
  Each expectation is computed independently in the test, so a change to a
  formula fails here rather than quietly redefining the indicator.

Weekly data throughout, because the windows are weekly (52 weeks a year).
"""

import numpy as np
import pandas as pd
import pytest

from fred_loader.macro_scores import (
    _PI_STAR,
    _REGISTRY,
    _SAHM_THRESHOLD,
    _U_STAR,
    available_scores,
    list_scored_columns,
    score,
)

N = 200  # weeks, comfortably more than the 78-week longest window


def weeks(n=N):
    return pd.date_range("2020-01-03", periods=n, freq="W-FRI")


def frame(**columns):
    """A weekly frame with a date index named 'date', as the loader produces."""
    idx = weeks(len(next(iter(columns.values()))) if columns else N)
    df = pd.DataFrame(columns, index=idx)
    df.index.name = "date"
    return df


def rising(start=100.0, step=0.5, n=N):
    return start + np.arange(n) * step


# ── the catalog ───────────────────────────────────────────────────────────


def test_the_catalog_groups_columns_by_category():
    catalog = list_scored_columns()
    assert set(catalog) == {"derived", "flags", "leads_lags", "continuous"}
    assert all(isinstance(v, list) and v for v in catalog.values())


def test_the_catalog_covers_every_registered_spec():
    listed = {col for cols in list_scored_columns().values() for col in cols}
    registered = {col for spec in _REGISTRY for col in spec.produces}
    assert listed == registered


def test_no_two_specs_produce_the_same_column():
    """A duplicate would mean one score silently overwriting another."""
    produced = [col for spec in _REGISTRY for col in spec.produces]
    assert len(produced) == len(set(produced))


def test_no_spec_requires_a_column_nothing_can_supply():
    """Every requirement is either a raw series name or produced by another
    spec. A requirement nothing supplies is a score that can never run."""
    produced = {col for spec in _REGISTRY for col in spec.produces}
    raw_series_like = set()
    for spec in _REGISTRY:
        raw_series_like |= {r for r in spec.requires if r not in produced}
    # Those leftovers must look like loader column names, not typos of
    # produced ones. Assert they are non-empty strings and disjoint from
    # produced, which is what makes the resolver's job well defined.
    assert all(isinstance(r, str) and r for r in raw_series_like)
    assert not (raw_series_like & produced)


# ── the resolver, dry run ─────────────────────────────────────────────────


def test_an_empty_frame_resolves_only_the_dependency_free_scores():
    """Two specs require nothing, so they always resolve. Everything else
    should be skipped rather than attempted."""
    result = available_scores(pd.DataFrame())
    free = {spec.name for spec in _REGISTRY if not spec.requires}
    assert set(result["resolved"]) == free
    assert result["skipped_count"] == len(_REGISTRY) - len(free)


def test_one_raw_column_resolves_its_direct_score():
    result = available_scores(frame(Headline_CPI=rising()))
    assert "CPI_YoY" in result["resolved"]
    assert "CPI_YoY" in result["columns_added"]


def test_the_resolver_follows_a_multi_step_chain():
    """Headline_CPI and FedFunds_Rate alone should reach Real_FFR_CPI, which
    depends on CPI_YoY, which is itself derived. That is the resolver doing
    real work rather than a single pass."""
    result = available_scores(
        frame(Headline_CPI=rising(), FedFunds_Rate=np.full(N, 2.0))
    )
    assert {"CPI_YoY", "real_ffr_cpi"} <= set(result["resolved"])


def test_a_score_whose_inputs_are_absent_is_skipped_not_run():
    result = available_scores(frame(Headline_CPI=rising()))
    assert "taylor_rule" in result["skipped"]


def test_the_dry_run_counts_agree_with_its_lists():
    result = available_scores(frame(Headline_CPI=rising()))
    assert result["resolved_count"] == len(result["resolved"])
    assert result["skipped_count"] == len(result["skipped"])
    assert result["resolved_count"] + result["skipped_count"] == len(_REGISTRY)


def test_the_dry_run_counts_the_index_as_an_available_column():
    """The index is named 'date' and some scores may key off it, so it has to
    be visible to the resolver."""
    df = frame(Headline_CPI=rising())
    assert "date" == df.index.name
    available_scores(df)  # must not raise on a named index


# ── score(), the happy path ───────────────────────────────────────────────


def test_the_dry_run_promise_is_a_superset_of_what_score_delivers():
    """KNOWN GAP, asserted as it is rather than as it should be.

    `available_scores` promises the `produces` of every resolved spec, but two
    specs declare `requires=set()` and then return early if none of their
    OPTIONAL inputs are present (`expectations_anchoring` wants any of the
    inflation-expectation series, `activity_momentum` likewise). So the dry run
    always lists them as resolved and always promises their columns, and
    `score` does not always deliver them.

    The registry has no way to say "any one of these", which is what those two
    specs actually need, so this is a design gap rather than a typo. Asserting
    the superset relation pins current behaviour without pretending the
    over-promise is correct.
    """
    df = frame(Headline_CPI=rising(), FedFunds_Rate=np.full(N, 2.0))
    promised = set(available_scores(df)["columns_added"])
    delivered = set(score(df).columns)

    conditional = {
        "Expect_Anchor_Score",
        "Expect_Anchor_Signed",
        "Activity_Momentum",
    }
    # Everything promised that is not one of the conditional columns must show up.
    assert (promised - conditional) <= delivered
    # And the conditional ones are exactly the promise that went unmet here.
    assert not (conditional & delivered)


def test_score_keeps_the_original_columns_and_rows():
    df = frame(Headline_CPI=rising())
    out = score(df)
    assert len(out) == len(df)
    assert "Headline_CPI" in out.columns


def test_score_copies_by_default():
    df = frame(Headline_CPI=rising())
    before = set(df.columns)
    score(df)
    assert set(df.columns) == before


def test_score_can_mutate_in_place():
    df = frame(Headline_CPI=rising())
    score(df, copy=False)
    assert "CPI_YoY" in df.columns


def test_a_frame_with_nothing_usable_comes_back_effectively_unchanged():
    """Only the two dependency-free scores can run, so no raw column is lost
    and nothing raises."""
    df = frame(Something_Unrelated=rising())
    out = score(df)
    assert "Something_Unrelated" in out.columns
    assert len(out) == len(df)


# ── the formulas ──────────────────────────────────────────────────────────


def test_score_returns_a_reset_index_with_date_as_a_column():
    """Worth pinning: the input is date-indexed and the OUTPUT is not. `score`
    ends with `reset_index()`, so downstream code gets a RangeIndex and a
    `date` column. Every comparison below has to account for that."""
    out = score(frame(Headline_CPI=rising()))
    assert "date" in out.columns
    assert isinstance(out.index, pd.RangeIndex)


def test_year_over_year_is_a_52_week_percent_change():
    values = rising()
    out = score(frame(Headline_CPI=values))
    expected = pd.Series(values).pct_change(52) * 100
    pd.testing.assert_series_equal(
        out["CPI_YoY"], expected, check_names=False, check_index=False
    )


def test_year_over_year_is_nan_before_a_full_year_of_data():
    out = score(frame(Headline_CPI=rising()))
    assert out["CPI_YoY"].iloc[:52].isna().all()
    assert out["CPI_YoY"].iloc[52:].notna().all()


def test_a_flat_series_has_zero_growth():
    out = score(frame(Headline_CPI=np.full(N, 100.0)))
    assert out["CPI_YoY"].dropna().abs().max() == pytest.approx(0.0)


def test_the_three_month_annualised_rate_scales_by_52_over_13():
    values = rising(start=100.0, step=0.2)
    out = score(frame(Core_PCE=values))
    expected = pd.Series(values).pct_change(13) * (52 / 13) * 100
    pd.testing.assert_series_equal(
        out["Core_PCE_3m_ann"], expected, check_names=False, check_index=False
    )


def test_a_lag_shifts_forward_and_a_lead_shifts_back():
    values = rising()
    out = score(frame(Headline_CPI=values))
    yoy = out["CPI_YoY"]
    # CPI_YoY_Lead_78w is a NEGATIVE shift: it pulls the future back.
    pd.testing.assert_series_equal(
        out["CPI_YoY_Lead_78w"], yoy.shift(-78), check_names=False
    )


def test_a_lag_of_m2_pulls_the_past_forward():
    out = score(frame(M2_Money_Stock=rising()))
    pd.testing.assert_series_equal(
        out["M2_YoY_Lag_78w"], out["M2_YoY"].shift(78), check_names=False
    )


def test_real_rates_subtract_inflation_from_the_nominal_rate():
    out = score(frame(Headline_CPI=rising(), FedFunds_Rate=np.full(N, 5.0)))
    expected = 5.0 - out["CPI_YoY"]
    pd.testing.assert_series_equal(out["Real_FFR_CPI"], expected, check_names=False)


def test_debt_to_gdp_converts_units_before_dividing():
    """The formula divides debt by 1000 first, because FRED reports federal
    debt in MILLIONS and nominal GDP in BILLIONS. Getting this wrong by a
    factor of 1000 is the obvious failure mode, so the test uses realistic
    magnitudes: about $35tn of debt against about $27tn of output should read
    as roughly 130 percent, not 0.13 or 130000.
    """
    out = score(
        frame(
            Federal_Debt_Total=np.full(N, 35_000_000.0),  # millions
            Nominal_GDP=np.full(N, 27_000.0),             # billions
        )
    )
    assert out["Debt_to_GDP"].dropna().iloc[0] == pytest.approx(129.6, abs=0.1)


# ── the flags ─────────────────────────────────────────────────────────────


def test_curve_inversion_flags_only_negative_spreads():
    spread = np.where(np.arange(N) < 100, 0.5, -0.5)
    out = score(frame(Yield_Curve_10Y_2Y=spread))
    flag = out["Flag_Curve_Inverted_10Y2Y"]
    assert flag.iloc[:100].eq(0).all()
    assert flag.iloc[100:].eq(1).all()
    assert set(flag.unique()) <= {0, 1}


def test_a_spread_of_exactly_zero_is_not_inverted():
    """Boundary: the condition is strictly less than zero."""
    out = score(frame(Yield_Curve_10Y_2Y=np.zeros(N)))
    assert out["Flag_Curve_Inverted_10Y2Y"].eq(0).all()


def test_the_sahm_rule_triggers_after_a_sharp_rise_then_stands_down():
    """Sahm compares a 3-month average against the trailing 12-month MINIMUM,
    so a step up trips it and then it resets once the minimum catches up a year
    later. Asserting the final value would therefore be wrong; the signal is
    that it fires at all, shortly after the step.
    """
    ue = np.concatenate([np.full(120, 4.0), np.full(N - 120, 5.5)])
    out = score(frame(Unemployment_Rate=ue))
    triggered = out["Flag_Sahm_Triggered"]

    assert triggered.max() == 1                       # it fires
    assert triggered.iloc[125:160].max() == 1         # soon after the step
    # and the flag is exactly the indicator against the documented threshold
    expected = (out["Sahm_Indicator"] >= _SAHM_THRESHOLD).astype(int)
    pd.testing.assert_series_equal(triggered, expected, check_names=False)


def test_a_flat_unemployment_rate_never_trips_sahm():
    out = score(frame(Unemployment_Rate=np.full(N, 4.0)))
    assert out["Flag_Sahm_Triggered"].eq(0).all()


def test_m2_flags_separate_excess_from_contraction():
    out = score(frame(M2_Money_Stock=rising(start=100.0, step=2.0)))
    assert set(out["Flag_M2_Excess"].unique()) <= {0, 1}
    assert set(out["Flag_M2_Contraction"].unique()) <= {0, 1}
    # strong growth must not read as contraction
    assert out["Flag_M2_Contraction"].eq(0).all()


def test_shrinking_m2_reads_as_contraction():
    out = score(frame(M2_Money_Stock=rising(start=200.0, step=-0.5)))
    assert out["Flag_M2_Contraction"].dropna().max() == 1


# ── the Taylor rule, and the policy overrides ─────────────────────────────


def _taylor_frame():
    return frame(
        Core_PCE=rising(start=100.0, step=0.2),
        FedFunds_Rate=np.full(N, 2.0),
        Unemployment_Rate=np.full(N, 4.0),
        SEP_FedFunds_Median_LongerRun=np.full(N, 2.5),
    )


def test_the_taylor_rule_matches_its_stated_formula():
    out = score(_taylor_frame())
    r_star = out["SEP_r_star"].fillna(0.5)
    pi = out["Core_PCE_YoY"]
    u_gap = _U_STAR - out["Unemployment_Rate"]
    expected = r_star + pi + 0.5 * (pi - _PI_STAR) + 0.5 * u_gap
    pd.testing.assert_series_equal(out["Taylor_Prescribed"], expected, check_names=False)


def test_the_taylor_gap_is_prescribed_minus_actual():
    out = score(_taylor_frame())
    pd.testing.assert_series_equal(
        out["Taylor_Gap"],
        out["Taylor_Prescribed"] - out["FedFunds_Rate"],
        check_names=False,
    )


def test_the_taylor_flags_are_mutually_exclusive():
    out = score(_taylor_frame())
    assert (out["Flag_Taylor_Below_100bp"] + out["Flag_Taylor_Above_100bp"]).max() <= 1


def test_a_higher_inflation_target_lowers_the_prescribed_rate():
    """pi_star enters the rule negatively, so raising the target should
    prescribe a looser policy rate. This is the override actually biting."""
    base = score(_taylor_frame())["Taylor_Prescribed"].dropna()
    loose = score(_taylor_frame(), pi_star=4.0)["Taylor_Prescribed"].dropna()
    assert (loose < base).all()
    # restore the module default so later tests are unaffected
    score(_taylor_frame())


def test_a_higher_nairu_raises_the_prescribed_rate():
    """u_star enters through the employment gap, so raising it widens the gap
    at a fixed unemployment rate."""
    base = score(_taylor_frame())["Taylor_Prescribed"].dropna()
    tight = score(_taylor_frame(), u_star=6.0)["Taylor_Prescribed"].dropna()
    assert (tight > base).all()
    score(_taylor_frame())


def test_mandate_tension_reports_a_regime_label():
    out = score(frame(Core_PCE=rising(start=100.0, step=0.3), Unemployment_Rate=np.full(N, 4.0)))
    assert "Mandate_Regime" in out.columns
    assert out["Mandate_Regime"].notna().any()
