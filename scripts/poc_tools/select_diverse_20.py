# coding: utf-8
"""
select_diverse_20.py — sélectionne N extraits avec diagnostics complets.

Usage:
  python scripts/poc_tools/select_diverse_20.py <candidates_csv> <out_csv> [--domain-cap 7] [--want 20] [--min-fcfi 1]

Sorties:
  - out_csv : lot final
  - artifacts/phase1/outputs/debug/select_debug_<ts>.csv : pool annoté (score, fc, fi, reasons)
  - résumé imprimé : tailles, répartitions, causes de rejet, caps atteints
"""
import sys, csv, re, os, argparse, time
from collections import Counter, defaultdict
from pathlib import Path

DEF_DOMAIN_CAP = 7
DEF_WANT = 20
DEF_MIN_FCFI = 1

FC_PAT = re.compile(r"\b(should|must|urge|enact|fund|invest|expand|mandate|tighten|ban|cap|prioritize|protect|ensure|guarantee|reform|repeal)\b", re.I)
FI_PAT = re.compile(r"\b(avoid|prevent|limit|reduce|mitigate|safeguard|not|without|except|unless)\b", re.I)

def nowstamp():
    return time.strftime("%Y%m%d_%H%M%S")

def norm_row(r):
    return {(k.lstrip("\ufeff").strip() if isinstance(k,str) else k): v for k,v in r.items()}

def score_row(ex:str, fc:int, fi:int, lex_div:float):
    bal = 1.0 - abs(fc - fi) / (fc + fi + 1e-6)
    return 0.55*bal + 0.25*min(fc+fi,6)/6 + 0.20*lex_div

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--domain-cap", type=int, default=int(os.getenv("DOMAIN_CAP", DEF_DOMAIN_CAP)))
    ap.add_argument("--want", type=int, default=int(os.getenv("WANT", DEF_WANT)))
    ap.add_argument("--min-fcfi", type=int, default=int(os.getenv("MIN_FCFI", DEF_MIN_FCFI)))
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    debug_dir = Path("artifacts/phase1/outputs/debug"); debug_dir.mkdir(parents=True, exist_ok=True)
    dbg = debug_dir / f"select_debug_{nowstamp()}.csv"

    # lecture candidats
    with src.open(encoding="utf-8") as f:
        rows = [norm_row(r) for r in csv.DictReader(f)]

    pool, reasons = [], defaultdict(int)
    for r in rows:
        ex = (r.get("excerpt_120_250w") or "").strip()
        if not ex:
            continue
        n = int(r.get("excerpt_len") or 0) or len(ex.split())
        if n < 120 or n > 250:
            pool.append({"r":r,"keep":False,"reason":"len_out_of_range","score":0,"dom":"","topic":"","stance":"","fc":0,"fi":0,"n":n,"lex":0})
            reasons["len_out_of_range"] += 1
            continue

        dom   = (r.get("source_domain") or r.get("source") or "").strip().lower()
        topic = (r.get("topic") or "").strip() or "MISC"
        stance= (r.get("stance_guess") or "Inter").strip() or "Inter"

        words = ex.split()
        lex_div = len(set(words))/max(len(words),1)
        fc = len(FC_PAT.findall(ex)); fi = len(FI_PAT.findall(ex))
        sc = score_row(ex, fc, fi, lex_div)

        pool.append({"r":r,"keep":True,"reason":"","score":sc,"dom":dom,"topic":topic,"stance":stance,"fc":fc,"fi":fi,"n":len(words),"lex":lex_div})

    # tri par score
    kept = [p for p in pool if p["keep"]]
    kept.sort(key=lambda x: x["score"], reverse=True)

    # passe principale: fc+fi >= min
    primary = [p for p in kept if (p["fc"]+p["fi"]) >= args.min_fcfi]
    fallback = [p for p in kept if (p["fc"]+p["fi"]) < args.min_fcfi]

    out, by_dom, by_topic, by_stance = [], Counter(), Counter(), Counter()
    def try_take(cand, tag):
        taken = 0
        for p in cand:
            if len(out) >= args.want: break
            if by_dom[p["dom"]]   >= args.domain_cap: p["reason"]=f"cap_dom({p['dom']})"; reasons[p["reason"]]+=1; continue
            if by_topic[p["topic"]] >= 999: p["reason"]="cap_topic"; reasons[p["reason"]]+=1; continue  # pas de cap topic strict ici
            if by_stance[p["stance"]] >= 999: p["reason"]="cap_stance"; reasons[p["reason"]]+=1; continue
            p["reason"]=f"selected_{tag}"; out.append(p)
            by_dom[p["dom"]] += 1; by_topic[p["topic"]] += 1; by_stance[p["stance"]] += 1; taken += 1
        return taken

    t1 = try_take(primary, "primary")
    if len(out) < args.want:
        # fallback: trier par diversité lexicale puis longueur
        fallback.sort(key=lambda x: (x["lex"], x["n"]), reverse=True)
        t2 = try_take(fallback, "fallback")
    else:
        t2 = 0

    # marquer les non-sélectionnés avec la raison dominante
    picked_ids = { id(p) for p in out }
    for p in pool:
        if id(p) in picked_ids: continue
        if p["reason"] == "": p["reason"] = "filtered_pre" if not p["keep"] else ("below_min_fcfi" if (p["fc"]+p["fi"]) < args.min_fcfi else "not_selected_lower_score")
        reasons[p["reason"]] += 1

    # écrire debug
    with dbg.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","url","dom","topic","stance","n_words","lex_div","fc","fi","score","reason"])
        for p in pool:
            r = p["r"]
            w.writerow([r.get("id") or r.get("\ufeffid") or "", r.get("url",""), p["dom"], p["topic"], p["stance"], p["n"], f"{p['lex']:.3f}", p["fc"], p["fi"], f"{p['score']:.3f}", p["reason"]])

    # écrire sortie
    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id","excerpt","telos_central","Fc_items","Fi_items",
            "stance_guess","topic","country","source","url","rationale","notes"
        ])
        w.writeheader()
        for p in out:
            r = p["r"]
            w.writerow({
                "id": r.get("id") or r.get("\ufeffid") or "",
                "excerpt": (r.get("excerpt_120_250w") or "").strip(),
                "telos_central": "",
                "Fc_items": f"auto_fc_hits={p['fc']}",
                "Fi_items": f"auto_fi_hits={p['fi']}",
                "stance_guess": p["stance"],
                "topic": p["topic"],
                "country": r.get("country",""),
                "source": p["dom"],
                "url": r.get("url",""),
                "rationale": f"score={p['score']:.3f}; pass={'primary' if 'primary' in p['reason'] else 'fallback'}; cap_dom={args.domain_cap}",
                "notes": ""
            })

    # résumé console
    print(f"POOL total: {len(pool)} | valides longueur: {len(kept)} | primary(fc+fi≥{args.min_fcfi}): {len(primary)} | fallback: {len(fallback)}")
    def tab(dist):
        return ", ".join([f"{k}:{v}" for k,v in dist.most_common()])
    print("Pool domaines:", tab(Counter([p['dom'] for p in kept])))
    print("Pool topics  :", tab(Counter([p['topic'] for p in kept])))
    print("Pool stances :", tab(Counter([p['stance'] for p in kept])))
    print(f"SELECTED {len(out)}/{args.want} | by_dom:", dict(by_dom))
    print("Reasons:", dict(reasons))
    print(f"DEBUG CSV -> {dbg}")
    print(f"OK -> {dst}")

if __name__ == "__main__":
    main()
