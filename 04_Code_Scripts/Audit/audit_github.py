# scripts/audit_github.py
"""
Audit du repository GitHub
Génère un rapport de structure, complétude, et conformité prereg
"""

import os
import json
from pathlib import Path
from datetime import datetime
import subprocess

def get_repo_info():
    """Récupère infos basiques du repo"""
    try:
        # URL remote
        url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], 
                                     text=True).strip()
        # Branch actuelle
        branch = subprocess.check_output(['git', 'branch', '--show-current'], 
                                        text=True).strip()
        # Dernier commit
        last_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%H|%ai|%s'], 
            text=True
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

def scan_directory_structure(root_path='.'):
    """Scanne structure de fichiers"""
    structure = {}
    
    # Patterns à chercher
    patterns = {
        'scripts': ['*.py'],
        'configs': ['*.csv', '*.yaml', '*.yml', '*.json'],
        'data': ['*.parquet', '*.csv', '*.json'],
        'docs': ['*.md', '*.pdf', '*.txt'],
        'notebooks': ['*.ipynb']
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Ignore .git, __pycache__, etc.
        dirnames[:] = [d for d in dirnames if not d.startswith('.') 
                      and d != '__pycache__']
        
        rel_path = os.path.relpath(dirpath, root_path)
        
        if rel_path not in structure:
            structure[rel_path] = {
                'files': [],
                'size_bytes': 0,
                'file_types': {}
            }
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            file_size = os.path.getsize(filepath)
            file_ext = os.path.splitext(filename)[1]
            
            structure[rel_path]['files'].append({
                'name': filename,
                'size': file_size,
                'ext': file_ext
            })
            structure[rel_path]['size_bytes'] += file_size
            
            # Compteur par type
            structure[rel_path]['file_types'][file_ext] = \
                structure[rel_path]['file_types'].get(file_ext, 0) + 1
    
    return structure

def check_prereg_compliance():
    """Vérifie présence fichiers requis par prereg"""
    required_files = {
        # OSF prereg p.10-12
        'actor_roster': ['07_Config/actors_and_shocks/actor_roster.csv', 
                        'config/actor_roster.csv',
                        'actors.csv'],
        'shocks': ['07_Config/actors_and_shocks/shocks.csv',
                  'config/shocks.csv',
                  'shocks.csv'],
        'lexicon': ['07_Config/lexicons/lexicon_conative_v1.clean.csv',
                   'config/lexicon*.csv',
                   'lexicon*.csv'],
        'requirements': ['requirements.txt', 'environment.yml', 'pyproject.toml'],
        'readme': ['README.md'],
        'license': ['LICENSE', 'LICENSE.txt', 'LICENSE.md'],
        
        # Données (si pushées)
        'corpus': ['artifacts/real/corpus_final.parquet',
                  'data/corpus*.parquet'],
        'features': ['artifacts/real/features_doc.parquet',
                    'data/features*.parquet'],
        
        # Scripts extraction
        'scrape_govuk': ['scripts/scrape_govuk*.py', 
                        'src/*govuk*.py'],
        'scrape_congress': ['scripts/scrape_congress*.py',
                           'src/*congress*.py'],
        
        # Scripts analyse
        'compute_features': ['scripts/compute_features*.py',
                            'src/*features*.py'],
        'validate': ['scripts/validate*.py',
                    'src/*validate*.py'],
    }
    
    compliance = {}
    
    for category, patterns in required_files.items():
        found = []
        for pattern in patterns:
            # Glob search
            matches = list(Path('.').glob(pattern))
            found.extend([str(m) for m in matches])
        
        compliance[category] = {
            'found': len(found) > 0,
            'paths': found if found else None,
            'status': '✅' if found else '❌'
        }
    
    return compliance

def analyze_code_quality():
    """Analyse qualité code (basique)"""
    stats = {
        'total_py_files': 0,
        'total_lines': 0,
        'total_functions': 0,
        'total_classes': 0,
        'has_tests': False,
        'has_docstrings': 0
    }
    
    for py_file in Path('.').rglob('*.py'):
        if '__pycache__' in str(py_file) or '.git' in str(py_file):
            continue
            
        stats['total_py_files'] += 1
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                stats['total_lines'] += len(lines)
                stats['total_functions'] += content.count('def ')
                stats['total_classes'] += content.count('class ')
                
                # Docstrings (approximatif)
                if '"""' in content or "'''" in content:
                    stats['has_docstrings'] += 1
                
                # Tests
                if 'test_' in py_file.name or py_file.parent.name == 'tests':
                    stats['has_tests'] = True
        except:
            pass
    
    return stats

def generate_report():
    """Génère rapport complet"""
    print("=== AUDIT GITHUB REPOSITORY ===\n")
    
    # 1. Info repo
    print("1. Repository Info")
    repo_info = get_repo_info()
    for k, v in repo_info.items():
        print(f"   {k}: {v}")
    
    # 2. Structure
    print("\n2. Directory Structure")
    structure = scan_directory_structure()
    
    total_size = sum(d['size_bytes'] for d in structure.values())
    print(f"   Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"   Directories: {len(structure)}")
    
    # Top directories par taille
    top_dirs = sorted(structure.items(), 
                     key=lambda x: x[1]['size_bytes'], 
                     reverse=True)[:5]
    print("\n   Top 5 directories by size:")
    for path, info in top_dirs:
        size_mb = info['size_bytes'] / 1024 / 1024
        print(f"     {path}: {size_mb:.2f} MB ({len(info['files'])} files)")
    
    # 3. Conformité prereg
    print("\n3. Preregistration Compliance")
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
    
    # 4. Code quality
    print("\n4. Code Quality")
    code_stats = analyze_code_quality()
    for k, v in code_stats.items():
        print(f"   {k}: {v}")
    
    # 5. Export JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'repo_info': repo_info,
        'structure': {k: {'file_count': len(v['files']), 
                         'size_mb': v['size_bytes']/1024/1024}
                     for k, v in structure.items()},
        'compliance': compliance,
        'code_stats': code_stats,
        'compliance_score': pct
    }
    
    output_path = 'audit_github_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Report saved: {output_path}")

if __name__ == '__main__':
    generate_report()