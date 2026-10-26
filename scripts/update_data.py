"""Fetch daily prices, compute the S&P 500 filter signal, write data/market.json.

Signal (same rule as the backtests): S&P 500 closes above its 200-day average AND its
20-day volatility (std of daily % changes x sqrt(252)) is under 25%. The state only
flips after the new condition has held for 2 closes in a row.
Standard library only, so the GitHub Action needs no installs."""
import json, math, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "market.json")
FUNDS = {  # tracker name -> Yahoo symbol
    "VOO": "VOO", "AVUV": "AVUV", "VUAA": "VUAA.L", "AVGS": "AVGS.L",
    "USSC": "USSC.L", "I500": "I500.L", "IB01": "IB01.L",
}
UA = {"User-Agent": "Mozilla/5.0 (fire-tracker data job)"}


def yahoo(sym, rng="2y"):
    last = None
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range={rng}&interval=1d"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                    res = json.load(r)["chart"]["result"][0]
                ts = res.get("timestamp") or []
                cl = res["indicators"]["quote"][0].get("close") or []
                rows = [(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), c) for t, c in zip(ts, cl) if c is not None]
                if rows:
                    return res["meta"], rows
            except Exception as e:  # network hiccup or rate limit: back off and retry
                last = e
                time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"{sym}: {last}")


def signal(rows):
    closes = [c for _, c in rows]
    out = []
    for i in range(len(closes)):
        if i < 200:
            out.append(None); continue
        sma = sum(closes[i - 199:i + 1]) / 200
        rets = [closes[j] / closes[j - 1] - 1 for j in range(i - 19, i + 1)]
        m = sum(rets) / 20
        vol = math.sqrt(sum((x - m) ** 2 for x in rets) / 19) * math.sqrt(252)
        out.append((sma, vol, closes[i] > sma and vol < 0.25))
    state = since = None; streak = 0
    for i, o in enumerate(out):
        if o is None: continue
        raw = o[2]
        if state is None:
            state, since = raw, rows[i][0]; continue
        streak = streak + 1 if raw != state else 0
        if streak >= 2:
            state, since, streak = raw, rows[i][0], 0
    sma, vol, raw = out[-1]
    return dict(date=rows[-1][0], close=round(closes[-1], 2), sma200=round(sma, 2), vol20=round(vol, 4),
                above=closes[-1] > sma, calm=vol < 0.25, raw=raw, on=state, since=since,
                pending=(raw != state), history=[[d, round(c, 2)] for d, c in rows[-260:]])


def main():
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {}
    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "errors": []}
    fx_cache = {"USD": 1.0}

    def to_usd(cur):
        if cur in fx_cache: return fx_cache[cur]
        base = "GBP" if cur in ("GBp", "GBX") else cur
        _, r = yahoo(f"{base}USD=X", "5d")
        rate = r[-1][1] / (100 if cur in ("GBp", "GBX") else 1)
        fx_cache[cur] = rate
        return rate

    try:
        meta, rows = yahoo("^GSPC")
        data["signal"] = signal(rows)
    except Exception as e:
        data["errors"].append(f"S&P 500: {e}")
        if "signal" in old: data["signal"] = old["signal"]

    prices = {}
    for name, sym in FUNDS.items():
        try:
            meta, rows = yahoo(sym, "5d")
            cur = meta.get("currency", "USD")
            px = rows[-1][1]
            prices[name] = dict(symbol=sym, currency=cur, price=round(px, 4), usd=round(px * to_usd(cur), 4), date=rows[-1][0])
        except Exception as e:
            data["errors"].append(f"{name}: {e}")
            if name in old.get("prices", {}): prices[name] = {**old["prices"][name], "stale": True}
    data["prices"] = prices

    try:
        _, r = yahoo("HKD=X", "5d")
        data["usdhkd"] = round(r[-1][1], 4)
    except Exception as e:
        data["errors"].append(f"USD/HKD: {e}")
        data["usdhkd"] = old.get("usdhkd", 7.8)

    # tell the workflow when the filter flips, so it can notify you
    was, now = old.get("signal", {}).get("on"), data.get("signal", {}).get("on")
    if os.environ.get("GITHUB_OUTPUT") and isinstance(was, bool) and isinstance(now, bool) and was != now:
        sg = data["signal"]
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"flip={'ON' if now else 'OFF'}\n")
            f.write(f"date={sg['date']}\n")
            f.write(f"detail=S&P 500 {sg['close']:,} vs 200-day average {sg['sma200']:,}; 20-day volatility {sg['vol20'] * 100:.1f}%\n")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=1)
    print(json.dumps({k: v for k, v in data.items() if k != "signal"}, indent=1))
    if "signal" in data: print({k: v for k, v in data["signal"].items() if k != "history"})
    if not data.get("signal") and not prices:
        sys.exit("No data fetched at all")


if __name__ == "__main__":
    main()
