# -*- coding: utf-8 -*-
"""
enrich_congress_from_govinfo.py

But
----
Enrichit les lignes "Congressional Record" (issues) en suivant l'URL publique
congress.gov -> lien PDF govinfo -> extraction texte (pdfminer) -> filtrage par
taille/nb tokens -> réécrit un CSV conforme au schéma PoC.

Entrée : CSV avec colonnes
  actor_id,country,domain_id,period,date,url,language,text,tokens

Sortie : même schéma, mais:
  - url = URL publique (congress.gov)
  - text = texte long extrait du PDF (si trouvé), ou titre fallback
  - tokens = recompté à partir du texte long

Seuils contrôlables par env:
  CONGRESS_MIN_TOKENS  (int, défaut 0)
  CONGRESS_PDF_MAX_MB  (float, défaut 25.0)
  CONGRESS_UA          (str,   défaut "Axiodynamics-POC/1.0 (+research)")

Usage
-----
python 04_Code_Scripts\collect\enrich_congress_from_govinfo.py input.csv [output.csv]

- Si output.csv est omis : overwrite en place (écriture atomique via .tmp puis remplacement).
"""

from __future__ import annotations
import os, sys, csv, re, io, time, shutil
from typing import Tuple, List, Dict, Any, Optional

import requests
import csv, sys  # (si pas déjà importés tout en haut)
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text


UA = os.environ.get("CONGRESS_UA", "Axiodynamics-POC/1.0 (+research)")
HDRS = {"User-Agent": UA}
MIN_TOK = int(os.environ.get("CONGRESS_MIN_TOKENS", "0") or "0")
PDF_MAX_MB = float(os.environ.get("CONGRESS_PDF_MAX_MB", "25") or "25")

def _bump_csv_limit():
    # Monte la limite CSV au maximum supporté par la plateforme
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = max_int // 10  # réduit jusqu'à passer


def _tokens_count(txt: str) -> int:
    return len(re.findall(r"\w+", txt or ""))

def _to_public_url(api_url: str) -> str:
    """
    Transforme une URL API → URL publique congress.gov
    Ex. https://api.congress.gov/v3/congressional-record/26532?format=json
        → https://www.congress.gov/congressional-record/26532
    Sinon retourne tel quel si déjà public.
    """
    if not api_url:
        return ""
    if "api.congress.gov" in api_url and "/congressional-record/" in api_url:
        m = re.search(r"/congressional-record/(\d+)", api_url)
        if m:
            rec_id = m.group(1)
            return f"https://www.congress.gov/congressional-record/{rec_id}"
    return api_url

def _http_get(url: str, allow_redirects: bool = True, timeout: int = 60) -> requests.Response:
    return requests.get(url, headers=HDRS, allow_redirects=allow_redirects, timeout=timeout)

def _find_pdf_url_from_public_page(public_url: str) -> str:
    """
    Ouvre la page congress.gov et tente d’extraire un lien PDF (.pdf),
    idéalement un lien govinfo.gov.
    """
    try:
        r = _http_get(public_url)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "lxml")
        # 1) Un lien dont le texte contient 'PDF'
        a = soup.find("a", string=lambda s: isinstance(s, str) and "pdf" in s.lower())
        if a and a.get("href"):
            href = a["href"]
            if href.startswith("//"): href = "https:" + href
            if href.startswith("/"):  href = "https://www.congress.gov" + href
            return href

        # 2) Tout lien .pdf (préférence govinfo)
        pdfs = []
        for a in soup.find_all("a", href=True):
            h = a["href"]
            if ".pdf" in h.lower():
                if h.startswith("//"): h = "https:" + h
                if h.startswith("/"):  h = "https://www.congress.gov" + h
                pdfs.append(h)
        if not pdfs:
            return ""
        # Priorité aux pdf govinfo
        govinfo = [h for h in pdfs if "govinfo" in h.lower()]
        return govinfo[0] if govinfo else pdfs[0]
    except Exception:
        return ""

def _download_pdf(url: str) -> Optional[bytes]:
    try:
        r = _http_get(url)
        if r.status_code != 200:
            return None
        return r.content
    except Exception:
        return None

