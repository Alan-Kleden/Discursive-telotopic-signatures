# Addendum — PoC Discursive Telotopic Signatures
## Axiodynamics Corpus Update — March 2026

**Project:** Discursive Telotopic Signatures (PoC)  
**OSF:** osf.io/rm42h  
**Date:** 2026-03-19  
**Author:** Alan Kleden  
**Status:** Internal working document — pipeline update & ontological grounding

---

## 1. Purpose

This addendum integrates into the PoC project the results and decisions produced during
Axiodynamics project sessions (March 2026) that have a direct impact on:

- the ontological justification for Fc/Fi annotation of institutional texts;
- the pipeline computation formulas (`fc_fi_v3.py`, `n_tel.py`, `run_mock_pipeline.py`);
- the citable reference chain for the corpus.

It does not replace the OSF preregistration (osf.io/rm42h). It is a continuity document
recording decisions made and corrections applied.

---

## 2. Ontological Grounding — Prolegomena v1.0

**Reference:** Kleden, A. (2026). *Axiodynamics — Prolegomena: Ontological Foundations
of the OBJ/Fc/Fi Structure*. Zenodo. doi:10.5281/zenodo.19003446

### 2.1 NSC Condition

The Prolegomena establishes the necessary and sufficient condition for a teleonomic
system S-tau:

> S-tau ⟺ { Mi ∧ Individuation ∧ Persistence } under Fc⊗Fi

The four-level stratification distinguishes:

| Level | Name | Scope |
|-------|------|-------|
| I | Universal teleonomy | Out of annotation scope |
| II | Mémotional zone (threshold 1) | Out of annotation scope |
| III | Explicit OBJ (threshold 2) | Borderline |
| **IV** | **Telos-α / Telos-β** | **Main annotation scope** |

### 2.2 Justification for Institutional Text Annotation

Institutional texts (political speeches, party programmes, legislative texts) are produced
by Level IV teleonomic systems: telos is **conscious, explicit, and representable** at this
level. Fc/Fi annotation is therefore not metaphorical — it captures a real structure of the
teleonomic system.

This argument directly addresses potential reviewer objections regarding the legitimacy of
Fc/Fi annotation in the OSF preregistration context.

> **Canonical reference for OSF/peer review:**
> Kleden (2026), Prolegomena v1.0, §6, doi:10.5281/zenodo.19003446

### 2.3 Fc⊗Fi Orthogonality — Architectural Decision

The Prolegomena validates Fc and Fi as two **orthogonal dimensions**, not as opposing
forces on a single axis:

- **Fc and Fi are NOT hierarchical.** Fc is not "more important" than Fi.
- Any formula reintroducing subtraction (Fc − Fi) is architecturally incompatible with
  the Prolegomena.
- The correct resultant in 2D orthogonal space is: ‖F_total‖ = √((ΣFc)² + (ΣFi)²)

---

## 3. Pipeline Corrections — March 2026

### 3.1 Verification Summary

| File | Point verified | Status |
|------|---------------|--------|
| `n_tel.py` | BETA: euclidean norm √(fc²+fi²)/√2 | ✅ Confirmed |
| `n_tel.py` | GAMMA: cos_t² (not abs(cos_t)) | ✅ Confirmed |
| `n_tel.py` | ambivalence_flag: ratio 2·min(fc,fi)/(fc+fi+ε) | ✅ Confirmed |
| `fc_fi_v3.py` | beta renamed to beta_dir (directional indicator) | ✅ Corrected |
| `fc_fi_v3.py` | f_total = √(fc²+fi²)/√2 added as correct resultant | ✅ Corrected |
| `run_mock_pipeline.py` | n_tel proxy: out["beta"] → out["f_total"] | ✅ Corrected |

### 3.2 Correction Detail — fc_fi_v3.py

