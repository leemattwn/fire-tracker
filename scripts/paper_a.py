"""Paper trading for alpha idea #2: industry momentum (pre-registered in the alpha project, PREREG_A.md).
NOT a trade instruction. Nothing here touches your real account. It only keeps a pretend portfolio so we can
see, after 6+ months, whether the backtested edge shows up with real sector ETFs.

Rule (fixed): at each month end, rank the 11 SPDR sector ETFs by total return over the past 12 months EXCLUDING the
most recent month. Hold the top 3, equal weight. To be realistic, the pretend trades happen at the close of the
FIRST trading day of the new month (one-day delay), cost 0.10% of every dollar traded, plus 0.10%/yr fund fees.
Compared with simply holding VOO (0.03%/yr). Starts with US$10,000 pretend money in December 2026.

Runs on the first trading days of each month; does nothing if this month is already recorded.
Writes data/paper_a.json and prints `msg=...` for the notification step."""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
BENCH = "VOO"
START_MONTH = "2026-12"          # first month the pretend portfolio trades (rule written 2026-11-20)
START_VALUE = 10_000.0
TOP, TRADE_COST, FEE, BENCH_FEE = 3, 0.001, 0.001, 0.0003
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "paper_a.json")
UA = {"User-Agent": "Mozilla/5.0 (fire-tracker paper job)"}


def adj_closes(sym):
    """[(YYYY-MM-DD, dividend-adjusted close)] for finished daily bars, about 2 years."""
    last = None
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=2y&interval=1d"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                    res = json.load(r)["chart"]["result"][0]
                reg = (res["meta"].get("currentTradingPeriod") or {}).get("regular") or {}
                live_from = reg.get("start") if reg.get("start") and time.time() < reg.get("end", 0) else None
                adj = res["indicators"]["adjclose"][0]["adjclose"]
                rows = [(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), c)
                        for t, c in zip(res["timestamp"], adj) if c is not None and not (live_from and t >= live_from)]
                if rows: return rows
            except Exception as e:
                last = e; time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"{sym}: {last}")


def month_ends(rows):
    """Last close of each calendar month, in order: [(YYYY-MM, date, price)]."""
    out = {}
    for d, p in rows: out[d[:7]] = (d, p)
    return [(m, d, p) for m, (d, p) in sorted(out.items())]


def step(state, prices):
    """prices: {sym: rows}. Returns (state, message or None). Pure function, so it can be tested offline."""
    bench_rows = prices[BENCH]
    exec_month = bench_rows[-1][0][:7]                         # month of the latest finished close
    if exec_month < START_MONTH: return state, None
    if state["months"] and state["months"][-1]["month"] >= exec_month: return state, None
    exec_date = next(d for d, _ in bench_rows if d[:7] == exec_month)   # first trading day of this month
    px = {}
    for s in ETFS + [BENCH]:
        hit = [p for d, p in prices[s] if d == exec_date]
        if not hit: raise RuntimeError(f"{s} has no close on {exec_date}")
        px[s] = hit[0]
    # signal: month-end closes strictly before this month; return from end of t-13 to end of t-2
    sig = {}
    for s in ETFS:
        me = [x for x in month_ends(prices[s]) if x[0] < exec_month]
        if len(me) < 13: raise RuntimeError(f"{s}: only {len(me)} month-ends of history")
        sig[s] = me[-2][2] / me[-13][2] - 1
    picks = sorted(ETFS, key=lambda s: -sig[s])[:TOP]
    new_w = {s: 1 / TOP for s in picks}
    if state["months"]:
        prev = state["months"][-1]
        grown = {s: w * px[s] / prev["px"][s] for s, w in prev["weights"].items()}
        g = sum(grown.values()); value = prev["value"] * g; drift = {s: v / g for s, v in grown.items()}
        months_held = max(1, (int(exec_month[:4]) - int(prev["month"][:4])) * 12 + int(exec_month[5:]) - int(prev["month"][5:]))
        value *= (1 - FEE / 12) ** months_held
        bench = prev["bench"] * px[BENCH] / prev["px"][BENCH] * (1 - BENCH_FEE / 12) ** months_held
    else:
        value, bench, drift = START_VALUE, START_VALUE, {}
    turnover = sum(abs(new_w.get(s, 0) - drift.get(s, 0)) for s in set(new_w) | set(drift))
    value *= 1 - TRADE_COST * turnover
    state["months"].append({"month": exec_month, "date": exec_date, "picks": picks, "weights": new_w,
                            "signal": {s: round(v, 4) for s, v in sig.items()},
                            "px": {s: px[s] for s in set(picks) | set(drift) | {BENCH}},
                            "value": round(value, 2), "bench": round(bench, 2), "turnover": round(turnover, 3)})
    n = len(state["months"]); gap = value / bench - 1
    msg = (f"Paper test only, no real trade. {exec_date}: now holding {', '.join(picks)}. "
           f"Pretend US${value:,.0f} vs VOO US${bench:,.0f} ({gap:+.1%}) after {n - 1} month(s).")
    return state, msg


def main():
    state = json.load(open(OUT)) if os.path.exists(OUT) else {
        "about": "Paper trading for industry momentum (pretend money, not advice). See scripts/paper_a.py.",
        "start_value": START_VALUE, "months": []}
    prices = {s: adj_closes(s) for s in ETFS + [BENCH]}
    state, msg = step(state, prices)
    if msg:
        json.dump(state, open(OUT, "w"), indent=1)
        print(msg)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f: f.write(f"msg={msg}\n")
    else:
        print("Nothing to do (already recorded this month, or before the start month).")


if __name__ == "__main__":
    main()
