# PoC T1 — OSF Preregistration (Extract)

## Scope
UK GOV.UK (Home Office/MoD) + US Congress (RSS subset). Period: 2021-03-01 → 2021-06-30.

## Hypotheses (conative/inhibitory lexicon)
H1: Doc-level Fc/Fi correlate with manual ratings (r ≥ 0.70 on 20 docs).
H2: Actor-level Fc shifts around shocks meet sign expectations.
H3: V2 (context/negation-aware) ≥ V1 on doc-level correlations.

## Data & Features
- `artifacts/real/corpus_final.parquet` (schema: actor_id, period, date, url, text, tokens…)
- `artifacts/real/features_doc.parquet` (Fc, Fi,…)

## Procedures (brief)
- Map V1 (EN-only) → build V2 (negation-aware) → validate vs 20-doc gold → compare V1/V2.

## Outputs expected
- `artifacts/real/lexicon_v2_eval/*`
- `artifacts/real/lexicon_comparison/by_actor_v1_vs_v2.csv`

## Deviations / Notes
- TF-IDF skipped (small sample).
- DOJ/DHS HTML blocked → RSS fallback (prereg-OK).
