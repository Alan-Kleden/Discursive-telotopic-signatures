# scripts/audit_local_env.py
"""
Audit de l'environnement local G:\Mon Drive\Signatures_Telotopiques_POC
Compare avec GitHub, identifie différences
"""

import os
import json
from pathlib import Path
from datetime import datetime
import hashlib

LOCAL_ROOT = r"G:\Mon Drive\Signatures_Telotopiques_POC"

def compute_file_hash(filepath):
    """Calcule hash MD5 d'un fichier"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def scan_local_environment(root=LOCAL_ROOT):
    """Scanne environnement local complet"""
    if not os.path.exists(root):
        return {'error': f'Path not found: {root}'}
    
    inventory = {
        'root': root,
        'scanned_at': datetime.now().isoformat(),
        'directories': {},
        'total_files': 0,
        'total_size_gb': 0,
        'file_types': {},
        'data_files': [],
        'config_files': [],
        'script_files': [],
        'missing_in_github': []
    }
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore certains dossiers
        dirnames[:] = [d for d in dirnames 
                      if d not in ['.git', '__pycache__', 'node_modules', 
                                   '.venv', 'venv']]
        
        rel_path = os.path.relpath(dirpath, root)
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            
            filepath = os.path.join(dirpath, filename)
            file_size = os.path.getsize(filepath)
            file_ext = os.path.splitext(filename)[1].lower()
            
            inventory['total_files'] += 1
            inventory['total_size_gb'] += file_size / (1024**3)
            
            # Compteur types
            inventory['file_types'][file_ext] = \
                inventory['file_types'].get(file_ext, 0) + 1
            
            # Catégorisation
            file_info = {
                'path': os.path.join(rel_path, filename),
                'size_mb': file_size / (1024**2),
                'modified': datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).isoformat()
            }
            
            # Data files
            if file_ext in ['.parquet', '.csv'] and file_size > 1024*1024:  # >1MB
                file_info['hash'] = compute_file_hash(filepath)
                inventory['data_files'].append(file_info)
            
            # Config files
            if file_ext in ['.yaml', '.yml', '.json', '.toml'] or \
               'config' in rel_path.lower():
                inventory['config_files'].append(file_info)
            
            # Scripts
            if file_ext == '.py':
                inventory['script_files'].append(file_info)
    
    return inventory

def compare_with_github(local_inventory):
    """Compare avec audit GitHub"""
    github_report_path = 'audit_github_report.json'
    
    if not os.path.exists(github_report_path):
        return {'error': 'Run audit_github.py first'}
    
    with open(github_report_path, 'r', encoding='utf-8') as f:
        github_report = json.load(f)
    
    comparison = {
        'files_only_local': [],
        'files_only_github': [],
        'size_differences': {},
        'data_sync_status': {}
    }
    
    # Fichiers locaux
    local_files = set()
    for category in ['data_files', 'config_files', 'script_files']:
        for item in local_inventory.get(category, []):
            local_files.add(item['path'])
    
    # Fichiers GitHub (approximatif via compliance)
    github_files = set()
    for category, info in github_report.get('compliance', {}).items():
        if info['found'] and info['paths']:
            for path in info['paths']:
                github_files.add(path)
    
    # Différences
    comparison['files_only_local'] = list(local_files - github_files)
    comparison['files_only_github'] = list(github_files - local_files)
    
    # Fichiers data non versionnés (normal mais à signaler)
    large_data = [f for f in local_inventory.get('data_files', []) 
                  if f['size_mb'] > 100]
    
    comparison['large_data_not_in_github'] = large_data
    
    return comparison

def check_data_integrity(local_inventory):
    """Vérifie intégrité données critiques"""
    critical_files = {
        'corpus': 'artifacts/real/corpus_final.parquet',
        'features': 'artifacts/real/features_doc.parquet',
        'actor_roster': '07_Config/actors_and_shocks/actor_roster.csv',
        'shocks': '07_Config/actors_and_shocks/shocks.csv',
        'lexicon_v1': '07_Config/lexicons/lexicon_conative_v1.clean.csv'
    }
    
    integrity = {}
    
    for name, expected_path in critical_files.items():
        full_path = os.path.join(LOCAL_ROOT, expected_path)
        
        if os.path.exists(full_path):
            size_mb = os.path.getsize(full_path) / (1024**2)
            modified = datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ).isoformat()
            file_hash = compute_file_hash(full_path)
            
            integrity[name] = {
                'status': '✅ Found',
                'path': expected_path,
                'size_mb': round(size_mb, 2),
                'modified': modified,
                'hash': file_hash
            }
        else:
            integrity[name] = {
                'status': '❌ Missing',
                'path': expected_path
            }
    
    return integrity

def generate_report():
    """Génère rapport audit local"""
    print("=== AUDIT LOCAL ENVIRONMENT ===\n")
    
    # 1. Scan local
    print(f"1. Scanning {LOCAL_ROOT}...")
    inventory = scan_local_environment()
    
    if 'error' in inventory:
        print(f"   ERROR: {inventory['error']}")
        return
    
    print(f"   Total files: {inventory['total_files']}")
    print(f"   Total size: {inventory['total_size_gb']:.2f} GB")
    
    # Top file types
    print("\n   Top file types:")
    sorted_types = sorted(inventory['file_types'].items(), 
                         key=lambda x: x[1], reverse=True)[:10]
    for ext, count in sorted_types:
        print(f"     {ext or '(no ext)'}: {count} files")
    
    # 2. Data files
    print(f"\n2. Data Files (>{1}MB)")
    print(f"   Count: {len(inventory['data_files'])}")
    for df in inventory['data_files'][:5]:
        print(f"     {df['path']}: {df['size_mb']:.2f} MB")
    
    # 3. Scripts
    print(f"\n3. Python Scripts")
    print(f"   Count: {len(inventory['script_files'])}")
    
    # 4. Data integrity
    print("\n4. Critical Files Integrity")
    integrity = check_data_integrity(inventory)
    
    for name, info in integrity.items():
        status = info['status']
        if 'size_mb' in info:
            print(f"   {status} {name}: {info['size_mb']} MB "
                  f"(modified: {info['modified'][:10]})")
        else:
            print(f"   {status} {name}")
    
    # 5. Comparaison GitHub
    print("\n5. Comparison with GitHub")
    comparison = compare_with_github(inventory)
    
    if 'error' not in comparison:
        print(f"   Files only in local: {len(comparison['files_only_local'])}")
        print(f"   Files only in GitHub: {len(comparison['files_only_github'])}")
        
        if comparison['files_only_local']:
            print("\n   ⚠️ Not pushed to GitHub (sample):")
            for f in comparison['files_only_local'][:5]:
                print(f"     - {f}")
        
        if comparison.get('large_data_not_in_github'):
            print("\n   📦 Large data files (not in GitHub):")
            for f in comparison['large_data_not_in_github']:
                print(f"     - {f['path']}: {f['size_mb']:.2f} MB")
    
    # 6. Export JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'inventory': {
            'total_files': inventory['total_files'],
            'total_size_gb': round(inventory['total_size_gb'], 2),
            'file_types': inventory['file_types'],
            'data_files_count': len(inventory['data_files']),
            'script_files_count': len(inventory['script_files'])
        },
        'integrity': integrity,
        'comparison': comparison
    }
    
    output_path = 'audit_local_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Report saved: {output_path}")

if __name__ == '__main__':
    generate_report()