#!/usr/bin/env python3
"""artha-pulse: what happened to NSE-listed companies — official NSE announcements first,
then Google News (India) headlines that actually name the company. Stdlib only."""
import argparse, datetime as dt, email.utils, html, json, os, re, sys, time, urllib.request
from http.cookiejar import CookieJar
from urllib.parse import quote

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
NSE = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={s}"
GN = "https://news.google.com/rss/search?q={q}+when:{d}d&hl=en-IN&gl=IN&ceid=IN:en"
YS = "https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=3&newsCount=0"
CACHE = os.environ.get("NEWS_CACHE", os.path.join(os.getcwd(), ".news-cache"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

NOISE_TITLE = re.compile(r"share price (today|live)|stock price (today|live)|live updates|stocks to (buy|watch)|top (gainers|losers)|market (live|today|wrap)|sensex|nifty (today|live)", re.I)
LOW_VALUE_NSE = re.compile(r"trading window|newspaper publication|loss of share certificate|duplicate share|investor complaints|compliance certificate|regulation 74|change in rta|shareholding pattern|certificate under", re.I)
KINDS = [("credit rating", r"credit rating"), ("results", r"\bresults?\b|q[1-4]\b|quarter|earnings|profit|revenue"), ("dividend", r"dividend|record date|bonus|split"),
         ("broker view", r"\btarget\b|buy |sell |hold |downgrade|upgrade|rating"), ("order/deal", r"\border\b|contract|acquisition|acquire|stake|merger|agreement|deal"),
         ("management", r"\bceo\b|\bcfo\b|director|resign|appoint"), ("regulatory", r"sebi|penalty|tax demand|notice|litigation|court|gst"),
         ("funding", r"qip|rights issue|preferential|fund ?rais|ncd|debenture"), ("investor meet", r"investor meet|analyst|con\. call|conference call")]

PRIORITY = {"results": 0, "dividend": 0, "order/deal": 1, "regulatory": 1, "funding": 1, "management": 2, "credit rating": 2,
            "broker view": 3, "other": 4, "investor meet": 5}
ROUTINE = {"investor meet"}          # collapsed into a count: schedules, outcomes, transcripts, recordings

def kind_of(t):
    for k, p in KINDS:
        if re.search(p, t, re.I): return k
    return "other"

def fetch(url, name, ttl_min=60, opener=None, headers=None):
    os.makedirs(CACHE, exist_ok=True); path = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", name)[:120])
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_min * 60: return open(path, encoding="utf-8").read()
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with (opener or urllib.request.build_opener()).open(req, timeout=25) as r: txt = r.read().decode("utf-8", "replace")
    open(path, "w", encoding="utf-8").write(txt); time.sleep(0.4); return txt

def company_name(sym):
    try:
        q = json.loads(fetch(YS.format(q=quote(sym)), f"ys-{sym}.json", 24 * 60)).get("quotes", [])
        n = next((x.get("longname") or x.get("shortname") for x in q if x.get("symbol", "").upper() in (sym + ".NS", sym + ".BO")), None)
    except Exception: n = None
    return n or sym

def short_name(name):
    n = re.sub(r"\b(limited|ltd\.?|india|industries|corporation|corp|company|co\.?)\b", " ", name, flags=re.I)
    toks = [t for t in re.split(r"\W+", n) if len(t) > 1]
    return " ".join(toks[:2]) if toks else name

def nse_items(sym, since):
    jar = CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        try: op.open(urllib.request.Request("https://www.nseindia.com/", headers={"User-Agent": UA}), timeout=15)
        except Exception: pass                          # homepage often 403s; the API usually still answers
        raw = json.loads(fetch(NSE.format(s=quote(sym)), f"nse-{sym}.json", 60, op, {"Referer": "https://www.nseindia.com/", "Accept": "application/json"}))
    except Exception as e:
        return None, f"NSE announcements unavailable ({type(e).__name__})"
    out = []
    for a in raw if isinstance(raw, list) else raw.get("data", []):
        try: when = dt.datetime.strptime(a["an_dt"], "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)
        except Exception: continue
        if when.date() < since: continue
        desc = a.get("desc") or ""; text = (a.get("attchmntText") or "").strip()
        if LOW_VALUE_NSE.search(desc + " " + text): continue
        out.append({"symbol": sym, "date": when.date().isoformat(), "title": f"{desc}: {text}"[:220], "source": "NSE filing",
                    "link": a.get("attchmntFile"), "kind": kind_of(desc + " " + text), "official": True})
    return out, None

def gn_items(sym, name, days, since):
    short = short_name(name)
    try: x = fetch(GN.format(q=quote(f'"{short}"'), d=days), f"gn-{sym}-{days}.xml", 60)
    except Exception as e: return [], f"Google News unavailable ({type(e).__name__})"
    out, seen = [], set()
    for it in re.findall(r"<item>(.*?)</item>", x, re.S):
        t = html.unescape(re.sub(r"<.*?>", "", re.search(r"<title>(.*?)</title>", it, re.S).group(1))).strip()
        src = re.search(r"<source[^>]*>(.*?)</source>", it); src = html.unescape(src.group(1)) if src else ""
        t = re.sub(r"\s+-\s+" + re.escape(src) + r"$", "", t) if src else t
        when = email.utils.parsedate_to_datetime(re.search(r"<pubDate>(.*?)</pubDate>", it).group(1)).astimezone(IST).date()
        if when < since or NOISE_TITLE.search(t): continue
        if short.split()[0].lower() not in t.lower(): continue          # must name the company
        key = re.sub(r"\W+", "", t.lower())[:60]
        if key in seen: continue
        seen.add(key)
        out.append({"symbol": sym, "date": when.isoformat(), "title": t[:220], "source": src or "Google News",
                    "link": html.unescape(re.search(r"<link>(.*?)</link>", it, re.S).group(1)).strip(), "kind": kind_of(t), "official": False})
    return out, None

def main():
    p = argparse.ArgumentParser(description="News and official announcements for NSE-listed companies.")
    p.add_argument("symbols", nargs="+", help="NSE symbols, e.g. INFY RELIANCE")
    p.add_argument("--days", type=int, default=7); p.add_argument("--max-per-symbol", type=int, default=6)
    p.add_argument("--state", help="JSON file of item keys already shown; only new items are returned and the file is updated")
    p.add_argument("--no-broker-calls", action="store_true", help="drop brokerage buy/sell/target headlines")
    p.add_argument("--out"); p.add_argument("--json", action="store_true"); a = p.parse_args()
    since = dt.datetime.now(IST).date() - dt.timedelta(days=a.days)
    seen = set(json.load(open(a.state))) if a.state and os.path.exists(a.state) else set()
    result, notes = [], []
    for raw in a.symbols:
        sym = raw.upper().replace(".NS", ""); name = company_name(sym)
        off, e1 = nse_items(sym, since); heads, e2 = gn_items(sym, name, a.days, since)
        for e in (e1, e2):
            if e: notes.append(f"{sym}: {e}")
        items = (off or []) + heads
        if a.no_broker_calls: items = [i for i in items if i["kind"] != "broker view"]
        routine = [i for i in items if i["kind"] in ROUTINE]
        items = [i for i in items if i["kind"] not in ROUTINE]
        items.sort(key=lambda i: (PRIORITY.get(i["kind"], 4), not i["official"], -int(i["date"].replace("-", ""))))
        off_keep = [i for i in items if i["official"]][: max(1, a.max_per_symbol - 2)]
        head_keep = [i for i in items if not i["official"]][: a.max_per_symbol - len(off_keep)]
        items = sorted(off_keep + head_keep, key=lambda i: (PRIORITY.get(i["kind"], 4), -int(i["date"].replace("-", ""))))
        new = [i for i in items if f"{i['symbol']}|{i['title'][:80]}" not in seen]
        result.append({"symbol": sym, "company": name, "items": new, "official_count": sum(1 for i in new if i["official"]),
                       "routine_filings": len(routine)})
        seen.update(f"{i['symbol']}|{i['title'][:80]}" for i in new)
    if a.state: json.dump(sorted(seen), open(a.state, "w"))
    out = {"since": since.isoformat(), "companies": result, "notes": notes,
           "method": "NSE corporate announcements (official) first, then Google News India headlines that name the company; price-ticker pages and routine compliance filings dropped."}
    if a.out: json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    if a.json: print(json.dumps(out, indent=1, ensure_ascii=False)); return
    for c in result:
        print(f"\n{c['symbol']} — {c['company']}  ({len(c['items'])} items, {c['official_count']} official)")
        for i in c["items"]: print(f"  {i['date']}  [{i['kind']}]{' 🏛' if i['official'] else ''} {i['title']}  — {i['source']}")
        if not c["items"]: print("  nothing new")
        if c["routine_filings"]: print(f"  + {c['routine_filings']} routine investor-meet filings (schedules, outcomes, transcripts)")
    for n in notes: print("⚠", n)

if __name__ == "__main__":
    main()
