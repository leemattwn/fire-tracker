import json, time, urllib.request, csv
UA={"User-Agent":"Mozilla/5.0 (research)"}
def get(sym):
    for host in ("query1","query2"):
        for a in range(3):
            try:
                u=f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=0&period2={int(time.time())}&interval=1d&events=div,split"
                r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60))["chart"]["result"][0]
                ts=r["timestamp"]; q=r["indicators"]["quote"][0]; adj=(r["indicators"].get("adjclose") or [{}])[0].get("adjclose") or q["close"]
                return [(time.strftime("%Y-%m-%d",time.gmtime(t)),c,ac,h,l) for t,c,ac,h,l in zip(ts,q["close"],adj,q["high"],q["low"]) if c is not None]
            except Exception as e: print(sym,e); time.sleep(3)
    raise SystemExit(f"failed {sym}")
import urllib.parse
for s,f in [("^VIX","vix"),("^GSPC","gspc"),("^SP500TR","sptr"),("IWN","iwn"),("AVUV","avuv"),("^IRX","irx"),("^TNX","tnx")]:
    rows=get(s); print(s,len(rows),rows[0][0],rows[-1][0])
    with open(f"vix/{f}.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["date","close","adjclose","high","low"]); w.writerows(rows)
    time.sleep(1)
