# verify_env.py — check versions + spaCy models + NLTK data, no fancy I/O
import json, sys

def check_import(modname, nice=None):
    name = nice or modname
    try:
        m = __import__(modname)
        ver = getattr(m, "__version__", "n/a")
        print(f"[OK]   {name}=={ver}")
        return True, ver
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")
        return False, None

def check_spacy_models(models):
    try:
        import spacy
        ok = True
        for name in models:
            try:
                spacy.load(name)
                print(f"[OK]   spaCy model: {name}")
            except Exception as e:
                print(f"[FAIL] spaCy model: {name} — {type(e).__name__}: {e}")
                ok = False
        return ok
    except Exception as e:
        print(f"[FAIL] spacy not importable for model test: {e}")
        return False

def check_nltk():
    try:
        import nltk
        status = True
        try:
            nltk.data.find("tokenizers/punkt")
            print("[OK]   NLTK: punkt")
        except Exception as e:
            print(f"[FAIL] NLTK: punkt — {type(e).__name__}: {e}")
            status = False
        try:
            nltk.data.find("corpora/stopwords")
            print("[OK]   NLTK: stopwords")
        except Exception as e:
            print(f"[FAIL] NLTK: stopwords — {type(e).__name__}: {e}")
            status = False
        return status
    except Exception as e:
        print(f"[FAIL] NLTK import — {type(e).__name__}: {e}")
        return False

def main():
    print("=== Environment check (telotopic-311) ===")
    print(f"Python: {sys.version.replace(chr(10),' ')}")
    libs = [
        ("spacy", None),
        ("spacy_transformers", "spacy-transformers"),
        ("transformers", None),
        ("tokenizers", None),
        ("torch", None),
        ("pandas", None),
        ("numpy", None),
        ("sklearn", "scikit-learn"),
        ("statsmodels", None),
    ]
    all_ok = True
    for mod, nice in libs:
        ok, _ = check_import(mod, nice)
        all_ok = all_ok and ok

    # Torch CUDA info (optional)
    try:
        import torch
        cuda = bool(torch.cuda.is_available())
        ndev = torch.cuda.device_count() if cuda else 0
        print(f"[INFO] torch CUDA={cuda} devices={ndev}")
    except Exception:
        pass

    # spaCy models
    models_ok = check_spacy_models(["fr_core_news_lg", "en_core_web_lg"])

    # NLTK data
    nltk_ok = check_nltk()

    print("=== Summary ===")
    if all_ok and models_ok and nltk_ok:
        print("ALL GOOD ✔")
        sys.exit(0)
    else:
        print("There are issues. See [FAIL] lines above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
