# 04_Code_Scripts/collect/fetch_congress.py
# -*- coding: utf-8 -*-
"""
US Congress collector (Congress.gov v3) — robust multi-endpoint (BILL-first) with strict date filtering + 500-safe

Ordre d'essai :
  1) bill/117?fromDate&toDate (filtré par chambre)
  2) bill?fromDate&toDate     (filtré par chambre)
  3) committee-report/117     (fallback)
  4) committee-report?fromDate&toDate
  5) committee-print/117
  6) committee-print?fromDate&toDate

Sortie (schéma PoC) :
  actor_id,country,domain_id,period,date,url,language,text,tokens
"""

from __future__ import annotations

import os, sys, csv, time, re
from datetime import datetime, date
from typing import List, Dict, Any, Optional

import requests

BASE = "https://api.congress.gov/v3"
MAX_PAGES_DEFAULT = 8
PAGE_SLEEP_SEC = 0.1

def _tokens_count(txt: str) -> int:
    return len(re.findall(r"\w+", txt or ""))

def _iso_date_from_any(s: str) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        try:
            return str(datetime.strptime(s[:10], "%Y-%m-%d").date())
        except Exception:
            return None

def _within_window(iso: str, d1: date, d2: date) -> bool:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
        return d1 <= d <= d2
    except Exception:
        return False

def _get_api_key() -> str:
    key = os.environ.get("CONGRESS_API_KEY", "").strip()
    if not key or key.startswith("<") or key.endswith(">"):
        raise RuntimeError(
            "CONGRESS_API_KEY is not set (or still a placeholder). "
            "Set it:  $env:CONGRESS_API_KEY = \"xxxxxxxx...\""
        )
    return key

def _req_json(path: str, params: dict) -> Optional[dict]:
    """GET JSON; renvoie None si 5xx pour passer au fallback."""
    key = _get_api_key()
    url = f"{BASE}/{path.lstrip('/')}"
    p = dict(params); p["api_key"] = key
    r = requests.get(url, params=p, timeout=30)
    if r.status_code >= 500:
        print(f"[WARN] Skip {path} (HTTP {r.status_code})")
        return None
    try:
        r.raise_for_status()
    except Exception as e:
        raise requests.HTTPError(
            f"[CONGRESS] HTTP {r.status_code} for {r.url}\nPreview: {r.text[:400]}"
        ) from e
    return r.json()

