from fredapi import Fred
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
import time
from .series import ALL_SERIES, CATEGORIES, SUBCATEGORIES


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SERIES RESOLVER                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Flattened so a subcategory can be named without knowing its parent.
_SUBCATEGORY_FLAT: dict[str, dict] = {}
for _cat, _subs in SUBCATEGORIES.items():
    for _subname, _subdict in _subs.items():
        _SUBCATEGORY_FLAT[_subname] = _subdict


def _resolve_one(token: str) -> dict:
    """Resolve one string token into a series dict.

    Order: exact series id, then category, then subcategory.
    """
    upper = token.upper()

    if upper in ALL_SERIES:
        return {upper: ALL_SERIES[upper]}
    if upper in CATEGORIES:
        return CATEGORIES[upper]
    if upper in _SUBCATEGORY_FLAT:
        return _SUBCATEGORY_FLAT[upper]

    raise KeyError(
        f"'{token}' is not a recognized series, category, or subcategory.\n"
        f"  Use available() to browse, or search('keyword') to find series."
    )


def resolve_series(spec) -> dict:
    """Turn a flexible series specification into the internal series dict.

    Accepted inputs
    ---------------
    None                        -> ALL_SERIES (everything)
    "CPIAUCSL"                  -> a single series
    "INFLATION"                 -> an entire category
    "CPI"                       -> a subcategory
    ["CPI", "TREASURIES"]       -> mix and match, merged
    dict                        -> passed straight through

    A dict passes through untouched, so every existing caller keeps working.
    """
    if spec is None:
        return ALL_SERIES
    if isinstance(spec, dict):
        return spec
    if isinstance(spec, str):
        return _resolve_one(spec)
    if isinstance(spec, (list, tuple)):
        merged: dict = {}
        for token in spec:
            merged.update(_resolve_one(token))
        return merged

    raise TypeError(
        f"series must be None, str, list[str], or dict, got {type(spec).__name__}"
    )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  DISCOVERY, browse and search the catalog without reading series.py      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


def available(category: str | None = None) -> None:
    """Print what is in the catalog.

    Call with no arguments for the categories, then pass one to drill in::

        available()             # every category
        available("INFLATION")  # series inside a category
        available("CPI")        # series inside a subcategory
    """
    if category is None:
        print("Categories  (pass one to available() to drill down)\n")
        for cat_name, cat_dict in CATEGORIES.items():
            subs = list(SUBCATEGORIES.get(cat_name, {}).keys())
            sub_str = f"\n    L {', '.join(subs)}" if subs else ""
            print(f"  {cat_name:<20s} ({len(cat_dict):>3d} series){sub_str}")
        print(f"\n  {'TOTAL':<20s} ({len(ALL_SERIES):>3d} series)")
        return

    upper = category.upper()
    if upper in CATEGORIES:
        target, label = CATEGORIES[upper], f"Category: {upper}"
    elif upper in _SUBCATEGORY_FLAT:
        target, label = _SUBCATEGORY_FLAT[upper], f"Subcategory: {upper}"
    else:
        print(f"'{category}' not found. Run available() with no args to see options.")
        return

    print(f"{label}  ({len(target)} series)\n")
    for series_id, (name, freq) in target.items():
        print(f"  {series_id:<24s}  {name:<40s}  [{freq}]")
    print()


def search(keyword: str) -> list[str]:
    """Search the catalog by keyword, case-insensitive.

    Matches the FRED series id AND the friendly name, so both
    `search("CPIAUCSL")` and `search("inflation")` work.

    Returns the list of matching series ids.
    """
    kw = keyword.lower()
    hits = [
        series_id
        for series_id, (name, _freq) in ALL_SERIES.items()
        if kw in series_id.lower() or kw in name.lower()
    ]

    if not hits:
        print(f"No series matching '{keyword}'.")
        return []

    print(f"Found {len(hits)} series matching '{keyword}':\n")
    for series_id in hits:
        name, freq = ALL_SERIES[series_id]
        print(f"  {series_id:<24s}  {name:<40s}  [{freq}]")
    print()
    return hits


def info(series_id: str) -> None:
    """Print everything known about one series::

        info("CPIAUCSL")
    """
    key = series_id.upper()
    if key not in ALL_SERIES:
        print(f"'{series_id}' not found. Try search('{series_id}').")
        return

    name, freq = ALL_SERIES[key]

    parent_cat = parent_sub = None
    for cat_name, cat_dict in CATEGORIES.items():
        if key in cat_dict:
            parent_cat = cat_name
            for sub_name, sub_dict in SUBCATEGORIES.get(cat_name, {}).items():
                if key in sub_dict:
                    parent_sub = sub_name
            break

    _FREQ_WORDS = {
        "D": "daily",
        "W": "weekly",
        "M": "monthly",
        "Q": "quarterly",
        "A": "annual",
        "SEP": "irregular (FOMC projections)",
    }

    print(f"\n  FRED id:      {key}")
    print(f"  Name:         {name}")
    print(f"  Category:     {parent_cat or '-'}")
    print(f"  Subcategory:  {parent_sub or '-'}")
    print(f"  Native freq:  {freq}  ({_FREQ_WORDS.get(freq, 'unknown')})")
    print(f"  FRED page:    https://fred.stlouisfed.org/series/{key}\n")


