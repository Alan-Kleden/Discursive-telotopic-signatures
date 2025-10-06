# 04_Code_Scripts/collect/scrape_dhs_archive.py
# -*- coding: utf-8 -*-
import argparse
from .scrape_press_generic import run_site, write_csv

# DHS — archive 2021, Press Releases (paginé par ?page=)
BASE = "https://www.dhs.gov/archive/news?year=2021&news_type=Press%20Releases&items_per_page=50"
LIST_SEL = ".view-content .views-row a[href^='/archive/news/2021/']"
DATE_SEL = "time[datetime], meta[property='article:published_time'], meta[name='date']"
CONTENT_SEL = "article, main, .region-content"

def main():
    p = argparse.ArgumentParser(prog="python -m collect.scrape_dhs_archive",
        description="Scrape DHS 2021 Press Releases (archive HTML, server-side pagination).")
    p.add_argument("actor_id"); p.add_argument("country"); p.add_argument("domain_id")
    p.add_argument("period"); p.add_argument("since"); p.add_argument("until")
    p.add_argument("count", type=int)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--start-page", type=int, default=0)   # vise ~42–45 pour mars 2021
    p.add_argument("--max-pages", type=int, default=3)    # augmente à ~60 en prod
    args = p.parse_args()

    rows = run_site(
        args.actor_id, args.country, args.domain_id, args.period,
        args.since, args.until, args.count,
        base_url=BASE, list_sel=LIST_SEL,
        date_sel=DATE_SEL, date_attr=None, content_sel=CONTENT_SEL,
        paginate_mode="query", max_pages=args.max_pages, debug=args.debug,
        start_page=args.start_page
    )
    out = write_csv(rows, args.actor_id, args.period, args.since)
    print(f"Wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()
