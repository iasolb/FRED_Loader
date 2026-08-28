"""Tests for the pull loop (load_fred_master) and the pull_fred entry point.

All network calls are intercepted by patching ``fred_loader.utils.Fred``.
No real API key, no .env reads, no network traffic.
"""
from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from fred_loader.utils import Config, load_fred_master
from fred_loader.load import pull_fred
from fred_loader.series import ALL_SERIES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DAILY_ID = "DAILY_X"
MONTHLY_ID = "MONTHLY_Y"

SMALL_CATALOG = {
    DAILY_ID: ("Daily Series", "D"),
    MONTHLY_ID: ("Monthly Series", "M"),
}

# A small daily series spanning ~3 weeks
_DATES_DAILY = pd.date_range("2020-01-01", periods=21, freq="D")
_VALUES_DAILY = [float(i) for i in range(1, 22)]  # 1..21

# A small monthly series: two data points
_DATES_MONTHLY = pd.date_range("2020-01-01", periods=3, freq="MS")
_VALUES_MONTHLY = [100.0, 200.0, 300.0]


def _make_series(dates, values, name=None):
    s = pd.Series(values, index=pd.DatetimeIndex(dates), name=name)
    return s


def _fake_get_series(daily_values=None, monthly_values=None):
    """Return a callable that mimics Fred.get_series for SMALL_CATALOG."""

    def _get(series_id, observation_start=None):
        if series_id == DAILY_ID:
            vals = daily_values if daily_values is not None else _VALUES_DAILY
            return _make_series(_DATES_DAILY, vals, name=series_id)
        if series_id == MONTHLY_ID:
            vals = monthly_values if monthly_values is not None else _VALUES_MONTHLY
            return _make_series(_DATES_MONTHLY, vals, name=series_id)
        raise ValueError(f"Unknown series id in fake: {series_id}")

    return _get


def _make_fred_mock(get_series_fn=None):
    mock_instance = MagicMock()
    mock_instance.get_series.side_effect = get_series_fn or _fake_get_series()
    return mock_instance


def _config(tmp_path, catalog=None, **kwargs):
    return Config(
        filename="test_out.csv",
        output_path=tmp_path,
        start="2020-01-01",
        series=catalog if catalog is not None else SMALL_CATALOG,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Test 1: successful pull returns one wide frame with friendly names
# ---------------------------------------------------------------------------

def test_successful_pull_wide_frame(tmp_path):
    mock_fred = _make_fred_mock(_fake_get_series())
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called, "Fake client was never called — patch missed"
    assert isinstance(df, pd.DataFrame)
    # Columns use friendly names, not FRED ids
    assert set(df.columns) == {"Daily Series", "Monthly Series"}
    assert df.index.name == "date"


# ---------------------------------------------------------------------------
# Test 2: daily series are averaged, monthly series take the last value
# ---------------------------------------------------------------------------

def test_mean_vs_last_aggregation(tmp_path):
    cfg = _config(tmp_path, resample_rule="W-FRI")
    mock_fred = _make_fred_mock(_fake_get_series())

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called

    # Compute expected weekly mean for the daily series independently
    daily_raw = _make_series(_DATES_DAILY, _VALUES_DAILY)
    expected_daily = daily_raw.resample("W-FRI").mean()

    # Compute expected weekly last for the monthly series independently
    monthly_raw = _make_series(_DATES_MONTHLY, _VALUES_MONTHLY)
    expected_monthly = monthly_raw.resample("W-FRI").last()

    # Compare for the first non-NaN week in the output
    daily_col = df["Daily Series"].dropna()
    for idx in daily_col.index:
        if idx in expected_daily.index and not pd.isna(expected_daily[idx]):
            assert daily_col[idx] == pytest.approx(expected_daily[idx])

    monthly_col = df["Monthly Series"].dropna()
    for idx in monthly_col.index:
        if idx in expected_monthly.index and not pd.isna(expected_monthly[idx]):
            assert monthly_col[idx] == pytest.approx(expected_monthly[idx])


# ---------------------------------------------------------------------------
# Test 3: mean_freqs is configurable — empty set makes daily use last
# ---------------------------------------------------------------------------

def test_mean_freqs_configurable(tmp_path):
    cfg = _config(tmp_path, mean_freqs=set())
    mock_fred = _make_fred_mock(_fake_get_series())

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called

    # With mean_freqs=set(), daily series should use .last() not .mean()
    daily_raw = _make_series(_DATES_DAILY, _VALUES_DAILY)
    expected_last = daily_raw.resample("W-FRI").last()

    daily_col = df["Daily Series"].dropna()
    for idx in daily_col.index:
        if idx in expected_last.index and not pd.isna(expected_last[idx]):
            assert daily_col[idx] == pytest.approx(expected_last[idx])


# ---------------------------------------------------------------------------
# Test 4: forward fill closes NaN gaps after low-frequency series resample
# ---------------------------------------------------------------------------

def test_forward_fill_closes_gaps(tmp_path):
    cfg = _config(tmp_path)
    mock_fred = _make_fred_mock(_fake_get_series())

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called

    # After the first real observation, no NaN should remain (due to ffill)
    monthly_col = df["Monthly Series"]
    first_real = monthly_col.first_valid_index()
    assert first_real is not None
    assert not monthly_col.loc[first_real:].isna().any(), (
        "Forward fill did not close gaps after first observation"
    )


# ---------------------------------------------------------------------------
# Test 5: one failing series does not abort the rest
# ---------------------------------------------------------------------------

def test_failing_series_does_not_abort(tmp_path, capsys):
    def _get(series_id, observation_start=None):
        if series_id == DAILY_ID:
            raise RuntimeError("Simulated FRED error")
        return _make_series(_DATES_MONTHLY, _VALUES_MONTHLY, name=series_id)

    mock_fred = MagicMock()
    mock_fred.get_series.side_effect = _get
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called
    # Successful series is in the frame
    assert "Monthly Series" in df.columns
    # Failed series is absent
    assert "Daily Series" not in df.columns
    # Failure is reported in output
    captured = capsys.readouterr()
    assert DAILY_ID in captured.out or "Daily Series" in captured.out


# ---------------------------------------------------------------------------
# Test 6: rate-limit delay is honoured — one sleep per series
# ---------------------------------------------------------------------------

def test_rate_limit_delay_per_series(tmp_path):
    mock_fred = _make_fred_mock(_fake_get_series())
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred), \
         patch("fred_loader.utils.time.sleep") as mock_sleep:
        load_fred_master(cfg)

    assert mock_fred.get_series.called
    n_series = len(SMALL_CATALOG)
    assert mock_sleep.call_count == n_series, (
        f"Expected {n_series} sleep calls (one per series), "
        f"got {mock_sleep.call_count}"
    )


