import pandas as pd
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr
from pathlib import Path

IN_DIR = Path("07_Config/validation")
A_FP = IN_DIR/"annotations_annotateur_A.csv"  # à déposer par l'annotateur A
B_FP = IN_DIR/"annotations_annotateur_B.csv"  # à déposer par l'annotateur B
OUT_FP = IN_DIR/"annotations_with_consensus.csv"

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def main():
    a = pd.read_csv(A_FP)
    b = pd.read_csv(B_FP)

    # Renomme colonnes d’annotation
    a = a.rename(columns={"fc_score":"fc_A","fi_score":"fi_A"})
    b = b.rename(columns={"fc_score":"fc_B","fi_score":"fi_B"})

    # Merge sur doc_id (garde métadonnées de A)
    keys = ["doc_id"]
    merged = pd.merge(a, b[keys+["fc_B","fi_B"]], on=keys, how="inner", validate="one_to_one")

    # Numériser
    for c in ["fc_A","fi_A","fc_B","fi_B"]:
        merged[c] = to_num(merged[c])

    complete = merged.dropna(subset=["fc_A","fi_A","fc_B","fi_B"]).copy()

    # Kappa (pondéré) après arrondi
    k_fc = cohen_kappa_score(complete["fc_A"].round(), complete["fc_B"].round(), weights="linear")
    k_fi = cohen_kappa_score(complete["fi_A"].round(), complete["fi_B"].round(), weights="linear")

    # Spearman entre annotateurs (info)
    s_fc, p_fc = spearmanr(complete["fc_A"], complete["fc_B"])
    s_fi, p_fi = spearmanr(complete["fi_A"], complete["fi_B"])

    # Consensus = moyenne
    complete["consensus_fc"] = complete[["fc_A","fc_B"]].mean(axis=1)
    complete["consensus_fi"] = complete[["fi_A","fi_B"]].mean(axis=1)

    # Sauvegarde
    complete.to_csv(OUT_FP, index=False, encoding="utf-8")

    print("Docs pris en compte :", len(complete))
    print(f"Cohen’s κ (FC): {k_fc:.3f}")
    print(f"Cohen’s κ (FI): {k_fi:.3f}")
    print(f"Spearman FC   : {s_fc:.3f} (p={p_fc:.4f})")
    print(f"Spearman FI   : {s_fi:.3f} (p={p_fi:.4f})")
    print(f"→ Gate κ≥0.70 sur FC et FI {'OK' if (k_fc>=0.70 and k_fi>=0.70) else 'NON'}")
    print(f"✓ Consensus sauvegardé : {OUT_FP}")

if __name__ == "__main__":
    main()
