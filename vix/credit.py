import urllib.request, zipfile, io, time, traceback
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept":"*/*"}
log=open("vix/credit_log.txt","w")
def get(u):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=300).read()
        except Exception as e: log.write(f"{u} try{a}: {e!r}\n"); log.flush(); time.sleep(5+10*a)
B="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
for n in ["F-F_Research_Data_Factors_daily_CSV.zip","6_Portfolios_2x3_daily_CSV.zip"]:
    d=get(B+n)
    if d:
        z=zipfile.ZipFile(io.BytesIO(d))
        for f in z.namelist(): open("vix/"+f,"wb").write(z.read(f)); log.write(f"ok {f}\n")
for s in ["BAA","AAA","BAA10Y"]:
    for u in [f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}", f"https://fred.stlouisfed.org/series/{s}/downloaddata/{s}.csv"]:
        d=get(u)
        if d and d[:4]!=b"<!DO": open(f"vix/{s}.csv","wb").write(d); log.write(f"ok {s} {len(d)} from {u}\n"); break
log.close()
