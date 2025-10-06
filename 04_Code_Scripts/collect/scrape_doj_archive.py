# 04_Code_Scripts/collect/scrape_doj_archive.py
# -*- coding: utf-8 -*-
import argparse
from .scrape_press_generic import run_site, write_csv

# DOJ — archives Press Releases (50 items/page, ?page=)
BASE = "https://www.justice.gov/archives/press-releases-archive?items_per_page=50"
LIST_SEL = ".view-content .views-row .node__title a, .view-content .views-row a[href^='/archives/']"
DATE_SEL = "time[datetime], .date, .published-date, meta[name='date'], meta[property='article:published_time']"
CONTENT_SEL = "article, main, .pane-node-content, .content"

def main():
    p = argparse.ArgumentParser(prog="python -m collect.scrape_doj_archive",
        description="Scrape DOJ Press Releases archive (HTML).")
    p.add_argument("actor_id"); p.add_argument("country"); p.add_argument("domain_id")
    p.add_argument("period"); p.add_argument("since"); p.add_argument("until")
    p.add_argument("count", type=int)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--start-page", type=int, default=0)   # ~25–30 ≈ mars 2021 (ajuste après 1er essai)
    p.add_argument("--max-pages", type=int, default=3)    # augmente à ~80 en prod
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
