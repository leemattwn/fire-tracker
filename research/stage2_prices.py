"""Stage 2: Yahoo daily adjusted close + volume for every ticker with a purchase, plus SPY and IJS.
Output: prices/ as monthly files: monthly.csv.gz (ticker, month, last adj close, avg daily dollar volume over month,
last trading date) and stage2_log.txt. Missing tickers are listed."""
import csv, gzip, json, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
UA = {"User-Agent": "Mozilla/5.0 (research)"}
tick = set()
for r in csv.DictReader(gzip.open("purchases.csv.gz", "rt")): tick.add(r["ticker"].replace(".", "-").replace("/", "-"))
tick |= {"SPY", "IJS"}
log = open("stage2_log.txt", "w"); out = gzip.open("monthly.csv.gz", "wt", newline=""); w = csv.writer(out)
w.writerow(["ticker", "month", "close", "dollar_vol", "last_date"]); miss = []
def fetch(sym):
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=1104537600&period2={int(time.time())}&interval=1d"
        for att in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return json.load(r)["chart"]["result"][0]
            except urllib.error.HTTPError as e:
                if e.code == 404: return None
                time.sleep(3 + 5 * att)
            except Exception: time.sleep(3 + 5 * att)
    return None
for i, s in enumerate(sorted(tick)):
    res = fetch(s); time.sleep(0.25)
    try:
        ts = res["timestamp"]; adj = res["indicators"]["adjclose"][0]["adjclose"]; q = res["indicators"]["quote"][0]
    except Exception:
        miss.append(s); continue
    m = {}
    for t, a, c, v in zip(ts, adj, q["close"], q["volume"]):
        if a is None or c is None: continue
        d = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"); mo = d[:7]
        e = m.setdefault(mo, [0, 0.0, 0, ""]); e[0] = a; e[1] += c * (v or 0); e[2] += 1; e[3] = d
    for mo, (a, dv, n, d) in sorted(m.items()): w.writerow([s, mo, round(a, 6), round(dv / n), d])
    if i % 200 == 0: print(i, len(tick), "missing so far", len(miss), flush=True)
out.close()
print(f"tickers {len(tick)}, missing {len(miss)}", file=log); print("missing:", " ".join(miss), file=log)
print(f"tickers {len(tick)}, missing {len(miss)}")
