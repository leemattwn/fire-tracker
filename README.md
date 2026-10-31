# Investment plan

A personal investment plan tracker for a 70% small value / 30% large-cap momentum plan, with a live market-filter signal.

**Open it:** https://leemattwn.github.io/fire-tracker/

The app only shows what to do and what happened. This page explains the rules behind it.

## The plan

- **Split:** 70% small value (AVUV now, AVGS once larger), 30% large caps (IUMO, or MTUM for small buys). VUAA or VOO bought before the switch to IUMO are kept, count toward the 30%, and are sold first whenever money comes out of that side.
- **Monthly buy (the 15th):** the whole amount goes to whichever side is below its target.
  - Buys under US$800 use the US-listed fund (AVUV or MTUM, US$0.35 a trade). Bigger buys go straight to the Irish fund (AVGS or IUMO, US$1.70 a trade).
  - The amount rises with Hong Kong inflation once a year from the plan start.
- **Move to Irish funds:** once US-listed funds (MTUM, AVUV, any VOO) pass US$3,000, sell them and buy IUMO and AVGS. Irish funds pay less dividend tax and avoid US estate tax.
- **Rebalance:** only if small value drifts outside 60–80% and the signal is ON. Monthly buys normally keep it inside the band, so this is rare.
- **Emergency fund (from full-time work):** 6 months of living costs in savings or IB01 comes first. It sits outside the plan.

## The signal

- **ON** while the S&P 500 **or** AVGS closes above its own 150-day average.
- **OFF** only when **both** close below their 150-day averages for two closes in a row. It turns back ON when either is above for two closes.
- **OFF:** sell AVUV/AVGS and buy IB01. While OFF, new small-value money waits in IB01, or as US$ cash for buys under US$800.
- **ON again:** sell IB01 and buy back small value.
- The filter only starts once small value (including IB01 and cash waiting) first reaches US$1,500. Below that, switching fees cost more than it saves. Once started, it stays on.
- The large-cap side (IUMO) is never switched.
- Alerts go to your phone (ntfy) and email (a GitHub issue) when the signal flips, plus a reminder before each month's buy.

## Phases

- **Studying (until full-time work):** invest the student amount each month. Protect your grades first.
- **Building:** emergency fund first, then the full monthly amount. Raise it with every pay rise.
- **Final approach (last ~5 years before FI):** keep the same plan and keep following the signal. In backtests, adding a cash buffer on top of the filter lowered results.
- **Retired:** withdraw your retirement income (4% of the target a year), raised with inflation. Keep following the signal. MPF from 65.

## Numbers in the app

- **Target** = monthly retirement income × 12 ÷ 4%, in today's money. It rises with inflation, so the app also shows it in future dollars.
- **Projection:** 6% a year after inflation (bad 4%, good 8%), starting from your latest balance. Future inflation is assumed to be Hong Kong's 20-year average CPI. Past inflation uses the actual CPI.
- **Plan says by now:** where the plan expected you to be today. It assumes each month's buy happens on the 15th.
- **Monthly check-in:** each time you open the app, it saves this month's balance (shares × latest prices, in HK$). The last one each month stays. The chart's past line is made of these check-ins.
- **History:** every buy, signal switch, rebalance and move, on the day it happened, with your balance right after.

## How the data works

- `index.html` is the whole tracker. Your plan, shares and history are saved in your own browser only (use Backup now and then). Nothing personal is stored in this repository.
- `.github/workflows/update-data.yml` runs hourly on weekdays while markets are open. It runs `scripts/update_data.py`, which downloads prices from Yahoo Finance (CNBC as a backup for the S&P 500) and writes `data/market.json`.
- `data/market.json` holds:
  - **signal**: S&P 500 and AVGS closes, each one's 150-day average, and the filter state.
  - **prices** in US$ for IUMO, MTUM, VOO, AVUV, VUAA, AVGS and IB01.
  - **usdhkd**: the USD/HKD rate.
  - **cpi**: Hong Kong Composite CPI (Census and Statistics Department).

To refresh the data by hand: Actions tab → "Update market data" → Run workflow.

This is a planning aid, not financial advice.
