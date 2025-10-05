# -*- coding: utf-8 -*-
"""
US Congress collector (Congress.gov v3) — OFFSET pagination + HTML & PDF enrichment (no-regression)

- Source principale : endpoint "congressional-record" paginé par OFFSET (stable pour remonter dans le temps).
- Fenêtre stricte [date_start .. date_end].
- Enrichissement par page publique :
    1) HTML (BeautifulSoup) → texte ; sinon
    2) PDF (pdfminer.six) si un lien .pdf est présent → texte intégral.

- Filtre confirmatory via env CONGRESS_MIN_TOKENS (par ex. 800).
  * Si non défini (=0), on garde le comportement historique (écrit même si texte court, fallback=title).
  * Zéro régression.

ENV (optionnels)
---------------
CONGRESS_API_KEY      : clé API Congress (utile pour quotas).
CONGRESS_MIN_TOKENS   : seuil minimal de tokens (défaut 0).
CONGRESS_PAGE_SIZE    : taille page offset (défaut 20).
CONGRESS_MAX_OFFSET   : offset max (défaut 2000).
CONGRESS_PDF_MAX_MB   : taille max PDF (défaut 30).
CONGRESS_HTTP_TIMEOUT : timeout HTTP sec (défaut 30).

Exemples (PowerShell)
---------------------
# Historique (pas de filtre confirmatory)
$env:PYTHONPATH = (Resolve-Path 04_Code_Scripts)
python -m collect.fetch_congress any any 2021-03-01 2021-03-31 5 T1 data/raw/US_Congress_T1_202103.csv

# Confirmatory (≥800 tokens), écriture sur un FICHIER DIFFÉRENT
$env:CONGRESS_MIN_TOKENS = "800"
python -m collect.fetch_congress any any 2021-03-01 2021-03-31 15 T1 data/raw/US_Congress_T1_202103_min800.csv
"""

from __future__ import annotations

import os
import sys
import csv
import re
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import requests

# ----------------------------
# Constantes / ENV
# ----------------------------
BASE = "https://api.congress.gov/v3"
DEFAULT_PAGE_SIZE = int(os.environ.get("CONGRESS_PAGE_SIZE", "20"))
DEFAULT_MAX_OFFSET = int(os.environ.get("CONGRESS_MAX_OFFSET", "2000"))
MIN_TOKENS = int(os.environ.get("CONGRESS_MIN_TOKENS", "0"))  # 0 = pas de filtre confirmatory
HTTP_TIMEOUT = int(os.environ.get("CONGRESS_HTTP_TIMEOUT", "30"))
PDF_MAX_MB = int(os.environ.get("CONGRESS_PDF_MAX_MB", "30"))  # taille max PDF
PDF_MAX_BYTES = PDF_MAX_MB * 1024 * 1024

HDRS = {
    "User-Agent": "Axiodynamics-POC/1.1 (+research)",
    "Accept-Language": "en",
}

_SESSION = requests.Session()
_SESSION.headers.update(HDRS)
_BACKOFFS = (0.5, 1.0, 2.0)


# ----------------------------
# Utilitaires
# ----------------------------
def _http_get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = HTTP_TIMEOUT) -> Optional[requests.Response]:
    """GET avec backoff minimal ; renvoie response ou None."""
    for i, delay in enumerate((0, *_BACKOFFS)):
        if delay:
            time.sleep(delay)
        try:
            r = _SESSION.get(url, params=params, timeout=timeout, stream=False)
        except requests.RequestException:
            if i == len(_BACKOFFS):
                return None
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            if i == len(_BACKOFFS):
                return r
            continue
        return r
    return None


def _tokens_count(txt: str) -> int:
    if not txt:
        return 0
    return len(re.findall(r"\w+", txt))


def _to_date(s: str) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _within_window(s: str, d1: date, d2: date) -> bool:
    d = _to_date(s)
    return bool(d and d1 <= d <= d2)


def _dig(obj: Any, *keys) -> Any:
    cur = obj
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return None
    return cur


def _params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = {"format": "json"}
    key = os.environ.get("CONGRESS_API_KEY", "").strip()
    if key:
        p["api_key"] = key
    if extra:
        p.update(extra)
    return p


# ----------------------------
# Extraction HTML (long text)
# ----------------------------
def _strip_noise_bs(soup):
    for tag in soup(["script", "style", "nav", "aside", "footer"]):
        try:
            tag.decompose()
        except Exception:
            pass


def _extract_long_text_from_html(html: str) -> str:
    """Extrait un texte lisible depuis l'HTML public (fallback brut si bs4 absent)."""
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup  # lazy import
    except Exception:
        # fallback : texte brut compacté
        return re.sub(r"\s+", " ", html)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    _strip_noise_bs(soup)

    main = (soup.find("main") or soup.find("article") or
            soup.find("div", {"id": "main"}) or
            soup.find("div", class_=re.compile(r"(content|record|article)", re.I)))
    root = main or soup

    parts = []
    for tag in root.find_all(["h1", "h2", "h3", "p", "li"]):
        t = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if t:
            parts.append(t)
    text = " ".join(parts).strip()
    if _tokens_count(text) < 100:
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return text


