import urllib.request, zipfile, io
H={"User-Agent":"Mozilla/5.0"}
B="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
for n in ["F-F_Research_Data_Factors_daily_CSV.zip","6_Portfolios_2x3_daily_CSV.zip"]:
    z=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(B+n,headers=H),timeout=180).read()))
    for f in z.namelist(): open("vix/"+f,"wb").write(z.read(f)); print(f)
for s in ["BAA","AAA","BAA10Y"]:
    d=urllib.request.urlopen(urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}",headers=H),timeout=120).read()
    open(f"vix/{s}.csv","wb").write(d); print(s,len(d))
