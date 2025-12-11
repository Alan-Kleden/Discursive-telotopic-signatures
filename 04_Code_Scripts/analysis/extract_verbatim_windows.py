"""
Extract Verbatim Windows for Manual Annotation (V1.2)
- Deterministic 300–500 word windows (no LLM)
- Adds `flag_incertain` in the template
- Outputs annotation_template_v2.csv (2 annotators)

Usage:
    python 04_Code_Scripts/analysis/extract_verbatim_windows.py

Outputs:
    - 07_Config/validation/verbatim_windows_all.csv
    - 07_Config/validation/verbatim_windows_sample20.csv
    - 07_Config/validation/annotation_template_v2.csv
    - 07_Config/validation/extraction_log.jsonl
"""
import re, json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# ============ CONFIG ============
CORPUS_PATH = Path('artifacts/real/corpus_final.parquet')
OUTPUT_DIR  = Path('07_Config/validation'); OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
MIN_LENGTH = 300     # words (skip shorter docs)
MAX_LENGTH = 500
TARGET_LENGTH = 400

TELOS_MARKERS = (
    r'\b(will|must|should|commit|plan|aim|urge|call on|support|oppose|'
    r'ensure|deliver|adopt|ban|expand|invest|protect|guarantee|'
    r'implement|legislate)\b'
)
# =================================

def count_words(text: str) -> int:
    return len(text.split())

def find_sentence_boundary(text: str, pos: int, direction: str='forward') -> int:
    if direction == 'forward':
        m = re.search(r'[.!?]\s+', text[pos:])
        return (pos + m.end()) if m else len(text)
    else:
        rev = text[:pos][::-1]
        m = re.search(r'\s+[.!?]', rev)
        return (pos - m.end() + 1) if m else 0

def extract_mode_a(text: str) -> Dict:
    words = text.split()[:TARGET_LENGTH]
    excerpt = ' '.join(words)
    if len(excerpt) < len(text):
        b = find_sentence_boundary(text, len(excerpt), 'backward')
        if b > 0 and count_words(text[:b]) >= MIN_LENGTH:
            excerpt = text[:b]
    return dict(mode='A', start_char=0, end_char=len(excerpt),
                length_words=count_words(excerpt), marker=None,
                excerpt_verbatim=excerpt.strip())

def extract_mode_b(text: str, marker_pos: int, marker_text: str) -> Dict:
    words_list = text.split()
    # seg1 ~175w from start
    seg1_words = words_list[:175]
    seg1 = ' '.join(seg1_words)
    b1 = find_sentence_boundary(text, len(seg1), 'backward')
    if b1 > 0: seg1 = text[:b1]
    # seg2 ~200w around marker (±100w)
    marker_wi = len(text[:marker_pos].split())
    s = max(0, marker_wi - 100); e = min(len(words_list), marker_wi + 100)
    seg2_words = words_list[s:e]
    chars_before_seg2 = len(' '.join(words_list[:s])) + (s if s>0 else 0)
    seg2_text = text[chars_before_seg2:]
    seg2_end = len(' '.join(seg2_words))
    b2s = find_sentence_boundary(seg2_text, 0, 'forward')
    b2e = find_sentence_boundary(seg2_text, seg2_end, 'backward')
    seg2 = seg2_text[b2s:b2e].strip()
    excerpt = f"{seg1.strip()} […] {seg2}"
    return dict(mode='B', start_char=0, end_char=chars_before_seg2+b2e,
                length_words=count_words(excerpt.replace('[…]','')), marker=marker_text,
                excerpt_verbatim=excerpt)

def extract_mode_c(text: str, marker_pos: int, marker_text: str) -> Dict:
    words_list = text.split()
    marker_wi = len(text[:marker_pos].split())
    s = max(0, marker_wi - 250); e = min(len(words_list), marker_wi + 250)
    window_words = words_list[s:e]
    chars_before = len(' '.join(words_list[:s])) + (s if s>0 else 0)
    win_text = text[chars_before:]; win_end = len(' '.join(window_words))
    bs = find_sentence_boundary(win_text, 0, 'forward')
    be = find_sentence_boundary(win_text, win_end, 'backward')
    excerpt = win_text[bs:be].strip()
    return dict(mode='C', start_char=chars_before+bs, end_char=chars_before+be,
                length_words=count_words(excerpt), marker=marker_text,
                excerpt_verbatim=excerpt)

def extract_window(text: str, doc_id: str) -> Dict:
    m = re.search(TELOS_MARKERS, text, re.IGNORECASE)
    if not m: return extract_mode_a(text)
    marker_pos = m.start(); marker_text = m.group().lower()
    wb = count_words(text[:marker_pos])
    if wb < 200:   return extract_mode_a(text)     # early → A
    if wb <= 1000: return extract_mode_b(text, marker_pos, marker_text)  # mid → B
    return extract_mode_c(text, marker_pos, marker_text)                 # late → C

