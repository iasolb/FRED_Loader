"""A readable Python interface to the FRED macro data API."""

from .load import pull_fred
from .macro_scores import available_scores, list_scored_columns, score
from .utils import Config

# Categories
from .series import INFLATION, OUTPUT, LABOR, RATES, MONEY, HOUSING, CONSUMER
from .series import TRADE, FINANCIAL, FISCAL, COMMODITIES, INEQUALITY, SEP, DEMOGRAPHICS
from .series import ALL_SERIES, CATEGORIES, SUBCATEGORIES

# Subcategories (importable directly, per the series catalog docs)
from .series import CPI, PCE, PPI, IMPORT_EXPORT_PRICES, INFLATION_EXPECTATIONS
from .series import GDP, PRODUCTION, BUSINESS_SURVEYS
from .series import EMPLOYMENT, UNEMPLOYMENT, JOLTS, PRODUCTIVITY
from .series import FED_FUNDS, OVERNIGHT_RATES, TREASURIES, YIELD_SPREADS
from .series import CREDIT_SPREADS, OTHER_RATES
from .series import MONEY_SUPPLY, BANK_CREDIT, CONSUMER_CREDIT
from .series import HOME_PRICES, HOUSING_ACTIVITY, HOUSING_INVENTORY
from .series import CONSUMER_SPENDING, CONSUMER_INCOME
from .series import TRADE_BALANCE, DOLLAR_INDICES, EXCHANGE_RATES
from .series import EQUITY_MARKETS, VOLATILITY, FINANCIAL_CONDITIONS
from .series import FEDERAL_DEBT, FEDERAL_BUDGET
from .series import ENERGY, METALS, AGRICULTURE, COMMODITY_INDICES

__all__ = [
    # Entry points and configuration
    "pull_fred",
    "Config",
    "score",
    "available_scores",
    "list_scored_columns",
    # Composites and lookups
    "ALL_SERIES",
    "CATEGORIES",
    "SUBCATEGORIES",
    # Categories
    "INFLATION",
    "OUTPUT",
    "LABOR",
    "RATES",
    "MONEY",
    "HOUSING",
    "CONSUMER",
    "TRADE",
    "FINANCIAL",
    "FISCAL",
    "COMMODITIES",
    "INEQUALITY",
    "SEP",
    "DEMOGRAPHICS",
    # Subcategories
    "CPI",
    "PCE",
    "PPI",
    "IMPORT_EXPORT_PRICES",
    "INFLATION_EXPECTATIONS",
    "GDP",
    "PRODUCTION",
    "BUSINESS_SURVEYS",
    "EMPLOYMENT",
    "UNEMPLOYMENT",
    "JOLTS",
    "PRODUCTIVITY",
    "FED_FUNDS",
    "OVERNIGHT_RATES",
    "TREASURIES",
    "YIELD_SPREADS",
    "CREDIT_SPREADS",
    "OTHER_RATES",
    "MONEY_SUPPLY",
    "BANK_CREDIT",
    "CONSUMER_CREDIT",
    "HOME_PRICES",
    "HOUSING_ACTIVITY",
    "HOUSING_INVENTORY",
    "CONSUMER_SPENDING",
    "CONSUMER_INCOME",
    "TRADE_BALANCE",
    "DOLLAR_INDICES",
    "EXCHANGE_RATES",
    "EQUITY_MARKETS",
    "VOLATILITY",
    "FINANCIAL_CONDITIONS",
    "FEDERAL_DEBT",
    "FEDERAL_BUDGET",
    "ENERGY",
    "METALS",
    "AGRICULTURE",
    "COMMODITY_INDICES",
]
