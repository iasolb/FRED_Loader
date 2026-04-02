# fmt: off
"""
FRED Series Catalog
====================

Hierarchical catalog with two levels of granularity:

    Subcategory:  from series import CPI, PPI, TREASURIES
    Category:     from series import INFLATION, RATES
    Everything:   from series import ALL_SERIES

Every series uses the most granular native frequency available from FRED.
The loader resamples to the user's chosen output frequency (default W-FRI).

Frequency codes: D=daily, W=weekly, M=monthly, Q=quarterly, A=annual, SEP=irregular
"""

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  INFLATION                                                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

CPI = {
    "CPIAUCSL":            ("Headline_CPI", "M"),                    # CPI-U: All Items
    "CPILFESL":            ("Core_CPI", "M"),                        # CPI-U: Less Food & Energy
    "CPIUFDSL":            ("CPI_Food", "M"),                        # CPI-U: Food
    "CPIENGSL":            ("CPI_Energy", "M"),                      # CPI-U: Energy
    "CUSR0000SAH1":        ("CPI_Shelter", "M"),                     # CPI-U: Shelter
    "CUSR0000SAM2":        ("CPI_Medical_Services", "M"),            # CPI-U: Medical Care Services
    "CUSR0000SETB01":      ("CPI_Gasoline", "M"),                    # CPI-U: Gasoline (all types)
    "CUSR0000SAT1":        ("CPI_Transportation", "M"),              # CPI-U: Transportation
    "CPIAPPSL":            ("CPI_Apparel", "M"),                     # CPI-U: Apparel (SA)
    "CUUR0000SAE1":        ("CPI_Education", "M"),                   # CPI-U: Education
    "STICKCPIM157SFRBATL": ("Sticky_CPI", "M"),                     # Atlanta Fed Sticky-Price CPI
    "CORESTICKM157SFRBATL":("Core_Sticky_CPI", "M"),                # Atlanta Fed Core Sticky-Price CPI
    "MEDCPIM158SFRBCLE":   ("Median_CPI", "M"),                     # Cleveland Fed Median CPI
    "TRMMEANCPIM158SFRBCLE":("Trimmed_Mean_CPI_16pct", "M"),        # Cleveland Fed 16% Trimmed-Mean CPI
}

PCE = {
    "PCEPI":               ("PCE_Price_Index", "M"),                 # PCE Chain-Type Price Index
    "PCEPILFE":            ("Core_PCE", "M"),                        # PCE Less Food & Energy
    "PCETRIM12M159SFRBDAL":("Trimmed_Mean_PCE_12mo", "M"),          # Dallas Fed Trimmed Mean PCE
    "DPCCRV1Q225SBEA":     ("Core_PCE_Quarterly", "Q"),              # PCE Excluding Food & Energy (quarterly)
}

PPI = {
    "PPIACO":              ("PPI_All_Commodities", "M"),             # PPI: All Commodities
    "PPIFIS":              ("PPI_Final_Demand", "M"),                # PPI: Final Demand
    "PPIFES":              ("PPI_Final_Demand_Less_FE", "M"),        # PPI: Final Demand Less Food & Energy
    "WPSFD4131":           ("PPI_Finished_Goods", "M"),              # PPI: Finished Goods
    "WPSID61":             ("PPI_Intermediate_Materials", "M"),      # PPI: Intermediate Materials
}

IMPORT_EXPORT_PRICES = {
    "IR":                  ("Import_Price_Index_All", "M"),          # Import Price Index: All Commodities
    "IQ":                  ("Export_Price_Index_All", "M"),          # Export Price Index: All Commodities
}

INFLATION_EXPECTATIONS = {
    "MICH":                ("UMich_Inflation_Expectations", "M"),    # UMich 1-Year Ahead
    "T5YIE":               ("Breakeven_Inflation_5Y", "D"),          # 5-Year TIPS Breakeven
    "T10YIE":              ("Breakeven_Inflation_10Y", "D"),         # 10-Year TIPS Breakeven
    "T5YIFR":              ("Forward_Inflation_5Y5Y", "D"),          # 5Y5Y Forward Inflation Expectation
    "EXPINF1YR":           ("Expected_Inflation_1Y_CleveFed", "M"), # Cleveland Fed 1-Year
    "EXPINF10YR":          ("Expected_Inflation_10Y_CleveFed", "M"),# Cleveland Fed 10-Year
}

