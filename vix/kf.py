import urllib.request, zipfile, io
B="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
for n in ["6_Portfolios_ME_Prior_12_2_CSV.zip","10_Portfolios_Prior_12_2_CSV.zip","F-F_Momentum_Factor_CSV.zip"]:
    d=urllib.request.urlopen(urllib.request.Request(B+n,headers={"User-Agent":"Mozilla/5.0"}),timeout=120).read()
    z=zipfile.ZipFile(io.BytesIO(d))
    for f in z.namelist(): open("vix/"+f,"wb").write(z.read(f)); print(f)
