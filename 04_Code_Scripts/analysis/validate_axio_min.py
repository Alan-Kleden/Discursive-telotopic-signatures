import os, re, math
import pandas as pd
import numpy as np
from datetime import timedelta

ROOT  = os.getcwd()
C_PAR = os.path.join("artifacts","real","corpus_final.parquet")
F_PAR = os.path.join("artifacts","real","features_doc.parquet")
LEX   = os.environ.get("CONATIVE_LEXICON_PATH", r"07_Config\lexicons\lexicon_conative_v1.clean.csv")
SHOCK = r"07_Config\actors_and_shocks\shocks.csv"  # présent dans le repo

# -------- load corpus + features --------
dfc = pd.read_parquet(C_PAR)
dff = pd.read_parquet(F_PAR)
df  = pd.merge(
    dfc, dff.drop_duplicates(["actor_id","date","url"]),
    on=["actor_id","date","url"], how="left", suffixes=("","_f")
)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# -------- conative intensity --------
use_fcfi = all(c in dff.columns for c in ["fc","fi"])
if use_fcfi:
    df["conative_intensity"] = df[["fc","fi"]].sum(axis=1)
else:
    # Lexique → fréquence pour 1k tokens
    lex = pd.read_csv(LEX)
    col = next((c for c in ["term","lemma","token"] if c in lex.columns), None)
    terms = [] if col is None else lex[col].dropna().astype(str).unique().tolist()
    pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms if t.strip()) + r")\b", flags=re.IGNORECASE) if terms else None
    def rate(text, toks):
        if not isinstance(text, str) or not isinstance(toks,(int,float)) or toks<=0 or pat is None: 
            return 0.0
        return (len(pat.findall(text)) / toks) * 1000.0
    df["conative_intensity"] = [rate(t, tok) for t, tok in zip(df["text"], df["tokens"])]

# -------- shocks (auto-détection colonnes) --------
sh = pd.read_csv(SHOCK)

# date: essaye ces noms dans l'ordre
date_col = next((c for c in ["date","shock_date","event_date","when"] if c in sh.columns), None)
if date_col is None:
    raise RuntimeError("Aucune colonne date trouvée dans shocks.csv (attendu: date/shock_date/event_date/when)")
sh[date_col] = pd.to_datetime(sh[date_col], errors="coerce")
sh = sh.dropna(subset=[date_col]).copy()

# acteur: optionnel → si absent, on fera un marquage global
actor_col = next((c for c in ["actor_id","actor","who","source","entity","organization"] if c in sh.columns), None)
if actor_col is None:
    sh["actor_id"] = "ALL"
    actor_col = "actor_id"
else:
    # normalise vers actor_id quand possible (si valeurs déjà de type 'UK_MoD', etc., on garde)
    sh["actor_id"] = sh[actor_col].astype(str).str.strip()

# -------- tagging fenêtre ±30 jours --------
win_days = 30
shocks_by_actor = {
    k: v[date_col].dropna().tolist() 
    for k,v in sh.groupby("actor_id")
}

def in_window(row):
    a, d = row["actor_id"], row["date"]
    if pd.isna(d): 
        return False
    # si on a des chocs spécifiques à l'acteur
    if a in shocks_by_actor:
        return any(abs((d - sd).days) <= win_days for sd in shocks_by_actor[a])
    # sinon, fallback global
    if "ALL" in shocks_by_actor:
        return any(abs((d - sd).days) <= win_days for sd in shocks_by_actor["ALL"])
    return False

df["in_window_±30"] = df.apply(in_window, axis=1)

# -------- résumés --------
by_act = df.groupby("actor_id")["conative_intensity"].agg(["count","mean","median","std"]).round(3)
win = df.groupby("in_window_±30")["conative_intensity"].agg(["count","mean","median","std"]).round(3)

# effet (Cohen's d) in-window vs off-window
w = df[df["in_window_±30"]==True]["conative_intensity"].astype(float).to_numpy()
o = df[df["in_window_±30"]==False]["conative_intensity"].astype(float).to_numpy()
def cohend(x,y):
    if len(x)<2 or len(y)<2: return float("nan")
    mx,my = np.nanmean(x), np.nanmean(y)
    sx,sy = np.nanstd(x, ddof=1), np.nanstd(y, ddof=1)
    nx,ny = len(x), len(y)
    sp = np.sqrt(((nx-1)*sx*sx + (ny-1)*sy*sy)/(nx+ny-2)) if (nx+ny-2)>0 else np.nan
    return (mx-my)/sp if (sp and not math.isclose(sp,0)) else float("nan")
d = cohend(w,o)

print("# === AXIO VALIDATION (MINI-PACK) ===")
print("\n[1] Intensité par acteur (conative_intensity):\n", by_act)
print("\n[2] Fenêtre chocs (±30j) vs hors-fenêtre:")
print(win.assign(cohens_d_overall=d))
print("\n[3] Corrélations internes (si features fc/fi/θ):")
if all(c in df.columns for c in ["fc","fi"]):
    have_theta = "theta" in df.columns
    cols = ["fc","fi"] + (["theta"] if have_theta else [])
    cmat = df[cols].corr(numeric_only=True).round(3)
    print(cmat)
else:
    print("fc/fi non présents → validation via lexique uniquement (prereg OK).")

# exports OSF
out_dir = os.path.join("artifacts","real","validation")
os.makedirs(out_dir, exist_ok=True)
by_act.to_csv(os.path.join(out_dir,"by_actor_conative.csv"))
win.assign(cohens_d_overall=d).to_csv(os.path.join(out_dir,"window_vs_off.csv"))
if all(c in df.columns for c in ["fc","fi"]):
    cmat.to_csv(os.path.join(out_dir,"corr_fc_fi_theta.csv"))
print("\n[OK] exports →", out_dir)