INFLATION = {**CPI, **PCE, **PPI, **IMPORT_EXPORT_PRICES, **INFLATION_EXPECTATIONS}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  OUTPUT & GROWTH                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

GDP = {
    "GDP":                 ("Nominal_GDP", "Q"),                     # Gross Domestic Product
    "GDPC1":               ("Real_GDP", "Q"),                        # Real GDP (chained 2017 $)
    "A939RX0Q048SBEA":     ("Real_GDP_Per_Capita", "Q"),             # Real GDP Per Capita
    "GDPPOT":              ("Potential_GDP", "Q"),                    # Real Potential GDP (CBO)
    "GDI":                 ("Gross_Domestic_Income", "Q"),           # GDI
    "CP":                  ("Corporate_Profits_After_Tax", "Q"),     # Corporate Profits After Tax
    "A053RC1Q027SBEA":     ("National_Income", "Q"),                 # National Income
    "GDPDEF":              ("GDP_Deflator", "Q"),                    # GDP Implicit Price Deflator
}

PRODUCTION = {
    "INDPRO":              ("Industrial_Production", "M"),           # Industrial Production Index
    "TCU":                 ("Capacity_Utilization", "M"),            # Capacity Utilization: Total
    "DGORDER":             ("Durable_Goods_Orders", "M"),            # Durable Goods New Orders
    "NEWORDER":            ("Manufacturers_New_Orders", "M"),        # All Manufacturing New Orders
    "AMTMNO":              ("Manufacturers_Total_Orders", "M"),      # Manufacturers Total Orders
    "TOTALSA":             ("Total_Vehicle_Sales", "M"),             # Total Vehicle Sales
    "IPMAN":               ("Industrial_Production_Mfg", "M"),      # IP: Manufacturing
}

BUSINESS_SURVEYS = {
    # NOTE: ISM PMI series (NAPM, NAPMNOI, NAPMEI, NMFCI) were removed from
    # FRED due to ISM licensing restrictions.  Use Fed regional surveys instead.
    "UMCSENT":             ("UMich_Consumer_Sentiment", "M"),        # UMich Consumer Sentiment
    "USSLIND":             ("Leading_Index_CB", "M"),                # Conference Board Leading Index
    "CFNAI":               ("Chicago_Fed_National_Activity", "M"),  # CFNAI
    "DGDSRG3M086SBEA":     ("Real_Personal_Income_Ex_Transfers", "M"),# Real Personal Income Less Transfers
}

OUTPUT = {**GDP, **PRODUCTION, **BUSINESS_SURVEYS}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  LABOR MARKET                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

EMPLOYMENT = {
    "PAYEMS":              ("Nonfarm_Payrolls", "M"),                # Total Nonfarm Payrolls
    "MANEMP":              ("Manufacturing_Employment", "M"),        # Manufacturing Employees
    "USGOVT":              ("Government_Employment", "M"),           # Government Employees
    "CES0500000003":       ("Avg_Hourly_Earnings", "M"),             # Avg Hourly Earnings: Total Private
    "CES0500000011":       ("Avg_Weekly_Earnings", "M"),             # Avg Weekly Earnings: Total Private
    "AWHAETP":             ("Avg_Weekly_Hours", "M"),                # Avg Weekly Hours: Total Private
    "CIVPART":             ("Labor_Force_Participation", "M"),       # LFPR
    "EMRATIO":             ("Employment_Population_Ratio", "M"),     # Employment-Population Ratio
    "LNS12300060":         ("Prime_Age_EPOP", "M"),                  # Employment-Population Ratio: 25-54
    "ADPWNUSNERSA":        ("ADP_Employment_Change", "M"),           # ADP National Employment Report
}

