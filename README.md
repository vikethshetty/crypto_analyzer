# AI Trade Check — Bitcoin Futures Research App

## Windows quick start
1. Install Python 3.10 or newer.
2. Extract this ZIP to a normal folder.
3. Open PowerShell or Command Prompt in that folder.
4. Run `py -m venv .venv`
5. Activate: PowerShell `\.venv\Scripts\Activate.ps1`; CMD `.venv\Scripts\activate.bat`
6. Run `python -m pip install -r requirements.txt`
7. Run `python -m streamlit run app.py`
8. Open `http://localhost:8501`.

## Run a command-line backtest
`python backtest.py --days 1095`
or use CSV: `python backtest.py --csv sample_ohlcv.csv --initial-equity 1000 --risk-pct 0.5 --rr 2`

All accounting values are USDT, not INR. Public exchange candles require internet, but no API keys.

## Included
Streamlit UI, daily-candle backtest, CCXT public candle fetch, CSV import, Signal Lab, charts, trade ledger export, CLI, sample CSV, tests, and guidebook.

## Strategy assumptions
Long: bullish completed candle closes above previous candle high. Short: bearish completed candle closes below previous candle low. Entry is next candle open; stop is signal candle low/high plus configurable buffer; target is fixed R. Fees and adverse slippage apply on entry and exit. If stop and target both touch within one daily candle, stop is assumed first. After 3 consecutive losses, the simulation pauses new entries for 3 days.

## Limitations
Research prototype only. Funding, liquidation, spread, partial fills, maintenance margin, exchange precision, outages and exact intrabar path are not fully modeled. Live order execution is intentionally not included.
