import os
import sys
import xml.etree.ElementTree as ET
import re
import json
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

# Configuration
SMALI_DIR = './SMALI'
LOG_FILE = './findings/account_deletion_findings.txt'

# Patterns to search for
DELETION_PATTERNS = [
    'delete account', 'deleteaccount', 'remove account', 'removeaccount',
    'account deletion', 'accountdeletion', 'delete my account', 'deletemyaccount',
    'close account', 'closeaccount', 'deactivate account', 'deactivateaccount',
    'delete profile', 'deleteprofile', 'gdpr delete', 'permanent delete',
    'terminate account', 'terminateaccount', 'account removal', 'accountremoval',
]


API_PATTERNS = [
    r'\/accounts?\/delete',
    r'\/users?\/delete',
    r'\/profile\/delete',
    r'\/auth\/delete',
    r'deleteUserAccount',
    r'deleteAccountPermanently',
    r'removeUserAccount',
    r'accountDeletionRequest'
]

UI_ELEMENTS = [
    'delete_account',
    'remove_account',
    'close_account',
    'deactivate_account',
    'account_deletion',
    'delete_profile',
    'account_termination'
]

def log_finding(app_name, finding_type, details):
    """Log findings to a file with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n[{timestamp}] {app_name} - {finding_type}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{details}\n")
        f.write("-" * 80 + "\n")

def analyze_strings_xml(app_dir, app_name):
    """Analyze strings.xml files for account deletion related strings"""
    deletion_strings = []
    try:
        # Look for strings.xml in the standard resource directories
        for values_dir in ['res/values', 'res/values-en-rAU', 'res/values-en-rGB']:
            strings_path = os.path.join(app_dir, values_dir, 'strings.xml')
            if os.path.exists(strings_path):
                tree = ET.parse(strings_path)
                root = tree.getroot()
                for string in root.findall('.//string'):
                    text = (string.text or '').lower()
                    name = (string.get('name', '') or '').lower()
                    
                    for pattern in DELETION_PATTERNS:
                        if pattern in text or pattern in name:
                            finding = {
                                'matched_pattern': pattern,
                                'name': string.get('name', ''),
                                'text': string.text
                            }
                            deletion_strings.append(finding)
                            log_finding(app_name, 'String Resource', 
                                      f"Found in strings.xml:\nID: {finding['name']}\nText: {finding['text']}")
    except Exception as e:
        print(f"Error analyzing strings.xml for {app_name}: {str(e)}", file=sys.stderr)
    return deletion_strings

def analyze_layout_files(app_dir, app_name):
    """Analyze layout XML files for account deletion related UI elements"""
    ui_elements = []
    try:
        layout_dir = os.path.join(app_dir, 'res/layout')
        if os.path.exists(layout_dir):
            for layout_file in os.listdir(layout_dir):
                if layout_file.endswith('.xml'):
                    tree = ET.parse(os.path.join(layout_dir, layout_file))
                    root = tree.getroot()
                    for element in root.findall('.//*'):
                        element_id = element.get('android:id', '')
                        element_text = element.get('android:text', '')
                        
                        for pattern in UI_ELEMENTS:
                            if pattern in str(element_id).lower() or pattern in str(element_text).lower():
                                finding = {
                                    'matched_pattern': pattern,
                                    'file': layout_file,
                                    'element_id': element_id,
                                    'element_type': element.tag,
                                    'element_text': element_text
                                }
                                ui_elements.append(finding)
                                log_finding(app_name, 'Layout Element',
                                          f"Found in {layout_file}:\nID: {element_id}\nType: {element.tag}\nText: {element_text}")
    except Exception as e:
        print(f"Error analyzing layout files for {app_name}: {str(e)}", file=sys.stderr)
    return ui_elements

def process_smali_file(args):
    """Enhanced Smali file analysis"""
    file_path, app_name = args
    findings = {
        'keyword_matches': [],
        'api_matches': [],
        'context': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            
            # Check for keyword matches using complete phrases
            for pattern in DELETION_PATTERNS:
                if pattern in content:
                    findings['keyword_matches'].append(pattern)
                    
                    # Get context (5 lines before and after)
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line.lower():
                            start = max(0, i - 5)
                            end = min(len(lines), i + 6)
                            context = '\n'.join(lines[start:end])
                            findings['context'].append({
                                'match': pattern,
                                'context': context
                            })
                            log_finding(app_name, 'Code Pattern',
                                      f"File: {file_path}\nPattern: {pattern}\nContext:\n{context}")
            
            # Check for API patterns
            for pattern in API_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    findings['api_matches'].append(match.group())
                    
                    # Get context
                    lines = content.split('\n')
                    line_no = content[:match.start()].count('\n')
                    start = max(0, line_no - 5)
                    end = min(len(lines), line_no + 6)
                    context = '\n'.join(lines[start:end])
                    findings['context'].append({
                        'match': match.group(),
                        'context': context
                    })
                    log_finding(app_name, 'API Pattern',
                              f"File: {file_path}\nAPI: {match.group()}\nContext:\n{context}")
            
            if findings['keyword_matches'] or findings['api_matches']:
                return file_path, findings
                
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
    return None

def get_app_directories(base_dir):
    """Get list of all app directories"""
    return [d for d in os.listdir(base_dir) 
            if os.path.isdir(os.path.join(base_dir, d))]

def analyze_app(app_dir, app_name):
    """Analyze a single app directory"""
    findings = {
        'app_name': app_name,
        'smali_analysis': [],
        'strings_analysis': [],
        'layout_analysis': [],
        'total_files_processed': 0
    }
    
    # Analyze resource files
    print(f"\nAnalyzing resources for {app_name}...")
    findings['strings_analysis'] = analyze_strings_xml(app_dir, app_name)
    findings['layout_analysis'] = analyze_layout_files(app_dir, app_name)
    
    # Get all smali files
    smali_files = []
    for root, _, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.smali'):
                smali_files.append((os.path.join(root, file), app_name))
    
    total_files = len(smali_files)
    if total_files == 0:
        print(f"No .smali files found for {app_name}")
        return findings
    
    # Process smali files in parallel
    num_cpus = int(os.environ.get('SLURM_CPUS_PER_TASK', 16))
    num_workers = min(num_cpus, 8)
    
    print(f"Processing {total_files} files for {app_name} using {num_workers} parallel processes")
    
    with tqdm(total=total_files, desc=f"Processing {app_name}", unit="file") as pbar:
        try:
            chunk_size = max(1, total_files // (num_workers * 4))
            
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                for result in executor.map(process_smali_file, smali_files, chunksize=chunk_size):
                    if result:
                        file_path, file_findings = result
                        findings['smali_analysis'].append({
                            'file': file_path,
                            'findings': file_findings
                        })
                    pbar.update(1)
                    findings['total_files_processed'] += 1
        
        except Exception as e:
            print(f"Error in parallel processing for {app_name}: {str(e)}", file=sys.stderr)

    with open(f'findings/{app_name}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(findings))
    
    return findings

def generate_summary_report(all_findings):
    """Generate a summary report of account deletion capabilities"""
    report = "Account Deletion Functionality Analysis Summary\n"
    report += "==========================================\n\n"
    
    for app_findings in all_findings:
        app_name = app_findings['app_name']
        report += f"\nApp: {app_name}\n"
        report += "-" * (len(app_name) + 5) + "\n"
        
        # Initialize evidence counters
        evidence = {
            'strings': len(app_findings['strings_analysis']),
            'layouts': len(app_findings['layout_analysis']),
            'code': len(app_findings['smali_analysis'])
        }
        
        # Determine likelihood of account deletion feature
        if sum(evidence.values()) > 0:
            report += "Evidence of account deletion functionality:\n"
            if evidence['strings']:
                report += f"- Found {evidence['strings']} relevant string resources\n"
            if evidence['layouts']:
                report += f"- Found {evidence['layouts']} relevant UI elements\n"
            if evidence['code']:
                report += f"- Found {evidence['code']} relevant code patterns\n"
            
            likelihood = "High" if sum(evidence.values()) >= 3 else "Medium" if sum(evidence.values()) >= 2 else "Low"
            report += f"\nLikelihood of account deletion feature: {likelihood}\n"
        else:
            report += "No clear evidence of account deletion functionality found.\n"
        
        report += "\n" + "-" * 50 + "\n"
    
    return report

if __name__ == "__main__":
    sys.stderr.flush()
    sys.stdout.flush()
    
    # Clear or create the log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("Account Deletion Analysis Log\n")
        f.write("=" * 30 + "\n")
    
    # Get all app directories
    app_dirs = get_app_directories(SMALI_DIR)
    all_findings = []
    
    # Process each app
    for app_name in app_dirs:
        app_dir = os.path.join(SMALI_DIR, app_name)
        findings = analyze_app(app_dir, app_name)
        all_findings.append(findings)
    
    # Generate and save summary report
    summary_report = generate_summary_report(all_findings)
    with open('account_deletion_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    print("\nAnalysis complete!")
    print(f"Detailed findings logged to: {LOG_FILE}")
    print("Summary report saved to: account_deletion_summary.txt")