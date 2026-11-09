#!/usr/bin/env python3
"""artha-navigator: real NAV history and returns for Indian mutual funds.

Sources (free, no keys):
  AMFI daily NAV file  https://portal.amfiindia.com/spages/NAVAll.txt  (active schemes, ISINs)
  mfapi.in             https://api.mfapi.in/mf/<code>                 (full daily NAV history)
  Yahoo Finance chart  https://query1.finance.yahoo.com/v8/finance/chart/<sym>  (index benchmarks)
Standard library only.
"""
import argparse, datetime as dt, json, os, re, sys, time, urllib.request

AMFI_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
MFAPI_URL = "https://api.mfapi.in/mf/{code}"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval=1d"
CACHE = os.environ.get("MFNAV_CACHE", os.path.join(os.getcwd(), ".mfnav-cache"))
UA = {"User-Agent": "Mozilla/5.0 (compatible; artha-skill/0.1.3; +https://github.com/gpavan1992/artha-skill)"}
STALE_DAYS = 7
BENCHMARKS = {"nifty50": "^NSEI", "nifty500": "^CRSLDX", "banknifty": "^NSEBANK"}

# ---------------- fetch + cache ----------------
def _get(url, ttl_hours, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_hours * 3600:
        return open(path, encoding="utf-8").read()
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                txt = r.read().decode("utf-8", "replace")
            open(path, "w", encoding="utf-8").write(txt)
            time.sleep(0.3)
            return txt
        except Exception as e:
            last = e; time.sleep(1.5 * (attempt + 1))
    if os.path.exists(path):
        print(f"note: using cached {name} (fetch failed: {last})", file=sys.stderr)
        return open(path, encoding="utf-8").read()
    raise SystemExit(f"error: could not fetch {url}: {last}")

def amfi_schemes():
    rows = []
    for line in _get(AMFI_URL, 12, "NAVAll.txt").splitlines():
        p = line.strip().split(";")
        if len(p) != 8 or not p[0].isdigit():
            continue
        code, isin1, isin2, name, plan, option, nav, date = p
        try:
            d = dt.datetime.strptime(date.strip(), "%d-%b-%Y").date()
            v = float(nav)
        except ValueError:
            continue
        rows.append({"code": int(code), "isin": isin1.strip(), "isin_reinvest": isin2.strip(),
                     "name": name.strip(), "plan": plan.strip(), "option": option.strip(),
                     "nav": v, "date": d.isoformat()})
    return rows

def history(code):
    data = json.loads(_get(MFAPI_URL.format(code=code), 12, f"mf-{code}.json"))
    pts = []
    for x in data.get("data", []):
        try:
            pts.append((dt.datetime.strptime(x["date"], "%d-%m-%Y").date(), float(x["nav"])))
        except (ValueError, KeyError):
            pass
    pts.sort()
    return data.get("meta", {}), pts

def index_history(sym, rng="10y"):
    from urllib.parse import quote
    txt = _get(YAHOO_URL.format(sym=quote(sym), rng=rng), 12, "yh-" + re.sub(r"\W", "_", sym) + f"-{rng}.json")
    r = json.loads(txt)["chart"]["result"][0]
    out = []
    for ts, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c is not None:
            out.append((dt.datetime.fromtimestamp(ts + 19800, dt.timezone.utc).date(), float(c)))
    return out

# ---------------- resolve ----------------
STOP = {"fund", "the", "plan", "option", "scheme", "of", "a", "-", "&", "and"}
def _toks(s):
    s = s.lower().replace("&", " and ").replace("pru ", "prudential ")
    s = re.sub(r"fund\s+of\s+funds?|\bfofs?\b", " fof ", s)
    return {t for t in re.split(r"[^a-z0-9]+", s) if t and t not in STOP}

OPTION_SYNONYMS = {"growth": ("growth", "cumulative", "accumulation"),
                   "idcw": ("idcw", "dividend", "payout", "reinvest")}
def _option_ok(want, have):
    have = have.lower()
    return any(s in have for s in OPTION_SYNONYMS.get(want.lower(), (want.lower(),)))

def resolve(query, plan="direct", option="growth", isin=None, rows=None):
    rows = rows or amfi_schemes()
    if isin:
        hit = [r for r in rows if isin in (r["isin"], r["isin_reinvest"])]
        return [dict(r, score=1.0) for r in hit]
    q = _toks(query)
    out = []
    for r in rows:
        unlabelled = not r["plan"] and not r["option"]
        if not unlabelled:
            if plan and plan.lower() not in r["plan"].lower():
                continue
            if option and not _option_ok(option, r["option"]):
                continue
        n = _toks(r["name"])
        if not q & n:
            continue
        score = len(q & n) / len(q | n)
        out.append(dict(r, score=round(score, 3), unlabelled=unlabelled))
    out = [r for r in out if r["score"] >= 0.5]
    # AMFI sometimes leaves plan/option blank. Among same-name unlabelled rows, Direct has
    # lower costs, so its NAV is higher: rank the higher NAV first when plan=direct.
    sign = -1 if (plan or "").lower() == "direct" else 1
    out.sort(key=lambda r: (-r["score"], r["name"], sign * r["nav"] if r.get("unlabelled") else 0))
    return out[:5]

# ---------------- returns ----------------
def on_or_before(pts, d):
    lo, hi, best = 0, len(pts) - 1, None
    while lo <= hi:
        m = (lo + hi) // 2
        if pts[m][0] <= d: best = pts[m]; lo = m + 1
        else: hi = m - 1
    return best

def last_friday(d):
    return d - dt.timedelta(days=(d.weekday() - 4) % 7)

def period_returns(pts):
    if not pts: return {}
    end_d, end_v = pts[-1]
    res = {"as_of": end_d.isoformat(), "nav": end_v}
    fri = last_friday(end_d)
    p0 = on_or_before(pts, fri - dt.timedelta(days=7)); p1 = on_or_before(pts, fri)
    res["1w"] = round((p1[1] / p0[1] - 1) * 100, 2) if p0 and p1 else None
    for k, days in [("1m", 30), ("3m", 91), ("6m", 182), ("1y", 365)]:
        b = on_or_before(pts, end_d - dt.timedelta(days=days))
        res[k] = round((end_v / b[1] - 1) * 100, 2) if b and (end_d - b[0]).days >= days - 7 else None
    for k, yrs in [("3y_cagr", 3), ("5y_cagr", 5)]:
        b = on_or_before(pts, end_d - dt.timedelta(days=int(365.25 * yrs)))
        ok = b and (end_d - b[0]).days >= 365 * yrs - 10
        res[k] = round(((end_v / b[1]) ** (1 / yrs) - 1) * 100, 2) if ok else None
    yr = [p for p in pts if p[0] >= end_d - dt.timedelta(days=365)]
    peak, mdd = 0, 0
    for _, v in yr:
        peak = max(peak, v); mdd = min(mdd, v / peak - 1)
    res["max_drawdown_1y"] = round(mdd * 100, 2) if yr else None
    return res

def fridays(end_d, weeks):
    f = last_friday(end_d)
    return [f - dt.timedelta(days=7 * i) for i in range(weeks, -1, -1)]

def weekly(pts, weeks):
    days = fridays(pts[-1][0], weeks)
    vals = []
    for d in days:
        p = on_or_before(pts, d)
        vals.append(p[1] if p else None)
    return [d.isoformat() for d in days], vals

def pct(a, b):
    return None if a is None or b is None else round((b / a - 1) * 100, 2)

# ---------------- commands ----------------
def check_fresh(r):
    age = (dt.date.today() - dt.date.fromisoformat(r["date"])).days
    return None if age <= STALE_DAYS else f"latest NAV is {age} days old — scheme may be merged, renamed or closed"

def cmd_resolve(a):
    rows = amfi_schemes()
    hits = resolve(a.query or "", a.plan, a.option, a.isin, rows)
    if a.json:
        print(json.dumps([dict(h, stale=check_fresh(h)) for h in hits], indent=1)); return
    if not hits:
        print("no match — try fewer words, or --plan regular / --option idcw"); sys.exit(1)
    for h in hits:
        s = check_fresh(h)
        lab = f"{h['plan']} · {h['option']}" if not h.get("unlabelled") else "plan/option not labelled by AMFI — higher NAV is usually Direct; confirm by ISIN"
        print(f"{h['code']:>7}  {h['isin']:<13} {h['score']:.2f}  {h['name']} · {lab}  NAV {h['nav']} ({h['date']}){'  ⚠ '+s if s else ''}")

def cmd_returns(a):
    out = []
    for code in a.codes:
        meta, pts = history(code)
        if not pts:
            print(f"{code}: no history", file=sys.stderr); continue
        r = period_returns(pts); r.update(code=code, name=meta.get("scheme_name"),
                                          category=meta.get("scheme_category"))
        age = (dt.date.today() - pts[-1][0]).days
        r["stale"] = None if age <= STALE_DAYS else f"history ends {pts[-1][0]} — resolve the current code"
        out.append(r)
    if a.benchmark:
        b = index_history(BENCHMARKS.get(a.benchmark, a.benchmark))
        r = period_returns(b); r.update(code=a.benchmark, name=f"Benchmark {a.benchmark}"); out.append(r)
    if a.json: print(json.dumps(out, indent=1)); return
    cols = ["1w", "1m", "3m", "6m", "1y", "3y_cagr", "5y_cagr", "max_drawdown_1y"]
    print(f"{'fund':48s} " + " ".join(f"{c:>8s}" for c in cols) + "  as_of")
    for r in out:
        print(f"{(r['name'] or str(r['code']))[:48]:48s} " +
              " ".join(f"{('%+.1f' % r[c]) if r.get(c) is not None else '—':>8s}" for c in cols) +
              f"  {r['as_of']}" + (f"  ⚠ {r['stale']}" if r.get("stale") else ""))
    print("1w = Friday-to-Friday NAV. 3y/5y = annualised (CAGR). Past returns, not a forecast.")

def cmd_portfolio(a):
    hold = json.load(open(a.holdings))
    funds = hold["funds"] if isinstance(hold, dict) else hold
    as_of = hold.get("as_of") if isinstance(hold, dict) else None
    series, warnings, used = [], [], []
    for f in funds:
        code = f.get("code")
        if not code:
            hits = resolve(f["name"], f.get("plan", "direct"), f.get("option", "growth"), f.get("isin"))
            if not hits or hits[0]["score"] < a.min_score:
                warnings.append(f"unresolved: {f['name']}"); continue
            code = hits[0]["code"]
            if hits[0].get("unlabelled"): warnings.append(f"plan not labelled by AMFI: '{f['name']}' → code {code}, assumed {f.get('plan','direct')} by NAV — add its ISIN to be sure")
            if hits[0]["score"] < 1.0: warnings.append(f"check match: '{f['name']}' → {hits[0]['name']} ({hits[0]['score']})")
        meta, pts = history(code)
        if not pts: warnings.append(f"no history: {code}"); continue
        if (dt.date.today() - pts[-1][0]).days > STALE_DAYS:
            warnings.append(f"stale: {f.get('name', code)} history ends {pts[-1][0]}"); continue
        if f.get("units"):
            units = f["units"]
        else:  # value is as of the holdings date, so divide by the NAV on that date
            ref = on_or_before(pts, dt.date.fromisoformat(as_of)) if as_of else pts[-1]
            units = f["value"] / ref[1]
        dates, vals = weekly(pts, a.weeks)
        series.append((units, vals)); used.append({"code": code, "name": meta.get("scheme_name"), "units": round(units, 4)})
    if not series: raise SystemExit("nothing to compute")
    n = len(series[0][1])
    tot = [None if any(v[i] is None for _, v in series) else sum(u * v[i] for u, v in series) for i in range(n)]
    out = {"dates": dates, "value": [round(x) if x else None for x in tot],
           "wow": [None] + [pct(tot[i - 1], tot[i]) for i in range(1, n)],
           "idx": [round(x / tot[0] * 100, 2) if x and tot[0] else None for x in tot],
           "funds": used, "warnings": warnings,
           "method": "Current units held constant at each Friday NAV (on-or-before). New SIP money excluded."}
    if a.benchmark:
        sym = BENCHMARKS.get(a.benchmark, a.benchmark)
        b = index_history(sym, "2y")
        bv = [(on_or_before(b, dt.date.fromisoformat(d)) or (None, None))[1] for d in dates]
        out["benchmark"] = a.benchmark
        out["bwow"] = [None] + [pct(bv[i - 1], bv[i]) for i in range(1, n)]
        out["bidx"] = [round(x / bv[0] * 100, 2) if x and bv[0] else None for x in bv]
        ret, bret = out["idx"][-1] - 100, out["bidx"][-1] - 100
        beat = sum(1 for x, y in zip(out["wow"][1:], out["bwow"][1:]) if x is not None and y is not None and x > y)
        out["summary"] = {"ret": round(ret, 2), "bret": round(bret, 2), "beat_weeks": beat}
    if a.out: json.dump(out, open(a.out, "w"), indent=1)
    if a.json: print(json.dumps(out, indent=1)); return
    print(f"{'week ending':12s} {'value':>12s} {'you':>7s}" + (f" {a.benchmark:>9s}" if a.benchmark else ""))
    for i, d in enumerate(dates):
        print(f"{d:12s} {('₹{:,}'.format(out['value'][i])) if out['value'][i] else '—':>12s} {('%+.2f' % out['wow'][i]) if out['wow'][i] is not None else '':>7s}" +
              (f" {('%+.2f' % out['bwow'][i]) if out['bwow'][i] is not None else '':>9s}" if a.benchmark else ""))
    if a.benchmark:
        s = out["summary"]; print(f"\n{a.weeks} weeks: you {s['ret']:+.2f}% vs {a.benchmark} {s['bret']:+.2f}% · beat it in {s['beat_weeks']} of {a.weeks} weeks")
    for w in warnings: print("⚠", w)

def main():
    p = argparse.ArgumentParser(description="Real NAV history and returns for Indian mutual funds.")
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("resolve", help="find the AMFI scheme code for a fund name or ISIN")
    r.add_argument("query", nargs="?"); r.add_argument("--isin")
    r.add_argument("--plan", default="direct"); r.add_argument("--option", default="growth")
    r.add_argument("--json", action="store_true"); r.set_defaults(f=cmd_resolve)
    t = sp.add_parser("returns", help="1W/1M/3M/6M/1Y/3Y/5Y returns and 1Y max drawdown")
    t.add_argument("codes", nargs="+", type=int); t.add_argument("--benchmark")
    t.add_argument("--json", action="store_true"); t.set_defaults(f=cmd_returns)
    o = sp.add_parser("portfolio", help="weekly value-weighted series for a holdings file, vs a benchmark")
    o.add_argument("holdings"); o.add_argument("--weeks", type=int, default=12)
    o.add_argument("--benchmark"); o.add_argument("--min-score", type=float, default=0.5)
    o.add_argument("--out"); o.add_argument("--json", action="store_true"); o.set_defaults(f=cmd_portfolio)
    a = p.parse_args(); a.f(a)

if __name__ == "__main__":
    main()
