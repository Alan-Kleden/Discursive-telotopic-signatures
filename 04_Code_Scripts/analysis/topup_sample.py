# 04_Code_Scripts/analysis/topup_sample.py
import pandas as pd, numpy as np
from pathlib import Path

TARGET = 20
SEED   = 42

base      = Path("07_Config/validation")
all_fp    = base / "verbatim_windows_all.csv"
sample_fp = base / "verbatim_windows_sample20.csv"
tpl_fp    = base / "annotation_template_v2.csv"

def main():
    allw   = pd.read_csv(all_fp)
    sample = pd.read_csv(sample_fp)

    # Exclure déjà pris + trop courts
    pool = allw[~allw['doc_id'].isin(sample['doc_id'])].copy()
    if 'length_words' not in pool.columns:
        pool['length_words'] = pool['excerpt_verbatim'].fillna('').str.split().map(len)
    pool['length_words'] = pd.to_numeric(pool['length_words'], errors='coerce').fillna(0).astype(int)
    pool = pool[pool['length_words'] >= 300].copy()

    need = max(0, TARGET - len(sample))
    if need == 0:
        print("✓ Déjà 20 docs. Rien à faire.")
        write_template(sample, tpl_fp)
        return

    if len(pool) < need:
        print(f"⚠️  Seulement {len(pool)} docs disponibles (besoin: {need}). On prend ce qu'il y a.")
        need = len(pool)

    # Prioriser acteurs sous-représentés (répartition simple, seed fixe)
    cur_counts = sample['actor_id'].value_counts().to_dict()
    pool['cur_n_actor'] = pool['actor_id'].map(cur_counts).fillna(0).astype(int)
    pool = pool.sample(frac=1.0, random_state=SEED).sort_values('cur_n_actor', ascending=True)

    add   = pool.head(need).copy()
    final = pd.concat([sample, add], ignore_index=True)

    print(f"Échantillon initial : {len(sample)}")
    print(f"Ajoutés             : {len(add)}")
    print(f"Total final         : {len(final)}\n")
    print("Distribution finale :")
    print(final['actor_id'].value_counts())

    if len(add) > 0:
        print("\nDocs ajoutés par acteur :")
        print(add['actor_id'].value_counts())

    # Écritures
    final.to_csv(sample_fp, index=False, encoding="utf-8")
    write_template(final, tpl_fp)
    print(f"\n✓ Mis à jour :\n - {sample_fp}\n - {tpl_fp}")

def write_template(df, tpl_fp: Path):
    cols = ['doc_id','actor_id','country','domain_id','date','url',
            'mode','length_words','marker','excerpt_verbatim']
    tpl = df[[c for c in cols if c in df.columns]].copy()
    for c in ['annotator_1_fc','annotator_1_fi','annotator_2_fc','annotator_2_fi','notes','flag_incertain']:
        tpl[c] = ""
    tpl.to_csv(tpl_fp, index=False, encoding="utf-8")

if __name__ == "__main__":
    main()
