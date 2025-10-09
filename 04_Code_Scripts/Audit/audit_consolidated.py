# audit_consolidated.py
"""
Rapport consolidé : GitHub + Local + Conformité OSF
"""
import os
import json
from datetime import datetime

# ============ CONFIGURATION ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUTPUT_PATH = os.path.join(ROOT, 'audit_consolidated_report.json')
# ========================================

def load_reports():
    """Charge les 2 rapports"""
    os.chdir(ROOT)
    
    try:
        with open('audit_github_report.json', 'r', encoding='utf-8') as f:
            github = json.load(f)
    except:
        github = None
    
    try:
        with open('audit_local_report.json', 'r', encoding='utf-8') as f:
            local = json.load(f)
    except:
        local = None
    
    return github, local

def calculate_overall_score(github, local):
    """Calcule score global de conformité OSF"""
    
    scores = {
        'infrastructure': 0,
        'data_collection': 0,
        'lexicon_validation': 0,
        'shocks_dynamics': 0,
        'statistical_models': 0,
        'documentation': 0
    }
    
    # Infrastructure
    if github:
        infra_score = 0
        compliance = github.get('compliance', {})
        
        if compliance.get('readme', {}).get('found'):
            infra_score += 30
        if compliance.get('requirements', {}).get('found'):
            infra_score += 20
        else:
            infra_score += 10  # Partial si environment.yml
        
        # Repo Git actif
        if github.get('repo_info', {}).get('url'):
            infra_score += 20
        
        # Compliance score
        comp_score = github.get('compliance_score', 0)
        infra_score += int(comp_score * 0.3)
        
        scores['infrastructure'] = min(infra_score, 100)
    
    # Data collection
    if local:
        data_score = 0
        integrity = local.get('integrity', {})
        
        if integrity.get('corpus', {}).get('status') == '✅ Found':
            data_score += 35
        if integrity.get('features', {}).get('status') == '✅ Found':
            data_score += 30
        if integrity.get('actor_roster', {}).get('status') == '✅ Found':
            data_score += 20
        if integrity.get('lexicon_v1', {}).get('status') == '✅ Found':
            data_score += 15
        
        scores['data_collection'] = data_score
    
    # Lexicon validation (manuel - pas encore fait)
    scores['lexicon_validation'] = 0
    
    # Shocks
    if local:
        integrity = local.get('integrity', {})
        if integrity.get('shocks', {}).get('status') == '✅ Found':
            scores['shocks_dynamics'] = 25
    
    # Statistical models (pas encore démarrés)
    scores['statistical_models'] = 0
    
    # Documentation
    if github:
        doc_score = 0
        compliance = github.get('compliance', {})
        
        if compliance.get('readme', {}).get('found'):
            doc_score += 40
        if compliance.get('license', {}).get('found'):
            doc_score += 30
        else:
            doc_score += 10  # Partial
        
        # Présence de rapport
        if local and local.get('inventory', {}).get('total_files', 0) > 50:
            doc_score += 30
        
        scores['documentation'] = min(doc_score, 100)
    
    return scores