def _dig(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _first_nonempty(*vals) -> Optional[str]:
    for v in vals:
        if isinstance(v, str) and v.strip(): return v.strip()
    for v in vals:  # list with urls
        if isinstance(v, list) and v:
            for el in v:
                if isinstance(el, dict) and el.get("url"):
                    return str(el["url"]).strip()
            return str(v[0]).strip()
    for v in vals:  # dict with url
        if isinstance(v, dict) and v.get("url"):
            return str(v["url"]).strip()
    for v in vals:
        if v is not None and str(v).strip(): return str(v).strip()
    return None

def _effective_url(item: Dict[str, Any]) -> Optional[str]:
    url_i = _first_nonempty(
        item.get("congressdotgov_url"),
        _dig(item, "html", "url"),
        item.get("url"),
        item.get("sourceLink"),
        item.get("link"),
        item.get("download"),
        item.get("downloads"),
        _dig(item, "gpoPdfLink"),
        _dig(item, "pdf", "url"),
    )
    if url_i and url_i.startswith("/"):
        url_i = "https://www.congress.gov" + url_i
    return url_i

def _normalize_generic(item: Dict[str, Any], endpoint: str) -> Optional[Dict[str, Any]]:
    title = _first_nonempty(item.get("title"), item.get("heading"),
                            item.get("documentTitle"), item.get("name"))
    desc  = _first_nonempty(item.get("description"), item.get("summary"),
                            item.get("abstract"))

    if not (title or desc) and endpoint == "committee-print":
        jacket   = _first_nonempty(item.get("jacketNumber"))
        chamber  = _first_nonempty(item.get("chamber"))
        congress = _first_nonempty(item.get("congress"))
        synth = []
        if jacket:   synth.append(f"Committee Print {jacket}")
        if chamber:  synth.append(str(chamber))
        if congress: synth.append(f"{congress}th Congress")
        title = " — ".join(synth) if synth else None

    text_base = f"{title} — {desc}" if title and desc and title != desc else (title or desc)
    url_i = _effective_url(item)
    # Date la plus pertinente disponible
    d_iso = None
    for c in [
        _dig(item, "latestAction", "actionDate"),
        _dig(item, "issuedDate"),
        _dig(item, "publicationDate"),
        item.get("dateIssued"),
        item.get("date"),
        item.get("updateDate"),
    ]:
        iso = _iso_date_from_any(c)
        if iso:
            d_iso = iso
            break

    if not text_base or not url_i or not d_iso:
        return None

    text = " ".join(text_base.split())
    return {"date": d_iso, "url": url_i, "language": "en", "text": text,
            "tokens": _tokens_count(text)}

def _normalize_bill(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalisation spécifique aux bills.
    Titre: title/shortTitle; Date: latestAction.actionDate > introducedDate; URL: congressdotgov_url > html/url.
    """
    title = _first_nonempty(item.get("title"), item.get("shortTitle"), item.get("documentTitle"))
    desc  = _first_nonempty(item.get("summary"), item.get("description"))
    text_base = f"{title} — {desc}" if title and desc and title != desc else (title or desc)

    url_i = _effective_url(item)
    d_iso = None
    for c in [
        _dig(item, "latestAction", "actionDate"),
        item.get("introducedDate"),
        item.get("updateDate"),
    ]:
        iso = _iso_date_from_any(c)
        if iso:
            d_iso = iso
            break

    if not text_base or not url_i or not d_iso:
        return None

    text = " ".join(text_base.split())
    return {"date": d_iso, "url": url_i, "language": "en", "text": text,
            "tokens": _tokens_count(text)}

def _yield_items(js: dict, keys: List[str]) -> List[Dict[str, Any]]:
    for k in keys:
        v = js.get(k)
        if isinstance(v, list) and v:
            return v
    return []

def _collect_from_path(path: str, array_keys: List[str], actor_id: str,
                       d1: date, d2: date, limit: int, max_pages: int,
                       normalizer: str = "generic", extra_params: dict | None = None,
                       endpoint_label: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    page = 1
    while len(rows) < limit and page <= max_pages:
        params = {"format":"json", "page": page}
        if extra_params:
            params.update(extra_params)
        js = _req_json(path, params)
        if js is None:
            break  # 5xx → fallback
        items = _yield_items(js, array_keys)
        label = endpoint_label or path
        print(f"[INFO] endpoint={label} page={page} items={len(items)} cum={len(rows)}")
        if not items:
            break

        for it in items:
            if normalizer == "bill":
                norm = _normalize_bill(it)
            else:
                norm = _normalize_generic(it, endpoint=path.split("?")[0].split("/")[-1])

            if not norm:
                continue
            if not _within_window(norm["date"], d1, d2):
                continue

            rows.append({
                "actor_id": actor_id,
                "country": "US",
                "domain_id": "",
                "period": "",
                **norm
            })
            if len(rows) >= limit:
                break

        page += 1
        time.sleep(PAGE_SLEEP_SEC)
    return rows

def _match_chamber(item: Dict[str, Any], want: str) -> bool:
    """
    Filtre par chambre pour les bills.
    - originChamber / originChamberCode ('House'/'Senate' ou 'H'/'S')
    - housePassage/senatePassage dates (si une seule des deux est non nulle, on infère la chambre d'origine)
    """
    want = (want or "").strip().lower()
    if want not in {"house", "senate", "any"}:
        return True

    origin = _first_nonempty(item.get("originChamber"), item.get("originChamberCode"))
    if origin:
        o = origin.strip().lower()
        if want == "any":
            return True
        if want == "house" and (o.startswith("h") or o == "house"):
            return True
        if want == "senate" and (o.startswith("s") or o == "senate"):
            return True

    # Heuristique légère : présence de date de passage spécifique
    if want == "house" and _iso_date_from_any(item.get("housePassage")):
        return True
    if want == "senate" and _iso_date_from_any(item.get("senatePassage")):
        return True

    # Pas d'info fiable → si 'any', on accepte ; sinon on rejette.
    return (want == "any")

def fetch_multi(chamber: str, date_start: str, date_end: str, limit: int,
                max_pages: int = MAX_PAGES_DEFAULT) -> List[Dict[str, Any]]:
    d1 = datetime.strptime(date_start, "%Y-%m-%d").date()
    d2 = datetime.strptime(date_end, "%Y-%m-%d").date()
    rows: List[Dict[str, Any]] = []

    # 1) bill/117 (limite rapide, filtré par chambre)
    if len(rows) < limit:
        page = 1
        while len(rows) < limit and page <= max_pages:
            js = _req_json("bill/117", {"format":"json", "fromDate": date_start, "toDate": date_end, "page": page})
            if js is None:  # 5xx
                break
            items = _yield_items(js, ["bills", "bill"])
            print(f"[INFO] endpoint=bill/117 page={page} items={len(items)} cum={len(rows)}")
            if not items:
                break
            for it in items:
                if not _match_chamber(it, chamber):
                    continue
                norm = _normalize_bill(it)
                if not norm or not _within_window(norm["date"], d1, d2):
                    continue
                rows.append({
                    "actor_id": "US_Congress_Bill",
                    "country": "US",
                    "domain_id": "",
                    "period": "",
                    **norm
                })
                if len(rows) >= limit:
                    break
            page += 1
            time.sleep(PAGE_SLEEP_SEC)

    # 2) bill (sans préciser la législature)
    if len(rows) < limit:
        rows += _collect_from_path("bill", ["bills", "bill"], "US_Congress_Bill",
                                   d1, d2, limit - len(rows), max_pages,
                                   normalizer="bill",
                                   extra_params={"fromDate": date_start, "toDate": date_end},
                                   endpoint_label="bill?fromDate&toDate")

    # 3) committee-report/117
    if len(rows) < limit:
        rows += _collect_from_path("committee-report/117", ["committeeReports","committeeReport"],
                                   "US_Congress_CommitteeReport", d1, d2, limit - len(rows), max_pages)

    # 4) committee-report (from/to)
    if len(rows) < limit:
        rows += _collect_from_path("committee-report", ["committeeReports","committeeReport"],
                                   "US_Congress_CommitteeReport", d1, d2, limit - len(rows), max_pages,
                                   extra_params={"fromDate": date_start, "toDate": date_end})

    # 5) committee-print/117
    if len(rows) < limit:
        rows += _collect_from_path("committee-print/117", ["committeePrints","committeePrint"],
                                   "US_Congress_CommitteePrint", d1, d2, limit - len(rows), max_pages)

    # 6) committee-print (from/to)
    if len(rows) < limit:
        rows += _collect_from_path("committee-print", ["committeePrints","committeePrint"],
                                   "US_Congress_CommitteePrint", d1, d2, limit - len(rows), max_pages,
                                   extra_params={"fromDate": date_start, "toDate": date_end})

    return rows

def main() -> None:
    if len(sys.argv) != 8:
        print("Usage: python -m collect.fetch_congress <chamber> <party> <date_start> <date_end> <limit> <period> <out_csv>")
        sys.exit(2)

    _, chamber, party, d1, d2, lim, period, out_csv = sys.argv
    try:
        limit = int(lim)
    except Exception:
        print("Error: <limit> doit être un entier.")
        sys.exit(2)

    rows = fetch_multi(chamber=chamber, date_start=d1, date_end=d2, limit=limit, max_pages=MAX_PAGES_DEFAULT)
    for r in rows:
        r["period"] = period

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["actor_id","country","domain_id","period","date","url","language","text","tokens"]
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {len(rows)} rows \u2192 {out_csv}")

if __name__ == "__main__":
    main()
