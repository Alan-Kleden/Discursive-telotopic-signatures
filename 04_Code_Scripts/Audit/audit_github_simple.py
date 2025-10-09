# audit_github_simple.py
import os
import json
from pathlib import Path
from datetime import datetime
import subprocess

# ============ CONFIGURATION ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUTPUT_PATH = os.path.join(ROOT, 'audit_github_report.json')
# ========================================

def get_repo_info():
    """Récupère infos basiques du repo"""
    try:
        url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], 
                                     text=True, cwd=ROOT).strip()
        branch = subprocess.check_output(['git', 'branch', '--show-current'], 
                                        text=True, cwd=ROOT).strip()
        last_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%H|%ai|%s'], 
            text=True, cwd=ROOT
        ).strip().split('|')
        
        return {
            'url': url,
            'branch': branch,
            'last_commit_hash': last_commit[0],
            'last_commit_date': last_commit[1],
            'last_commit_msg': last_commit[2]
        }
    except Exception as e:
        return {'error': str(e)}

def check_prereg_compliance():
    """Vérifie présence fichiers requis par prereg"""
    os.chdir(ROOT)  # Important : se placer à la racine
    
    required_files = {
        'actor_roster': ['07_Config/actors_and_shocks/actor_roster.csv'],
        'shocks': ['07_Config/actors_and_shocks/shocks.csv'],
        'lexicon': ['07_Config/lexicons/lexicon_conative_v1.clean.csv'],
        'requirements': ['requirements.txt', 'environment.yml'],
        'readme': ['README.md'],
        'license': ['LICENSE', 'LICENSE.txt'],
        'corpus': ['artifacts/real/corpus_final.parquet'],
        'features': ['artifacts/real/features_doc.parquet'],
    }
    
    compliance = {}
    
    for category, patterns in required_files.items():
        found = []
        for pattern in patterns:
            if os.path.exists(pattern):
                found.append(pattern)
        
        compliance[category] = {
            'found': len(found) > 0,
            'paths': found if found else None,
            'status': '✅' if found else '❌'
        }
    
    return compliance

def generate_report():
    """Génère rapport simplifié"""
    os.chdir(ROOT)  # Se placer à la racine
    
    print("=== AUDIT GITHUB (SIMPLIFIÉ) ===\n")
    
    # 1. Info repo
    print("1. Repository Info")
    repo_info = get_repo_info()
    for k, v in repo_info.items():
        print(f"   {k}: {v}")
    
    # 2. Conformité prereg
    print("\n2. Preregistration Compliance")
    compliance = check_prereg_compliance()
    
    compliant = sum(1 for c in compliance.values() if c['found'])
    total = len(compliance)
    pct = (compliant / total * 100) if total > 0 else 0
    
    print(f"   Score: {compliant}/{total} ({pct:.1f}%)")
    print("\n   Details:")
    for category, info in compliance.items():
        status = info['status']
        paths = info['paths']
        if paths:
            print(f"     {status} {category}: {paths[0]}")
        else:
            print(f"     {status} {category}: MISSING")
    
    # 3. Export JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'repo_info': repo_info,
        'compliance': compliance,
        'compliance_score': pct
    }
    
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Report saved: {OUTPUT_PATH}")
        
        if os.path.exists(OUTPUT_PATH):
            size = os.path.getsize(OUTPUT_PATH)
            print(f"✓ File verified: {size} bytes")
            print(f"✓ Absolute path: {os.path.abspath(OUTPUT_PATH)}")
    except Exception as e:
        print(f"✗ ERROR saving report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    generate_report()