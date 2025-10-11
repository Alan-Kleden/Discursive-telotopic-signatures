# Harvesting Protocol (Public Text Collection)
_Last updated: 2025-10-10 • Version 1.1_

**Related documents**
- Preregistration: https://osf.io/kjpmz (registered 2025-10-02)
- Working project: https://osf.io/rm42h

## 1) Scope & principles
- **Scope**: Public texts (2020–2024), ≥10 actors across ≥4 domains.
- **Confirmatory language**: **EN-only** (V1 lexicon is EN); FR may be explored post-hoc (exploratory).
- **Outcome-independent inclusion**: selection never uses model scores or manual labels.
- **Procedural materials** (codes/guidances/manuals): allowed but **capped at ≤10%** as controls.
- **Blinding / no-peeking**: features & aggregate metrics are hidden until the confirmatory run.

## 2) Channels (eligible formats)
- **Speeches** (addresses, statements)
- **Press releases / newsroom items**
- **Op-eds / columns** (official blogs, party/NGO outlets)
- **Party/NGO blogs** (position pieces)
- **Parliamentary debates / hearings / transcripts**
- **Q&A / briefings / official statements**
- (Controls, ≤10%): **codes**, **guidances**, **manuals**, **policy handbooks**

## 3) Fixed parameters
- **K (per actor–year–domain–channel)**: _up to_ **3** items  
- **N (search cut)**: first **50** eligible results per query  
- **L (min length)**: **120 words** (post-clean)  
- **Seed**: **42** (wherever randomness is involved)  
- **Dates**: 2020-01-01 → 2024-12-31 (publication date, not crawl time)

## 4) Inclusion / exclusion
- **Include**: public, textual, EN, ≥ L words, unique after dedup (URL **and** sha256 of **normalized text**).  
- **Exclude**: non-public paywalls; scanned PDFs **unreadable**; duplicates/near-dupes; pure metadata pages; multimedia without transcript.  
- **Normalized text** (for hashing): lowercased, HTML removed, boilerplate stripped, collapsed whitespace.
- **Meta-fields required**: `actor_id, actor_name, domain, channel, date, url, title, word_count`.

## 5) Uniform queries (examples)
For each **actor** and **channel**, run standardized queries and record the **exact** query string in the log (seeded where applicable).

## 6) Procedure per actor–year–domain–channel
1) Apply date filter (2020–2024) → run uniform query → take first **N=50**.  
2) Apply inclusion criteria; deduplicate via **URL + sha256(normalized text)**.  
3) Keep **up to K=3** items.  
4) Save normalized text & metadata; compute and store **sha256**.  
5) Append a line to **harvest_log.csv**.

## 7) Harvest log schema (UTF-8 CSV)
```csv timestamp_utc,actor_id,actor_name,domain,channel,pub_date,url,title,words,query,seed,rank_in_search,accepted,reason_if_rejected,sha256_text ```

## 8) Data-freeze (before confirmatory analyses)

Generate freeze/manifest_SHA256.txt (recursive checksums), tag Git, and upload the manifest on OSF.

## 9) Rationale for parameters
K=3: balances coverage vs manual review feasibility.
N=50: standard search depth for institutional sources.
L=120: ensures substantive content (excludes title-only briefs).
Seed=42: conventional reproducibility in computational social science.
Procedural cap ≤10%: controls for non-discursive texts.

## 10) Re-use & license (optional)
Unless otherwise noted, materials are shared under a permissive license; see the project LICENSE file.