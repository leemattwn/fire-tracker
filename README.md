# FIRE tracker

A personal FIRE (financial independence) tracker for a 30% S&P 500 / 70% small-value plan, with a live market-filter signal.

**Open it:** https://leemattwn.github.io/fire-tracker/ (once GitHub Pages is switched on).

## How it works

- `index.html` is the whole tracker. Your plan, shares and check-ins are saved in your own browser only (use the Backup button now and then). Nothing personal is stored in this repository.
- `.github/workflows/update-data.yml` runs every weekday after the US and London closes. It runs `scripts/update_data.py`, which downloads prices from Yahoo Finance and writes `data/market.json`.
- `data/market.json` holds:
  - **signal**: S&P 500 close, 200-day average, 20-day volatility, and the filter state. ON means the S&P 500 is above its 200-day average and 20-day volatility is under 25%; the state only flips after two closes in a row agree.
  - **prices** in US$ for VOO, AVUV, VUAA, AVGS, USSC, I500 and IB01.
  - **usdhkd**: the USD/HKD rate used to convert check-ins.

To refresh the data by hand: Actions tab → "Update market data" → Run workflow.

This is a planning aid, not financial advice.
