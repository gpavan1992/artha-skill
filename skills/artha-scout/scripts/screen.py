#!/usr/bin/env python3
"""artha-scout: filter NSE stocks against your own rules using reported fundamentals.
Universe from NSE index lists; numbers from the artha-analyst skill. Stdlib only."""
import argparse, csv, importlib.util, io, json, os, sys, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; artha-skill/0.1.2; +https://github.com/gpavan1992/artha-skill)"}
LISTS = {"nifty50": "ind_nifty50list", "niftynext50": "ind_niftynext50list", "nifty100": "ind_nifty100list",
         "nifty200": "ind_nifty200list", "nifty500": "ind_nifty500list", "midcap150": "ind_niftymidcap150list",
         "smallcap100": "ind_niftysmallcap100list"}
SRC = ["https://www.niftyindices.com/IndexConstituent/{f}.csv", "https://nsearchives.nseindia.com/content/indices/{f}.csv"]
OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, "<": lambda a, b: a < b,
       "==": lambda a, b: a == b, "!=": lambda a, b: a != b}

def universe(name):
    f = LISTS.get(name.lower())
    if not f: raise SystemExit(f"unknown index '{name}' — choose from {', '.join(LISTS)}")
    for u in SRC:
        try:
            with urllib.request.urlopen(urllib.request.Request(u.format(f=f), headers=UA), timeout=30) as r:
                rows = list(csv.DictReader(io.StringIO(r.read().decode("utf-8", "replace"))))
            return [{"symbol": x["Symbol"].strip(), "name": x["Company Name"].strip(), "industry": x.get("Industry", "").strip()} for x in rows if x.get("Symbol")]
        except Exception as e: err = e
    raise SystemExit(f"could not download {name} constituents: {err}")

def fund_module():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in [os.environ.get("FUND_PY"), os.path.join(here, "..", "..", "artha-analyst", "scripts", "fund.py")]:
        if p and os.path.exists(p):
            spec = importlib.util.spec_from_file_location("fund", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    return None

def check(row, rule):
    v = row.get(rule["field"])
    if v is None: return False, "missing data", None
    ok = OPS[rule["op"]](v, rule["value"])
    gap = (v - rule["value"]) if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(rule["value"], (int, float)) else None
    return ok, None, gap

def headroom(row, rules):
    """Average margin of safety over numeric thresholds (0 = just passes); used only to rank passers."""
    hs = []
    for r in rules:
        v, t = row.get(r["field"]), r["value"]
        if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(t, (int, float)) and t:
            h = (v - t) / abs(t) if r["op"] in (">=", ">") else (t - v) / abs(t) if r["op"] in ("<=", "<") else 0
            hs.append(max(-1, min(h, 2)))
    return round(sum(hs) / len(hs), 2) if hs else 0.0

def main():
    p = argparse.ArgumentParser(description="Screen NSE stocks against your rules (reported fundamentals).")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--index", help=", ".join(LISTS)); src.add_argument("--symbols", nargs="+"); src.add_argument("--metrics", help="artha-analyst --out JSON")
    p.add_argument("--rules", default=os.path.join(os.path.dirname(__file__), "..", "rules.example.json"))
    p.add_argument("--limit", type=int, help="screen only the first N stocks (testing)")
    p.add_argument("--out"); p.add_argument("--json", action="store_true"); a = p.parse_args()
    R = json.load(open(a.rules)); rules = R["rules"]
    meta = {}
    if a.metrics: rows = json.load(open(a.metrics))
    else:
        uni = universe(a.index) if a.index else [{"symbol": s.upper().replace(".NS", ""), "name": "", "industry": ""} for s in a.symbols]
        if a.limit: uni = uni[: a.limit]
        meta = {u["symbol"] + ".NS": u for u in uni}
        fm = fund_module()
        if not fm: raise SystemExit("artha-analyst not found next to this skill — run it first:\n  fund.py <symbols> --out fundamentals.json\nthen: screen.py --metrics fundamentals.json")
        rows = []
        for i, u in enumerate(uni, 1):
            try: rows.append(fm.snapshot(u["symbol"] + ".NS"))
            except SystemExit as e: rows.append({"symbol": u["symbol"] + ".NS", "error": str(e)})
            if sys.stderr.isatty(): print(f"\rfetched {i}/{len(uni)}", end="", file=sys.stderr)
            elif i % 25 == 0 or i == len(uni): print(f"fetched {i}/{len(uni)}", file=sys.stderr)
    passed, near, failed = [], [], []
    for row in rows:
        m = meta.get(row.get("symbol"), {})
        if row.get("error"): failed.append({"symbol": row["symbol"], "reason": row["error"]}); continue
        res = [(r, *check(row, r)) for r in rules]
        misses = [(r, why, gap) for r, ok, why, gap in res if not ok]
        base = {"symbol": row["symbol"].replace(".NS", ""), "name": m.get("name", ""), "industry": m.get("industry", ""),
                "pe": row.get("pe"), "revenue_growth": row.get("revenue_growth_yoy_pct"), "profit_growth": row.get("profit_growth_yoy_pct"),
                "roe": row.get("roe_pct"), "warnings": row.get("warnings", [])}
        if not misses: passed.append(dict(base, score=headroom(row, rules)))
        else:
            reasons = [f"{r.get('label', r['field'])}: {why or (str(row.get(r['field'])) + ' vs ' + r['op'] + ' ' + str(r['value']))}" for r, why, gap in misses]
            (near if len(misses) == 1 and not misses[0][1] else failed).append(dict(base, reason="; ".join(reasons)))
    passed.sort(key=lambda x: -x["score"])
    out = {"name": R.get("name", "screen"), "rules": rules, "screened": len(rows), "passed": passed, "near_misses": near,
           "failed_count": len(failed), "failed": failed,
           "note": "Filters reported numbers only. Passing is not a buy signal; missing data always fails."}
    if a.out: json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    if a.json: print(json.dumps(out, indent=1, ensure_ascii=False)); return
    print(f"{out['name']}: {len(passed)} of {len(rows)} pass\n")
    for x in passed: print(f"  ✅ {x['symbol']:<12} score {x['score']:+.2f}  rev {x['revenue_growth']}% · profit {x['profit_growth']}% · P/E {x['pe']} · ROE {x['roe']}%  {x['industry']}")
    if near: print("\nNear misses (fail one rule):"); [print(f"  ⚠ {x['symbol']:<12} {x['reason']}") for x in near]
    print(f"\n{len(failed)} failed more than one rule or had missing data. {out['note']}")

if __name__ == "__main__":
    main()
