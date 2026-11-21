import urllib.request, time
H={"User-Agent":"Mozilla/5.0"}
log=open("vix/credit_log.txt","w")
src={"jsv":"justusschenk/valueinvesting/HEAD/Data","sor":"Snow-Ouyang/Market-Regime-Clustering/HEAD/data_raw/macro/Credit","qfb":"QF-Bench/QuantitativeFinance-Bench/HEAD/tasks/credit-spread-decomposition/environment/data"}
for k,p in src.items():
    for s in ["BAA","AAA"]:
        try:
            d=urllib.request.urlopen(urllib.request.Request(f"https://raw.githubusercontent.com/{p}/{s}.csv",headers=H),timeout=60).read()
            open(f"vix/{k}_{s}.csv","wb").write(d); log.write(f"ok {k} {s} {len(d)}\n")
        except Exception as e: log.write(f"{k} {s}: {e!r}\n")
log.close()
