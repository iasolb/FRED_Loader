"""
FRED Series Catalog
====================

Each category is a standalone dict mapping FRED series IDs to
``(friendly_name, native_frequency)`` tuples.

Import individual categories and combine them to build a custom pull::

    from series import INFLATION, LABOR, HOUSING
    from load import pull_fred

    df = pull_fred("subset.csv", series={**INFLATION, **LABOR, **HOUSING})

Or use ``ALL_SERIES`` for the full catalog::

    from series import ALL_SERIES

Frequency codes
---------------
D   = daily      — resampled via MEAN by default (captures intra-period moves)
W   = weekly     — resampled via MEAN by default
M   = monthly    — resampled via LAST (point-in-time snapshot)
Q   = quarterly  — resampled via LAST
A   = annual     — resampled via LAST
SEP = irregular  — FOMC Summary of Economic Projections (forward-filled)
"""

# ── Prices & Inflation ────────────────────────────────────────────────────
# Headline and core price indices, inflation expectations, and breakevens.
# Covers CPI, PCE, and market-implied inflation across multiple horizons.
INFLATION = {
    "CPIAUCSL": ("Headline_CPI", "M"),
    "CPILFESL": ("Core_CPI", "M"),
    "PCEPI": ("PCE_Price_Index", "M"),
    "PCEPILFE": ("Core_PCE", "M"),
    "CPIUFDSL": ("CPI_Food", "M"),
    "CPIENGSL": ("CPI_Energy", "M"),
    "MICH": ("UMich_Inflation_Expectations", "M"),
    "T5YIE": ("Breakeven_Inflation_5Y", "D"),
    "T10YIE": ("Breakeven_Inflation_10Y", "D"),
}

# ── Output & Growth ───────────────────────────────────────────────────────
# GDP (nominal and real), industrial production, and vehicle sales.
# Quarterly GDP series are forward-filled into higher-frequency output.
OUTPUT = {
    "GDP": ("Nominal_GDP", "Q"),
    "GDPC1": ("Real_GDP", "Q"),
    "A939RX0Q048SBEA": ("Real_GDP_Per_Capita", "Q"),
    "INDPRO": ("Industrial_Production", "M"),
    "TOTALSA": ("Total_Vehicle_Sales", "M"),
}

# ── Labor Market ──────────────────────────────────────────────────────────
# Unemployment, payrolls, claims, earnings, openings, and participation.
# Core inputs for Sahm rule, JOLTS/UE ratio, and dual-mandate scoring.
LABOR = {
    "UNRATE": ("Unemployment_Rate", "M"),
    "U6RATE": ("U6_Underemployment", "M"),
    "PAYEMS": ("Nonfarm_Payrolls", "M"),
    "ICSA": ("Initial_Jobless_Claims", "W"),
    "AWHAETP": ("Avg_Weekly_Hours", "M"),
    "CES0500000003": ("Avg_Hourly_Earnings", "M"),
    "JTSJOL": ("JOLTS_Job_Openings", "M"),
    "CIVPART": ("Labor_Force_Participation", "M"),
}

# ── Interest Rates & Yields ──────────────────────────────────────────────
# Fed funds, Treasury curve (2Y/10Y/30Y), yield curve spreads, credit
# spreads (HY and IG OAS), and the 30-year mortgage rate.
RATES = {
    "FEDFUNDS": ("FedFunds_Rate", "M"),
    "DFF": ("FedFunds_Daily", "D"),
    "DGS2": ("Treasury_2Y", "D"),
    "DGS10": ("Treasury_10Y", "D"),
    "DGS30": ("Treasury_30Y", "D"),
    "T10Y2Y": ("Yield_Curve_10Y_2Y", "D"),
    "T10Y3M": ("Yield_Curve_10Y_3M", "D"),
    "BAMLH0A0HYM2": ("HY_OAS_Spread", "D"),
    "BAMLC0A0CM": ("IG_OAS_Spread", "D"),
    "MORTGAGE30US": ("Mortgage_Rate_30Y", "W"),
}

# ── Money Supply & Credit ────────────────────────────────────────────────
# M2, bank reserves, commercial lending, and consumer credit (total and
# revolving).  Key inputs for M2→CPI lead signals and credit impulse.
MONEY = {
    "M2SL": ("M2_Money_Stock", "M"),
    "TOTRESNS": ("Total_Reserves", "M"),
    "BUSLOANS": ("Commercial_Loans", "M"),
    "TOTALSL": ("Consumer_Credit_Total", "M"),
    "REVOLSL": ("Consumer_Credit_Revolving", "M"),
}

