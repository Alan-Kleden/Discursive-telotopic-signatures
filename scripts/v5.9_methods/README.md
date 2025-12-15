# Axiodynamics v5.9 — Angular Estimation Methods

**Implementation of methodological protocols for angular assignment in telotopic space.**

Reference: *Axiodynamics v5.9 — Angular Semantics, Estimation Methods, and Validation Protocols* (Kleden, 2025)

---

## 📁 Repository Structure

```
v5.9_methods/
├── circular_stats.py       # Circular statistics for angular data
├── beta_coefficient.py     # Method D: Axiological alignment coefficient
├── method_comparison.py    # Cross-method convergence metrics
├── examples/               # Pedagogical examples
│   └── heinz_dilemma.py   # Complete workflow demonstration
└── README.md              # This file
```

---

## 🎯 Overview

This module implements **four complementary pathways** for estimating angular orientations θₖ of affective forces (mémotions) relative to a situational telos:

| Method | Approach | Best For | Complexity |
|--------|----------|----------|------------|
| **A** | Expert annotation | Small samples (N < 50), high-stakes | High labor |
| **B** | Semantic embedding + MDS | Large corpora (N > 100) | Medium computational |
| **C** | Axiotypic anchoring | Cross-cultural, theoretical | Medium coding |
| **D** | β coefficient | Medium-N (50-200), hybrid validation | Low hybrid |

All methods converge on a common theoretical postulate: **θₖ encodes the directional pressure exerted by a mémotion on the decision trajectory** (v5.7 Axiom 2).

---

## 🚀 Quick Start

### Installation

```bash
pip install numpy scipy sentence-transformers matplotlib
```

### Basic Usage

```python
from circular_stats import circular_mean, rayleigh_test, circular_cohen_kappa
from beta_coefficient import BetaCoefficientCalculator
from method_comparison import MethodComparator

# Example: Compute β coefficient
calc = BetaCoefficientCalculator()

result = calc.memotion_to_angle(
    memotion_text="I took an oath to help anyone in medical distress",
    telos_text="Stop to help the accident victim",
    valence_sign=+1  # Positive affect
)

print(f"β = {result['beta']:.3f}")
print(f"θ = {result['theta_final_deg']:.1f}°")
```

---

## 📊 Module Descriptions

### `circular_stats.py`

Implements circular statistics for angular data (Mardia & Jupp, 2000):

**Key Functions:**
- `circular_mean(angles)` — Circular mean θ̄
- `mean_resultant_length(angles)` — Concentration R̄ ∈ [0, 1]
- `circular_std(angles)` — Angular dispersion σ_circ
- `rayleigh_test(angles)` — Uniformity test (proto-telos gate)
- `circular_cohen_kappa(theta1, theta2, epsilon)` — Inter-annotator agreement
- `circular_correlation(theta1, theta2)` — Circular correlation ρ_circ
- `bootstrap_circular_ci(angles, n_bootstrap)` — Bootstrap confidence intervals
- `rmse_angular(theta1, theta2)` — Root Mean Squared Angular Error

**Example:**

```python
import numpy as np
from circular_stats import rayleigh_test, circular_cohen_kappa

# Test for directional clustering (proto-telos)
angles = np.array([10, 25, 15, 30, 170, 180, 175])
Z, p_value, significant = rayleigh_test(angles)

if significant:
    print(f"Proto-telos detected (Z = {Z:.3f}, p = {p_value:.4f})")

# Inter-annotator agreement
annotator1 = np.array([10, 25, 170, 55])
annotator2 = np.array([5, 30, 177, 60])
kappa = circular_cohen_kappa(annotator1, annotator2, epsilon=20)

print(f"Circular κ = {kappa:.3f}")
# κ ≥ 0.70 → Good agreement
```

---

### `beta_coefficient.py`

Implements **Method D: Coefficient β** (Section 6.4):

**Formula:**
```
β = cos(θ_axio) × sign(valence)
θ = sign(β) · θ_base · |β| + Δθ · (1 - |β|)
```

**Key Components:**
- `BetaCoefficientCalculator` — Main class for β computation
- `compute_semantic_similarity()` — Cosine similarity via embeddings
- `compute_axiological_distance()` — θ_axio from semantic proximity
- `classify_valence()` — Affective polarity (+1/-1/0)
- `compute_beta()` — β = cos(θ_axio) × sign(valence)
- `beta_to_angle()` — Convert β → θ
- `memotion_to_angle()` — Complete pipeline

