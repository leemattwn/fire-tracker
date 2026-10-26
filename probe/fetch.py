"""One-off: download daily history for the USSC vs AVUV comparison."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import urllib.request, urllib.parse, time
UA = {"User-Agent": "Mozilla/5.0 (fire-tracker probe)"}
def hist(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=0&period2={int(time.time())}&interval=1d&events=div"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.load(r)["chart"]["result"][0]
    q = res["indicators"]; ts = res.get("timestamp") or []
    adj = (q.get("adjclose") or [{}])[0].get("adjclose") or [None] * len(ts)
    cl = q["quote"][0]["close"]
    divs = {str(k): v["amount"] for k, v in (res.get("events", {}).get("dividends") or {}).items()}
    return {"meta": {k: res["meta"].get(k) for k in ("currency", "exchangeName", "longName", "firstTradeDate")}, "t": ts, "close": cl, "adj": adj, "divs": divs}
out = {}
for s in ["USSC.L", "ZPRV.DE", "AVUV", "VOO", "AVGS.L", "IWN", "VBR", "EURUSD=X", "GBPUSD=X"]:
    try: out[s] = hist(s)
    except Exception as e: out[s] = {"error": str(e)}
os.makedirs("probe", exist_ok=True)
json.dump(out, open("probe/out.json", "w"))
print({k: (v.get("meta"), len(v.get("t", []))) if "t" in v else v for k, v in out.items()})
