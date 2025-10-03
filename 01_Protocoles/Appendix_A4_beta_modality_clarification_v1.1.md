# A4 — β (Modality) via Conative Markers and Directional Alignment (clarification)

**Scope.** This note clarifies the operationalization of the **β (modality)** component without changing hypotheses H1–H4, decision thresholds, or the fixed weights α…ε specified in the preregistration. It is a *pre-data* clarification.

---

## Definitions

For a document \(d\) and a telos \(T\).

- **Directional alignment** \(a(d,T)\in[0,1]\) derived from \(\theta\) (e.g.,
  \[
  a(d,T)=\frac{\cos\theta(d,T)+1}{2}
  \]
  ), or any preregistered projection remapped to \([0,1]\).

- **Conative markers**:
  - **push** \(p(d)\in[0,1]\): modal/actional cues (e.g., *devoir* / *must*, *falloir* / *need*, *accélérer* / *accelerate*, *exiger* / *demand*, *il est temps de…* / *it is time to…*).
  - **inhibit** \(h(d)\in[0,1]\): blocking/negation cues (e.g., *bloquer* / *block*, *empêcher* / *prevent*, *s’opposer* / *oppose*, *refuser de* / *refuse to*, *ne pas* + VERB).

  Marker intensities come from a **fixed lexicon** (lemma/phrase weights \([0,1]\)), negation rules, then **p90 normalization** and **clipping** to \([0,1]\).

- **Cross-term coefficient** \(\lambda\) is **fixed a priori** to \(0.5\) (theoretical compromise between instrumental vs. substantive readings).

---

## Construction of \(F_c, F_i\)

We define forward-concordant and forward-contrary forces as:

\[
F_c(d,T) \;=\; p(d)\cdot a(d,T) \;+\; \lambda\cdot h(d)\cdot\bigl(1-a(d,T)\bigr),
\]

\[
F_i(d,T) \;=\; h(d)\cdot a(d,T) \;+\; \lambda\cdot p(d)\cdot\bigl(1-a(d,T)\bigr),
\]

with \(\lambda=0.5\). By construction, \(F_c,F_i\in[0,1]\).

### Invariants

- **Bounds:** \(F_c,F_i\in[0,1]\).
- **Neutrality:** if \(p=h=0\), then \(F_c=F_i=0\).
- **Monotonicity:** for fixed \(p,h\), \(F_c\) increases with \(a\); \(F_i\) decreases with \(a\).
- **Anti-telos behavior:** if \(a\approx 0\) and \(p>0\), push contributes to \(F_i\) (pushing against \(T\)); if \(a\approx 1\) and \(h>0\), inhibition contributes to \(F_i\) (blocking within the telos direction). The cross-term with \(\lambda\) ensures symmetric credit assignment when push/inhibit target anti-telic content.

---

## Modality scalar for \(N_{\text{tel}}\)

The β component used in the weighted norm \(N_{\text{tel}}\) is derived from \((F_c,F_i)\) as a single scalar:

\[
M(d,T)=F_c(d,T)-F_i(d,T)\in[-1,1], \qquad
\beta(d,T)=\frac{M(d,T)+1}{2}\in[0,1].
\]

Other channels and weights \((\alpha,\gamma,\delta,\varepsilon)\) remain unchanged and fixed *a priori* as preregistered.

---

## Compliance note

This clarification does **not** modify any confirmatory tests (H1–H4), thresholds (\(\Delta\)AUC, \(\Delta R^2\), FDR, etc.), or the fixed weights \(\alpha\ldots\varepsilon\). It only specifies how **β** is computed from already defined quantities (conation + alignment), with \(\lambda=0.5\) fixed *a priori*.

### Implementation and Artifacts (fixed a priori)

- **Code implementing β (modality):**  
  `04_Code_Scripts/features/fc_fi_v3.py` (commit `SHA`, tag `TAG`)

- **Conative lexicon (fixed weights):**  
  `01_Protocoles/lexicon_conative.csv` (commit `SHA`, tag `TAG`)  
  CSV schema: `lemma,type,weight,lang`  
  Example rows:
    devoir,push,0.9,fr
    falloir,push,0.8,fr
    empêcher,inhibit,0.9,fr
    bloquer,inhibit,0.85,fr
    must,push,0.9,en
    prevent,inhibit,0.9,en
    
- **Unit tests (bounds, neutrality, monotonicity, limit cases):**  
`tests/test_beta_modality.py` (commit `SHA`, tag `TAG`)

- **Fixed cross-term coefficient:**  
λ = 0.5 (set a priori; not tuned)

- **Directional alignment a(d, T):**  
Derived from the preregistered theta; we only remap to `[0,1]` as:
`a = (cos(theta) + 1) / 2`. This does not alter geometry, thresholds, or hypotheses.

- **Fc/Fi construction (symmetric form):**
Fc(d,T) = p(d) * a(d,T) + λ * h(d) * (1 - a(d,T))
Fi(d,T) = h(d) * a(d,T) + λ * p(d) * (1 - a(d,T))

with `λ = 0.5`, `p,h ∈ [0,1]`, hence `Fc, Fi ∈ [0,1]`.

- **Scalar used for β in N_tel:**
M(d,T) = Fc(d,T) - Fi(d,T) # in [-1, 1]
β(d,T) = (M(d,T) + 1) / 2 # in [0, 1]


**Provenance note.** The above artifacts were committed and tagged **before any target-corpus collection or feature extraction** (date: `2025-10-03`). OSF upload references Git tag `TAG`.