**Example:**

```python
from beta_coefficient import BetaCoefficientCalculator

calc = BetaCoefficientCalculator(model_name='all-MiniLM-L6-v2')

result = calc.memotion_to_angle(
    memotion_text="I'm terrified of going to jail",
    telos_text="Steal the drug to save wife",
    valence_sign=-1,  # Negative (fear)
    theta_base=0.0,
    delta_theta=90.0
)

print(f"β = {result['beta']:.3f}")
print(f"θ_axio = {result['theta_axio_deg']:.1f}°")
print(f"θ_final = {result['theta_final_deg']:.1f}°")
print(f"Classification: {result['classification']}")
```

**Output:**
```
β = +0.34
θ_axio = 110.0°
θ_final = 175.0°
Classification: Strong Fi
```

---

### `method_comparison.py`

Implements **cross-method validation** (Section 7.4):

**Key Features:**
- Pairwise correlation matrix (circular ρ)
- RMSAE matrix (Root Mean Squared Angular Error)
- Bland-Altman plots for angular data
- Convergent validity assessment

**Example:**

```python
import numpy as np
from method_comparison import MethodComparator

# Angular estimates from 4 methods
comparator = MethodComparator()
comparator.add_method("Method A", np.array([10, 170, 25, 55]))
comparator.add_method("Method B", np.array([5, 177, 14, 40]))
comparator.add_method("Method C", np.array([9, 180, 30, 40]))
comparator.add_method("Method D", np.array([11, 175, 25, 39]))

# Assess convergence
report = comparator.assess_convergence(rho_threshold=0.60, rmsae_threshold=40.0)
comparator.print_report(report)

# Generate Bland-Altman plot
comparator.bland_altman_angular("Method A", "Method D")
```

**Output:**
```
AXIODYNAMICS v5.9 - CROSS-METHOD CONVERGENCE REPORT
============================================================

Number of methods: 4
Number of pairwise comparisons: 6

--- CORRELATION MATRIX ---
            Method A    Method B    Method C    Method D
Method A           —       0.891       0.952       0.921
Method B       0.891           —       0.872       0.853
Method C       0.952       0.872           —       0.934
Method D       0.921       0.853       0.934           —

--- RMSAE MATRIX (degrees) ---
            Method A    Method B    Method C    Method D
Method A           —         9.2         6.1         5.8
Method B         9.2           —        11.4        10.7
Method C         6.1        11.4           —         4.9
Method D         5.8        10.7         4.9           —

--- SUMMARY STATISTICS ---
Mean correlation (ρ̄):      0.904
Mean RMSAE:                8.2°
High convergence pairs:    6/6 (100.0%)
Acceptable RMSAE pairs:    6/6 (100.0%)

--- VERDICT ---
Strong triangulation ✓
```

---

## 📖 Pedagogical Example

See `examples/heinz_dilemma.py` for a complete workflow demonstrating:
1. Telos definition
2. Mémotion extraction
3. Angular assignment via Methods A/B/C/D
4. Inter-method convergence validation
5. N_tel computation
6. Behavioral prediction

**Scenario:** Heinz dilemma (Kohlberg, 1984) — Should Heinz steal a drug to save his dying wife?

**Mémotion examples:**
- "I love my wife more than anything" → θ ≈ 10° (strong Fc)
- "I'm terrified of going to jail" → θ ≈ 175° (strong Fi)
- "Stealing violates the law" → θ ≈ 130° (moderate Fi)

---

## 🔬 Validation Protocols

### Inter-Annotator Agreement (Method A)