# ---------------------------------------------------------------------------
# Test 7: start is passed through to the client as observation_start
# ---------------------------------------------------------------------------

def test_start_passed_to_client(tmp_path):
    start_date = "2015-06-01"
    cfg = Config(
        filename="test_out.csv",
        output_path=tmp_path,
        start=start_date,
        series=SMALL_CATALOG,
    )

    mock_fred = _make_fred_mock(_fake_get_series())

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        load_fred_master(cfg)

    assert mock_fred.get_series.called
    for c in mock_fred.get_series.call_args_list:
        assert c.kwargs.get("observation_start") == start_date or (
            len(c.args) > 1 and c.args[1] == start_date
        ) or c.kwargs.get("observation_start") == start_date


# ---------------------------------------------------------------------------
# Test 8: resample_rule is honoured
# ---------------------------------------------------------------------------

def test_resample_rule_honoured(tmp_path):
    cfg_weekly = _config(tmp_path, resample_rule="W-FRI")
    cfg_monthly = _config(tmp_path, resample_rule="MS")

    mock_weekly = _make_fred_mock(_fake_get_series())
    mock_monthly = _make_fred_mock(_fake_get_series())

    with patch("fred_loader.utils.Fred", return_value=mock_weekly):
        df_w = load_fred_master(cfg_weekly)

    with patch("fred_loader.utils.Fred", return_value=mock_monthly):
        df_m = load_fred_master(cfg_monthly)

    assert mock_weekly.get_series.called
    assert mock_monthly.get_series.called
    # Weekly should have more rows than monthly for the same date range
    assert len(df_w) >= len(df_m)


# ---------------------------------------------------------------------------
# Test 9: pull_fred end-to-end — writes CSV, returns frame; apply_scores paths
# ---------------------------------------------------------------------------

def test_pull_fred_end_to_end(tmp_path):
    mock_fred = _make_fred_mock(_fake_get_series())
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        result = pull_fred(cfg, apply_scores=False)

    assert mock_fred.get_series.called
    assert isinstance(result, pd.DataFrame)
    assert (tmp_path / "test_out.csv").exists()


def test_pull_fred_apply_scores_true(tmp_path):
    """apply_scores=True must reach the scoring layer without crashing."""
    mock_fred = _make_fred_mock(_fake_get_series())
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        result = pull_fred(cfg, apply_scores=True)

    assert mock_fred.get_series.called
    assert isinstance(result, pd.DataFrame)
    assert (tmp_path / "test_out.csv").exists()


def test_pull_fred_apply_scores_false_skips_scoring(tmp_path):
    """apply_scores=False returns only raw FRED columns."""
    mock_fred = _make_fred_mock(_fake_get_series())
    cfg = _config(tmp_path)

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        result = pull_fred(cfg, apply_scores=False)

    assert mock_fred.get_series.called
    # The raw output should have exactly the friendly names from SMALL_CATALOG
    assert set(result.columns) == {"Daily Series", "Monthly Series"}


# ---------------------------------------------------------------------------
# Test 10: default catalog is the whole catalog
# ---------------------------------------------------------------------------

def test_default_catalog_uses_all_series(tmp_path):
    """Config with no series= must pull every entry in ALL_SERIES."""

    def _tiny_series(series_id, observation_start=None):
        return pd.Series(
            [1.0, 2.0],
            index=pd.DatetimeIndex(pd.date_range("2020-01-01", periods=2, freq="W-FRI")),
        )

    mock_fred = MagicMock()
    mock_fred.get_series.side_effect = _tiny_series

    # No series= → should default to ALL_SERIES
    cfg = Config(
        filename="all_series_test.csv",
        output_path=tmp_path,
        start="2020-01-01",
        series=None,
    )
    assert cfg.SERIES is ALL_SERIES, "Config with series=None must use ALL_SERIES"

    with patch("fred_loader.utils.Fred", return_value=mock_fred):
        df = load_fred_master(cfg)

    assert mock_fred.get_series.called
    expected_calls = len(ALL_SERIES)
    assert mock_fred.get_series.call_count == expected_calls, (
        f"Expected {expected_calls} calls (one per ALL_SERIES entry), "
        f"got {mock_fred.get_series.call_count}"
    )
