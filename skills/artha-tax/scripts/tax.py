#!/usr/bin/env python3
"""artha-tax: capital-gains classification, tax estimates, ELSS lock-in and LTCG
harvesting for an Indian resident's mutual funds, shares and foreign shares.

Rules encoded for FY 2026-27 (verified Nov 2026; see SKILL.md). Standard library only.
This is an estimate for planning, not a tax computation for filing.
"""
import argparse, datetime as dt, json, sys

EXEMPTION_112A = 125000      # yearly LTCG exemption, equity-oriented only, shared across all sales
CESS = 0.04
D_2023 = dt.date(2023, 4, 1)

# type → (months to be long-term, LT rate, ST rate, uses 112A exemption)
#   ST rate None = taxed at the investor's slab rate
RULES = {
    "equity":         (12, 0.125, 0.20, True),   # equity MF, equity index fund, equity FoF (90%+ equity ETFs)
    "elss":           (12, 0.125, 0.20, True),   # + 3-year lock-in per lot
    "listed_share":   (12, 0.125, 0.20, True),   # NSE/BSE shares, equity ETFs
    "other_listed":   (12, 0.125, None, False),  # gold/silver/international ETFs on an Indian exchange
    "other_unlisted": (24, 0.125, None, False),  # gold/silver/international FoFs, hybrid non-equity
    "foreign_share":  (24, 0.125, None, False),  # US/Canadian shares, RSUs after vest
    "specified_debt": (24, 0.125, None, False),  # debt funds: bought before 1 Apr 2023 only; after → always slab
}

def d(s): return dt.date.fromisoformat(s)

def months_between(a, b):
    m = (b.year - a.year) * 12 + (b.month - a.month)
    return m if b.day >= a.day else m - 1

def fy_of(day):
    y = day.year if day.month >= 4 else day.year - 1
    return f"FY{y}-{str(y + 1)[-2:]}"

