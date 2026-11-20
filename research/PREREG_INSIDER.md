# Insider cluster buying — pre-registered test (written 2026-11-20, before downloading any insider or price data)

## Question
Do US stocks where several company insiders recently bought shares with their own money beat the market and
small value, AFTER realistic costs, by enough to be worth doing?

## Data (free)
- SEC "Insider Transactions Data Sets" (Forms 3/4/5), quarterly, 2006 Q1 onward.
- Daily dividend-adjusted prices and volume from Yahoo Finance.
- KNOWN FLAW: Yahoo has no prices for most delisted companies (bankrupt or bought out), so results will look
  BETTER than reality. Therefore the test is one-sided:
  * FAIL is final: if it can't pass even with this flattering bias, we stop.
  * PASS only earns a re-run on paid survivorship-free data (e.g. Sharadar or Norgate) before any paper trading.
  * The share of signals with no price data is reported; if over 25%, the result is marked unreliable (counts as no pass).

## Signal (fixed now; ONE rule)
A "cluster buy" month for a company = in one calendar month (by SEC FILING date, when the public could know):
- at least 2 different insiders who are officers or directors,
- each made an open-market purchase (transaction code P, shares acquired) of the company's stock,
- with total purchase value across them of at least US$100,000.

## Portfolio (fixed now)
- At each month end, the portfolio holds every stock with a cluster buy filed in the last 3 months (this month and the
  previous two), equal weight, rebalanced monthly. Trades at that month-end close (signal uses filings up to that day).
- Tradability filter at signal time: price >= US$5 and average daily dollar volume >= US$1 million over the prior
  3 months. Stocks failing it are skipped.
- If fewer than 5 stocks qualify, the unused share sits in SPY.
- A stock whose price series ends while held: its last available return is used and the position goes to cash (no
  invented delisting loss, which is part of why the bias is flattering).

## Costs (fixed now)
- 0.50% of every dollar traded (spreads and commissions on smaller stocks), from actual turnover.
- Benchmarks: SPY 0.09%/yr, IJS (S&P 600 small value) 0.18%/yr, using their actual total returns.

## Periods (fixed now)
- In-sample: Apr 2006 - Dec 2015
- Out-of-sample: Jan 2016 - Dec 2020
- Hold-out (looked at ONCE, at the end): Jan 2021 - latest

## Pass rule (fixed now)
Passes only if, after costs, in BOTH in-sample and out-of-sample:
1. it beats SPY by >= 2.0%/yr, AND
2. it beats IJS by >= 1.5%/yr, AND
3. its worst drawdown is no more than 10 percentage points deeper than IJS's, AND
4. missing-price share <= 25%.
The hold-out cannot rescue a failure. If it fails, we stop: no other thresholds, holding periods or filters.