class Config:
    """
    Configuration for a FRED data pull.

    Parameters
    ----------
    filename : str
        Name of the output CSV file (e.g. "fred_master.csv").
    output_path : Path
        Directory where the CSV will be saved.
    start : str, optional
        Observation start date in 'YYYY-MM-DD' format.
        Defaults to '1990-01-01'.
    resample_rule : str, optional
        Pandas resample frequency string.  Controls the output granularity.
        Defaults to 'W-FRI' (weeks ending Friday).
    mean_freqs : set[str], optional
        Set of native-frequency codes whose series should be aggregated
        via MEAN when resampling (e.g. daily series averaged into weekly
        buckets).  All other frequencies use LAST.
        Defaults to {'D'} — daily series are averaged; everything else
        takes the last observation per period.
    series : dict, optional
        Custom series catalog mapping FRED IDs to (friendly_name, native_freq)
        tuples.  When None the full built-in catalog is used.
        Build a custom one by merging category dicts from fred_loader::

            from fred_loader import INFLATION, LABOR
            Config(..., series={**INFLATION, **LABOR})
    """

    def __init__(
        self,
        filename: str,
        output_path: Path | str,
        start: str = "1990-01-01",
        resample_rule: str = "W-FRI",
        mean_freqs: Optional[set] = None,
        series: Optional[dict] = None,
        pi_star: Optional[float] = 2.0,
        u_star: Optional[float] = 4.0,
    ):
        self.FILENAME = filename
        self.OUTPUT_PATH = Path(output_path).resolve()
        self.START = start
        self.RESAMPLE_RULE = resample_rule
        self.MEAN_FREQS = mean_freqs if mean_freqs is not None else {"D"}
        # Resolved here so `series=` accepts a category name, a subcategory, a
        # single FRED id, or a list of any of those, as well as the dict it has
        # always taken. A dict passes through untouched and None still means
        # the whole catalog, so nothing that worked before changes.
        self._series_input = series
        self.SERIES = resolve_series(series)
        self.INFLATION_TARGET = pi_star if pi_star else 2.0
        self.NATURAL_RATE_UNEMPLOYMENT = u_star if u_star else 4.0


def load_fred_master(config: Config) -> pd.DataFrame:
    """
    Pull series from FRED, resample to a uniform frequency, and save to CSV.

    Parameters
    ----------
    config : Config
        Fully-populated configuration object.

    Returns
    -------
    pd.DataFrame
        Wide DataFrame indexed by date with one column per series,
        forward-filled after merge.
    """
    load_dotenv()
    fred = Fred(api_key=os.getenv("FRED_API_KEY"))

    # Resolve which series catalog to use
    series_dict = config.SERIES if config.SERIES is not None else ALL_SERIES

    # ── Pull & resample ───────────────────────────────────────────────────

    def pull_all(series_dict: dict) -> pd.DataFrame:
        """
        Pull every series from FRED, resample, and forward-fill.

        Daily series  → weekly MEAN  (captures full week's behavior)
        All others    → weekly LAST  (point-in-time, then ffill fills the gaps)

        Returns a single wide DataFrame indexed by week-ending date.
        """
        frames = {}
        failed = []

        for series_id, (name, native_freq) in series_dict.items():
            try:
                s = fred.get_series(series_id, observation_start=config.START)
                s.name = name

                if native_freq in config.MEAN_FREQS:
                    s = s.resample(config.RESAMPLE_RULE).mean()
                else:
                    s = s.resample(config.RESAMPLE_RULE).last()

                frames[name] = s
                agg = "mean" if native_freq in config.MEAN_FREQS else "last"
                print(f"  ✓ {name:<40s} ({series_id:<18s} {native_freq} → {agg})")
                time.sleep(0.5)  # be nice to the API
            except Exception as e:
                failed.append((series_id, name, str(e)))
                print(f"  ✗ {name:<40s} ({series_id}) — {e}")
                time.sleep(0.5)  # be nice to the API

        df = pd.DataFrame(frames)
        df = df.ffill()
        df.index.name = "date"

        if failed:
            print(f"\n⚠  {len(failed)} series failed:")
            for sid, nm, err in failed:
                print(f"    {nm} ({sid}): {err}")

        print(
            f"\nLoaded {len(frames)} series  |  {df.shape[0]} weeks  |  {df.columns.size} columns"
        )
        return df

    df = pull_all(series_dict)

    return df
