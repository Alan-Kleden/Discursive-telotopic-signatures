# Harvesting Protocol (Public Text Collection)

_Archived – superseded by v1.1
_Last updated: 2025-10-10 • Version 1.0_

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
- **Seed**: **42** (applied wherever randomness is involved)
- **Dates**: 2020-01-01 → 2024-12-31 (publication time, not crawl time)

## 4) Inclusion / exclusion
- **Include**: public, textual, EN, ≥ L words, unique after dedup (URL and sha256 of normalized text).
- **Exclude**: non-public paywalls; PDFs scanned illisibles; duplicates/near-dupes; pure metadata pages; multimedia sans transcription.
- **Meta-fields required**: actor_id, actor_name, domain, channel, date, url, title, word_count.

## 5) Uniform queries (examples)
For each actor and channel, use standardized queries and record them in the log.

## 6) Procedure per actor–year–domain–channel
1) Date filter → uniform query → take first N=50  
2) Filter inclusion criteria; dedup URL + sha256  
3) Keep up to K=3 items  
4) Save normalized text & metadata; compute sha256  
5) Append to harvest_log.csv

## 7) Harvest log schema (UTF-8 CSV)
timestamp_utc,actor_id,actor_name,domain,channel,pub_date,url,title,words,query,seed,rank_in_search,accepted,reason_if_rejected,sha256_text

## 8) Data-freeze (before confirmatory analyses)
Generate freeze/manifest_SHA256.txt, tag Git, upload manifest on OSF.