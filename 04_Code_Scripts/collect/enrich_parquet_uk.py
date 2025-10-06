# -*- coding: utf-8 -*-
import os, sys, time, re, io
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp

USER_AGENT = os.environ.get("SCRAPER_USER_AGENT","Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
TIMEOUT    = int(os.environ.get("SCRAPER_TIMEOUT_S","20"))
PDF_MAX_MB = int(os.environ.get("PDF_MAX_MB","30"))
TARGETS = {"UK_HomeOffice","UK_MoD"}

def clean_text(s: str) -> str:
    return re.sub(r"\s+"," ", (s or "").strip())

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # zones GOV.UK fréquentes
    article = (soup.select_one(".gem-c-govspeak") or
               soup.select_one(".govuk-grid-column-two-thirds") or
               soup.select_one(".govuk-main-wrapper") or
               soup.select_one("main") or soup)
    # enlever chrome / méta
    for sel in [
        "nav","aside","footer","script","style","form","header",
        ".gem-c-metadata",".gem-c-title",".gem-c-title__context",
        ".gem-c-breadcrumbs",".govuk-breadcrumbs",".gem-c-social-media-links",
        ".gem-c-contextual-breadcrumbs",".gem-c-related-navigation",
        ".app-c-published-dates",".print-link",".gem-c-contents-list"
    ]:
        for n in article.select(sel): n.decompose()
    parts=[]
    for tag in article.find_all(["h1","h2","h3","p","li","blockquote","figcaption"]):
        txt = clean_text(tag.get_text(" "))
        if txt: parts.append(txt)
    return clean_text(" ".join(parts))

def fetch(url: str) -> requests.Response:
    return requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True)

def extract_pdf_text_from_url(pdf_url: str) -> str:
    r = fetch(pdf_url)
    r.raise_for_status()
    size_mb = len(r.content) / (1024*1024)
    if size_mb > PDF_MAX_MB:
        raise RuntimeError(f"PDF too large ({size_mb:.1f} MB > {PDF_MAX_MB} MB)")
    out = io.StringIO()
    extract_text_to_fp(io.BytesIO(r.content), out)  # pdfminer
    return clean_text(out.getvalue())

def find_pdf_on_page(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    # Attachments GOV.UK : .gem-c-attachment, .attachment, ou simple lien .pdf
    for sel in ["a[href$='.pdf']", ".gem-c-attachment a[href$='.pdf']", ".attachment a[href$='.pdf']"]:
        a = soup.select_one(sel)
        if a and a.get("href"):
            href = a["href"]
            if href.startswith("//"): return "https:" + href
            if href.startswith("http"): return href
            # relatif
            from urllib.parse import urljoin
            return urljoin(base_url, href)
    return None

def extract_best_text(url: str) -> tuple[str,int]:
    # 1) HTML
    r = fetch(url); r.raise_for_status()
    html_text = html_to_text(r.text)
    tokens_html = len(html_text.split())
    # 2) Fallback PDF si court
    if tokens_html < 800:
        pdf_url = find_pdf_on_page(r.text, url)
        if pdf_url:
            try:
                pdf_text = extract_pdf_text_from_url(pdf_url)
                tokens_pdf = len(pdf_text.split())
                if tokens_pdf > tokens_html:
                    return pdf_text, tokens_pdf
            except Exception as e:
                print(f"[pdf-fail] {pdf_url} :: {e}")
    return html_text, tokens_html

def main():
    in_path = os.path.join("artifacts","real","corpus_final.parquet")
    bak     = in_path + ".bak"
    out_path= in_path

    print("Loading:", in_path)
    df = pd.read_parquet(in_path)
    mask = df["actor_id"].isin(TARGETS)
    sub  = df.loc[mask].copy()
    print("UK rows:", len(sub))

    # enrichir si tokens < 800 (suspect court)
    need_idx = sub[(~sub["url"].isna()) & (sub["tokens"].fillna(0) < 800)].index.tolist()
    print("Rows to enrich:", len(need_idx))

    updated = 0
    for idx in need_idx:
        url = df.at[idx,"url"]
        try:
            text, tok = extract_best_text(url)
            df.at[idx,"text"]   = text
            df.at[idx,"tokens"] = tok
            updated += 1
            print(f"[ok] tokens={tok} :: {url}")
        except Exception as e:
            print(f"[fail] {url} :: {e}")
        time.sleep(0.4)

    print("Updated:", updated)
    if updated > 0:
        if os.path.exists(bak):
            os.remove(bak)
        os.replace(in_path, bak)
        df.to_parquet(out_path, index=False)
        print("Wrote:", out_path, "(backup:", bak, ")")
    else:
        print("No change; leaving original file as-is.")

if __name__ == "__main__":
    main()