UNEMPLOYMENT = {
    "UNRATE":              ("Unemployment_Rate", "M"),               # U-3 Unemployment Rate
    "U6RATE":              ("U6_Underemployment", "M"),              # U-6 Underemployment Rate
    "ICSA":                ("Initial_Jobless_Claims", "W"),          # Initial Claims
    "CCSA":                ("Continued_Jobless_Claims", "W"),        # Continued Claims
    "UEMPMEAN":            ("Mean_Duration_Unemployment", "M"),      # Mean Duration of Unemployment (weeks)
    "LNS13025703":         ("Part_Time_Economic_Reasons", "M"),      # Part-Time for Economic Reasons
    "UEMP27OV":            ("Long_Term_Unemployed_27wk", "M"),       # Number Unemployed 27 Weeks & Over
}

JOLTS = {
    "JTSJOL":              ("JOLTS_Job_Openings", "M"),              # Job Openings
    "JTSQUL":              ("JOLTS_Quits", "M"),                     # Quits
    "JTSHIL":              ("JOLTS_Hires", "M"),                     # Hires
    "JTSTSL":              ("JOLTS_Total_Separations", "M"),         # Total Separations
    "JTSLDR":              ("JOLTS_Layoffs_Discharges", "M"),        # Layoffs & Discharges
}

PRODUCTIVITY = {
    "OPHNFB":              ("Nonfarm_Output_Per_Hour", "Q"),         # Nonfarm Business: Output Per Hour
    "ULCNFB":              ("Nonfarm_Unit_Labor_Cost", "Q"),         # Nonfarm Business: Unit Labor Costs
    "COMPNFB":             ("Nonfarm_Compensation_Per_Hour", "Q"),  # Nonfarm Business: Compensation Per Hour
    "PRS85006092":         ("Nonfarm_Labor_Productivity", "Q"),      # Nonfarm Business Labor Productivity
}

LABOR = {**EMPLOYMENT, **UNEMPLOYMENT, **JOLTS, **PRODUCTIVITY}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  INTEREST RATES & YIELDS                                                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

FED_FUNDS = {
    "DFF":                 ("FedFunds_Daily", "D"),                  # Effective FFR (daily)
    "FEDFUNDS":            ("FedFunds_Rate", "M"),                   # Effective FFR (monthly avg)
    "DFEDTARU":            ("FedFunds_Target_Upper", "D"),           # FFR Target Range Upper
    "DFEDTARL":            ("FedFunds_Target_Lower", "D"),           # FFR Target Range Lower
}

OVERNIGHT_RATES = {
    "SOFR":                ("SOFR", "D"),                            # Secured Overnight Financing Rate
    "OBFR":                ("OBFR", "D"),                            # Overnight Bank Funding Rate
    "IORB":                ("Interest_On_Reserve_Balances", "D"),    # Interest Rate on Reserve Balances
    "RRPONTSYD":           ("Overnight_RRP_Rate", "D"),              # Overnight Reverse Repo Rate
}

TREASURIES = {
    "DGS1MO":              ("Treasury_1M", "D"),                     # 1-Month Treasury
    "DGS3MO":              ("Treasury_3M", "D"),                     # 3-Month Treasury
    "DGS6MO":              ("Treasury_6M", "D"),                     # 6-Month Treasury
    "DGS1":                ("Treasury_1Y", "D"),                     # 1-Year Treasury
    "DGS2":                ("Treasury_2Y", "D"),                     # 2-Year Treasury
    "DGS3":                ("Treasury_3Y", "D"),                     # 3-Year Treasury
    "DGS5":                ("Treasury_5Y", "D"),                     # 5-Year Treasury
    "DGS10":               ("Treasury_10Y", "D"),                    # 10-Year Treasury
    "DGS20":               ("Treasury_20Y", "D"),                    # 20-Year Treasury
    "DGS30":               ("Treasury_30Y", "D"),                    # 30-Year Treasury
    "DFII5":               ("TIPS_5Y", "D"),                         # 5-Year TIPS
    "DFII10":              ("TIPS_10Y", "D"),                        # 10-Year TIPS
    "DFII20":              ("TIPS_20Y", "D"),                        # 20-Year TIPS
    "DFII30":              ("TIPS_30Y", "D"),                        # 30-Year TIPS
}

