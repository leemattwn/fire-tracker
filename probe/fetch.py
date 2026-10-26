"""One-off: daily history for DFSV vs AVUV vs USSC."""
import json, os, time, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0 (fire-tracker probe)"}
def hist(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=0&period2={int(time.time())}&interval=1d&events=div"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.load(r)["chart"]["result"][0]
    q = res["indicators"]
    return {"meta": {k: res["meta"].get(k) for k in ("currency", "longName", "firstTradeDate")}, "t": res.get("timestamp") or [],
            "close": q["quote"][0]["close"], "adj": (q.get("adjclose") or [{}])[0].get("adjclose"),
            "divs": {str(k): v["amount"] for k, v in (res.get("events", {}).get("dividends") or {}).items()}}
out = {}
for s in ["DFSV", "AVUV", "USSC.L", "ZPRV.DE", "AVGS.L", "EURUSD=X"]:
    try: out[s] = hist(s)
    except Exception as e: out[s] = {"error": str(e)}
json.dump(out, open("probe/out.json", "w"))
