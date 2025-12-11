# coding: utf-8
"""
Phase 1 runner (rejouable sous Win/Linux/CI).
Sous-commandes:
  ingest   --feeds FEEDS_TXT              -> artifacts/phase1/inputs/rss_items.csv
  enrich   --in rss_items.csv --out RAW   -> artifacts/phase1/inputs/lot_raw.csv
  excerpts --in RAW --out CAND            -> artifacts/phase1/inputs/candidates_25.csv
  select   --in CAND --out LOT [...]      -> artifacts/phase1/inputs/lot20_final.csv
  validate --in LOT                       -> OK/ERR
  export   --in LOT --out ANNOTATORS_CSV  -> fichier annotateurs (colonnes annotator_X_*)
"""
import argparse, csv, os, sys, time, re
from pathlib import Path

# --- util ---
def ts(): return time.strftime("%Y%m%d_%H%M")
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "phase1"
INP = ART / "inputs"
OUT = ART / "outputs"
DBG = OUT / "debug"
for d in (INP, OUT, DBG): d.mkdir(parents=True, exist_ok=True)

def read_lines(p: Path):
    with p.open(encoding="utf-8") as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            yield s

# --- 1) INGEST: lire des flux RSS (sans dépendre d’un script externe) ---
def cmd_ingest(args):
    try:
        import feedparser
    except ImportError:
        print("feedparser requis: pip install feedparser"); sys.exit(1)

    feeds = list(read_lines(Path(args.feeds)))
    rows = []
    for url in feeds:
        d = feedparser.parse(url)
        for e in d.entries:
            rows.append({
                "source": url,
                "title": getattr(e, "title", ""),
                "link": getattr(e, "link", ""),
                "published": getattr(e, "published", ""),
                "summary": getattr(e, "summary", ""),
            })

    out = INP / "rss_items.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source","title","link","published","summary"])
        w.writeheader(); w.writerows(rows)
    print(f"OK -> {out}")

# --- 2) ENRICH: télécharger HTML et extraire plein texte -> lot_raw.csv ---
def _extract_text_from_url(url: str):
    import requests
    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        # simple fallback: retirer scripts/styles et prendre <p>
        for tag in soup(["script","style","noscript"]): tag.decompose()
        ps = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        txt = " ".join([t for t in ps if t]) or soup.get_text(" ", strip=True)
        # normalisation légère
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt
    except Exception:
        return ""

def cmd_enrich(args):
    # choisir la source: --in si fourni, sinon rss_items.csv
    src = Path(args.in_path) if args.in_path else INP / "rss_items.csv"
    if not src.exists():
        print(f"Introuvable: {src}. Lancez d'abord 'ingest' ou passez --in.")
        sys.exit(2)

    rows = []
    with src.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        i = 0
        for r in rdr:
            url = r.get("url") or r.get("link") or ""
            if not url: continue
            text = _extract_text_from_url(url)
            if not text: continue
            i += 1
            rows.append({
                "id": f"C{i:03d}",
                "actor_id": "",
                "country": "",
                "domain_id": "",
                "period": "",
                "date": r.get("published",""),
                "title": r.get("title",""),
                "url": url,
                "text": text,
                "tokens": "",
                "source": url.split("/")[2] if "://" in url else "",
            })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["actor_id","country","domain_id","period","date","title","url","text","tokens","source","id"])
        w.writeheader(); w.writerows(rows)
    print(f"OK -> {out}")

# --- 3) EXCERPTS: fenêtres 120–250 mots -> candidates_25.csv ---
def cmd_excerpts(args):
    # réutilise votre script existant
    import subprocess
    src = str(Path(args.in_path))
    dst = str(Path(args.out))
    py = sys.executable
    script = ROOT / "scripts" / "poc_tools" / "make_excerpts.py"
    if not script.exists():
        print(f"Introuvable: {script}"); sys.exit(2)
    subprocess.check_call([py, str(script), "--in", src, "--out", dst])
    print(f"OK -> {dst}")

# --- 4) SELECT: 20 extraits diversifiés -> lot20_final.csv ---
def cmd_select(args):
    import subprocess
    py = sys.executable
    script = ROOT / "scripts" / "poc_tools" / "select_diverse_20.py"
    if not script.exists():
        print(f"Introuvable: {script}"); sys.exit(2)
    cmd = [py, str(script), str(Path(args.in_path)), str(Path(args.out))]
    if args.domain_cap is not None: cmd += ["--domain-cap", str(args.domain_cap)]
    if args.want is not None:       cmd += ["--want", str(args.want)]
    if args.min_fcfi is not None:   cmd += ["--min-fcfi", str(args.min_fcfi)]
    import subprocess as sp
    sp.check_call(cmd)

# --- 5) VALIDATE: schéma/contraintes ---
def cmd_validate(args):
    import subprocess
    py = sys.executable
    script = ROOT / "scripts" / "poc_tools" / "validate_lot.py"
    if not script.exists():
        print(f"Introuvable: {script}"); sys.exit(2)
    subprocess.check_call([py, str(script)])

# --- 6) EXPORT: CSV annotateurs ---
def cmd_export(args):
    src = Path(args.in_path)
    dst = Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        out_rows = []
        for r in rdr:
            out_rows.append({
                "id": r.get("id",""),
                "excerpt": r.get("excerpt",""),
                "annotator_X_telos_central": "",
                "annotator_X_fc": "",
                "annotator_X_fi": "",
                "annotator_X_notes": "",
                "flag_incertain": "",
            })
    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id","excerpt",
            "annotator_X_telos_central","annotator_X_fc","annotator_X_fi",
            "annotator_X_notes","flag_incertain"
        ])
        w.writeheader(); w.writerows(out_rows)
    print(f"OK -> {dst}")

# --- CLI ---
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("ingest");   p1.add_argument("--feeds", required=True); p1.set_defaults(fn=cmd_ingest)

    p2 = sub.add_parser("enrich");   p2.add_argument("--in", dest="in_path", required=False)
    p2.add_argument("--out", required=True); p2.set_defaults(fn=cmd_enrich)

    p3 = sub.add_parser("excerpts"); p3.add_argument("--in", dest="in_path", required=True)
    p3.add_argument("--out", required=True); p3.set_defaults(fn=cmd_excerpts)

    p4 = sub.add_parser("select");   p4.add_argument("--in", dest="in_path", required=True)
    p4.add_argument("--out", required=True)
    p4.add_argument("--domain-cap", type=int, default=7)
    p4.add_argument("--want", type=int, default=20)
    p4.add_argument("--min-fcfi", type=int, default=1)
    p4.set_defaults(fn=cmd_select)

    p5 = sub.add_parser("validate"); p5.add_argument("--in", dest="in_path", required=True)
    p5.set_defaults(fn=cmd_validate)

    p6 = sub.add_parser("export");   p6.add_argument("--in", dest="in_path", required=True)
    p6.add_argument("--out", required=True)
    p6.set_defaults(fn=cmd_export)

    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
