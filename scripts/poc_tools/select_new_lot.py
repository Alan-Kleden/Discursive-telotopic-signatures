# select_new_lot.py  — sélectionne 20 nouveaux articles en excluant des URLs déjà utilisées
import argparse, re, random
from pathlib import Path
import pandas as pd

def _int_from_flag(s: str, key: str) -> int:
    if not isinstance(s, str): return 0
    m = re.search(rf"{re.escape(key)}=(\d+)", s)
    return int(m.group(1)) if m else 0

def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--exclude-lot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--domain-cap", type=int, default=7)
    ap.add_argument("--want", type=int, default=20)
    ap.add_argument("--min-fcfi", type=int, default=1)
    ap.add_argument("--seed", type=int, default=123)
    args = ap.parse_args()

    rnd = random.Random(args.seed)

    cand = load_csv(Path(args.candidates))
    # Colonnes attendues côté candidats
    needed_cols = ["id","excerpt","Fc_items","Fi_items","source","url","topic","country","stance_guess","telos_central","notes","rationale"]
    for col in needed_cols:
        if col not in cand.columns:
            cand[col] = ""

    # score fc+fi
    cand["fc"] = cand["Fc_items"].map(lambda s: _int_from_flag(s, "auto_fc_hits"))
    cand["fi"] = cand["Fi_items"].map(lambda s: _int_from_flag(s, "auto_fi_hits"))
    cand["score"] = cand["fc"] + cand["fi"]

    # Exclusion par URL déjà utilisée
    excl = load_csv(Path(args.exclude_lot))
    excl_urls = set(excl["url"].dropna().astype(str)) if "url" in excl.columns else set()
    before = len(cand)
    cand = cand[~cand["url"].isin(excl_urls)].copy()

    # Filtre seuil fc+fi
    cand = cand[cand["score"] >= args.min_fcfi].copy()

    # Dédupe par URL si besoin
    cand = cand.sort_values(["score"], ascending=False)
    cand = cand.drop_duplicates(subset=["url"])

    # Tri final par score puis léger hasard reproductible
    cand["rand"] = [rnd.random() for _ in range(len(cand))]
    cand = cand.sort_values(["score","rand"], ascending=[False, False]).reset_index(drop=True)

    # Application cap par domaine
    out_rows = []
    per_dom = {}
    for _, r in cand.iterrows():
        dom = r["source"]
        if per_dom.get(dom, 0) >= args.domain_cap:
            continue
        out_rows.append(r)
        per_dom[dom] = per_dom.get(dom, 0) + 1
        if len(out_rows) >= args.want:
            break

    sel = pd.DataFrame(out_rows, columns=cand.columns) if out_rows else pd.DataFrame(columns=cand.columns)

    # Mise en forme de sortie attendue par validate/export
    if not sel.empty:
        sel = sel.assign(
            id=[f"C{i:03d}" for i in range(1, len(sel)+1)],
            telos_central=sel.get("telos_central",""),
            rationale=sel.get("rationale","Fc/Fi>=1 + diversité domaine/topic/stance"),
            notes=sel.get("notes","")
        )
        # Colonnes finales minimales
        final_cols = ["id","excerpt","telos_central","Fc_items","Fi_items","stance_guess","topic","country","source","url","rationale","notes"]
        for c in final_cols:
            if c not in sel.columns: sel[c] = ""
        sel = sel[final_cols]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sel.to_csv(args.out, index=False, encoding="utf-8")

    # Logs console
    pool_total = before
    after_excl = len(cand)
    picked = len(sel)
    dom_counts = ", ".join(f"{k}:{v}" for k,v in sorted(per_dom.items(), key=lambda kv:-kv[1]))
    print(f"POOL total(before)={pool_total} | after_exclusion+min_fcfi={after_excl} | SELECTED {picked}/{args.want}")
    print(f"by_domain: {dom_counts}")
    print(f"OK -> {args.out}")

if __name__ == "__main__":
    main()
