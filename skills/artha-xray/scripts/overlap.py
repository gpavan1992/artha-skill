#!/usr/bin/env python3
"""artha-xray: stock and sector overlap across a mutual fund portfolio, using each fund's
disclosed holdings (e.g. IND Money get_mf_funds_details includes=["holdings"]). Stdlib only."""
import argparse, itertools, json, re

DROP = re.compile(r"\b(ltd|limited|ordinary shares|class [ab] shares|shs|inc|corp(oration)?|co)\b\.?", re.I)
def key(name):
    n = DROP.sub(" ", name.lower()).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", n).strip()

def pct(x):
    if isinstance(x, (int, float)): return float(x)
    return float(str(x).replace("%", "").strip() or 0)

def from_indmoney(raw, values):
    """Accept IND Money get_mf_funds_details output; keep only the Equity group (debt rows reuse company names)."""
    out = []
    for item in raw.get("data", raw if isinstance(raw, list) else []):
        fd = item["data"]["fund_detail"]; groups = item["data"].get("holdings", {}).get("holdings", [])
        eq = [h for g in groups if g.get("name") == "Equity" for h in g.get("holds", [])]
        eqp = next((c.get("perc") for c in item["data"].get("holdings", {}).get("holdings_count", []) if c.get("name") == "Equity Holdings"), None)
        name = fd.get("fund_app_short_name") or fd["name"]
        out.append({"name": name, "value": values.get(name, values.get(str(item.get("fund_id")), 0)), "equity_pct": eqp, "holdings": eq})
    return out

def load(path, values=None):
    funds = json.load(open(path))
    if isinstance(funds, dict) and "data" in funds: funds = from_indmoney(funds, values or {})
    funds = funds["funds"] if isinstance(funds, dict) else funds
    out = []
    for f in funds:
        hs = {}
        names = {}
        for h in f.get("holdings", []):
            k = key(h["name"]); hs[k] = hs.get(k, 0) + pct(h.get("perc", h.get("weight", 0))); names[k] = h["name"]
            if h.get("sector"): names[k + "#sector"] = h["sector"]
        cov = sum(hs.values())
        out.append({"name": f["name"], "value": float(f.get("value", 0)), "w": hs, "names": names,
                    "coverage": round(cov, 1), "equity_pct": f.get("equity_pct")})
    return out

def main():
    p = argparse.ArgumentParser(description="Mutual fund portfolio overlap and look-through exposure.")
    p.add_argument("funds", help="funds.json, or raw IND Money get_mf_funds_details output (use with --values)")
    p.add_argument("--values", help='JSON {fund name or fund_id: rupee value}'); p.add_argument("--top", type=int, default=15); p.add_argument("--flag", type=float, default=30.0)
    p.add_argument("--out"); p.add_argument("--json", action="store_true"); a = p.parse_args()
    F = load(a.funds, json.load(open(a.values)) if a.values else None); total = sum(f["value"] for f in F) or 1
    pairs = []
    for x, y in itertools.combinations(F, 2):
        common = set(x["w"]) & set(y["w"])
        ov = sum(min(x["w"][k], y["w"][k]) for k in common)
        if common:
            pairs.append({"a": x["name"], "b": y["name"], "overlap_pct": round(ov, 1), "common_stocks": len(common),
                          "top_common": [x["names"][k] for k in sorted(common, key=lambda k: -min(x["w"][k], y["w"][k]))[:5]],
                          "flag": ov >= a.flag})
    pairs.sort(key=lambda r: -r["overlap_pct"])
    stock, sector, names = {}, {}, {}
    for f in F:
        for k, w in f["w"].items():
            rs = f["value"] * w / 100; stock[k] = stock.get(k, 0) + rs; names[k] = f["names"][k]
            sec = f["names"].get(k + "#sector")
            if sec: sector[sec] = sector.get(sec, 0) + rs
        if f["names"] and not any(n.endswith("#sector") for n in f["names"]): pass
    covered = sum(stock.values())
    top = sorted(stock.items(), key=lambda kv: -kv[1])[:a.top]
    out = {
        "portfolio_value": round(total),
        "coverage_pct": round(covered / total * 100, 1),
        "funds": [{"name": f["name"], "value": round(f["value"]), "listed_weight_pct": f["coverage"],
                   "warning": (f"disclosed holdings cover {f['coverage']}% of the fund{' (equity ' + str(round(f['equity_pct'])) + '%)' if f.get('equity_pct') else ''} — overlap with it is understated" if f["coverage"] and f["coverage"] < 80 else None)
                              if f["w"] else "no holdings supplied"} for f in F],
        "pairs": pairs,
        "top_stocks": [{"stock": names[k], "rupees": round(v), "pct_of_portfolio": round(v / total * 100, 2),
                        "in_funds": sum(1 for f in F if k in f["w"])} for k, v in top],
        "sectors": [{"sector": s, "rupees": round(v), "pct_of_portfolio": round(v / total * 100, 1), "pct_of_visible": round(v / covered * 100, 1) if covered else None} for s, v in sorted(sector.items(), key=lambda kv: -kv[1])],
        "concentration_hhi": round(sum((v / covered) ** 2 for v in stock.values()) * 10000) if covered else None,
        "method": "Look-through = Σ fund value × stock weight, using each fund's disclosed holdings (often top holdings only). Overlap between two funds = Σ min(weight) over common stocks."}
    if a.out: json.dump(out, open(a.out, "w"), indent=1)
    if a.json: print(json.dumps(out, indent=1)); return
    print(f"Portfolio ₹{out['portfolio_value']:,} · holdings visible for {out['coverage_pct']}% of it\n")
    print("Most-overlapping fund pairs:")
    for r in pairs[:8]: print(f"  {r['overlap_pct']:5.1f}%  {r['a']} × {r['b']}  ({r['common_stocks']} common: {', '.join(r['top_common'][:3])}){'  ⚠' if r['flag'] else ''}")
    print("\nBiggest look-through stocks:")
    for t in out["top_stocks"]: print(f"  {t['pct_of_portfolio']:5.2f}%  ₹{t['rupees']:>9,}  {t['stock']}  (in {t['in_funds']} fund{'' if t['in_funds'] == 1 else 's'})")
    if out["sectors"]:
        print("\nSectors (share of visible holdings):"); [print(f"  {s['pct_of_visible']:5.1f}%  {s['sector']}") for s in out["sectors"][:8]]
    for f in out["funds"]:
        if f["warning"]: print(f"⚠ {f['name']}: {f['warning']}")

if __name__ == "__main__":
    main()
