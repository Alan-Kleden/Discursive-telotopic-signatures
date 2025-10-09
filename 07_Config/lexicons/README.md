# Lexicons – Documentation

## Files
- lexicon_conative_v1.clean.csv  
  Original curated terms (multilingual). Columns: concept_id, lemma, language, type(push|inhibit), pos, pattern_lemma_re, weight, notes.

- lexicon_conative_v1.mapped.csv  
  English-only mapping used to feed v2. Columns: pattern, class(fc|fi).
  Mapping rules:
  - type=push  → class=fc
  - type=inhibit → class=fi
  - lemma becomes whole-word regex: \blemma\b unless pattern_lemma_re is provided.

- lexicon_conative_v2_enhanced.csv  
  Exploratory lexicon v2 assembled from:
  1) v1.mapped (regex tokens)
  2) contextual regex patterns (imperatives, US-Congress locutions, with negation handling)
  3) optional TF-IDF candidates (if sample size allows)
  Columns: pattern, kind=regex, class(fc|fi|neutral), weight, note, source.

- lexicon_v2_enhanced.changelog.md  
  Auto-generated; counts, parameters, sources.

## Status
- v1: confirmatory (prereg baseline)
- v2: exploratory – don’t mix with confirmatory analyses.

## Caveats
- Negations are neutralized when matched explicitly (weight=0).
- If TF-IDF is skipped, v2 contains v1.mapped + contextual patterns only.