def _extract_text_from_pdf_bytes(b: bytes) -> str:
    try:
        with io.BytesIO(b) as bio:
            txt = extract_text(bio)
        # Nettoyage léger
        txt = re.sub(r"\s+", " ", txt or "").strip()
        return txt
    except Exception:
        return ""

def _enrich_row(row: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Tente d’enrichir UNE ligne issue (Congressional Record) :
      - URL publique
      - PDF → texte long
      - Filtrage par taille/tokens
    Retourne la ligne enrichie ou None si rejetée.
    """
    api_url = (row.get("url") or "").strip()
    title   = (row.get("text") or "").strip()

    public_url = _to_public_url(api_url)
    if not public_url:
        # fallback : garder la ligne si titre assez long (peu probable)
        if _tokens_count(title) >= MIN_TOK:
            row["url"] = api_url
            row["text"] = title
            row["tokens"] = str(_tokens_count(title))
            return row
        return None

    pdf_url = _find_pdf_url_from_public_page(public_url)
    if not pdf_url:
        # pas de PDF → garder titre si assez long
        if _tokens_count(title) >= MIN_TOK:
            row["url"] = public_url
            row["text"] = title
            row["tokens"] = str(_tokens_count(title))
            return row
        return None

    b = _download_pdf(pdf_url)
    if not b:
        # fallback titre
        if _tokens_count(title) >= MIN_TOK:
            row["url"] = public_url
            row["text"] = title
            row["tokens"] = str(_tokens_count(title))
            return row
        return None

    size_mb = len(b) / 1e6
    if size_mb > PDF_MAX_MB:
        # trop gros → fallback titre
        if _tokens_count(title) >= MIN_TOK:
            row["url"] = public_url
            row["text"] = title
            row["tokens"] = str(_tokens_count(title))
            return row
        return None

    txt = _extract_text_from_pdf_bytes(b)
    if _tokens_count(txt) < MIN_TOK:
        # texte trop court → fallback titre si possible
        if _tokens_count(title) >= MIN_TOK:
            row["url"] = public_url
            row["text"] = title
            row["tokens"] = str(_tokens_count(title))
            return row
        return None

    # Enrichissement réussi
    row["url"] = public_url
    row["language"] = row.get("language") or "EN"
    row["text"] = txt
    row["tokens"] = str(_tokens_count(txt))
    return row

def _read_rows(path: str) -> List[Dict[str,str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd)

def _write_rows(path: str, rows: List[Dict[str,str]], fieldnames: List[str]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fieldnames)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r.get(k, "") for k in fieldnames})
    shutil.move(tmp, path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python enrich_congress_from_govinfo.py input.csv [output.csv]", file=sys.stderr)
        sys.exit(2)
    inp = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) >= 3 else inp
    
    _bump_csv_limit()

    rows_in = _read_rows(inp)
    if not rows_in:
        print(f"[WARN] Empty or header-only: {inp}")
        # crée quand même une sortie vide avec header si in-place
        _write_rows(outp, [], ["actor_id","country","domain_id","period","date","url","language","text","tokens"])
        return

    kept: List[Dict[str,str]] = []
    seen = 0

    # “Jauge” discrète
    total = len(rows_in)
    print(f"[ENRICH] {inp}  total={total}  (MIN_TOKENS={MIN_TOK}, MAX_MB={PDF_MAX_MB})")
    for i, row in enumerate(rows_in, 1):
        seen += 1
        enriched = _enrich_row(dict(row))
        if enriched:
            kept.append(enriched)

        # jauge : un tick tous les 1 éléments au début, puis 5, 10…
        if i <= 10 or i % 5 == 0:
            # affiche une info compacte sans spammer
            dt = row.get("date","")
            print(f"  [{i}/{total}] seen={seen} kept={len(kept)} last_date={dt}")

    # champs normalisés (schéma PoC)
    fields = ["actor_id","country","domain_id","period","date","url","language","text","tokens"]
    _write_rows(outp, kept, fields)

    print(f"[OK] Enriched: {outp}  kept={len(kept)} / seen={seen}  (MIN_TOKENS={MIN_TOK}, MAX_MB={PDF_MAX_MB})")

if __name__ == "__main__":
    main()
