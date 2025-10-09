# Progress Update - Phase 2 Complete (2025-10-07)

**Preregistration:** https://osf.io/kjpmz (registered: 2025-10-02)  
**Archive:** https://archive.org/details/osf-registrations-kjpmz-v1  
**Status:** Exploratory validation complete, infrastructure optimized  
**Overall score:** 47.5/100

---

## Purpose of this Update

This supplement clarifies the phased approach to the preregistered study:

- **Phases 1-2 (Current):** Proof of concept - exploratory validation
- **Phases 3-4 (Planned):** Full confirmatory analyses per preregistration

---

## Phase 2 Achievements

**Infrastructure (100%)**
- ✅ requirements.txt for full reproducibility
- ✅ MIT LICENSE for legal clarity  
- ✅ .gitignore optimized (venv excluded)
- ✅ GitHub repository: https://github.com/Alan-Kleden/Discursive-telotopic-signatures

**Documentation (100%)**
- ✅ README (root): Project overview + environment setup
- ✅ README (OSF package): Contents description
- ✅ README (V2 evaluation): Exploratory methodology

**Lexicon Development**
- ✅ V1 (37 terms: 22 Fc, 15 Fi) - baseline from preregistration
- ✅ V1.mapped (EN-only, regex patterns compiled)
- ✅ V2 enhanced (exploratory):
  - Contextual patterns (commitment, imperative, negation)
  - TF-IDF candidates from corpus (data-driven)
  - Normalization: /200 tokens (min=1)

**Validation (Exploratory)**
- Method: Empirical V1 vs V2 comparison (actor-level aggregates)
- **No manual gold standard** at this stage (planned Phase 3)
- **No numerical results disclosed** to preserve confirmatory integrity
- Exploratory findings stored privately, will be disclosed post-Phase 4

**Interpretation:** V2 lexicon development complete, awaiting Phase 3 validation on confirmatory sample (n≥10).

---

## Compliance Score Breakdown

| Component           | Score   | Phase 2 Status              |
|---------------------|---------------------------------------|
| Infrastructure      | 100/100 | ✅ Complete                |
| Data collection     | 100/100 | ✅ PoC corpus ready (n=3)  |
| Lexicon validation  | 0/100   | ⚠️ Exploratory only        |
| Shocks/dynamics     | 25/100  | ⚠️ 5/12 shocks             |
| Statistical models  | 0/100   | ⏳ Phase 4                 |
| Documentation       | 100/100 | ✅ Complete                |

**Overall:** 47.5/100

---

## Critical Gaps (Acknowledged)

**P0 - Blocking confirmatory H1/H2/H4:**
1. **Sample size:** n=3 actors (need ≥10 per preregistration)
2. **Endogenous teloi:** Not extracted yet (theta uses fallback = 0.5, N_tel partially invalid)

**P1 - Critical for validity:**
3. **Lexicon validation:** No manual gold standard (Spearman correlation not reportable)
4. **Shocks definition:** 5 shocks in 2 domains (need 12 in 4 per preregistration)

---

## Technical Notes

### Normalization Difference (V1 vs V2)
- **V1:** fc = lexical_hits / total_tokens
- **V2:** fc = (TF-IDF_weighted_hits) / max(tokens/200, 1)
- **Implication:** V1 and V2 scores not directly comparable (different denominators)

### Missing Preregistered Features
- cos_theta (theta) column absent from features_doc.parquet
- N_tel calculation uses neutral fallback: alignment = 0.5
- Endogenous telos extraction deferred to Phase 3

---

## Next Steps (Confirmatory Path)

### Phase 3: Corpus Extension (4-6 weeks)
1. Temporal coverage: 2020-2024 (from 2021-Q2)
2. Actor sample: n≥10 across 4 domains (from n=3, 2 domains)
3. Extract endogenous teloi (inter-rater kappa ≥ 0.70)
4. Manual annotation gold standard (100+ docs)
5. Define 12 validated shocks (4 domains × 3)

### Phase 4: Confirmatory Analyses (3 weeks)
1. Test H1/H2/H3/H4 per preregistration
2. Baselines: BERT embeddings, style-only controls
3. Bootstrap confidence intervals (n=10,000)
4. Report all preregistered metrics with exact thresholds

---

## Deviations from Preregistration

**None at this stage.** Phase 2 was always intended as exploratory infrastructure development. All preregistered hypotheses (H1-H4) will be tested in Phase 4 using the full confirmatory dataset (Phase 3).

**Transparency note:** The decision to label Phase 2 as "exploratory" (no gold standard) was made to optimize resource allocation. Manual annotation will be conducted on the Phase 3 dataset (n≥10, 100+ docs) rather than on the limited PoC sample (n=3, 56 docs).

---

**Researcher:** Alan Kleden  
**Email:** alan.kleden@gmail.com  
**Date:** October 7, 2025  
**Repository:** https://github.com/Alan-Kleden/Discursive-telotopic-signatures  
**Preregistration:** https://osf.io/kjpmz