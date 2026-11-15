"""Fetch your IBKR positions with a Flex Query and save them ENCRYPTED to data/ibkr.enc.json.

The repository is public, so nothing readable is written: positions, cash and trades are encrypted with
AES-256-GCM using a key derived (PBKDF2-SHA256) from PLAN_SYNC_KEY, a passphrase only you and your phone know.
The app decrypts it in your browser. Nothing about your account is printed to the job log.

Needs three GitHub secrets: IBKR_FLEX_TOKEN, IBKR_FLEX_QUERY_ID, PLAN_SYNC_KEY. If any is missing, it does nothing."""
import base64, json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "ibkr.enc.json")
BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
UA = {"User-Agent": "fire-tracker/1.0 (Python urllib)"}
KNOWN = {"IUMO", "MTUM", "VUAA", "VOO", "AVUV", "AVGS", "IB01"}      # the funds the tracker knows
ITER = 310_000


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def fetch_statement(token, qid):
    q = urllib.parse.urlencode({"t": token, "q": qid, "v": 3})
    root = ET.fromstring(get(f"{BASE}/SendRequest?{q}"))
    if root.findtext("Status") != "Success":
        raise RuntimeError(f"SendRequest failed: code {root.findtext('ErrorCode')}: {root.findtext('ErrorMessage')}")
    ref, url = root.findtext("ReferenceCode"), root.findtext("Url") or f"{BASE}/GetStatement"
    for attempt in range(12):                               # the report can take a little while to generate
        time.sleep(5 + 5 * attempt)
        body = get(f"{url}?{urllib.parse.urlencode({'t': token, 'q': ref, 'v': 3})}")
        r = ET.fromstring(body)
        if r.tag == "FlexQueryResponse":
            return r
        code = r.findtext("ErrorCode")
        if code not in ("1019", "1018", "1009"):            # 1019: still generating; 1018/1009: busy, try again
            raise RuntimeError(f"GetStatement failed: code {code}: {r.findtext('ErrorMessage')}")
    raise RuntimeError("statement still not ready after several minutes")


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def parse(root):
    st = root.find(".//FlexStatement")
    if st is None: raise RuntimeError("no FlexStatement in the response (check the query's sections)")
    shares, other = {}, []
    for p in st.iter("OpenPosition"):
        if (p.get("levelOfDetail") or "SUMMARY").upper() not in ("SUMMARY", ""): continue
        sym = (p.get("symbol") or "").upper().split(".")[0]
        qty = num(p.get("position"))
        if sym in KNOWN: shares[sym] = shares.get(sym, 0) + qty
        elif qty: other.append({"symbol": sym, "qty": qty, "value": num(p.get("positionValue")), "currency": p.get("currency")})
    cash = {}
    for c in st.iter("CashReportCurrency"):
        cur = c.get("currency")
        if cur and cur != "BASE_SUMMARY" and (c.get("levelOfDetail") or "Currency") in ("Currency", "", "Summary"):
            cash[cur] = round(cash.get(cur, 0) + num(c.get("endingCash")), 2)
    trades = []
    for t in st.iter("Trade"):
        sym = (t.get("symbol") or "").upper().split(".")[0]
        trades.append({"symbol": sym, "date": (t.get("tradeDate") or "")[:8], "qty": num(t.get("quantity")),
                       "price": num(t.get("tradePrice")), "side": t.get("buySell")})
    asof = st.get("toDate") or st.get("whenGenerated", "")[:8]
    if len(asof) == 8: asof = f"{asof[:4]}-{asof[4:6]}-{asof[6:]}"
    return {"asof": asof, "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "shares": {k: round(v, 6) for k, v in shares.items()}, "cash": {k: v for k, v in cash.items() if v},
            "other": other, "trades": trades[-50:]}


def encrypt(obj, passphrase):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(passphrase.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}


def main():
    token, qid, key = (os.environ.get(k, "").strip() for k in ("IBKR_FLEX_TOKEN", "IBKR_FLEX_QUERY_ID", "PLAN_SYNC_KEY"))
    if not (token and qid and key):
        print("IBKR sync not set up (add IBKR_FLEX_TOKEN, IBKR_FLEX_QUERY_ID and PLAN_SYNC_KEY secrets). Skipping."); return
    if len(key) < 12: sys.exit("PLAN_SYNC_KEY is too short: use a long passphrase (12+ characters).")
    data = parse(fetch_statement(token, qid))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(encrypt(data, key), open(OUT, "w"), indent=1)
    print(f"Saved encrypted positions as of {data['asof']}: {len(data['shares'])} tracker funds, "
          f"{len(data['other'])} other holdings, {len(data['cash'])} cash currencies.")   # counts only, no amounts


if __name__ == "__main__":
    main()
