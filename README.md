# FRED_Loader
Generalized FRED Data Loader

## Install

pip install -e .

## Project Structure

FRED_Loader/
  pyproject.toml
  requirements.txt
  README.md
  .env-example
  src/fred_loader/
    __init__.py       # public API re-exports
    utils.py          # Config
    load.py           # pull_fred entry point
    series.py         # series catalog: categories and subcategories
    macro_scores.py   # scoring layer: score, available_scores
  demo/               # example notebook, data, and outputs

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
