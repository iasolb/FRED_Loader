# FRED_Loader

A Python wrapper around the FRED API that puts readable names in front of
raw series codes, with batching and rate-limit handling. Installs as
`fred-loader`.

## Install

```bash
pip install -e .
```

## Quickstart

```python
from fred_loader import Config, pull_fred

cfg = Config(filename="fred_master.csv", output_path="./data")
df = pull_fred(cfg)
```

Cherry-pick series categories:

```python
from fred_loader import INFLATION, LABOR, RATES, Config, pull_fred

cfg = Config(
    filename="policy_inputs.csv",
    output_path="./data",
    series={**INFLATION, **LABOR, **RATES},
)
df = pull_fred(cfg)
```

## Project structure

```
src/fred_loader/
  __init__.py       # public API re-exports
  utils.py          # Config
  load.py           # pull_fred entry point
  series.py         # series catalog: categories and subcategories
  macro_scores.py   # scoring layer: score, available_scores
demo/               # example notebook, data, and outputs
```

## Start here

Open the example notebook in `demo/` for a worked pull.
