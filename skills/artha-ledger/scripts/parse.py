#!/usr/bin/env python3
"""artha-ledger: turn Indian bank/card transaction-alert emails into categorised spend.

Input: alerts.json = [{"id", "date" (YYYY-MM-DD), "subject", "text"}] — gathered from Gmail
(search alerts, read full bodies where the snippet is cut). Standard library only.
Privacy: card numbers, UPI IDs and names of individuals are never written to the output.
"""
import argparse, json, os, re, sys
from collections import defaultdict

AMT = r"(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d{1,2})?)"
MERCHANT = [r"towards\s+(.+?)(?:\s+on\s+\d|\s+on\s+[a-z]{3}|\.|$)", r"\bat\s+(.+?)(?:\s+on\s+\d|\s+on\s+[a-z]{3}|\.\s|\s+via|\s+avl|$)",
            r"info:?\s*([^.\n]+)", r"(?:to|for)\s+vpa\s+(\S+)", r"\bto\s+([A-Z][A-Za-z0-9&' .-]{2,40}?)(?:\s+on\s+|\.|$)"]
CARD = r"(?:ending|xx|\*\*|card no\.?\s*x+)\s*(\d{4})"
SKIP = re.compile(r"\b(otp|one time password|statement is ready|payment (?:of .* )?received|credited to your|thank you for your payment|e-mandate registration|declined)\b", re.I)
REFUND = re.compile(r"\b(refund|reversed|reversal|credited back)\b", re.I)
VPA = re.compile(r"[\w.\-]+@[a-z]+", re.I)   # UPI IDs: never stored

def bank_of(t):
    for b in ["HDFC", "ICICI", "SBI", "Axis", "Kotak", "American Express", "IndusInd", "Yes Bank", "IDFC", "AU "]:
        if b.lower() in t.lower(): return b.strip()
    return "Other"

def parse_one(a, cats):
    text = re.sub(r"\s+", " ", f"{a.get('subject','')} . {a.get('text','')}")
    if SKIP.search(text) and not re.search(r"spent|debited|used for", text, re.I): return None, "skipped (not a spend)"
    m = re.search(AMT, text, re.I)
    if not m: return None, "no amount"
    amount = float(m.group(1).replace(",", ""))
    merchant = None
    for pat in MERCHANT:
        mm = re.search(pat, text, re.I)
        if mm:
            merchant = mm.group(1).strip(" .,:-"); break
    card = re.search(CARD, text, re.I); bank = bank_of(text)
    kind = "card" if re.search(r"credit card|card ending|card xx", text, re.I) else "account/upi"
    to_vpa = bool(merchant and VPA.search(merchant)) or bool(re.search(r"to vpa", text, re.I))
    person = to_vpa and kind != "card"            # account → VPA: most likely a person; never keep the name
    if to_vpa or not merchant:
        label = "UPI/transfer to a person" if person else ("UPI payment (merchant not named)" if to_vpa else "Unknown merchant")
        cat = "Transfers" if person else "Uncategorised"
    else:
        label = re.sub(r"\s{2,}", " ", merchant)[:40].title()
        low = f" {merchant.lower()} "
        cat = next((c for c, kws in cats.items() if any(k in low for k in kws)), "Other")
    return {"id": a.get("id"), "date": a["date"], "amount": amount, "merchant": label, "category": cat,
            "source": f"{bank} {'card' if kind == 'card' else 'account'}" + (f" ••{card.group(1)}" if card and kind == "card" else ""),
            "refund": bool(REFUND.search(text))}, None

def main():
    p = argparse.ArgumentParser(description="Categorise Indian card/UPI alert emails into spend.")
    p.add_argument("alerts"); p.add_argument("--categories", default=os.path.join(os.path.dirname(__file__), "..", "categories.json"))
    p.add_argument("--period", help="label, e.g. 'October 2026'"); p.add_argument("--cards-only", action="store_true", help="ignore account/UPI debits")
    p.add_argument("--include-transfers", action="store_true", help="count person-to-person transfers in totals")
    p.add_argument("--out"); p.add_argument("--json", action="store_true"); a = p.parse_args()
    cats = json.load(open(a.categories)); alerts = json.load(open(a.alerts))
    txns, issues, seen = [], [], set()
    for al in alerts:
        t, why = parse_one(al, cats)
        if not t: issues.append({"id": al.get("id"), "why": why}); continue
        k = (t["amount"], t["date"], t["source"])
        if k in seen: issues.append({"id": al.get("id"), "why": "duplicate alert"}); continue
        seen.add(k); txns.append(t)
    spend = [t for t in txns if not t["refund"] and (a.include_transfers or t["category"] != "Transfers") and (not a.cards_only or "card" in t["source"])]
    refunds = [t for t in txns if t["refund"]]
    tot = sum(t["amount"] for t in spend) - sum(t["amount"] for t in refunds)
    by = lambda key: sorted(((k, sum(t["amount"] for t in spend if t[key] == k), sum(1 for t in spend if t[key] == k)) for k in {t[key] for t in spend}), key=lambda r: -r[1])
    merch = [r for r in by("merchant") if r[0] not in ("UPI/transfer to a person", "Unknown merchant", "UPI payment (merchant not named)")][:8]
    out = {"period": a.period or (f"{min(t['date'] for t in spend)} to {max(t['date'] for t in spend)}" if spend else ""),
           "total": round(tot), "txns": len(spend),
           "categories": [{"name": k, "amount": round(v), "count": n} for k, v, n in by("category")],
           "cards": [{"name": k, "amount": round(v), "count": n} for k, v, n in by("source")],
           "top_merchants": [{"name": k, "amount": round(v), "count": n} for k, v, n in merch],
           "refunds": round(sum(t["amount"] for t in refunds)),
           "transfers_excluded": round(sum(t["amount"] for t in txns if t["category"] == "Transfers" and not a.include_transfers)),
           "coverage": f"{len(txns)} of {len(alerts)} alerts parsed; {len([i for i in issues if i['why'] != 'duplicate alert'])} not parsed",
           "unparsed": issues}
    if a.out: json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    if a.json: print(json.dumps(out, indent=1, ensure_ascii=False)); return
    print(f"{out['period']}: ₹{out['total']:,} across {out['txns']} transactions (refunds −₹{out['refunds']:,}; transfers to people excluded ₹{out['transfers_excluded']:,})\n")
    for c in out["categories"]: print(f"  {c['name']:22s} ₹{c['amount']:>9,}  ({c['count']})")
    print("\nTop merchants:"); [print(f"  {m['name']:30s} ₹{m['amount']:>9,}  ×{m['count']}") for m in out["top_merchants"]]
    print("\nBy card/account:"); [print(f"  {c['name']:30s} ₹{c['amount']:>9,}") for c in out["cards"]]
    print(f"\n{out['coverage']}"); [print(f"  · {i['id']}: {i['why']}") for i in issues]

if __name__ == "__main__":
    main()
