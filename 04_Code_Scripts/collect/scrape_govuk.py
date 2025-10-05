# 04_Code_Scripts/collect/scrape_govuk.py
# -*- coding: utf-8 -*-
"""
GOV.UK collector (Home Office / Ministry of Defence, etc.)

Objectif:
- Interroger l'API Search GOV.UK pour un organisme (ex: home-office, ministry-of-defence)
- Écrire un CSV T1 avec au moins une ligne de données si disponible

Points clés API:
- Pas de paramètre "page" ⇒ utiliser "start" (offset 0-based) + "count"
- Paramètre valide pour l’organisme: "filter_organisations" (sans crochets [])
- Filtre de dates côté API: "filter_public_timestamp=from:YYYY-MM-DD,to:YYYY-MM-DD"
- Tri: order=-public_timestamp
- L’API répond 422 si un paramètre est inconnu/incorrect.

Colonnes de sortie:
  actor_id,country,domain_id,period,date,url,language,text,tokens
"""

from __future__ import annotations

import csv
import sys
import os
import math
import datetime as dt
from typing import Any, Dict, List

import requests


API_URL = "https://www.gov.uk/api/search.json"
DEFAULT_COUNT = 50  # batch size pour l'API


def _tokens_count(text: str) -> int:
    return len(text.split()) if text else 0


def _search_once(org_slug: str,
                 date_from: str,
                 date_to: str,
                 start: int,
                 count: int = DEFAULT_COUNT) -> Dict[str, Any]:
    """
    Appel unique à l’API GOV.UK Search.
    Utilise les paramètres *valides*:
      - filter_organisations
      - filter_public_timestamp=from:...,to:...
      - order=-public_timestamp
      - start / count
    """
    params = {
        "filter_organisations": org_slug,
        "filter_public_timestamp": f"from:{date_from},to:{date_to}",
        "order": "-public_timestamp",
        "start": start,
        "count": count,
    }

    r = requests.get(API_URL, params=params, timeout=30)
    try:
        r.raise_for_status()
    except Exception as e:
        # Aide au diagnostic
        preview = r.text[:500] if r.text else ""
        raise requests.HTTPError(
            f"[GOVUK] HTTP {r.status_code} for {r.url}\n"
            f"Content-Type: {r.headers.get('Content-Type')}\n"
            f"Preview:\n{preview}"
        ) from e

    return r.json()


def _normalize_item(item: Dict[str, Any],
                    actor_id: str,
                    country: str,
                    domain_id: str,
                    period: str) -> Dict[str, Any]:
    """
    Convertit un item de l’API en ligne CSV normalisée.
    Champs typiques retournés par la Search API:
      - "public_timestamp": ex "2021-02-18T12:34:56.000+00:00"
      - "link": "/government/..."
      - "title"
      - "description"
      - "content_store_document_type" etc.

    On compose "text" = "title — description" (quand dispo).
    """
    url_path = item.get("link", "")
    url_full = f"https://www.gov.uk{url_path}" if url_path.startswith("/") else url_path or ""

    # date = public_timestamp en ISO date (YYYY-MM-DD)
    ts = item.get("public_timestamp") or item.get("public_updated_at") or ""
    date_iso = ""
    if ts:
        # on convertit en YYYY-MM-DD si possible
        try:
            # formats typiques: "2021-02-18T12:34:56.000+00:00"
            dt_obj = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            date_iso = dt_obj.date().isoformat()
        except Exception:
            # si non-parseable, on laisse brut
            date_iso = ts

    title = item.get("title", "") or ""
    desc = item.get("description", "") or ""
    if title and desc:
        text = f"{title} — {desc}"
    else:
        text = title or desc

    language = "en"  # GOV.UK
    tokens = _tokens_count(text)

    return {
        "actor_id": actor_id,
        "country": country,
        "domain_id": domain_id,
        "period": period,
        "date": date_iso,
        "url": url_full,
        "language": language,
        "text": text.replace("\r", " ").replace("\n", " ").strip(),
        "tokens": tokens,
    }


def scrape_department(actor_id: str,
                      country: str,
                      org_slug: str,
                      period: str,
                      date_start: str,
                      date_end: str,
                      limit: int) -> List[Dict[str, Any]]:
    """
    Collecte jusqu’à `limit` éléments pour un organisme donné, entre date_start et date_end.
    Pagination via start/count.
    """
    rows: List[Dict[str, Any]] = []
    start = 0
    remaining = limit

    while remaining > 0:
        count = min(DEFAULT_COUNT, remaining)
        js = _search_once(org_slug=org_slug,
                          date_from=date_start,
                          date_to=date_end,
                          start=start,
                          count=count)
        items = js.get("results", []) or []
        if not items:
            break

        for it in items:
            row = _normalize_item(it, actor_id, country, org_slug, period)
            rows.append(row)
            remaining -= 1
            if remaining <= 0:
                break

        start += count

    return rows


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def main() -> None:
    """
    Usage:
      python -m collect.scrape_govuk <actor_id> <country> <org_slug> <period> <date_start> <date_end> <limit>

    Exemple:
      python -m collect.scrape_govuk UK_HomeOffice UK home-office T1 2021-01-01 2021-06-30 5
      python -m collect.scrape_govuk UK_MoD       UK ministry-of-defence T1 2021-01-01 2021-06-30 5
    """
    if len(sys.argv) != 8:
        print("Usage: python -m collect.scrape_govuk <actor_id> <country> <org_slug> <period> <date_start> <date_end> <limit>")
        sys.exit(2)

    actor_id = sys.argv[1]
    country = sys.argv[2]
    org_slug = sys.argv[3]
    period = sys.argv[4]
    date_start = sys.argv[5]  # YYYY-MM-DD
    date_end = sys.argv[6]    # YYYY-MM-DD
    try:
        limit = int(sys.argv[7])
    except Exception:
        print("Error: <limit> doit être un entier.")
        sys.exit(2)

    # Collecte
    rows = scrape_department(actor_id, country, org_slug, period, date_start, date_end, limit)

    # Écriture CSV
    out_csv = f"data/raw/{actor_id}_{period}.csv"
    _ensure_parent_dir(out_csv)

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["actor_id", "country", "domain_id", "period", "date", "url", "language", "text", "tokens"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {len(rows)} rows \u2192 {out_csv}")


if __name__ == "__main__":
    main()
