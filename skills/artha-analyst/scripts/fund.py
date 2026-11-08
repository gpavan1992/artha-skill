#!/usr/bin/env python3
"""artha-analyst: reported financials for NSE/BSE companies (revenue, profit, margins,
EPS, debt, ROE, cash flow) from Yahoo's public fundamentals time series. Stdlib only.
Values in ₹ crore unless noted."""
import argparse, json, os, re, sys, time, urllib.request
from urllib.parse import quote

TS = ("https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{s}"
      "?type={t}&period1=1420070400&period2=" + str(int(time.time()) + 86400))
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=10y&interval=1mo&events=split"
UA = {"User-Agent": "Mozilla/5.0 (artha-analyst; personal research)"}
CACHE = os.environ.get("FUND_CACHE", os.path.join(os.getcwd(), ".fund-cache"))
A = ["TotalRevenue", "OperatingIncome", "NetIncome", "DilutedEPS", "TotalDebt", "StockholdersEquity", "FreeCashFlow", "OperatingCashFlow"]
Q = ["TotalRevenue", "OperatingIncome", "NetIncome", "DilutedEPS"]
CR = 1e7

def get(url, name, ttl_h=12):
    os.makedirs(CACHE, exist_ok=True); path = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", name))
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_h * 3600: return json.load(open(path))
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: d = json.loads(r.read())
            json.dump(d, open(path, "w")); time.sleep(0.3); return d
        except Exception as e: err = e; time.sleep(1.5 * (i + 1))
    raise SystemExit(f"error fetching {url}: {err}")

def norm(s): return s.upper() if "." in s else s.upper() + ".NS"

def series(sym):
    types = ",".join([f"annual{x}" for x in A] + [f"quarterly{x}" for x in Q])
    d = get(TS.format(s=quote(sym), t=types), f"ts-{sym}.json")
    out, cur = {}, {}
    for r in (d.get("timeseries") or {}).get("result") or []:
        t = r["meta"]["type"][0]; vals = sorted([x for x in (r.get(t) or []) if x], key=lambda x: x["asOfDate"])
        out[t] = [(x["asOfDate"], x["reportedValue"]["raw"]) for x in vals]
        cur[t] = next((x.get("currencyCode") for x in reversed(vals) if x.get("currencyCode")), "INR")
    return out, cur

def fx_to_inr(cur):
    """Today's rate for <cur>→INR from Yahoo (USDINR=X etc.); None if unavailable."""
    if cur in (None, "INR"): return 1.0
    try:
        r = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(cur + 'INR=X')}?range=5d&interval=1d", f"fx-{cur}.json", 1)["chart"]["result"][0]
        return float(r["meta"]["regularMarketPrice"])
    except Exception:
        return None

def price_and_splits(sym):
    r = get(CHART.format(s=quote(sym)), f"px-{sym}.json", 1)["chart"]["result"]
    if not r: return None, []
    r = r[0]; sp = (r.get("events") or {}).get("splits") or {}
    return r["meta"].get("regularMarketPrice"), sorted(time.strftime("%Y-%m-%d", time.gmtime(int(k))) + f" ({v['numerator']}:{v['denominator']})" for k, v in sp.items())

def last(s, k, n=1): v = s.get(k) or []; return v[-n:] if v else []
def yoy(a, b): return None if not a or not b or b == 0 else round((a / b - 1) * 100, 1)
def pct(a, b): return None if a is None or not b else round(a / b * 100, 1)

