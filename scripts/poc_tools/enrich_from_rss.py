# coding: utf-8
"""
enrich_from_rss.py — lit rss_items_*.csv, télécharge chaque URL, extrait un plein-texte propre
et ajoute source_domain,country,actor_id. Écrit lot_raw_YYYYMMDD_HHMM.csv.
Dépendances: requests, bs4 (BeautifulSoup). Si bs4 absent, extraction fallback simple.
"""
import sys, csv, re, time
from urllib.parse import urlparse
import requests

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

csv.field_size_limit(10_000_000)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AxioPoC/1.0; +https://example.org)"
}
TIMEOUT = 20

def hostname(u:str)->str:
    try:
        return (urlparse(u).hostname or "").lower()
    except Exception:
        return ""

def country_from_host(h:str)->str:
    if re.search(r"\.uk$|guardian|telegraph|spectator|unherd|newstatesman|ft\.com|economist\.com", h): return "UK"
    return "US"

def clean_text_html(html:str)->str:
    if not html:
        return ""
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        # supprimer chrome / nav
        for sel in ["header","nav","footer","aside","form","script","style","noscript","figure","figcaption","iframe"]:
            for t in soup.find_all(sel):
                t.decompose()
        # supprimer éléments denses en liens
        for a in soup.find_all("a"):
            a.unwrap()
        # récupérer principaux blocs <article> sinon <main> sinon <div>
        art = soup.find("article")
        if not art:
            art = soup.find("main") or soup
        # concaténer les paragraphes
        parts = []
        for p in art.find_all(["p","h2","h3","li"]):
            txt = (p.get_text(" ", strip=True) or "")
            if len(txt) >= 20:
                parts.append(txt)
        text = " ".join(parts)
    else:
        # fallback brut si bs4 non dispo
        text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
    # heuristique: retirer les 10–15 premiers mots souvent “chrome”
    words = text.split()
    if len(words) > 40:
        text = " ".join(words[12:])
    return text

def fetch(url:str)->str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 200 and r.status_code < 400 and r.text:
            return r.text
    except Exception:
        return ""
    return ""

def run(src_csv:str, dst_csv:str):
    fields_out = ["actor_id","country","domain_id","period","date","title","url","text","tokens","source",
                  "source_domain"]
    n_ok = n_all = 0
    with open(src_csv, encoding="utf-8") as fin, open(dst_csv, "w", encoding="utf-8", newline="") as fout:
        rdr = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=fields_out)
        w.writeheader()
        for r in rdr:
            n_all += 1
            url = (r.get("url") or "").strip()
            if not url:
                continue
            host = hostname(url)
            html = fetch(url)
            text = clean_text_html(html)
            tokens = len(text.split())
            out = {
                "actor_id": r.get("actor_id","") or "MIX_MISC",
                "country": r.get("country","") or country_from_host(host),
                "domain_id": r.get("domain_id","") or "mix",
                "period": r.get("period","") or "T1",
                "date": r.get("date",""),
                "title": r.get("title",""),
                "url": url,
                "text": text,
                "tokens": str(tokens),
                "source": r.get("source","rss") or "rss",
                "source_domain": host
            }
            if tokens >= 120:  # garde-fou minimal
                w.writerow(out); n_ok += 1
            else:
                # on écrit quand même pour audit, mais utilisable en aval seulement si make_excerpts y arrive
                w.writerow(out)
            time.sleep(0.3)  # politesse minimale
    print(f"OK enrich: {n_ok}/{n_all} textes >=120 tokens -> {dst_csv}")

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    run(src, dst)