def generate_consolidated_report():
    """Rapport final consolidé"""
    os.chdir(ROOT)
    
    print("=== CONSOLIDATED AUDIT REPORT ===\n")
    
    github, local = load_reports()
    
    if not github and not local:
        print("ERROR: No audit reports found.")
        print("Run audit_github_simple.py and audit_local_env.py first.")
        return
    
    # 1. Scores
    print("1. OSF Preregistration Compliance Scores\n")
    scores = calculate_overall_score(github, local)
    
    # Pondération
    weights = {
        'infrastructure': 0.15,
        'data_collection': 0.20,
        'lexicon_validation': 0.20,
        'shocks_dynamics': 0.10,
        'statistical_models': 0.25,
        'documentation': 0.10
    }
    
    weighted_total = sum(scores[k] * weights[k] for k in scores)
    
    for component, score in scores.items():
        weight = weights[component]
        contribution = score * weight
        bar = '█' * int(score/5) + '░' * (20 - int(score/5))
        print(f"   {component:25s} {score:3d}/100 {bar} ({contribution:.1f} weighted)")
    
    print(f"\n   {'OVERALL SCORE':25s} {weighted_total:3.1f}/100")
    
    # 2. GitHub status
    if github:
        print("\n2. GitHub Repository Status\n")
        repo_info = github.get('repo_info', {})
        print(f"   URL: {repo_info.get('url', 'N/A')}")
        print(f"   Branch: {repo_info.get('branch', 'N/A')}")
        print(f"   Last commit: {repo_info.get('last_commit_date', 'N/A')[:10]}")
        
        compliance_score = github.get('compliance_score', 0)
        print(f"   Compliance: {compliance_score:.1f}%")
    
    # 3. Local environment
    if local:
        print("\n3. Local Environment Status\n")
        inv = local.get('inventory', {})
        print(f"   Total files: {inv.get('total_files', 0)}")
        print(f"   Total size: {inv.get('total_size_gb', 0):.2f} GB")
        print(f"   Data files: {inv.get('data_files_count', 0)}")
        print(f"   Scripts: {inv.get('script_files_count', 0)}")
        
        print("\n   Critical files:")
        integrity = local.get('integrity', {})
        for name, info in integrity.items():
            status = info.get('status', '❌')
            size = info.get('size_mb', 0)
            print(f"     {status} {name}: {size} MB")
    
    # 4. Gaps analysis
    print("\n4. Critical Gaps\n")
    
    gaps = []
    
    # Sample size
    gaps.append({
        'category': 'Sample size',
        'issue': 'Only 3 actors (need ≥10 per prereg)',
        'priority': 'P0 - BLOCKING',
        'impact': 'Cannot run confirmatory H1/H2/H4'
    })
    
    # Teloi
    gaps.append({
        'category': 'Telos extraction',
        'issue': 'No endogenous teloi extracted',
        'priority': 'P0 - BLOCKING',
        'impact': 'θ and N_tel invalid, H1/H2/H4 impossible'
    })
    
    # Lexicon
    if scores['lexicon_validation'] == 0:
        gaps.append({
            'category': 'Lexicon validation',
            'issue': 'No manual annotations (gold standard)',
            'priority': 'P1 - CRITICAL',
            'impact': 'Fc/Fi validity unknown'
        })
    
    # Shocks
    if scores['shocks_dynamics'] < 50:
        gaps.append({
            'category': 'Shocks definition',
            'issue': 'Insufficient shocks or not validated',
            'priority': 'P1 - CRITICAL',
            'impact': 'H3 not testable'
        })
    
    # Requirements
    if github and not github.get('compliance', {}).get('requirements', {}).get('found'):
        gaps.append({
            'category': 'Reproducibility',
            'issue': 'Missing requirements.txt/environment.yml',
            'priority': 'P2 - HIGH',
            'impact': 'Cannot reproduce environment'
        })
    
    # License
    if github and not github.get('compliance', {}).get('license', {}).get('found'):
        gaps.append({
            'category': 'Legal',
            'issue': 'Missing LICENSE file',
            'priority': 'P3 - MEDIUM',
            'impact': 'Unclear usage rights'
        })
    
    for i, gap in enumerate(gaps, 1):
        print(f"   Gap {i}: {gap['category']}")
        print(f"     Issue: {gap['issue']}")
        print(f"     Priority: {gap['priority']}")
        print(f"     Impact: {gap['impact']}\n")
    
    # 5. Recommendations
    print("5. Immediate Actions (Priority Order)\n")
    
    actions = [
        ("1. Clean .venv_old from Git", "10 min", "Reduce repo bloat (855→~50 py files)"),
        ("2. Create requirements.txt", "5 min", "Enable reproducibility"),
        ("3. Add LICENSE", "5 min", "Legal clarity"),
        ("4. Annotate 20 docs manually", "4 hours", "Enable lexicon validation"),
        ("5. Define 12 shocks (4 domains)", "4 hours", "Enable H3 testing"),
        ("6. Extract teloi (≥3 actors)", "1 week", "Enable H1/H2/H4"),
        ("7. Extend corpus (≥10 actors)", "3-4 weeks", "Meet prereg minima"),
    ]
    
    for action, duration, outcome in actions:
        print(f"   {action}")
        print(f"     Duration: {duration}")
        print(f"     Outcome: {outcome}\n")
    
    # 6. Export JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'scores': scores,
        'weighted_total': round(weighted_total, 1),
        'github_summary': {
            'compliance_score': github.get('compliance_score') if github else None,
            'last_commit': github.get('repo_info', {}).get('last_commit_date') if github else None
        },
        'local_summary': {
            'total_files': local.get('inventory', {}).get('total_files') if local else None,
            'total_size_gb': local.get('inventory', {}).get('total_size_gb') if local else None
        },
        'critical_gaps': gaps,
        'recommended_actions': [
            {'action': a, 'duration': d, 'outcome': o} 
            for a, d, o in actions
        ]
    }
    
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Report saved: {OUTPUT_PATH}")
        
        if os.path.exists(OUTPUT_PATH):
            size = os.path.getsize(OUTPUT_PATH)
            print(f"✓ File verified: {size} bytes")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    generate_consolidated_report()