def _find_pdf_links(html: str, base_url: str = "") -> List[str]:
    """Repère des liens .pdf dans la page ; renvoie liste d'URLs absolues si possible."""
    urls: List[str] = []
    try:
        from bs4 import BeautifulSoup  # lazy import
    except Exception:
        return urls
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"\.pdf(\?|$)", href, re.I):
            # Absolutiser si nécessaire
            if href.lower().startswith("http"):
                urls.append(href)
            else:
                # très basique : joindre au domaine de base si fourni
                if base_url and base_url.lower().startswith("http"):
                    try:
                        from urllib.parse import urljoin
                        urls.append(urljoin(base_url, href))
                    except Exception:
                        pass
    # petite dédup
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out


# ----------------------------
# Extraction PDF (pdfminer.six)
# ----------------------------
def _pdf_bytes_limited(url: str) -> Optional[bytes]:
    """Télécharge un PDF avec limite de taille ; renvoie bytes ou None."""
    try:
        with _SESSION.get(url, timeout=HTTP_TIMEOUT, stream=True, headers=HDRS) as r:
            if r.status_code != 200:
                return None
            # Head content-length si dispo
            clen = r.headers.get("Content-Length")
            if clen:
                try:
                    n = int(clen)
                    if n > PDF_MAX_BYTES:
                        return None
                except Exception:
                    pass
            # Téléchargement limité
            chunks = []
            total = 0
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > PDF_MAX_BYTES:
                    return None
            return b"".join(chunks)
    except requests.RequestException:
        return None


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extrait du texte depuis des bytes PDF avec pdfminer.six ; fallback si non dispo."""
    if not data:
        return ""
    try:
        from pdfminer.high_level import extract_text
        import io
        with io.BytesIO(data) as f:
            try:
                text = extract_text(f) or ""
            except Exception:
                text = ""
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        # pdfminer non dispo → fallback vide
        return ""


# ----------------------------
# Trouver public URL + extraire long text (HTML puis PDF)
# ----------------------------
def _dig_congressdotgov_url(js: dict) -> str:
    paths = [
        ("congressionalRecord", "congressdotgov_url"),
        ("congressional_record", "congressdotgov_url"),
        ("results", "congressdotgov_url"),
    ]
    for a, b in paths:
        try:
            v = js.get(a, {}).get(b) or ""
        except Exception:
            v = ""
        if v:
            return v
    return ""


def _expand_issue_text(api_detail_url: str) -> Tuple[str, str]:
    """
    Retourne (public_url, full_text) :
      - charge le JSON détail pour obtenir la public URL ;
      - tente extraction HTML ;
      - si tokens insuffisants (<400), cherche un lien PDF et extrait via pdfminer.six ;
      - fallback final = titre (géré à l'appelant).
    """
    public_url = ""
    full_text = ""

    # 1) Obtenir l'URL publique
    try:
        if api_detail_url.startswith(BASE):
            r = _http_get(api_detail_url, params=_params())
            if r is not None and r.status_code == 200:
                try:
                    js = r.json()
                except Exception:
                    js = None
                if isinstance(js, dict):
                    public_url = _dig_congressdotgov_url(js)
        else:
            public_url = api_detail_url
    except Exception:
        public_url = ""

    # 2) HTML → texte
    try:
        if public_url:
            rh = _http_get(public_url)
            if rh is not None and rh.status_code == 200:
                full_text = _extract_long_text_from_html(rh.text)
    except Exception:
        full_text = ""

    # 3) Si peu de tokens, tenter PDF
    if _tokens_count(full_text) < 400 and public_url:
        # Essayer de trouver un lien PDF dans la page
        pdf_urls = []
        try:
            rh2 = _http_get(public_url)
            if rh2 is not None and rh2.status_code == 200:
                pdf_urls = _find_pdf_links(rh2.text, base_url=public_url) or []
        except Exception:
            pdf_urls = []

        for pu in pdf_urls:
            pdf_bytes = _pdf_bytes_limited(pu)
            if not pdf_bytes:
                continue
            pdf_text = _extract_text_from_pdf_bytes(pdf_bytes)
            if _tokens_count(pdf_text) >= _tokens_count(full_text):
                # remplace si mieux
                full_text = pdf_text
                public_url = pu  # pointer directement sur le PDF pour traçabilité
            # si déjà “assez long”, on peut s’arrêter
            if _tokens_count(full_text) >= max(MIN_TOKENS, 800):
                break

    return public_url or api_detail_url, full_text


# ----------------------------
# Collecte via OFFSET
# ----------------------------
def _collect_cr_by_offset(d1: date, d2: date, limit: int,
                          page_size: int = DEFAULT_PAGE_SIZE,
                          max_offset: int = DEFAULT_MAX_OFFSET) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()  # (date,url)

    for offset in range(1, max_offset + 1, page_size):
        params = _params({"pageSize": page_size, "offset": offset})
        url = f"{BASE}/congressional-record"
        r = _http_get(url, params=params)
        if r is None:
            print(f"[WARN] endpoint=congressional-record offset={offset} error=None", flush=True)
            continue
        try:
            js = r.json()
        except Exception:
            print(f"[WARN] endpoint=congressional-record offset={offset} non-json status={r.status_code}", flush=True)
            continue

        issues = _dig(js, "Results", "Issues") or []
        print(f"[INFO] endpoint=congressional-record offset={offset} items={len(issues)} cum={len(rows)}", flush=True)
        if not issues:
            if r.status_code == 200:
                break
            continue

        # borne rapide : si la page est entièrement < d1 → stop
        dates_page = []
        for it in issues:
            d = _to_date(str(_dig(it, "PublishDate") or ""))
            if d:
                dates_page.append(d)
        if dates_page and max(dates_page) and max(dates_page) < d1:
            break

        # parcourir les issues
        for it in issues:
            vol = str(_dig(it, "Volume") or "").strip()
            issue_no = str(_dig(it, "Issue") or "").strip()
            pub = str(_dig(it, "PublishDate") or "").strip()
            d_iso = pub[:10] if pub else ""
            if not _within_window(d_iso, d1, d2):
                continue

            issue_id = str(_dig(it, "Id") or "").strip()
            if not issue_id:
                continue

            api_detail_url = f"{BASE}/congressional-record/{issue_id}?format=json"
            title = f"Congressional Record — Vol {vol}, Issue {issue_no}".strip(" —")

            public_url, long_text = _expand_issue_text(api_detail_url)
            # Fallback historique : si extraction faible, retitre
            if _tokens_count(long_text) < 50:
                long_text = title
            tok = _tokens_count(long_text)

            # Filtre confirmatory (optionnel)
            if MIN_TOKENS > 0 and tok < MIN_TOKENS:
                continue

            key = (d_iso, public_url)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "actor_id": "US_Congress_CongressionalRecord",
                "country": "US",
                "domain_id": "",
                "period": "",
                "date": d_iso,
                "url": public_url,
                "language": "en",
                "text": long_text,
                "tokens": tok,
            })
            if len(rows) >= limit:
                break

        if len(rows) >= limit:
            break

    return rows


# ----------------------------
# CLI
# ----------------------------
def _parse_args(argv: List[str]) -> Tuple[str, str, date, date, int, str, str]:
    if len(argv) != 8:
        print(
            "Usage:\n"
            "  python -m collect.fetch_congress <chamber> <party> <date_start> <date_end> <limit> <period> <out_csv>\n"
            "Args:\n"
            "  chamber     : House|Senate|any (informative)\n"
            "  party       : Democratic|Republican|any (informative)\n"
            "  date_start  : YYYY-MM-DD\n"
            "  date_end    : YYYY-MM-DD\n"
            "  limit       : max docs\n"
            "  period      : ex. T1/T2 (repassé dans le CSV)\n"
            "  out_csv     : chemin CSV de sortie\n",
            file=sys.stderr,
        )
        sys.exit(2)

    _, chamber, party, ds, de, lim, period, out_csv = argv
    try:
        d1 = datetime.strptime(ds, "%Y-%m-%d").date()
        d2 = datetime.strptime(de, "%Y-%m-%d").date()
    except Exception:
        print("[ERR] Dates invalides (YYYY-MM-DD).", file=sys.stderr)
        sys.exit(2)

    try:
        limit = int(lim)
    except Exception:
        print("[ERR] <limit> doit être un entier.", file=sys.stderr)
        sys.exit(2)

    return chamber, party, d1, d2, limit, period, out_csv


def main() -> None:
    chamber, party, d1, d2, limit, period, out_csv = _parse_args(sys.argv)

    rows = _collect_cr_by_offset(d1=d1, d2=d2, limit=limit)

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    wrote = 0
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["actor_id", "country", "domain_id", "period", "date", "url", "language", "text", "tokens"])
        for r in rows:
            w.writerow([
                r.get("actor_id", ""),
                r.get("country", ""),
                r.get("domain_id", ""),
                period,
                r.get("date", ""),
                r.get("url", ""),
                r.get("language", "en"),
                r.get("text", ""),
                r.get("tokens", 0),
            ])
            wrote += 1

    print(f"Wrote {wrote} rows → {out_csv}")
    if wrote == 0:
        print(f"[FAIL] No data rows in: {out_csv}")


if __name__ == "__main__":
    main()