YIELD_SPREADS = {
    "T10Y2Y":              ("Yield_Curve_10Y_2Y", "D"),             # 10Y minus 2Y
    "T10Y3M":              ("Yield_Curve_10Y_3M", "D"),             # 10Y minus 3M
    "T10YFF":              ("Yield_Curve_10Y_FFR", "D"),            # 10Y minus FFR
}

CREDIT_SPREADS = {
    "BAMLH0A0HYM2":       ("HY_OAS_Spread", "D"),                  # ICE BofA High Yield OAS
    "BAMLC0A0CM":          ("IG_OAS_Spread", "D"),                  # ICE BofA Investment Grade OAS
    "BAMLH0A0HYM2EY":     ("HY_Effective_Yield", "D"),             # ICE BofA HY Effective Yield
    "BAMLC0A4CBBBEY":      ("BBB_Effective_Yield", "D"),            # ICE BofA BBB Effective Yield
    "AAA":                 ("Moodys_AAA_Yield", "D"),               # Moody's AAA Corporate Bond Yield
    "BAA":                 ("Moodys_BAA_Yield", "D"),               # Moody's BAA Corporate Bond Yield
    "BAA10Y":              ("BAA_10Y_Spread", "D"),                 # BAA minus 10Y Treasury
}

OTHER_RATES = {
    "MORTGAGE30US":        ("Mortgage_Rate_30Y", "W"),              # 30-Year Fixed Mortgage
    "MORTGAGE15US":        ("Mortgage_Rate_15Y", "W"),              # 15-Year Fixed Mortgage
    "DPRIME":              ("Prime_Rate", "D"),                      # Bank Prime Loan Rate
    "DCPN3M":              ("Commercial_Paper_3M_Nonfinancial", "D"),# 3-Month AA Nonfinancial CP
    "DCPF3M":              ("Commercial_Paper_3M_Financial", "D"),  # 3-Month AA Financial CP
    "TEDRATE":             ("TED_Spread", "D"),                     # TED Spread (3M LIBOR - 3M T-Bill)
}

RATES = {**FED_FUNDS, **OVERNIGHT_RATES, **TREASURIES, **YIELD_SPREADS,
         **CREDIT_SPREADS, **OTHER_RATES}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  MONEY SUPPLY & CREDIT                                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

MONEY_SUPPLY = {
    "BOGMBASE":            ("Monetary_Base", "M"),                   # Monetary Base (St. Louis Adjusted)
    "M1SL":                ("M1_Money_Stock", "M"),                  # M1 Money Stock
    "M2SL":                ("M2_Money_Stock", "M"),                  # M2 Money Stock
    "M2V":                 ("M2_Velocity", "Q"),                     # Velocity of M2
    "TOTRESNS":            ("Total_Reserves", "M"),                  # Total Reserves
    "EXCSRESNS":           ("Excess_Reserves", "M"),                 # Excess Reserves (discontinued 2020)
    "WRESBAL":             ("Reserve_Balances_Fed", "W"),            # Reserve Balances with Fed
    "WALCL":               ("Fed_Total_Assets", "W"),                # Fed Total Assets (balance sheet)
}

BANK_CREDIT = {
    "BUSLOANS":            ("Commercial_Industrial_Loans", "M"),     # C&I Loans
    "REALLN":              ("Real_Estate_Loans", "M"),               # Real Estate Loans
    "CONSUMER":            ("Consumer_Loans_Banks", "M"),            # Consumer Loans at Banks
    "TOTLL":               ("Total_Loans_Leases", "M"),              # Total Loans & Leases
    "TOTBKCR":             ("Total_Bank_Credit", "M"),               # Total Bank Credit
    "DRTSCILM":            ("Senior_Loan_Officer_CI_Tightening", "Q"),  # SLOOS: Net % Tightening C&I
    "DRTSCLCC":            ("Senior_Loan_Officer_CC_Tightening", "Q"),  # SLOOS: Net % Tightening Credit Cards
}

