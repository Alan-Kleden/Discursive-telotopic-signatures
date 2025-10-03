from pathlib import Path
import json

def main():
    h = json.loads(Path("artifacts/mock/hypotheses.json").read_text(encoding="utf-8"))
    s = json.loads(Path("artifacts/mock/scores_baselines.json").read_text(encoding="utf-8"))
    md = f"""# PoC — Résultats (mock)

## Baselines (AUC)
- Télotopique (linéaire): **{s['AUC_telotopic_linear']:.3f}**
- Style-only: **{s['AUC_style_only']:.3f}**
- Party-line: **{s['AUC_party_line']:.3f}**

## H1 — ΔAUC (Télotopique − Style)
- ΔAUC: **{h['H1_delta_auc_telotopic_minus_style']:.3f}**
- IC95%: **[{h['H1_delta_auc_ci95'][0]:.3f}, {h['H1_delta_auc_ci95'][1]:.3f}]**

## H3 — LRT (fenêtres, GLM binomial sur proportions)
- χ²: **{h['H3_lrt_stat']:.3f}**
- p: **{h['H3_lrt_p']:.3e}**

_Généré automatiquement depuis artifacts/mock/*._
"""
    out = Path("artifacts/mock/report_poc.md")
    out.write_text(md, encoding="utf-8")
    print(f"OK: {out}")

if __name__ == "__main__":
    main()
