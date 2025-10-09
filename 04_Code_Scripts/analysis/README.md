# Analysis Pipeline (PoC T1)

This folder hosts the scripts used for the PoC analysis.

## Scripts (order of use)
1. generate_validation_sample.py – draws a stratified sample (n≈20) for manual annotation.
2. enrich_lexicon_v2_enhanced.py – builds an exploratory lexicon v2 (mapped v1 + contextual patterns; TF-IDF optional).
3. validate_lexicon_v2.py – computes doc-level and actor-level scores with v2 and exports histograms/correlations.
4. compare_v1_v2_performance.py – compares v1 vs v2 at actor-level and (optionally) document-level.
5. validate_axio_min.py – confirmatory window-of-shocks test (±30 days) using 07_Config/shocks.csv.

## Typical commands (PowerShell)
conda activate telotopic-311
Set-Location "G:\Mon Drive\Signatures_Telotopiques_POC"
\G:\Mon Drive\Signatures_Telotopiques_POC\04_Code_Scripts = (Resolve-Path ".\04_Code_Scripts")

# 1) Sample for manual annotation
python .\04_Code_Scripts\analysis\generate_validation_sample.py
# fill 07_Config\validation_manual_template.csv and save as 07_Config\validation_manual.csv (optional)

# 2) Exploratory v2 build (small-corpus settings)
python .\04_Code_Scripts\analysis\enrich_lexicon_v2_enhanced.py --quantile-high 0.60 --quantile-low 0.40 --min-pattern-freq 3

# 3) Validate v2
python .\04_Code_Scripts\analysis\validate_lexicon_v2.py

# 4) Compare v1 vs v2
python .\04_Code_Scripts\analysis\compare_v1_v2_performance.py

# 5) Confirmatory shock windows (if shocks.csv present)
python .\04_Code_Scripts\analysis\validate_axio_min.py

## Notes
- v1 (confirmatory) is the preregistered baseline.
- v2 is exploratory and applies /200-token normalization to reduce document-length bias.
- If TF-IDF says “insufficient sample”, v2 = v1.mapped + contextual patterns only.