def snapshot(sym):
    s, cur = series(sym); price, splits = price_and_splits(sym)
    fxnote, fx_used = [], {}
    for k, vals in list(s.items()):
        c = cur.get(k) or "INR"
        if c == "INR": continue
        if c not in fx_used: fx_used[c] = fx_to_inr(c)
        fx = fx_used[c]
        if fx is None: s[k] = []; fxnote.append(f"financials are reported in {c} and the {c}/INR rate could not be fetched: figures dropped rather than mixed with ₹ prices")
        else: s[k] = [(d_, v * fx) for d_, v in vals]
    for c, fx in fx_used.items():
        if fx: fxnote.append(f"financials are reported in {c}; converted to ₹ at today's {c}/INR {fx:.2f}. Absolute ₹ amounts and P/E are approximate (older years use today's rate); growth, margins and ROE are unaffected")
    rev = last(s, "annualTotalRevenue", 4); ni = last(s, "annualNetIncome", 4); op = last(s, "annualOperatingIncome", 4)
    eq = last(s, "annualStockholdersEquity"); debt = last(s, "annualTotalDebt"); fcf = last(s, "annualFreeCashFlow", 3)
    qrev = last(s, "quarterlyTotalRevenue", 8); qni = last(s, "quarterlyNetIncome", 8); qeps = last(s, "quarterlyDilutedEPS", 4)
    aeps = last(s, "annualDilutedEPS", 2)
    bank = not op and bool(ni)            # banks/NBFCs report no operating income; their "debt" is deposits/borrowings
    o = {"symbol": sym, "price": price, "kind": "bank/financial" if bank else "company",
         "annual": [{"fy_end": d[:7], "revenue_cr": round(v / CR), "net_income_cr": round(dict(ni).get(d, 0) / CR) if dict(ni).get(d) is not None else None,
                     "op_margin_pct": None if bank else pct(dict(op).get(d), v)} for d, v in rev] if rev else [],
         "revenue_growth_yoy_pct": yoy(rev[-1][1], rev[-2][1]) if len(rev) >= 2 else None,
         "profit_growth_yoy_pct": yoy(ni[-1][1], ni[-2][1]) if len(ni) >= 2 else None,
         "net_margin_pct": pct(ni[-1][1], rev[-1][1]) if ni and rev else None,
         "roe_pct": pct(ni[-1][1], eq[0][1]) if ni and eq else None,
         "debt_to_equity": None if bank or not (debt and eq) else round(debt[0][1] / eq[0][1], 2),
         "free_cash_flow_cr": [round(v / CR) for _, v in fcf] if fcf and not bank else None,
         "reporting_currency": ", ".join(sorted(fx_used)) or "INR",
         "quarters": [], "warnings": list(dict.fromkeys(fxnote))}
    qr = dict(qrev); qn = dict(qni)
    for dq, v in qrev[-4:]:
        prev = next((x for x in qr if x[:4] == str(int(dq[:4]) - 1) and x[5:7] == dq[5:7]), None)
        o["quarters"].append({"quarter_end": dq[:7], "revenue_cr": round(v / CR), "net_income_cr": round(qn[dq] / CR) if dq in qn else None,
                              "revenue_yoy_pct": yoy(v, qr.get(prev)) if prev else None})
    lq = [q["revenue_yoy_pct"] for q in o["quarters"] if q["revenue_yoy_pct"] is not None]
    o["latest_quarter_revenue_yoy_pct"] = lq[-1] if lq else None
    if len(qeps) == 4 and all(x[1] for x in qeps):
        ttm = sum(x[1] for x in qeps); o["eps_ttm"] = round(ttm, 2); o["eps_basis"] = "sum of last 4 quarters (diluted)"
    elif aeps:
        ttm = aeps[-1][1]; o["eps_ttm"] = round(ttm, 2); o["eps_basis"] = f"last annual (FY to {aeps[-1][0][:7]}, diluted)"; o["warnings"].append("quarterly EPS incomplete — P/E uses last full-year EPS")
    else: ttm = None
    o["pe"] = round(price / ttm, 1) if price and ttm and ttm > 0 else None
    if ttm is not None and ttm <= 0: o["warnings"].append("loss-making on this EPS basis — P/E not meaningful")
    if splits: o["splits_bonuses"] = splits[-3:]; o["warnings"].append("split/bonus history present — compare diluted (restated) EPS only, never basic EPS across years")
    if bank: o["warnings"].append("bank/financial: debt-to-equity and operating margin don't apply. Yahoo's bank figures may be consolidated and can differ from reported standalone results — verify ROE/profit against the bank's results before relying on them")
    oneoff = [d[:7] for d, v in ni if dict(op).get(d) and v > dict(op)[d] * 1.1]
    o["one_off_years"] = oneoff
    o["one_off_latest"] = bool(oneoff and rev and oneoff[-1] == rev[-1][0][:7])
    if oneoff: o["warnings"].append(f"profit above operating income in FY→{', '.join(oneoff)} — likely one-off gains or tax credits; don't read that year's profit growth as business growth")
    if not rev: o["warnings"].append("no revenue series — check the symbol, or the company may be newly listed")
    return o

def main():
    p = argparse.ArgumentParser(description="Reported financials for NSE/BSE companies.")
    p.add_argument("symbols", nargs="+"); p.add_argument("--json", action="store_true"); p.add_argument("--out"); a = p.parse_args()
    res = [snapshot(norm(x)) for x in a.symbols]
    if a.out: json.dump(res, open(a.out, "w"), indent=1)
    if a.json: print(json.dumps(res, indent=1)); return
    f = lambda v, s="": "—" if v is None else f"{v:,}{s}"
    for o in res:
        print(f"\n{o['symbol']}  ₹{f(o['price'])}  P/E {f(o['pe'])}  ({o['kind']})")
        for y in o["annual"]: print(f"  FY→{y['fy_end']}: revenue ₹{f(y['revenue_cr'])} Cr · profit ₹{f(y['net_income_cr'])} Cr · op margin {f(y['op_margin_pct'],'%')}")
        print(f"  growth: revenue {f(o['revenue_growth_yoy_pct'],'%')} · profit {f(o['profit_growth_yoy_pct'],'%')} · net margin {f(o['net_margin_pct'],'%')} · ROE {f(o['roe_pct'],'%')} · D/E {f(o['debt_to_equity'])}")
        for q in o["quarters"]: print(f"  Q→{q['quarter_end']}: revenue ₹{f(q['revenue_cr'])} Cr ({f(q['revenue_yoy_pct'],'% YoY')}) · profit ₹{f(q['net_income_cr'])} Cr")
        if o.get("eps_ttm") is not None: print(f"  EPS ₹{o['eps_ttm']} ({o['eps_basis']})")
        for w in o["warnings"]: print(f"  ⚠ {w}")

if __name__ == "__main__":
    main()
