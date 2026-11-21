import urllib.request, zipfile, io, time, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept":"*/*"}
log=open("vix/credit_log.txt","w")
def get(u,tries=2,to=40):
    for a in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=to).read()
        except Exception as e: log.write(f"{u} try{a}: {e!r}\n"); log.flush(); time.sleep(3)
B="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
for n in []:
    d=get(B+n,3,120)
    if d:
        z=zipfile.ZipFile(io.BytesIO(d))
        for f in z.namelist(): open("vix/"+f,"wb").write(z.read(f)); log.write(f"ok {f}\n")
# DBnomics mirror of the Fed's H.15 release (Moody's Aaa/Baa, monthly)
import urllib.parse
dim=urllib.parse.quote(json.dumps({"FREQ":["129"],"INSTRUMENT":["AAA","BAA"]}))
d=get(f"https://api.db.nomics.world/v22/series/FED/H15?dimensions={dim}&observations=1&limit=50&format=json",3,90)
if d: open("vix/dbn_h15.json","wb").write(d); log.write(f"ok dbn h15 {len(d)}\n")
for s in []:
    d=get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}",1,30)
    if d and d[:4]!=b"<!DO": open(f"vix/{s}.csv","wb").write(d); log.write(f"ok {s} {len(d)}\n")
log.close()
