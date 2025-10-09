import os, sys, json, textwrap, importlib.util as iu, traceback
print("="*72)
print("CWD              :", os.getcwd())
print("CONDA ENV        :", os.environ.get("CONDA_DEFAULT_ENV"))
print("PYTHONPATH       :", os.environ.get("PYTHONPATH"))
print("="*72)

# --- Versions clés ---
def v(pk):
    try:
        m = __import__(pk)
        return getattr(m, "__version__", "n/a")
    except Exception as e:
        return f"ERR: {e.__class__.__name__}"

mods = ["pandas","sklearn","torch","transformers","sentence_transformers","spacy"]
vers = {m: v(m) for m in mods}
print("VERSIONS:")
for k in mods:
    print(f"  {k:22s} -> {vers[k]}")
print("-"*72)

# Torch quick check
try:
    import torch
    print("torch.cuda.is_available():", torch.cuda.is_available())
    print("torch.__config__.show():")
    print(textwrap.indent(getattr(torch.__config__,"show")() or "", "  "), end="")
except Exception as e:
    print("Torch check error:", e)
print("-"*72)

# sentence-transformers smoke test (sans download long)
try:
    from sentence_transformers import SentenceTransformer
    # On évite de télécharger; simple import suffit
    print("sentence-transformers import: OK")
except Exception as e:
    print("sentence-transformers import: FAIL ->", e)
print("-"*72)

# spaCy smoke test (modèle déjà installé ?)
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_lg")
        print("spacy en_core_web_lg: OK (", len(nlp.pipe_names), "pipes )")
    except Exception as ee:
        print("spacy model load FAIL:", ee)
except Exception as e:
    print("spacy import FAIL:", e)
print("-"*72)

# --- Paquet local "collect" ---
def spec(s): 
    try: return iu.find_spec(s) is not None
    except: return False
print("Local packages visible via PYTHONPATH?")
print("  collect                       :", spec("collect"))
print("  collect.scrape_press_generic  :", spec("collect.scrape_press_generic"))
print("-"*72)

# --- Fichiers clés (corpus/features) ---
from pathlib import Path
def chk(path):
    p = Path(path);  ex = p.exists()
    msg = f"OK ({p.stat().st_size} bytes)" if ex else "MISSING"
    print(f"{path:55s} -> {msg}")
    return ex

ok_corpus  = chk("artifacts/real/corpus_final.parquet")
ok_feat    = chk("artifacts/real/features_doc.parquet")
ok_v1      = chk("07_Config/lexicons/lexicon_conative_v1.clean.csv")
ok_v1m     = chk("07_Config/lexicons/lexicon_conative_v1.mapped.csv")
ok_v2      = chk("07_Config/lexicons/lexicon_conative_v2_enhanced.csv")
ok_manual  = chk("07_Config/validation_manual.csv")

print("-"*72)
import pandas as pd
if ok_corpus:
    try:
        dfc = pd.read_parquet("artifacts/real/corpus_final.parquet")
        print("corpus_final.parquet ->", dfc.shape, "| cols:", list(dfc.columns)[:10], "...")
    except Exception as e:
        print("READ corpus_final FAIL:", e)
if ok_feat:
    try:
        dff = pd.read_parquet("artifacts/real/features_doc.parquet")
        has = {c:(c in dff.columns) for c in ["actor_id","date","url","fc","fi","theta"]}
        print("features_doc.parquet ->", dff.shape, "| has cols:", has)
    except Exception as e:
        print("READ features_doc FAIL:", e)

print("-"*72)
# --- Lexicon v1 audit & mapping comptage ---
if ok_v1:
    try:
        v1 = pd.read_csv("07_Config/lexicons/lexicon_conative_v1.clean.csv", encoding="utf-8", on_bad_lines="skip")
        print("v1 columns:", list(v1.columns))
        print("v1 head:", v1.head(3).to_dict(orient="records"))
        type_col = "type" if "type" in v1.columns else None
        lex_col  = next((c for c in ["lemma","term","token"] if c in v1.columns), None)
        w_col    = "weight" if "weight" in v1.columns else None
        if type_col and lex_col:
            raw_counts = v1[type_col].value_counts(dropna=False).to_dict()
            print("v1 type raw counts:", raw_counts)
            # mapping light -> fc/fi
            m = {"push":"fc","fc":"fc",
                 "pull":"fi","oppose":"fi","critic":"fi",
                 "forward":"fc","contra":"fi"}
            v1["__mapped__"] = v1[type_col].map(m).fillna(v1[type_col])
            mapped = v1[v1["__mapped__"].isin(["fc","fi"])]
            print(f"v1 mapped -> {len(mapped)} entrées (fc={(mapped['__mapped__']=='fc').sum()}, fi={(mapped['__mapped__']=='fi').sum()})")
        else:
            print("v1 mapping SKIP (colonnes manquantes).")
    except Exception as e:
        print("v1 audit FAIL:", e)

print("-"*72)
# --- Mini cohérence “join key” corpus vs features ---
try:
    if ok_corpus and ok_feat:
        dfc2 = pd.read_parquet("artifacts/real/corpus_final.parquet")[["actor_id","date","url"]]
        dff2 = pd.read_parquet("artifacts/real/features_doc.parquet")[["actor_id","date","url"]]
        inter = len(pd.merge(dfc2, dff2, on=["actor_id","date","url"], how="inner"))
        print(f"Join corpus x features (actor_id,date,url) -> overlap rows = {inter}")
except Exception as e:
    print("Join check FAIL:", e)

print("="*72)