CONSUMER_CREDIT = {
    "TOTALSL":             ("Consumer_Credit_Total", "M"),           # Total Consumer Credit
    "REVOLSL":             ("Consumer_Credit_Revolving", "M"),       # Revolving Consumer Credit
    "NONREVSL":            ("Consumer_Credit_Nonrevolving", "M"),    # Nonrevolving Consumer Credit
    "CCLACBW027SBOG":      ("Credit_Card_Balances_Banks", "W"),     # Credit Card Loans at Banks
    "DRALACBN":            ("Delinquency_All_Loans", "Q"),           # Delinquency Rate: All Loans
    "DRCCLACBS":           ("Delinquency_Credit_Cards", "Q"),       # Delinquency Rate: Credit Cards
    "DRSFRMACBS":          ("Delinquency_Residential_RE", "Q"),     # Delinquency Rate: Residential RE
}

MONEY = {**MONEY_SUPPLY, **BANK_CREDIT, **CONSUMER_CREDIT}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  HOUSING                                                                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

HOME_PRICES = {
    "CSUSHPISA":           ("Case_Shiller_Home_Price", "M"),         # S&P/Case-Shiller National
    "CSUSHPINSA":          ("Case_Shiller_Home_Price_NSA", "M"),     # S&P/Case-Shiller National (NSA)
    "USSTHPI":             ("FHFA_Home_Price_Index", "Q"),           # FHFA All-Transactions HPI
    "MSPUS":               ("Median_Home_Sale_Price", "Q"),          # Median Sales Price of Houses Sold
    "ASPUS":               ("Average_Home_Sale_Price", "Q"),         # Average Sales Price of Houses Sold
}

HOUSING_ACTIVITY = {
    "HOUST":               ("Housing_Starts", "M"),                  # Housing Starts
    "HOUST1F":             ("Housing_Starts_Single_Family", "M"),    # Housing Starts: Single-Family
    "PERMIT":              ("Building_Permits", "M"),                # Building Permits
    "PERMIT1":             ("Building_Permits_Single_Family", "M"), # Building Permits: Single-Family
    "HSN1F":               ("New_Home_Sales", "M"),                  # New Single-Family Houses Sold
    "EXHOSLUSM495S":       ("Existing_Home_Sales", "M"),             # Existing Home Sales
}

HOUSING_INVENTORY = {
    "MSACSR":              ("Months_Supply_Housing", "M"),           # Months' Supply
    "ACTLISCOUUS":         ("Active_Listings", "M"),                 # Active Listing Count (Realtor.com)
    "RRVRUSQ156N":         ("Rental_Vacancy_Rate", "Q"),            # Rental Vacancy Rate
    "RSAHORUSQ156S":       ("Homeownership_Rate", "Q"),             # Homeownership Rate
}

HOUSING = {**HOME_PRICES, **HOUSING_ACTIVITY, **HOUSING_INVENTORY}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  CONSUMER & INCOME                                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

CONSUMER_SPENDING = {
    "PCE":                 ("Personal_Consumption_Expenditures", "M"),# PCE
    "PCEDG":               ("PCE_Durable_Goods", "M"),               # PCE: Durable Goods
    "PCEND":               ("PCE_Nondurable_Goods", "M"),            # PCE: Nondurable Goods
    "PCES":                ("PCE_Services", "M"),                    # PCE: Services
    "RSAFS":               ("Retail_Sales", "M"),                    # Retail Sales: Total
    "RRSFS":               ("Retail_Sales_Ex_Food_Services", "M"),   # Retail Sales ex Food Services
    "FRBKCLMCIM":          ("KC_Fed_Macro_Momentum", "M"),          # KC Fed Macro Momentum (real-time PCE)
}

CONSUMER_INCOME = {
    "PI":                  ("Personal_Income", "M"),                 # Personal Income
    "DSPIC96":             ("Real_Disposable_Income", "M"),          # Real Disposable Personal Income
    "PSAVERT":             ("Personal_Savings_Rate", "M"),           # Personal Savings Rate
    "MEHOINUSA672N":       ("Median_Household_Income", "A"),         # Median Household Income
}

CONSUMER = {**CONSUMER_SPENDING, **CONSUMER_INCOME}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  TRADE & EXCHANGE RATES                                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

