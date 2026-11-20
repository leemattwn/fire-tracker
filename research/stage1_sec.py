"""Stage 1: download SEC insider data sets (2006Q1..latest) and keep open-market purchases (code P, acquired)
by officers/directors. Output: purchases.csv.gz (one row per filing x owner) + stage1_log.txt."""
import csv, gzip, io, sys, time, urllib.request, zipfile
from datetime import date, datetime
UA = {"User-Agent": "Matt Lee leemattwn@users.noreply.github.com", "Accept-Encoding": "identity", "Host": "www.sec.gov"}
URLS = ["https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{y}q{q}_form345.zip",
        "https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/{y}q{q}_form345.zip"]
log = open("stage1_log.txt", "w")
def say(*a): print(*a); print(*a, file=log); log.flush()
def rows(z, name):
    n = [x for x in z.namelist() if x.upper().endswith(name)][0]
    with z.open(n) as f:
        r = csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in r: yield {k.strip().upper(): (v or "").strip() for k, v in row.items() if k}
def fdate(s):
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try: return datetime.strptime(s, fmt).date()
        except ValueError: pass
    return None
out = gzip.open("purchases.csv.gz", "wt", newline=""); w = csv.writer(out)
w.writerow(["filing_date", "cik", "ticker", "owner", "value", "shares"])
today = date.today(); total = 0
for y in range(2006, today.year + 1):
    for q in range(1, 5):
        if (y, q) > (today.year, (today.month - 1) // 3 + 1): break
        data, err = None, None
        for u in URLS:
            for att in range(3):
                try:
                    with urllib.request.urlopen(urllib.request.Request(u.format(y=y, q=q), headers=UA), timeout=180) as r: data = r.read()
                    break
                except Exception as e:
                    err = e; time.sleep(2 + 4 * att)
                    if getattr(e, "code", 0) == 404: break
            if data: break
        if not data:
            say(f"{y}Q{q}: not available ({err})"); continue
        z = zipfile.ZipFile(io.BytesIO(data))
        if total == 0: say("files:", z.namelist())
        sub = {}
        for s in rows(z, "SUBMISSION.TSV"):
            if s.get("DOCUMENT_TYPE", "4").startswith("4"):
                sub[s["ACCESSION_NUMBER"]] = (fdate(s.get("FILING_DATE", "")), s.get("ISSUERCIK", ""), s.get("ISSUERTRADINGSYMBOL", "").upper())
        own = {}
        for o in rows(z, "REPORTINGOWNER.TSV"):
            rel = o.get("RPTOWNER_RELATIONSHIP", "").lower()
            if "director" in rel or "officer" in rel:
                own.setdefault(o["ACCESSION_NUMBER"], set()).add(o.get("RPTOWNERCIK", ""))
        agg = {}
        for t in rows(z, "NONDERIV_TRANS.TSV"):
            a = t["ACCESSION_NUMBER"]
            if t.get("TRANS_CODE") != "P" or t.get("TRANS_ACQUIRED_DISP_CD") != "A" or a not in sub or a not in own: continue
            try: sh = float(t.get("TRANS_SHARES") or 0); px = float(t.get("TRANS_PRICEPERSHARE") or 0)
            except ValueError: continue
            if sh <= 0 or px <= 0: continue
            v = agg.setdefault(a, [0.0, 0.0]); v[0] += sh * px; v[1] += sh
        n = 0
        for a, (val, sh) in agg.items():
            fd, cik, tk = sub[a]
            if not fd or not tk or tk in ("NONE", "N/A"): continue
            owners = sorted(own[a])
            for oc in owners:   # joint filings: split value equally between the reporting owners
                w.writerow([fd.isoformat(), cik, tk, oc, round(val / len(owners), 2), round(sh / len(owners), 2)]); n += 1
        total += n
        say(f"{y}Q{q}: {len(sub)} form-4 filings, {len(agg)} with officer/director open-market buys, {n} rows")
        time.sleep(0.5)
out.close(); say("total rows", total)
if total == 0: sys.exit("no data downloaded")