# ── Housing ──────────────────────────────────────────────────────────────
# Home prices (Case-Shiller), starts, permits, existing sales, and
# months of supply.  Feeds housing affordability pressure scores and
# the home-price→shelter-CPI lead signal.
HOUSING = {
    "CSUSHPISA": ("Case_Shiller_Home_Price", "M"),
    "HOUST": ("Housing_Starts", "M"),
    "PERMIT": ("Building_Permits", "M"),
    "EXHOSLUSM495S": ("Existing_Home_Sales", "M"),
    "MSACSR": ("Months_Supply_Housing", "M"),
}

# ── Consumer & Sentiment ─────────────────────────────────────────────────
# Michigan sentiment, retail sales, personal consumption, and savings rate.
# Drives the consumer-side of the activity momentum composite.
CONSUMER = {
    "UMCSENT": ("UMich_Consumer_Sentiment", "M"),
    "RSAFS": ("Retail_Sales", "M"),
    "PCE": ("Personal_Consumption_Expenditures", "M"),
    "PSAVERT": ("Personal_Savings_Rate", "M"),
}

# ── Trade & Dollar ───────────────────────────────────────────────────────
# Trade balance and the broad trade-weighted dollar index.
TRADE = {
    "BOPGSTB": ("Trade_Balance", "M"),
    "DTWEXBGS": ("Trade_Weighted_USD_Broad", "D"),
}

# ── Financial Conditions & Volatility ────────────────────────────────────
# VIX, S&P 500, Chicago Fed NFCI, and St. Louis Fed financial stress.
# NFCI < 0 = looser than average; used in FCI-contradiction flags.
FINANCIAL = {
    "VIXCLS": ("VIX", "D"),
    "SP500": ("SP500", "D"),
    "NFCI": ("Chicago_Fed_Financial_Conditions", "W"),
    "STLFSI2": ("StL_Fed_Financial_Stress", "W"),
}

# ── Fiscal ───────────────────────────────────────────────────────────────
# Federal debt, annual surplus/deficit, and the monthly Treasury statement.
# Used for debt/GDP ratio and fiscal-dominance risk flags.
FISCAL = {
    "GFDEBTN": ("Federal_Debt_Total", "Q"),
    "FYFSD": ("Federal_Surplus_Deficit", "A"),
    "MTSDS133FMS": ("Monthly_Treasury_Statement_Deficit", "M"),
}

# ── Inequality ───────────────────────────────────────────────────────────
# Annual Gini index for the US — sparse but useful for long-run context.
INEQUALITY = {
    "SIPOVGINIUSA": ("Gini_Index_USA", "A"),
}

# ── FOMC SEP Projections ─────────────────────────────────────────────────
# Median dot-plot projections: fed funds, GDP, unemployment, PCE, core PCE.
# Published ~4x/year; forward-filled to fill weekly gaps.
# Powers the SEP-based r* estimate and policy-stance scoring.
SEP = {
    "FEDTARMD": ("SEP_FedFunds_Median", "SEP"),
    "FEDTARMDLR": ("SEP_FedFunds_Median_LongerRun", "SEP"),
    "GDPC1MD": ("SEP_RealGDP_Median", "SEP"),
    "UNRATEMD": ("SEP_Unemployment_Median", "SEP"),
    "PCECTPIMD": ("SEP_PCE_Inflation_Median", "SEP"),
    "JCXFEMD": ("SEP_CorePCE_Median", "SEP"),
}


# ── Composite ────────────────────────────────────────────────────────────
# Merge every category into one dict.  This is the default when no custom
# series= argument is passed to pull_fred().

ALL_SERIES = {
    **INFLATION,
    **OUTPUT,
    **LABOR,
    **RATES,
    **MONEY,
    **HOUSING,
    **CONSUMER,
    **TRADE,
    **FINANCIAL,
    **FISCAL,
    **INEQUALITY,
    **SEP,
}

# Convenience list so users can see what's available
CATEGORIES = {
    "INFLATION": INFLATION,
    "OUTPUT": OUTPUT,
    "LABOR": LABOR,
    "RATES": RATES,
    "MONEY": MONEY,
    "HOUSING": HOUSING,
    "CONSUMER": CONSUMER,
    "TRADE": TRADE,
    "FINANCIAL": FINANCIAL,
    "FISCAL": FISCAL,
    "INEQUALITY": INEQUALITY,
    "SEP": SEP,
}