TRADE_BALANCE = {
    "BOPGSTB":             ("Trade_Balance_Goods_Services", "M"),    # Trade Balance: Goods & Services
    "BOPGTB":              ("Trade_Balance_Goods", "M"),             # Trade Balance: Goods Only
    "BOPSTB":              ("Trade_Balance_Services", "M"),          # Trade Balance: Services Only
    "IEABC":               ("Current_Account_Balance", "Q"),         # Current Account Balance
    "IMPGS":               ("Imports_Goods_Services", "Q"),          # Imports of Goods & Services
    "EXPGS":               ("Exports_Goods_Services", "Q"),          # Exports of Goods & Services
}

DOLLAR_INDICES = {
    "DTWEXBGS":            ("Trade_Weighted_USD_Broad", "D"),        # Trade-Weighted USD: Broad
    "DTWEXAFEGS":          ("Trade_Weighted_USD_Advanced", "D"),     # Trade-Weighted USD: Advanced Economies
    "DTWEXEMEGS":          ("Trade_Weighted_USD_Emerging", "D"),     # Trade-Weighted USD: Emerging Economies
}

EXCHANGE_RATES = {
    "DEXUSEU":             ("USD_EUR", "D"),                         # USD per Euro
    "DEXJPUS":             ("JPY_USD", "D"),                         # Yen per USD
    "DEXUSUK":             ("USD_GBP", "D"),                         # USD per British Pound
    "DEXCAUS":             ("CAD_USD", "D"),                         # Canadian Dollar per USD
    "DEXCHUS":             ("CNY_USD", "D"),                         # Chinese Yuan per USD
    "DEXMXUS":             ("MXN_USD", "D"),                         # Mexican Peso per USD
    "DEXKOUS":             ("KRW_USD", "D"),                         # Korean Won per USD
    "DEXSZUS":             ("CHF_USD", "D"),                         # Swiss Franc per USD
    "DEXINUS":             ("INR_USD", "D"),                         # Indian Rupee per USD
    "DEXBZUS":             ("BRL_USD", "D"),                         # Brazilian Real per USD
}

TRADE = {**TRADE_BALANCE, **DOLLAR_INDICES, **EXCHANGE_RATES}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FINANCIAL CONDITIONS & MARKETS                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

EQUITY_MARKETS = {
    "SP500":               ("SP500", "D"),                           # S&P 500 Index
    "DJIA":                ("DJIA", "D"),                            # Dow Jones Industrial Average
    "NASDAQCOM":           ("NASDAQ_Composite", "D"),                # NASDAQ Composite
}

VOLATILITY = {
    "VIXCLS":              ("VIX", "D"),                             # CBOE VIX
    "VXVCLS":              ("VXV_3M_Vol", "D"),                      # CBOE 3-Month Volatility
}

FINANCIAL_CONDITIONS = {
    "NFCI":                ("Chicago_Fed_Financial_Conditions", "W"),# Chicago Fed NFCI
    "ANFCI":               ("Adjusted_NFCI", "W"),                   # Chicago Fed Adjusted NFCI
    "STLFSI2":             ("StL_Fed_Financial_Stress", "W"),        # StL Fed Financial Stress Index
    "KCFSI":               ("KC_Fed_Financial_Stress", "M"),         # KC Fed Financial Stress Index
    "DRTSCIS":             ("SLOOS_Demand_CI_Loans", "Q"),          # SLOOS: Demand for C&I Loans
}

FINANCIAL = {**EQUITY_MARKETS, **VOLATILITY, **FINANCIAL_CONDITIONS}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FISCAL                                                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

FEDERAL_DEBT = {
    "GFDEBTN":             ("Federal_Debt_Total", "Q"),              # Federal Debt: Total Public Debt
    "GFDEGDQ188S":         ("Federal_Debt_Pct_GDP", "Q"),           # Federal Debt as % of GDP
    "FDHBFIN":             ("Debt_Held_By_Foreign", "M"),            # Federal Debt Held by Foreign Investors
    "FDHBFRBN":            ("Debt_Held_By_Fed", "M"),                # Federal Debt Held by Federal Reserve
}

