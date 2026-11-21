import urllib.request, zipfile, io, time
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
log=open("vix/credit_log.txt","w")
B="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
for n in ["Developed_ex_US_6_Portfolios_ME_BE-ME_CSV.zip","6_Portfolios_ME_Prior_12_2_Daily_CSV.zip","6_Portfolios_2x3_CSV.zip"]:
    for a in range(3):
        try:
            d=urllib.request.urlopen(urllib.request.Request(B+n,headers=H),timeout=120).read()
            z=zipfile.ZipFile(io.BytesIO(d))
            for f in z.namelist(): open("vix/"+f,"wb").write(z.read(f)); log.write(f"ok {f}\n")
            break
        except Exception as e: log.write(f"{n} try{a}: {e!r}\n"); time.sleep(5)
log.close()
