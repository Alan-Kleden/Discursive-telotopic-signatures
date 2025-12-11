import re, sys, argparse, pandas as pd, numpy as np
from pathlib import Path

RULES = [
  ("speech",      r"(speech|address|statement|remarks|speeches|statements)"),
  ("press",       r"(press[-_/ ]?release|newsroom|media[-_/ ]?center|press)"),
  ("op_ed",       r"(op[-_ ]?ed|opinion|column|blog)"),
  ("debate",      r"(debate|hearing|transcript)"),
  ("qa",          r"(q[-_& ]?a|briefing|questions[-_ ]and[-_ ]answers)"),
  ("procedural",  r"(guidance|code[-_ ]of[-_ ]practice|manual|handbook|regulation|policy[-_ ]paper)")
]

def channel_of(row):
    text = " ".join([str(row.get(k,"")) for k in ["url","title","text"]]).lower()
    for name, pat in RULES:
        if re.search(pat, text):
            return name
    return "other"

def main():
    ap = argparse.ArgumentParser(description="Micro-diagnostic lot 20 (axiodynamique)")
    ap.add_argument("--csv", default="07_Config/validation_sample_texts.csv", help="Chemin CSV lot (par défaut: 07_Config/validation_sample_texts.csv)")
    ap.add_argument("--outdir", default="artifacts/diagnostics/lot20", help="Dossier sortie (txt/csv)")
    ap.add_argument("--min_words", type=int, default=120, help="Longueur médiane cible (>=)")
    args = ap.parse_args()

    csv = Path(args.csv)
    if not csv.exists():
        print(f"[ERR] Fichier introuvable: {csv}")
        sys.exit(2)

    df = pd.read_csv(csv, dtype=str).fillna("")
    df["word_count"] = df["text"].str.split().map(len, na_action='ignore').fillna(0).astype(int)
    actor_col = "actor_id" if "actor_id" in df.columns else ("source" if "source" in df.columns else None)
    df["actor"] = df[actor_col] if actor_col else ""

    df["channel"] = df.apply(channel_of, axis=1)

    n = len(df)
    by_channel = df["channel"].value_counts().rename_axis("channel").reset_index(name="n")
    procedural_pct = (df["channel"].eq("procedural").mean()*100) if n else 0
    len_med = int(df["word_count"].median()) if n else 0
    len_p10 = int(np.percentile(df["word_count"],10)) if n else 0
    len_p90 = int(np.percentile(df["word_count"],90)) if n else 0
    n_actors = df["actor"].replace("", np.nan).dropna().nunique()
    affect_heavy = df["channel"].isin(["speech","op_ed","press","debate","qa"]).mean()*100 if n else 0

    flags=[]
    if procedural_pct > 10: flags.append(f"Procedural too high: {procedural_pct:.1f}% (cap ≤10%)")
    if len_med < args.min_words: flags.append(f"Median length low: {len_med} (< {args.min_words})")
    if n_actors < 3: flags.append(f"Low actor diversity: {n_actors} unique actors (<3)")
    if affect_heavy < 60: flags.append(f"Low affective share: {affect_heavy:.1f}% (<60%)")

    print("\n=== MICRO-DIAGNOSTIC (lot) ===")
    print(f"N docs            : {n}")
    print(f"Actors (unique)   : {n_actors}")
    print(f"Words (p10/med/p90): {len_p10}/{len_med}/{len_p90}")
    print("\nBy channel:")
    for _,r in by_channel.iterrows():
        print(f"  - {r.channel:<11} : {int(r.n):>2}")
    print(f"\nProcedural share  : {procedural_pct:.1f}%  (cap ≤10%)")
    print(f"Affect-heavy share: {affect_heavy:.1f}%  (target ≥60%)")
    print("\nFLAGS:" if flags else "\nFLAGS: none ✅")
    for f in flags: print(" -", f)

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir/"lot_with_channels.csv", index=False, encoding="utf-8")
    by_channel.to_csv(outdir/"channels_summary.csv", index=False, encoding="utf-8")
    with open(outdir/"diagnostic.txt","w",encoding="utf-8") as f:
        f.write("\n".join([
            f"N={n}", f"actors={n_actors}",
            f"words_p10/med/p90={len_p10}/{len_med}/{len_p90}",
            f"procedural_pct={procedural_pct:.1f}",
            f"affect_heavy_pct={affect_heavy:.1f}",
            "flags=" + ("; ".join(flags) if flags else "none")
        ]))
    print(f"\nSaved: {outdir}/diagnostic.txt and CSVs.")
if __name__ == "__main__":
    main()