FEDERAL_BUDGET = {
    "FYFSD":               ("Federal_Surplus_Deficit", "A"),         # Federal Surplus or Deficit
    "MTSDS133FMS":         ("Monthly_Treasury_Deficit", "M"),        # Monthly Treasury Statement Deficit
    "FGRECPT":             ("Federal_Receipts", "Q"),                # Federal Government Current Receipts
    "FGEXPND":             ("Federal_Expenditures", "Q"),            # Federal Government Expenditures
    "A091RC1Q027SBEA":     ("Federal_Interest_Payments", "Q"),       # Federal Gov Interest Payments
}

FISCAL = {**FEDERAL_DEBT, **FEDERAL_BUDGET}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  COMMODITIES                                                            ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

ENERGY = {
    "DCOILWTICO":          ("Crude_Oil_WTI", "D"),                   # WTI Crude Oil (Cushing, OK)
    "DCOILBRENTEU":        ("Crude_Oil_Brent", "D"),                 # Brent Crude Oil (Europe)
    "DHHNGSP":             ("Natural_Gas_Henry_Hub", "D"),           # Henry Hub Natural Gas Spot
    "GASREGW":             ("Gasoline_Regular_Price", "W"),          # US Regular Gasoline Price
    "DPROPANEMBTX":        ("Propane_Mont_Belvieu", "D"),            # Propane (Mont Belvieu, TX)
}

METALS = {
    "PCOPPUSDM":           ("Copper_Price_Global", "M"),             # Global Copper Price (IMF)
    "PMETAINDEXM":         ("Metals_Index_IMF", "M"),                # IMF Metals Price Index
}

AGRICULTURE = {
    "PMAIZMTUSDM":         ("Corn_Price_Global", "M"),               # Global Corn Price (IMF)
    "PWHEAMTUSDM":         ("Wheat_Price_Global", "M"),              # Global Wheat Price (IMF)
    "PSOYBUSDQ":           ("Soybeans_Price_Global", "Q"),           # Global Soybeans Price (IMF)
    "PRICENPQUSDM":        ("Rice_Price_Global", "M"),               # Global Rice Price (IMF)
    "PCOTTINDUSDM":        ("Cotton_Price_Global", "M"),             # Global Cotton Price (IMF)
    "PSUGAISAUSDM":        ("Sugar_Price_Global", "M"),              # Global Sugar Price (IMF)
    "PCOFFOTMUSDM":        ("Coffee_Price_Global", "M"),             # Global Coffee Price (IMF)
    "WPU0811":             ("PPI_Lumber", "M"),                      # PPI: Lumber & Wood Products
}

COMMODITY_INDICES = {
    "PALLFNFINDEXQ":       ("All_Commodity_Index_IMF", "Q"),         # IMF All Commodity Price Index
    "PFANDBINDEXM":        ("Food_Bev_Index_IMF", "M"),              # IMF Food & Beverage Index
    "PNRGINDEXM":          ("Energy_Index_IMF", "M"),                # IMF Energy Price Index
}

COMMODITIES = {**ENERGY, **METALS, **AGRICULTURE, **COMMODITY_INDICES}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  INEQUALITY                                                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

INEQUALITY = {
    "SIPOVGINIUSA":        ("Gini_Index_USA", "A"),                  # Gini Index
    "LES1252881600Q":      ("Median_Weekly_Earnings", "Q"),          # Median Weekly Earnings: Full-Time
}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FOMC SEP PROJECTIONS                                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

SEP = {
    "FEDTARMD":            ("SEP_FedFunds_Median", "SEP"),           # SEP: Fed Funds Rate Median
    "FEDTARMDLR":          ("SEP_FedFunds_Median_LongerRun", "SEP"),# SEP: Fed Funds Rate Longer Run
    "GDPC1MD":             ("SEP_RealGDP_Median", "SEP"),            # SEP: Real GDP Growth Median
    "UNRATEMD":            ("SEP_Unemployment_Median", "SEP"),       # SEP: Unemployment Rate Median
    "PCECTPIMD":           ("SEP_PCE_Inflation_Median", "SEP"),      # SEP: PCE Inflation Median
    "JCXFEMD":             ("SEP_CorePCE_Median", "SEP"),            # SEP: Core PCE Inflation Median
}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  POPULATION & DEMOGRAPHICS                                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

