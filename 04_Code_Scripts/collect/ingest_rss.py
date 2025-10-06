# -*- coding: utf-8 -*-
"""
collect.ingest_rss
Usage:
  python -m collect.ingest_rss <actor_id> <country> <domain_id> <period> <since> <until> <count> --feed URL [--feed URL ...] [--debug]

Ex:
  python -m collect.ingest_rss US_DOJ_SDNY US doj T1 2021-03-01 2021-03-31 5 --feed "https://..."
"""
import argparse, csv, os, sys, re, time, datetime as dt
from typing import List, Dict
try:
    import feedparser
except Exception as e:
    print("Missing dependency: feedparser. Install with: pip install feedparser", file=sys.stderr)
    raise

DEF_OUT_DIR = os.path.join("data", "us_press")
os.makedirs(DEF_OUT_DIR, exist_ok=True)

def parse_date(entry) -> dt.date | None:
    # Try common fields
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, key, None) or entry.get(key)
        if val:
            try:
                return dt.date(val.tm_year, val.tm_mon, val.tm_mday)
            except Exception:
                pass
    # Fallback: try to parse 'published'/'updated' strings yyyy-mm-dd
    for key in ("published", "updated", "created"):
        s = entry.get(key)
        if s:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
            if m:
                y, mth, d = map(int, m.groups())
                try:
                    return dt.date(y, mth, d)
                except Exception:
                    pass
    return None

def within(d: dt.date, since: dt.date, until: dt.date) -> bool:
    return (d >= since) and (d <= until)

def monthstamp(since: dt.date) -> str:
    return f"{since.year:04d}{since.month:02d}"

def write_csv(rows: List[Dict], actor_id: str, period: str, since: dt.date) -> str:
    out = os.path.join(DEF_OUT_DIR, f"{actor_id}_{period}_{monthstamp(since)}.csv")
    # Schéma minimal PoC (compatible avec vos autres scripts)
    cols = ["actor_id","country","domain_id","period","date","title","url","text","tokens","source"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    return out

def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m collect.ingest_rss", description="Ingest RSS feeds into PoC CSV schema.")
    p.add_argument("actor_id"); p.add_argument("country"); p.add_argument("domain_id")
    p.add_argument("period"); p.add_argument("since"); p.add_argument("until"); p.add_argument("count", type=int)
    p.add_argument("--feed", action="append", required=True, help="RSS feed URL (repeatable)")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args(argv)

    since = dt.datetime.strptime(args.since, "%Y-%m-%d").date()
    until = dt.datetime.strptime(args.until, "%Y-%m-%d").date()

    kept, seen = [], set()
    for feed_url in args.feed:
        if args.debug:
            print(f"[rss] feed='{feed_url}' ...", flush=True)
        d = feedparser.parse(feed_url)
        status = getattr(d, "status", None) or d.get("status")
        entries = getattr(d, "entries", []) or d.get("entries", [])
        if args.debug:
            print(f"[rss] status={status} entries={len(entries)}", flush=True)

        for e in entries:
            if len(kept) >= args.count:
                break
            url = e.get("link") or e.get("id") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            dd = parse_date(e)
            if dd is None:
                if args.debug:
                    print(f"[no_date] {url}")
                continue
            if not within(dd, since, until):
                if args.debug:
                    print(f"[out] {dd} {url}")
                continue
            title = (e.get("title") or "").strip()
            kept.append({
                "actor_id": args.actor_id,
                "country": args.country,
                "domain_id": args.domain_id,
                "period": args.period,
                "date": dd.isoformat(),
                "title": title,
                "url": url,
                "text": "",          # pas d'extraction plein texte depuis RSS à ce stade
                "tokens": 0,
                "source": "rss"
            })
            if args.debug:
                print(f"[keep] {dd} {url}")

    out = write_csv(kept, args.actor_id, args.period, since)
    if args.debug:
        print(f"[summary] feeds={len(args.feed)} kept={len(kept)} -> {out}")
    else:
        print(f"Wrote {len(kept)} rows -> {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