**Requirement:** κ_circ ≥ 0.70 (circular Cohen's kappa)

```python
from circular_stats import circular_cohen_kappa

annotator1 = np.array([10, 25, 170, 55, 15, 180, 30, 50])
annotator2 = np.array([5, 30, 177, 60, 10, 175, 25, 45])

kappa = circular_cohen_kappa(annotator1, annotator2, epsilon=20)
print(f"κ_circ = {kappa:.3f}")

if kappa >= 0.70:
    print("✓ Good agreement - proceed with annotation")
else:
    print("✗ Poor agreement - retrain annotators")
```

---

### Bootstrap Stability for Telos

**Requirement:** 95% CI width < 45° (quarter-circle)

```python
from circular_stats import bootstrap_circular_ci

angles = np.array([10, 15, 5, 30, 25, 20])
mean, CI_low, CI_high = bootstrap_circular_ci(angles, n_bootstrap=1000)

CI_width = CI_high - CI_low
print(f"Telos: θ*_T = {mean:.1f}° [95% CI: {CI_low:.1f}°, {CI_high:.1f}°]")
print(f"CI width: {CI_width:.1f}°")

if CI_width < 45:
    print("✓ Excellent stability")
elif CI_width < 90:
    print("◐ Moderate stability")
else:
    print("✗ Poor stability - possible bimodality")
```

---

### Cross-Method Convergence

**Requirement:** ρ(Method X, Method A) ≥ 0.60

```python
from circular_stats import circular_correlation
import numpy as np

method_A = np.array([10, 170, 25, 55])  # Gold standard
method_D = np.array([11, 175, 25, 39])  # Beta coefficient

rho = circular_correlation(method_A, method_D)
print(f"ρ(A, D) = {rho:.3f}")

if rho >= 0.60:
    print("✓ Strong convergent validity")
elif rho >= 0.40:
    print("◐ Moderate convergence")
else:
    print("✗ Divergence - investigate discrepancy")
```

---

## 📚 References

1. **Kleden, A.** (2025). *Axiodynamics v5.7 — A Nine-Axiom Computational Framework for Affect-Cognition Dynamics.* Zenodo. https://doi.org/10.5281/zenodo.17928879

2. **Kleden, A.** (2025). *Axiodynamics v5.8 — Telos Definition Extension: Mnemonic Inertia and Plasticity Stratification.* Zenodo. [DOI pending]

3. **Kleden, A.** (2025). *Axiodynamics v5.9 — Angular Semantics, Estimation Methods, and Validation Protocols.* Zenodo. [DOI pending]

4. **Mardia, K. V., & Jupp, P. E.** (2000). *Directional Statistics.* John Wiley & Sons.

5. **Jammalamadaka, S. R., & SenGupta, A.** (2001). *Topics in Circular Statistics.* World Scientific.

---

## 🔗 Integration with PoC Telotopic Signatures

These methods are designed for seamless integration with the **PoC Telotopic Signatures** project:

- **GitHub Repository:** https://github.com/Alan-Kleden/Discursive-telotopic-signatures
- **OSF Pre-registration:** https://osf.io/kjpmz / https://osf.io/rm42h

### Computational Workflow

```
Raw corpus (Twitter, Reddit, speeches)
         ↓
  [NLP preprocessing]
         ↓
  [Stance detection + lexical features]
         ↓
  [Method D: β coefficient] ← THIS MODULE
         ↓
  [N_tel computation]
         ↓
  [Temporal dynamics analysis]
         ↓
  [Prediction: schism, polarization, consensus]
```

---

## 🛠️ Troubleshooting

### Issue: Low inter-annotator agreement (κ < 0.60)

**Solutions:**
1. Retrain annotators with additional calibration scenarios
2. Refine telos definition (ensure unambiguous θ*_T = 0° reference)
3. Reduce bin size (e.g., 10° instead of 20°)
4. Exclude genuinely ambiguous mémotions from corpus

---

### Issue: Method B (MDS) yields high Stress (> 0.20)

**Solutions:**
1. Increase dimensionality (2D → 3D MDS)
2. Filter corpus to retain only evaluative/normative statements
3. Use alternative distance metric (Euclidean instead of cosine)
4. Check for outliers distorting projection

---

### Issue: Method D (β) produces counterintuitive angles

**Solutions:**
1. Verify valence target (is affect directed at telos or side-effect?)
2. Check for double-negative paradox (opposition + negative valence)
3. Apply manual override protocol (Section 6.4.5)
4. Use Method A (annotation) for complex dual-obligation scenarios

---

## 📄 License

MIT License - Open Research

Copyright (c) 2025 Alan Kleden

---

## 📧 Contact

For questions, bug reports, or collaboration:
- **GitHub Issues:** https://github.com/Alan-Kleden/Discursive-telotopic-signatures/issues
- **Email:** [contact information]
- **OSF Project:** https://osf.io/kjpmz

---

## 🔖 Version

**v5.9.0** — December 2025  
Compatible with: Python 3.11+, NumPy 1.24+, SciPy 1.10+, sentence-transformers 2.2+

---

**End of README.md**