DEMOGRAPHICS = {
    "POPTHM":              ("Total_Population", "M"),                # Total Population
    "LFWA64TTUSM647S":     ("Working_Age_Population", "M"),          # Working Age Population (15-64)
    "CLF16OV":             ("Civilian_Labor_Force", "M"),            # Civilian Labor Force Level
}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  COMPOSITES                                                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

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
    **COMMODITIES,
    **INEQUALITY,
    **SEP,
    **DEMOGRAPHICS,
}

# ── Category lookup (top-level) ───────────────────────────────────────────
CATEGORIES = {
    "INFLATION":    INFLATION,
    "OUTPUT":       OUTPUT,
    "LABOR":        LABOR,
    "RATES":        RATES,
    "MONEY":        MONEY,
    "HOUSING":      HOUSING,
    "CONSUMER":     CONSUMER,
    "TRADE":        TRADE,
    "FINANCIAL":    FINANCIAL,
    "FISCAL":       FISCAL,
    "COMMODITIES":  COMMODITIES,
    "INEQUALITY":   INEQUALITY,
    "SEP":          SEP,
    "DEMOGRAPHICS": DEMOGRAPHICS,
}

# ── Subcategory lookup (nested, with variable references) ─────────────────
SUBCATEGORIES = {
    "INFLATION": {
        "CPI": CPI, "PCE": PCE, "PPI": PPI,
        "IMPORT_EXPORT_PRICES": IMPORT_EXPORT_PRICES,
        "INFLATION_EXPECTATIONS": INFLATION_EXPECTATIONS,
    },
    "OUTPUT": {
        "GDP": GDP, "PRODUCTION": PRODUCTION,
        "BUSINESS_SURVEYS": BUSINESS_SURVEYS,
    },
    "LABOR": {
        "EMPLOYMENT": EMPLOYMENT, "UNEMPLOYMENT": UNEMPLOYMENT,
        "JOLTS": JOLTS, "PRODUCTIVITY": PRODUCTIVITY,
    },
    "RATES": {
        "FED_FUNDS": FED_FUNDS, "OVERNIGHT_RATES": OVERNIGHT_RATES,
        "TREASURIES": TREASURIES, "YIELD_SPREADS": YIELD_SPREADS,
        "CREDIT_SPREADS": CREDIT_SPREADS, "OTHER_RATES": OTHER_RATES,
    },
    "MONEY": {
        "MONEY_SUPPLY": MONEY_SUPPLY, "BANK_CREDIT": BANK_CREDIT,
        "CONSUMER_CREDIT": CONSUMER_CREDIT,
    },
    "HOUSING": {
        "HOME_PRICES": HOME_PRICES, "HOUSING_ACTIVITY": HOUSING_ACTIVITY,
        "HOUSING_INVENTORY": HOUSING_INVENTORY,
    },
    "CONSUMER": {
        "CONSUMER_SPENDING": CONSUMER_SPENDING, "CONSUMER_INCOME": CONSUMER_INCOME,
    },
    "TRADE": {
        "TRADE_BALANCE": TRADE_BALANCE, "DOLLAR_INDICES": DOLLAR_INDICES,
        "EXCHANGE_RATES": EXCHANGE_RATES,
    },
    "FINANCIAL": {
        "EQUITY_MARKETS": EQUITY_MARKETS, "VOLATILITY": VOLATILITY,
        "FINANCIAL_CONDITIONS": FINANCIAL_CONDITIONS,
    },
    "FISCAL": {
        "FEDERAL_DEBT": FEDERAL_DEBT, "FEDERAL_BUDGET": FEDERAL_BUDGET,
    },
    "COMMODITIES": {
        "ENERGY": ENERGY, "METALS": METALS,
        "AGRICULTURE": AGRICULTURE, "COMMODITY_INDICES": COMMODITY_INDICES,
    },
    "INEQUALITY": {},
    "SEP": {},
    "DEMOGRAPHICS": {},
}
