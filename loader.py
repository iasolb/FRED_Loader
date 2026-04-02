from fredapi import Fred
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
import time
from series import ALL_SERIES


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
        Build a custom one by merging category dicts from series.py::

            from series import INFLATION, LABOR
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
        self.SERIES = series  # None → use ALL_SERIES
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
