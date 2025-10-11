# OSF Package — Annexes
_Last updated: 2025-10-10 · Version: v1.1 (Phase 3 start)_

## Internal navigation (relative links)
Use these when browsing inside **Files ▸ OSF Storage** (project file tree).

- [A1_Prereg_Extract.md](01_Preregistration_Protocol/A1_Prereg_Extract.md)
- [A2_T1T2_Calendar.md](A2_T1T2_Calendar.md)
- [A3_Telos_Annotation_Protocol.md](A3_Telos_Annotation_Protocol.md)
- [A4_Feature_Definitions.md](A4_Feature_Definitions.md)
- [A5_Data_Dictionary.md](A5_Data_Dictionary.md)
- [Progress_Update_Phase2.md](Progress_Update_Phase2.md)
- [Harvesting_v1.1.md](Harvesting_v1.1.md)

---

## Direct OSF links (canonical URLs)
**Note:** If a link doesn’t open on left-click in the OSF preview, **right-click → Open link in new tab**.

- [A1_Prereg_Extract.md](https://osf.io/rm42h/files/osfstorage/68e77774bfc8d416aae47400/)
- [A2_T1T2_Calendar.md](https://osf.io/rm42h/files/osfstorage/68e7732b607d8ac8d6c51c7e/)
- [A3_Telos_Annotation_Protocol.md](https://osf.io/rm42h/files/osfstorage/68e7733083343861a0a0db60/)
- [A4_Feature_Definitions.md](https://osf.io/rm42h/files/osfstorage/68e773303f9a31503ba0db1c/)
- [A5_Data_Dictionary.md](https://osf.io/rm42h/files/osfstorage/68e77334b0342f2e1cde4df3/)
- [Progress_Update_Phase2.md](https://osf.io/rm42h/files/osfstorage/68e77345403137d61fc517da/)
- [Harvesting_v1.1.md](https://osf.io/rm42h/files/osfstorage/68ea0004f48636971ec51dcd)

---

## Sampling frame (clarification)
We analyze **public texts (2020–2024)** from **≥10 actors** across **≥4 domains**.  
Eligible channels include **speeches**, **press releases/newsroom items**, **op-eds/columns**, **party/NGO blogs**, **parliamentary debates/hearings**, and **Q&A/transcripts**.  
**Procedural materials** (codes/guidances/manuals) are allowed but **capped at ≤10%** as controls.  
Inclusion is **independent of outcomes**; no selection uses model scores or label previews.

## Harvesting protocol
Per **actor–year–domain**, we retrieve **up to K = 3 items per channel** via **uniform queries (fixed seed)**, selecting the first **N = 50** eligible results (**deduplicated; minimum length L = 120 words**).  
Queries, timestamps, and URLs are logged. A **SHA256 data-freeze** precedes confirmatory analyses.

### Blinding & no-peeking
Features and aggregated performance metrics remain hidden until the final confirmatory run. Placebos must fail (AUC < 0.55). Temporal split and seeds are fixed.

### Annotators (not participants)
Volunteer annotators act as **research coders** to produce a manual gold standard (inter-rater gate **κ ≥ 0.70**) **prior to** confirmatory tests.  
Annotators are **not study participants**; only operational contact info is handled off-OSF.

---

## Project structure (key files)
- `Harvesting_v1.1.md` — Data collection protocol (K/N/L/seed; rationale)  
- `actor_roster.csv` — Actors & domains  
- `shocks.csv` — Temporal markers  
- `lexicon_conative_v1.clean.csv` — FC/FI lexicon (V1)  
- `data/logs/harvest_log.csv` — Traceability log  
- `freeze/manifest_SHA256.txt` — Data-freeze checksums