def process_corpus(sample_size: Optional[int]=None) -> pd.DataFrame:
    print(f"Loading corpus from {CORPUS_PATH}...")
    corpus = pd.read_parquet(CORPUS_PATH)
    if sample_size:
        print(f"Sampling {sample_size} documents (stratified by actor, seed={SEED})...")
        n_per_actor = sample_size // corpus['actor_id'].nunique()
        corpus = corpus.groupby('actor_id', group_keys=False).apply(
            lambda x: x.sample(min(len(x), n_per_actor), random_state=SEED)
        ).reset_index(drop=True)

    print(f"Processing {len(corpus)} documents...")
    rows, logs = [], []
    for idx, row in corpus.iterrows():
        doc_id = f"doc_{idx:03d}"
        text = row['text']
        if count_words(text) < MIN_LENGTH:
            print(f"  ⚠️  Skipping {doc_id} (too short: {count_words(text)} words)")
            continue
        win = extract_window(text, doc_id)
        rows.append({
            'doc_id': doc_id,
            'actor_id': row['actor_id'],
            'country': row['country'],
            'domain_id': row['domain_id'],
            'date': row['date'],
            'url': row['url'],
            'original_length_words': row['tokens'],
            **win
        })
        logs.append({
            'timestamp_utc': datetime.utcnow().isoformat(),
            'doc_id': doc_id, 'actor_id': row['actor_id'], 'url': row['url'],
            'extraction_method': 'deterministic_regex_v1',
            'seed': SEED, 'markers_regex': TELOS_MARKERS, **win
        })
        print(f"  ✓ {doc_id} ({row['actor_id']}): Mode {win['mode']}, {win['length_words']} words, marker={win['marker']}")
    with open(OUTPUT_DIR/'extraction_log.jsonl','w',encoding='utf-8') as f:
        for e in logs: f.write(json.dumps(e, ensure_ascii=False)+'\n')
    print(f"\n✓ Logs saved: {OUTPUT_DIR/'extraction_log.jsonl'}")
    return pd.DataFrame(rows)

# --- remplace l'ancienne écriture du template par ceci ---
def write_annotation_template_single(df, out_name: str):
    cols = ['doc_id','actor_id','country','domain_id','date','url',
            'mode','length_words','marker','excerpt_verbatim']
    tpl = df[[c for c in cols if c in df.columns]].copy()
    # Une seule colonne d'annotation
    tpl['fc_score'] = ""          # 0..5 (décimales ok)
    tpl['fi_score'] = ""          # 0..5 (décimales ok)
    tpl['flag_incertain'] = ""    # 1 si hésitation, sinon vide
    tpl['notes'] = ""
    outp = OUTPUT_DIR / out_name
    tpl.to_csv(outp, index=False, encoding='utf-8')
    print(f"✓ Annotation template (single) saved: {outp}")

def main():
    print("="*60); print("VERBATIM WINDOW EXTRACTION (Deterministic)"); print("="*60); print()
    # All
    print("1. Processing entire corpus...\n")
    all_win = process_corpus(sample_size=None)
    all_fp = OUTPUT_DIR/'verbatim_windows_all.csv'
    all_win.to_csv(all_fp, index=False, encoding='utf-8')
    print(f"\n✓ All windows saved: {all_fp}")
    # Sample 20
    print("\n2. Generating sample for annotation (n=20)...\n")
    sample = process_corpus(sample_size=20)
    sample_fp = OUTPUT_DIR/'verbatim_windows_sample20.csv'
    sample.to_csv(sample_fp, index=False, encoding='utf-8')
    print(f"✓ Sample saved: {sample_fp}")
    # Template V2
    print("\n3. Generating annotation template (V2)...\n")
    write_annotation_template_single(sample, 'annotation_template_single.csv')

    # Summary
    print("\n"+"="*60); print("SUMMARY"); print("="*60)
    print(f"Total documents processed: {len(all_win)}")
    print(f"Sample for annotation: {len(sample)}\n")
    if not all_win.empty: print("Mode distribution (all):"); print(all_win['mode'].value_counts(),"\n")
    if not sample.empty:  print("Mode distribution (sample):"); print(sample['mode'].value_counts(),"\n")
    if not sample.empty:  print("Actor distribution (sample):"); print(sample['actor_id'].value_counts(),"\n")
    print("Files generated:")
    print(f"  - {all_fp}\n  - {sample_fp}\n  - {OUTPUT_DIR/'annotation_template_v2.csv'}\n  - {OUTPUT_DIR/'extraction_log.jsonl'}")
    print("\n✓ Ready for manual annotation!\n"+"="*60)

if __name__ == '__main__':
    main()
