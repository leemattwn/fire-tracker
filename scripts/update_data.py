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
    "IB01": "IB01.L",
}
UA = {"User-Agent": "Mozilla/5.0 (fire-tracker data job)"}


def yahoo(sym, rng="2y", closed_only=False):
    last = None
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range={rng}&interval=1d"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                    res = json.load(r)["chart"]["result"][0]
                ts = res.get("timestamp") or []
                cl = res["indicators"]["quote"][0].get("close") or []
                meta = res["meta"]
                # During trading, Yahoo's last daily bar is today's unfinished session. Keep it for live
                # prices, but flag it so the signal only ever uses finished closes.
                reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
                live_from = reg.get("start") if reg.get("start") and time.time() < reg.get("end", 0) else None
                rows = [(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), c) for t, c in zip(ts, cl)
                        if c is not None and not (live_from and t >= live_from and closed_only)]
                if rows:
                    return meta, rows
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


def hk_cpi():
    """Hong Kong Composite CPI, monthly, from the Census and Statistics Department (table 510-60001)."""
    url = "https://www.censtatd.gov.hk/api/get.php?id=510-60001&lang=en&full_series=1"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        ds = json.load(r)["dataSet"]
    idx, yoy = {}, {}
    for d in ds:
        if d.get("freq") != "M" or d.get("sv") != "CC_CM_1920" or d.get("figure") in (None, ""): continue
        p = str(d["period"]); key = f"{p[:4]}-{p[4:6]}"
        if d.get("svDesc") == "Index": idx[key] = float(d["figure"])
        elif d.get("svDesc") == "Year-on-year % change": yoy[key] = float(d["figure"])
    if not idx: raise RuntimeError("no Composite CPI rows")
    months = sorted(idx); last = months[-1]
    def ago(n):
        y, m = int(last[:4]), int(last[5:]) - n
        while m <= 0: y, m = y - 1, m + 12
        return f"{y}-{m:02d}"
    avg = lambda yrs: round(((idx[last] / idx[ago(12 * yrs)]) ** (1 / yrs) - 1) * 100, 2) if ago(12 * yrs) in idx else None
    return {"latest": last, "yoy": yoy.get(last), "avg5": avg(5), "avg10": avg(10), "avg20": avg(20),
            "index": {k: idx[k] for k in months if k >= "1995-01"}}


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
        meta, rows = yahoo("^GSPC", closed_only=True)       # the signal uses finished closes only
        data["signal"] = signal(rows)
    except Exception as e:
        data["errors"].append(f"S&P 500: {e}")
        if "signal" in old: data["signal"] = old["signal"]

    prices = {}
    for name, sym in FUNDS.items():
        try:
            meta, rows = yahoo(sym, "5d")
            cur = meta.get("currency", "USD")
            px = meta.get("regularMarketPrice") or rows[-1][1]                # latest trade (about 15 min delayed)
            when = meta.get("regularMarketTime")
            prices[name] = dict(symbol=sym, currency=cur, price=round(px, 4), usd=round(px * to_usd(cur), 4), date=rows[-1][0],
                                time=datetime.fromtimestamp(when, timezone.utc).isoformat(timespec="minutes") if when else None)
        except Exception as e:
            data["errors"].append(f"{name}: {e}")
            if name in old.get("prices", {}): prices[name] = {**old["prices"][name], "stale": True}
    data["prices"] = prices

    try:
        m, r = yahoo("HKD=X", "5d")
        data["usdhkd"] = round(m.get("regularMarketPrice") or r[-1][1], 4)
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

    try:
        data["cpi"] = hk_cpi()
    except Exception as e:
        data["errors"].append(f"HK CPI: {e}")
        if "cpi" in old: data["cpi"] = old["cpi"]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=1)
    print(json.dumps({k: v for k, v in data.items() if k not in ("signal", "cpi")}, indent=1))
    if "cpi" in data: print({k: v for k, v in data["cpi"].items() if k != "index"})
    if "signal" in data: print({k: v for k, v in data["signal"].items() if k != "history"})
    if not data.get("signal") and not prices:
        sys.exit("No data fetched at all")


if __name__ == "__main__":
    main()
