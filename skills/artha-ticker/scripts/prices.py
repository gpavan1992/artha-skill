#!/usr/bin/env python3
"""artha-ticker: NSE/BSE prices, history, corporate actions and market calendar.

Sources (free, no keys): Yahoo Finance search + chart APIs (delayed ~15 min);
NSE holiday calendar bundled in data/nse_holidays.json. Standard library only.
"""
import argparse, datetime as dt, json, os, re, sys, time, urllib.request
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
HOLIDAYS = os.path.join(HERE, "..", "data", "nse_holidays.json")
CACHE = os.environ.get("PRICES_CACHE", os.path.join(os.getcwd(), ".prices-cache"))
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}&events=div%7Csplit"
SEARCH = "https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=8&newsCount=0"
UA = {"User-Agent": "Mozilla/5.0 (artha-ticker; personal portfolio analysis)"}
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
BENCHMARKS = {"nifty50": "^NSEI", "nifty500": "^CRSLDX", "banknifty": "^NSEBANK"}

def _get(url, ttl_min, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", name))
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_min * 60:
        return json.load(open(path))
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                data = json.loads(r.read().decode())
            json.dump(data, open(path, "w")); time.sleep(0.25); return data
        except Exception as e:
            last = e; time.sleep(1.5 * (i + 1))
    if os.path.exists(path):
        print(f"note: using cached {name} ({last})", file=sys.stderr); return json.load(open(path))
    raise SystemExit(f"error: could not fetch {url}: {last}")

def norm(sym):
    s = sym.strip()
    if s.lower() in BENCHMARKS: return BENCHMARKS[s.lower()]
    if s.startswith("^") or "." in s: return s.upper() if not s.startswith("^") else s
    return s.upper() + ".NS"          # bare symbols default to NSE

def _r(x): return None if x is None else round(x, 2)

def chart(sym, rng="1y", iv="1d", ttl=20):
    d = _get(CHART.format(sym=quote(sym), rng=rng, iv=iv), ttl, f"c-{sym}-{rng}-{iv}.json")
    res = (d.get("chart") or {}).get("result")
    if not res: raise SystemExit(f"error: no data for {sym} — check the symbol with `resolve`")
    r = res[0]; q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    rows = []
    for i, ts in enumerate(r.get("timestamp") or []):
        c = q["close"][i]
        if c is None: continue
        rows.append({"date": dt.datetime.fromtimestamp(ts, IST).date().isoformat(),
                     "open": _r(q["open"][i]), "high": _r(q["high"][i]), "low": _r(q["low"][i]), "close": round(c, 2),
                     "adj_close": round(adj[i], 2) if adj and adj[i] is not None else None,
                     "volume": q["volume"][i]})
    ev = r.get("events") or {}
    splits = [{"date": dt.datetime.fromtimestamp(int(k), IST).date().isoformat(), "ratio": f"{v['numerator']}:{v['denominator']}"}
              for k, v in sorted((ev.get("splits") or {}).items())]
    divs = [{"date": dt.datetime.fromtimestamp(int(k), IST).date().isoformat(), "amount": v["amount"]}
            for k, v in sorted((ev.get("dividends") or {}).items())]
    return r["meta"], rows, splits, divs

# ---------- calendar ----------
def _hol():
    return json.load(open(HOLIDAYS))

def day_status(d):
    h = _hol(); y = h["years"].get(str(d.year))
    for s in (y or {}).get("special_sessions", []):
        if s["date"] == d.isoformat(): return "special", s["name"]
    if d.weekday() >= 5: return "closed", "weekend"
    if not y: return "unknown", f"NSE holiday list for {d.year} not loaded — weekends only"
    for x in y["holidays"]:
        if x["date"] == d.isoformat(): return "closed", x["name"]
    return "open", "trading day"

def next_session(d):
    for i in range(1, 15):
        n = d + dt.timedelta(days=i); st, _ = day_status(n)
        if st in ("open", "unknown"): return n
    return None

def cmd_market(a):
    now = dt.datetime.now(IST) if not a.date else dt.datetime.fromisoformat(a.date).replace(tzinfo=IST)
    d = now.date(); st, why = day_status(d); hrs = _hol()["hours_ist"]["normal"]
    t = now.strftime("%H:%M")
    if st == "open":
        state = "OPEN" if hrs[0] <= t < hrs[1] else ("PRE-MARKET" if t < hrs[0] else "CLOSED (after hours)")
    elif st == "special": state = f"SPECIAL SESSION: {why} (timing per NSE circular)"
    elif st == "unknown": state = "UNKNOWN — " + why
    else: state = f"CLOSED — {why}"
    out = {"now_ist": now.strftime("%Y-%m-%d %H:%M"), "state": state, "hours_ist": f"{hrs[0]}–{hrs[1]}",
           "next_trading_day": (next_session(d) or d).isoformat()}
    up = [x for x in _hol()["years"].get(str(d.year), {}).get("holidays", []) if x["date"] > d.isoformat()][:3]
    out["upcoming_holidays"] = up
    if not _hol()["years"].get(str(d.year + 1)) and d.month >= 11:
        out["warning"] = f"{d.year + 1} holiday list not loaded yet — add it to data/nse_holidays.json when NSE publishes it"
    print(json.dumps(out, indent=1, ensure_ascii=False))

# ---------- commands ----------
def cmd_resolve(a):
    d = _get(SEARCH.format(q=quote(a.query)), 24 * 60, f"s-{a.query}.json")
    # Yahoo's exchange code flips between NSI/NSE and BSE/BOM, so trust the symbol suffix.
    rows = [q for q in d.get("quotes", []) if q.get("symbol", "").endswith((".NS", ".BO")) or q.get("symbol", "").startswith("^")]
    funds = [q for q in rows if q.get("quoteType") == "MUTUALFUND"]
    rows = [q for q in rows if q.get("quoteType") != "MUTUALFUND"]
    if a.exchange: rows = [q for q in rows if q["symbol"].endswith({"nse": ".NS", "bse": ".BO"}[a.exchange])]
    if funds: print(f"note: {len(funds)} mutual fund result(s) hidden — use the artha-navigator skill for real NAVs", file=sys.stderr)
    if not rows: print("no NSE/BSE match — try the company's short name"); sys.exit(1)
    for q in rows:
        ex = "NSE" if q["symbol"].endswith(".NS") else "BSE" if q["symbol"].endswith(".BO") else "INDEX"
        print(f"{q['symbol']:<16} {ex:5} {q.get('quoteType',''):7} {q.get('longname') or q.get('shortname','')}")

def quote_one(sym):
    meta, rows, splits, _ = chart(sym, "1y", "1d")
    if len(rows) < 2: return {"symbol": sym, "error": "not enough data"}
    last, prev = rows[-1], rows[-2]
    hi = max(r["high"] for r in rows if r["high"]); lo = min(r["low"] for r in rows if r["low"])
    asof = dt.datetime.fromtimestamp(meta.get("regularMarketTime", 0), IST)
    age = (dt.datetime.now(IST) - asof).days
    o = {"symbol": sym, "name": meta.get("longName") or meta.get("shortName"), "currency": meta.get("currency"),
         "price": meta.get("regularMarketPrice", last["close"]), "prev_close": prev["close"],
         "change_pct": round((last["close"] / prev["close"] - 1) * 100, 2),
         "high_52w": round(hi, 2), "low_52w": round(lo, 2),
         "from_high_pct": round((last["close"] / hi - 1) * 100, 1),
         "as_of_ist": asof.strftime("%Y-%m-%d %H:%M"), "delayed": "~15 min (Yahoo)"}
    if splits and splits[-1]["date"] >= rows[0]["date"]:
        o["warning"] = f"split/bonus {splits[-1]['ratio']} on {splits[-1]['date']} — compare adjusted prices"
    if age > 5: o["stale"] = f"last price is {age} days old — suspended, delisted or wrong symbol?"
    return o

def cmd_quote(a):
    out = [quote_one(norm(s)) for s in a.symbols]
    if a.json: print(json.dumps(out, indent=1, ensure_ascii=False)); return
    for q in out:
        if "error" in q: print(q["symbol"], q["error"]); continue
        print(f"{q['symbol']:<14} {q['currency']} {q['price']:>10,.2f}  {q['change_pct']:+6.2f}%  52w {q['low_52w']:,.2f}–{q['high_52w']:,.2f} ({q['from_high_pct']:+.1f}% from high)  as of {q['as_of_ist']} IST"
              + (f"  ⚠ {q['warning']}" if q.get("warning") else "") + (f"  ⚠ {q['stale']}" if q.get("stale") else ""))

def cmd_history(a):
    meta, rows, splits, divs = chart(norm(a.symbol), a.range, a.interval)
    out = {"symbol": norm(a.symbol), "currency": meta.get("currency"), "candles": rows, "splits": splits, "dividends": divs}
    if a.out: json.dump(out, open(a.out, "w"), indent=1)
    if a.json: print(json.dumps(out, indent=1)); return
    print("date,open,high,low,close,adj_close,volume")
    for r in rows: print(",".join(str(r[k]) for k in ["date", "open", "high", "low", "close", "adj_close", "volume"]))
    for s in splits: print(f"# split/bonus {s['ratio']} on {s['date']}")

def on_or_before(rows, d):
    best = None
    for r in rows:
        if r["date"] <= d: best = r
        else: break
    return best

def fridays(weeks, today=None):
    t = today or dt.datetime.now(IST).date()
    f = t - dt.timedelta(days=(t.weekday() - 4) % 7)
    return [(f - dt.timedelta(days=7 * i)).isoformat() for i in range(weeks, -1, -1)]

def pct(x, y): return None if x is None or y is None else round((y / x - 1) * 100, 2)

def cmd_weekly(a):
    hold = json.load(open(a.holdings)); stocks = hold["stocks"] if isinstance(hold, dict) else hold
    dates = fridays(a.weeks); series, warn, used = [], [], []
    for s in stocks:
        sym = norm(s["symbol"]); _, rows, splits, _ = chart(sym, "2y", "1d")
        recent = [x for x in splits if x["date"] >= dates[0]]
        if recent: warn.append(f"{sym}: split/bonus {recent[-1]['ratio']} on {recent[-1]['date']} inside the window — using adjusted closes")
        key = "adj_close" if recent else "close"
        closes = [(on_or_before(rows, d) or {}).get(key) for d in dates]
        held = [(on_or_before(rows, d) or {}).get("date") for d in dates]
        hol = [d for d, h in zip(dates, held) if h and h != d]
        if hol: warn.append(f"{sym}: no trading on {', '.join(hol[-3:])} (holiday) — used the previous close")
        units = s.get("units") or s["value"] / closes[-1]
        series.append((units, closes)); used.append({"symbol": sym, "units": round(units, 4)})
    n = len(dates)
    tot = [None if any(c[i] is None for _, c in series) else sum(u * c[i] for u, c in series) for i in range(n)]
    out = {"dates": dates, "value": [round(x) if x else None for x in tot], "wow": [None] + [pct(tot[i-1], tot[i]) for i in range(1, n)],
           "idx": [round(x / tot[0] * 100, 2) if x and tot[0] else None for x in tot], "stocks": used, "warnings": sorted(set(warn)),
           "method": "Current units at each Friday close (previous trading day if Friday was a holiday). Prices delayed ~15 min."}
    if a.benchmark:
        _, b, _, _ = chart(norm(a.benchmark), "2y", "1d"); bv = [(on_or_before(b, d) or {}).get("close") for d in dates]
        out.update(benchmark=a.benchmark, bwow=[None] + [pct(bv[i-1], bv[i]) for i in range(1, n)],
                   bidx=[round(x / bv[0] * 100, 2) if x and bv[0] else None for x in bv])
        out["summary"] = {"ret": round(out["idx"][-1] - 100, 2), "bret": round(out["bidx"][-1] - 100, 2),
                          "beat_weeks": sum(1 for x, y in zip(out["wow"][1:], out["bwow"][1:]) if x is not None and y is not None and x > y)}
    if a.out: json.dump(out, open(a.out, "w"), indent=1)
    if a.json: print(json.dumps(out, indent=1)); return
    print(f"{'week ending':12s} {'value':>12s} {'you':>7s}" + (f" {a.benchmark:>9s}" if a.benchmark else ""))
    for i, d in enumerate(dates):
        print(f"{d:12s} {('₹{:,}'.format(out['value'][i])) if out['value'][i] else '—':>12s} {('%+.2f' % out['wow'][i]) if out['wow'][i] is not None else '':>7s}"
              + (f" {('%+.2f' % out['bwow'][i]) if out['bwow'][i] is not None else '':>9s}" if a.benchmark else ""))
    if a.benchmark:
        s = out["summary"]; print(f"\n{a.weeks} weeks: you {s['ret']:+.2f}% vs {a.benchmark} {s['bret']:+.2f}% · beat it in {s['beat_weeks']} of {a.weeks} weeks")
    for w in out["warnings"]: print("⚠", w)

def main():
    p = argparse.ArgumentParser(description="NSE/BSE prices, history and market calendar.")
    sp = p.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("resolve"); x.add_argument("query"); x.add_argument("--exchange", choices=["nse", "bse"]); x.set_defaults(f=cmd_resolve)
    x = sp.add_parser("quote"); x.add_argument("symbols", nargs="+"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_quote)
    x = sp.add_parser("history"); x.add_argument("symbol"); x.add_argument("--range", default="1y"); x.add_argument("--interval", default="1d", choices=["1d", "1wk", "1mo"])
    x.add_argument("--out"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_history)
    x = sp.add_parser("weekly"); x.add_argument("holdings"); x.add_argument("--weeks", type=int, default=12); x.add_argument("--benchmark")
    x.add_argument("--out"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_weekly)
    x = sp.add_parser("market"); x.add_argument("--date", help="ISO datetime in IST, e.g. 2026-11-10T10:00"); x.set_defaults(f=cmd_market)
    a = p.parse_args(); a.f(a)

if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