**Previous formula (invalid under Fc⊗Fi):**
```
beta = ((fc - fi) + 1.0) / 2.0
```
Anomaly: fc=0.5 / fi=0.5 → beta=0.5 (neutral), same as fc=0 / fi=0.
The subtraction reintroduces a Fc > Fi hierarchy incompatible with Fc⊗Fi.

**Correction applied (Option A — Lakatosian continuity):**

- `beta_dir` (renamed from `beta`): directional polarity indicator kept as Lakatosian
  approximation valid in low-tension unidimensional cases. NOT a resultant.
- `f_total` (new column): Euclidean resultant under Fc⊗Fi orthogonality.
  fc=1 / fi=1 → f_total ≈ 0.707 (maximal decisional potential, not zero).

```python
# beta_dir — directional polarity indicator (Lakatosian approximation)
beta_dir = ((fc - fi) + 1.0) / 2.0

# f_total — correct resultant under Fc⊗Fi orthogonality
f_total = sqrt(fc² + fi²) / sqrt(2)
```

### 3.3 N_tel Compatibility

The angular formula (cos²β) in `n_tel.py` (v5.9) is compatible with Fc⊗Fi orthogonality
and requires no revision. Only the resultant ‖F_total‖ was affected.

### 3.4 Git Commit Reference

```
commit e0cc6d1
branch feat/phase1-editorials
repo   Alan-Kleden/Discursive-telotopic-signatures
date   2026-03-19

fix: Fc⊗Fi orthogonality correction — beta→beta_dir, add f_total, update mock proxy
```

---

## 4. Citable Corpus — DOI Status as of 2026-03-19

| Document | DOI | Status |
|----------|-----|--------|
| Prolegomena v1.0 | 10.5281/zenodo.19003446 | Published |
| v5.7 rev.2 | 10.5281/zenodo.19051159 | Published |
| v5.8 rev.2 | 10.5281/zenodo.19052733 | Published |
| v5.9 rev.2 | 10.5281/zenodo.19053052 | Published |
| v5.10 | To be assigned | In progress |

All citations in PoC documents should use the rev.2 chain for v5.7–v5.9.

---

## 5. Pending Actions

| Action | Priority | Session |
|--------|----------|---------|
| Correct "v5.10 candidate" → "Prolegomena v1.0" in FR/ES annotation guides (4 PDFs) | High | Separate session |
| First deposit of v5.10 (Zenodo) | Medium | Axiodynamics project |
| Update OSF preregistration citations with rev.2 DOIs | Medium | Separate session |

---

## 6. Decision Log Entry

**2026-03-19 — Pipeline correction & ontological grounding**

- Verified `n_tel.py`: all three corrections from OSF Amendment (March 2026) confirmed present.
- Corrected `fc_fi_v3.py`: beta (subtractive, invalid) → beta_dir (directional, Lakatosian)
  + f_total (Euclidean resultant, Fc⊗Fi compliant). Commit e0cc6d1.
- Corrected `run_mock_pipeline.py`: n_tel proxy updated from beta to f_total.
- Prolegomena v1.0 (doi:10.5281/zenodo.19003446) formally integrated as ontological
  justification for Level IV annotation of institutional texts.
- Full DOI chain v5.7–v5.9 rev.2 confirmed citable.

---

## References

Kleden, A. (2026). *Axiodynamics — Prolegomena: Ontological Foundations of the
OBJ/Fc/Fi Structure* (v1.0). Zenodo. doi:10.5281/zenodo.19003446

Kleden, A. (2026). *Axiodynamics v5.7 rev.2 — Nine-Axiom Computational Framework
for Affect-Cognition Dynamics*. Zenodo. doi:10.5281/zenodo.19051159

Kleden, A. (2026). *Axiodynamics v5.8 rev.2 — Telos Definition Extension*. Zenodo.
doi:10.5281/zenodo.19052733

Kleden, A. (2026). *Axiodynamics v5.9 rev.2 — Angular Semantics and Coordinate
Conventions*. Zenodo. doi:10.5281/zenodo.19053052