def classify(lot, sell_date):
    t = lot["type"]
    if t not in RULES: raise SystemExit(f"unknown type '{t}' for {lot.get('asset')} — use one of {', '.join(RULES)}")
    months, lt_rate, st_rate, exempt = RULES[t]
    buy = d(lot["buy_date"]); held = months_between(buy, sell_date)
    if t == "specified_debt" and buy >= D_2023:
        return {"term": "ST", "rate": None, "exempt": False, "held_months": held, "note": "debt fund bought on/after 1 Apr 2023: slab rate at any holding period"}
    lt = held >= months and (sell_date - buy).days > months * 30   # "more than" 12/24 months
    out = {"term": "LT" if lt else "ST", "rate": lt_rate if lt else st_rate, "exempt": exempt and lt, "held_months": held}
    if t == "elss":
        unlock = dt.date(buy.year + 3, buy.month, min(buy.day, 28))
        if sell_date < unlock: out["locked_until"] = unlock.isoformat()
    if not lt:
        nd = dt.date(buy.year + (buy.month + months - 1) // 12, (buy.month + months - 1) % 12 + 1, min(buy.day, 28)) + dt.timedelta(days=1)
        out["long_term_from"] = nd.isoformat()
    return out

def cost_of(lot, units=None):
    units = lot["units"] if units is None else units
    per = lot["cost"] / lot["units"] if "cost" in lot else lot["buy_price"]
    if lot.get("fmv_2018") and d(lot["buy_date"]) < dt.date(2018, 2, 1) and lot["type"] in ("equity", "elss", "listed_share"):
        per = max(per, min(lot["fmv_2018"], lot["current_price"]))   # grandfathering (31 Jan 2018 FMV)
    return per * units

def evaluate(lots, sell_date, slab):
    rows = []
    for l in lots:
        c = classify(l, sell_date); val = l["units"] * l["current_price"]; gain = val - cost_of(l)
        rows.append(dict(asset=l["asset"], type=l["type"], buy_date=l["buy_date"], units=l["units"], value=round(val), gain=round(gain), **c))
    return rows

def tax_on(rows, slab, realized_ltcg=0.0):
    """Tax if every row were sold now. Losses offset gains only within the same bucket here (simplified)."""
    eq_lt = sum(r["gain"] for r in rows if r["exempt"])
    room = max(0.0, EXEMPTION_112A - realized_ltcg)
    taxable_eq_lt = max(0.0, eq_lt - room)
    t = taxable_eq_lt * 0.125
    for r in rows:
        if r["exempt"] or r["gain"] <= 0: continue
        rate = r["rate"] if r["rate"] is not None else (slab / 100 if slab is not None else None)
        if rate is None: r["tax"] = "slab rate — pass --slab"; continue
        r["tax"] = round(r["gain"] * rate * (1 + CESS)); t += r["gain"] * rate
    return {"equity_ltcg": round(eq_lt), "exemption_left_before": round(room), "taxable_equity_ltcg": round(taxable_eq_lt),
            "estimated_tax_incl_cess": round(t * (1 + CESS))}

def load(path, prices):
    data = json.load(open(path)); lots = data["lots"] if isinstance(data, dict) else data
    for l in lots:
        if "current_price" not in l:
            if l.get("asset") in prices: l["current_price"] = prices[l["asset"]]
            else: raise SystemExit(f"missing current_price for {l['asset']} — add it or pass --prices")
    return lots, (data.get("realized_ltcg_this_fy", 0.0) if isinstance(data, dict) else 0.0)

def cmd_gains(a):
    lots, realized = load(a.lots, json.load(open(a.prices)) if a.prices else {})
    when = d(a.as_of) if a.as_of else dt.date.today()
    rows = evaluate(lots, when, a.slab); summ = tax_on(rows, a.slab, a.realized if a.realized is not None else realized)
    out = {"as_of": when.isoformat(), "fy": fy_of(when), "lots": rows, "if_sold_today": summ}
    if a.json: print(json.dumps(out, indent=1)); return
    print(f"{'asset':34s} {'type':14s} {'bought':10s} {'term':4s} {'gain':>10s}  note")
    for r in rows:
        note = (f"locked until {r['locked_until']}" if r.get("locked_until") else "") or (f"long-term from {r['long_term_from']}" if r.get("long_term_from") else "") or r.get("note", "")
        print(f"{r['asset'][:34]:34s} {r['type']:14s} {r['buy_date']:10s} {r['term']:4s} {r['gain']:>10,}  {note}")
    s = summ; print(f"\n{out['fy']}: equity LTCG if all sold today ₹{s['equity_ltcg']:,} · exemption left ₹{s['exemption_left_before']:,} · est. tax incl. 4% cess ₹{s['estimated_tax_incl_cess']:,}"
                    + ("" if a.slab is not None else "  (slab-rate items excluded — pass --slab)"))

def fifo_sell(lots, asset, units, when):
    """Mutual fund and share redemptions are matched first-in, first-out per folio/demat."""
    mine = sorted([l for l in lots if l["asset"] == asset], key=lambda l: l["buy_date"]); left = units; parts = []
    for l in mine:
        if left <= 0: break
        u = min(left, l["units"]); c = classify(l, when)
        parts.append(dict(buy_date=l["buy_date"], units=round(u, 4), gain=round(u * l["current_price"] - cost_of(l, u)), **c)); left -= u
    if left > 1e-6: raise SystemExit(f"only {units - left:.4f} units of {asset} available")
    return parts

def cmd_whatif(a):
    lots, realized = load(a.lots, json.load(open(a.prices)) if a.prices else {})
    when = d(a.as_of) if a.as_of else dt.date.today(); parts = []
    for spec in a.sell:
        asset, units = spec.rsplit(":", 1); parts += [dict(p, asset=asset) for p in fifo_sell(lots, asset, float(units), when)]
    locked = [p for p in parts if p.get("locked_until")]
    summ = tax_on(parts, a.slab, a.realized if a.realized is not None else realized)
    out = {"as_of": when.isoformat(), "parts": parts, "summary": summ, "blocked": bool(locked)}
    if a.json: print(json.dumps(out, indent=1)); return
    for p in parts: print(f"{p['asset'][:30]:30s} lot {p['buy_date']} {p['units']:>10} units  {p['term']}  gain ₹{p['gain']:,}" + (f"  ⛔ ELSS locked until {p['locked_until']}" if p.get("locked_until") else ""))
    print(f"\nEst. tax incl. cess: ₹{summ['estimated_tax_incl_cess']:,}  (exemption used first: ₹{min(summ['equity_ltcg'], summ['exemption_left_before']):,})")
    if locked: print("⛔ Some units are still in ELSS lock-in: this redemption isn't possible as entered.")

def cmd_harvest(a):
    """Units to redeem (FIFO) so realised equity LTCG stays within the remaining exemption, never touching ST or locked lots."""
    lots, realized = load(a.lots, json.load(open(a.prices)) if a.prices else {})
    when = d(a.as_of) if a.as_of else dt.date.today(); room = max(0.0, EXEMPTION_112A - (a.realized if a.realized is not None else realized))
    plan = []; assets = sorted({l["asset"] for l in lots if RULES[l["type"]][3]})
    for asset in assets:
        if room <= 1: break
        units = 0.0; gain = 0.0
        for l in sorted([x for x in lots if x["asset"] == asset], key=lambda x: x["buy_date"]):
            c = classify(l, when)
            if c["term"] != "LT" or c.get("locked_until"): break    # FIFO: can't skip past a ST/locked lot
            per_gain = (l["units"] * l["current_price"] - cost_of(l)) / l["units"]
            if per_gain <= 0: units += l["units"]; continue
            u = min(l["units"], room / per_gain); units += u; gain += u * per_gain; room -= u * per_gain
            if u < l["units"]: break
        if gain > 0: plan.append({"asset": asset, "units": round(units, 3), "ltcg_realised": round(gain)})
    out = {"as_of": when.isoformat(), "fy": fy_of(when), "plan": plan, "exemption_unused_after": round(room),
           "note": "Redeem these units and (if you want to stay invested) buy back — the higher cost base cuts future tax. Exit loads and the next FY's exemption are separate."}
    if a.json: print(json.dumps(out, indent=1)); return
    for p in plan: print(f"{p['asset'][:40]:40s} redeem {p['units']:>10} units → tax-free LTCG ₹{p['ltcg_realised']:,}")
    print(f"\nExemption left unused: ₹{out['exemption_unused_after']:,}. {out['note']}")

def cmd_lockin(a):
    lots, _ = load(a.lots, json.load(open(a.prices)) if a.prices else {})
    when = d(a.as_of) if a.as_of else dt.date.today()
    for l in sorted([x for x in lots if x["type"] == "elss"], key=lambda x: x["buy_date"]):
        c = classify(l, when); print(f"{l['asset'][:34]:34s} {l['buy_date']}  {l['units']:>10} units  " + (f"locked until {c['locked_until']}" if c.get("locked_until") else "free"))

def main():
    p = argparse.ArgumentParser(description="Indian capital-gains estimates (FY 2026-27 rules).")
    sp = p.add_subparsers(dest="cmd", required=True)
    for name, f in [("gains", cmd_gains), ("whatif", cmd_whatif), ("harvest", cmd_harvest), ("lockin", cmd_lockin)]:
        x = sp.add_parser(name); x.add_argument("lots"); x.add_argument("--as-of"); x.add_argument("--prices", help="JSON {asset: current_price}")
        x.add_argument("--slab", type=float, help="your income-tax slab %% for slab-rate gains"); x.add_argument("--realized", type=float, help="equity LTCG already realised this FY")
        x.add_argument("--json", action="store_true"); x.set_defaults(f=f)
        if name == "whatif": x.add_argument("--sell", nargs="+", required=True, help='"Asset name:units"')
    a = p.parse_args(); a.f(a)

if __name__ == "__main__":
    main()
