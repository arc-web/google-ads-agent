#!/usr/bin/env python3
"""
Client Directory Structure Validator

Validates client directories against organizational patterns and provides
inference-based suggestions for missing files and incorrect naming.

Usage:
    python client_structure_validator.py --client collab_med_spa
    python client_structure_validator.py --all  # Check all clients
    python client_structure_validator.py --fix  # Auto-fix issues
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import re

try:
    import yaml
except ImportError:
    yaml = None

# #region agent log
import sys
# #endregion

@dataclass
class StructureRule:
    """Defines a structure validation rule"""
    path_pattern: str
    required: bool
    file_type: Optional[str] = None  # 'file' or 'dir'
    naming_pattern: Optional[str] = None
    content_template: Optional[str] = None

@dataclass
class ValidationIssue:
    """Represents a validation issue found"""
    severity: str  # 'error', 'warning', 'info'
    path: str
    issue_type: str
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False

class ClientStructureValidator:
    """Validates and enforces client directory structure patterns"""
    
    # #region agent log
    def __init__(self, base_path: str = "google_ads_agent"):
        self.base_path = Path(base_path)
        self.issues: List[ValidationIssue] = []
        self.patterns = self._load_patterns()
        self.examples = self._analyze_examples()
    # #endregion
    
    def _load_patterns(self) -> Dict:
        """Load structure patterns from config or infer from examples"""
        # #region agent log
        patterns = {
            'required_dirs': [
                'campaigns',
                'docs',
                'assets',
                'search_themes'
            ],
            'required_files': [
                'README.md',
                '{client_name}_client_config.yaml'
            ],
            'naming_patterns': {
                'csv_files': r'{client_name}_[A-Za-z_]+_\d{4}\.csv',
                'config_file': r'{client_name}_client_config\.yaml',
                'docs': r'[A-Z_]+\.md'
            },
            'doc_patterns': [
                'ANALYSIS_REPORT.md',
                'CLIENT_SPECIFIC_IMPLEMENTATION.md'
            ]
        }
        # #endregion
        return patterns
    
    def _analyze_examples(self) -> Dict:
        """Analyze existing client directories to infer patterns"""
        # #region agent log
        examples = {
            'campaigns': defaultdict(list),
            'docs': defaultdict(list),
            'structure': {}
        }
        
        if not self.base_path.exists():
            return examples
        
        for client_dir in self.base_path.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith('_'):
                continue
            
            # Analyze campaigns directory
            campaigns_dir = client_dir / 'campaigns'
            if campaigns_dir.exists():
                for item in campaigns_dir.iterdir():
                    if item.is_file() and item.suffix == '.csv':
                        examples['campaigns']['csv_names'].append(item.name)
                    elif item.is_dir():
                        examples['campaigns']['subdirs'].append(item.name)
            
            # Analyze docs directory
            docs_dir = client_dir / 'docs'
            if docs_dir.exists():
                for item in docs_dir.iterdir():
                    if item.is_file() and item.suffix == '.md':
                        examples['docs']['doc_names'].append(item.name)
        
        # #endregion
        return examples
    
    def validate_client(self, client_name: str, auto_fix: bool = False) -> List[ValidationIssue]:
        """Validate a single client directory"""
        # #region agent log
        self.issues = []
        client_path = self.base_path / client_name
        
        if not client_path.exists():
            self.issues.append(ValidationIssue(
                severity='error',
                path=str(client_path),
                issue_type='missing_directory',
                message=f"Client directory does not exist: {client_name}",
                auto_fixable=False
            ))
            return self.issues
        
        # Validate required directories
        self._validate_directories(client_path, client_name)
        
        # Validate required files
        self._validate_files(client_path, client_name)
        
        # Validate naming conventions
        self._validate_naming(client_path, client_name)
        
        # Validate file content patterns
        self._validate_content(client_path, client_name)
        
        # Auto-fix if requested
        if auto_fix:
            self._auto_fix_issues(client_path, client_name)
        
        # #endregion
        return self.issues
    
    def _validate_directories(self, client_path: Path, client_name: str):
        """Validate required directory structure"""
        # #region agent log
        required_dirs = self.patterns['required_dirs']
        
        for dir_name in required_dirs:
            dir_path = client_path / dir_name
            if not dir_path.exists():
                self.issues.append(ValidationIssue(
                    severity='error',
                    path=str(dir_path),
                    issue_type='missing_directory',
                    message=f"Missing required directory: {dir_name}",
                    suggestion=f"Create directory: mkdir -p {dir_path}",
                    auto_fixable=True
                ))
        # #endregion
    
    def _validate_files(self, client_path: Path, client_name: str):
        """Validate required files"""
        # #region agent log
        # Check README.md
        readme_path = client_path / 'README.md'
        if not readme_path.exists():
            self.issues.append(ValidationIssue(
                severity='error',
                path=str(readme_path),
                issue_type='missing_file',
                message="Missing README.md",
                suggestion="Create README.md following client directory template",
                auto_fixable=True
            ))
        
        # Check client config
        config_pattern = self.patterns['required_files'][1].format(client_name=client_name)
        config_path = client_path / config_pattern
        if not config_path.exists():
            # Try to find any config file
            config_files = list(client_path.glob('*_client_config.yaml'))
            if config_files:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    path=str(config_files[0]),
                    issue_type='naming_convention',
                    message=f"Config file should be named: {config_pattern}",
                    suggestion=f"Rename to: {config_pattern}",
                    auto_fixable=True
                ))
            else:
                self.issues.append(ValidationIssue(
                    severity='error',
                    path=str(config_path),
                    issue_type='missing_file',
                    message=f"Missing client config: {config_pattern}",
                    suggestion=f"Create {config_pattern} following template",
                    auto_fixable=True
                ))
        # #endregion
    
    def _validate_naming(self, client_path: Path, client_name: str):
        """Validate file naming conventions"""
        # #region agent log
        # Validate CSV files in campaigns
        campaigns_dir = client_path / 'campaigns'
        if campaigns_dir.exists():
            # Build pattern dynamically
            client_name_clean = client_name.replace('_', '')
            csv_pattern_template = self.patterns['naming_patterns']['csv_files']
            # Replace {client_name} placeholder
            csv_pattern = csv_pattern_template.replace('{client_name}', client_name_clean)
            
            for csv_file in campaigns_dir.rglob('*.csv'):
                if csv_file.name.startswith('.'):
                    continue
                
                # Check if matches pattern
                if not re.match(csv_pattern, csv_file.name, re.IGNORECASE):
                    # Check if it's an import/archive file
                    if 'import' in str(csv_file.parent) or 'archive' in str(csv_file.parent):
                        continue  # Skip imports/archives
                    
                    expected_name = self._infer_csv_name(csv_file.name, client_name)
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        path=str(csv_file),
                        issue_type='naming_convention',
                        message=f"CSV file doesn't follow naming pattern: {csv_file.name}",
                        suggestion=f"Consider renaming to: {expected_name}",
                        auto_fixable=False  # Manual review needed
                    ))
        # #endregion
    
    def _validate_content(self, client_path: Path, client_name: str):
        """Validate file content patterns"""
        # #region agent log
        # Check README structure
        readme_path = client_path / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            required_sections = [
                'Directory Structure',
                'Quick Access',
                'Campaign Overview'
            ]
            
            for section in required_sections:
                if section not in content:
                    self.issues.append(ValidationIssue(
                        severity='info',
                        path=str(readme_path),
                        issue_type='content_structure',
                        message=f"README.md missing section: {section}",
                        suggestion=f"Add '{section}' section to README.md",
                        auto_fixable=False
                    ))
        # #endregion
    
    def _infer_csv_name(self, current_name: str, client_name: str) -> str:
        """Infer proper CSV name from current name"""
        # #region agent log
        # Extract meaningful parts
        base_name = client_name.replace('_', '')
        base_name = ''.join(word.capitalize() for word in base_name.split('_'))
        
        # Try to extract description from current name
        if 'keyword' in current_name.lower():
            desc = 'Keywords'
        elif 'campaign' in current_name.lower():
            desc = 'Campaign'
        else:
            desc = 'Campaign'
        
        return f"{base_name}_{desc}_2025.csv"
        # #endregion
    
    def _auto_fix_issues(self, client_path: Path, client_name: str):
        """Automatically fix issues where possible"""
        # #region agent log
        for issue in self.issues:
            if not issue.auto_fixable:
                continue
            
            if issue.issue_type == 'missing_directory':
                Path(issue.path).mkdir(parents=True, exist_ok=True)
                issue.message = f"✅ Fixed: Created {issue.path}"
            
            elif issue.issue_type == 'missing_file':
                if 'README.md' in issue.path:
                    self._create_readme_template(client_path, client_name)
                elif 'client_config.yaml' in issue.path:
                    self._create_config_template(client_path, client_name)
        # #endregion
    
    def _create_readme_template(self, client_path: Path, client_name: str):
        """Create README.md template"""
        # #region agent log
        template = f"""# {client_name.replace('_', ' ').title()} Campaign Management

This directory contains all {client_name.replace('_', ' ')} campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
{client_name}/
├── campaigns/              # CSV exports for Google Ads Editor
├── docs/                   # Documentation and reports
├── assets/                 # Campaign assets (images, videos, etc.)
├── search_themes/          # Search theme configurations
├── {client_name}_client_config.yaml  # Client configuration
└── README.md              # This file
```

## 🎯 Quick Access

### Current Campaign CSVs
- Check `campaigns/` directory for available CSV files

### Documentation
- Analysis reports in `docs/` directory

## 📊 Campaign Overview

- **Client**: {client_name.replace('_', ' ').title()}
- **Account Status**: To be determined
- **Primary Services**: To be determined

## 🔧 Tools Available

### Campaign Tools (Agent Level - `../tools/`)
- `../tools/campaign/` - Campaign management tools

## 📈 Performance Notes

- Add campaign performance notes here
"""
        (client_path / 'README.md').write_text(template)
        # #endregion
    
    def _create_config_template(self, client_path: Path, client_name: str):
        """Create client config template"""
        # #region agent log
        config_name = f"{client_name}_client_config.yaml"
        template = f"""# {client_name.replace('_', ' ').title()} Client Configuration
# This file contains client-specific settings for {client_name.replace('_', ' ')} campaign management

client:
  name: "{client_name.replace('_', ' ').title()}"
  website: "To be determined"
  phone: "To be determined"
  industry: "To be determined"
  account_status: "To be determined"

services:
  - "Service 1"
  - "Service 2"

campaign_settings:
  primary_goal: "lead_generation"
  conversion_types: ["phone_calls", "form_submissions"]
  target_cpa: 40.00
  target_roas: 300

geographic_targeting:
  primary_location: "To be determined"
  radius_miles: 25
  additional_cities: []

performance_targets:
  monthly_conversions: 100
  cost_per_conversion: 40.00
  conversion_rate: 0.03
  return_on_ad_spend: 3.0

notes:
  - "Add client-specific notes here"
"""
        (client_path / config_name).write_text(template)
        # #endregion
    
    def infer_structure(self, client_name: str) -> Dict:
        """Infer optimal structure for a new client based on examples"""
        # #region agent log
        inference = {
            'recommended_dirs': self.patterns['required_dirs'].copy(),
            'recommended_files': [],
            'naming_suggestions': {},
            'content_suggestions': {}
        }
        
        # Analyze what other clients have
        common_docs = set()
        common_csv_patterns = []
        
        for client_dir in self.base_path.iterdir():
            if not client_dir.is_dir() or client_dir.name == client_name:
                continue
            
            # Collect common docs
            docs_dir = client_dir / 'docs'
            if docs_dir.exists():
                for doc in docs_dir.glob('*.md'):
                    common_docs.add(doc.name)
            
            # Collect CSV patterns
            campaigns_dir = client_dir / 'campaigns'
            if campaigns_dir.exists():
                for csv in campaigns_dir.glob('*.csv'):
                    if 'import' not in str(csv.parent) and 'archive' not in str(csv.parent):
                        common_csv_patterns.append(csv.name)
        
        inference['recommended_files'] = [
            'README.md',
            f'{client_name}_client_config.yaml'
        ]
        
        inference['content_suggestions'] = {
            'common_docs': list(common_docs),
            'common_csv_patterns': common_csv_patterns[:5]  # Top 5
        }
        
        # #endregion
        return inference

def main():
    parser = argparse.ArgumentParser(description='Validate client directory structure')
    parser.add_argument('--client', help='Client name to validate')
    parser.add_argument('--all', action='store_true', help='Validate all clients')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues where possible')
    parser.add_argument('--infer', help='Infer structure for new client')
    parser.add_argument('--output', help='Output JSON report file')
    
    args = parser.parse_args()
    
    validator = ClientStructureValidator()
    
    if args.infer:
        inference = validator.infer_structure(args.infer)
        print("\n🔍 Structure Inference for:", args.infer)
        print(json.dumps(inference, indent=2))
        return
    
    if args.all:
        clients = [d.name for d in validator.base_path.iterdir() 
                  if d.is_dir() and not d.name.startswith('_')]
        all_issues = {}
        for client in clients:
            issues = validator.validate_client(client, auto_fix=args.fix)
            all_issues[client] = [asdict(i) for i in issues]
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(all_issues, f, indent=2)
        
        # Print summary
        total_errors = sum(len([i for i in issues if i['severity'] == 'error']) 
                          for issues in all_issues.values())
        total_warnings = sum(len([i for i in issues if i['severity'] == 'warning']) 
                            for issues in all_issues.values())
        
        print(f"\n📊 Validation Summary:")
        print(f"   Clients checked: {len(clients)}")
        print(f"   Errors: {total_errors}")
        print(f"   Warnings: {total_warnings}")
        
    elif args.client:
        issues = validator.validate_client(args.client, auto_fix=args.fix)
        
        if not issues:
            print(f"✅ {args.client} structure is valid!")
        else:
            print(f"\n📋 Issues found for {args.client}:")
            for issue in issues:
                icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[issue.severity]
                print(f"{icon} [{issue.severity.upper()}] {issue.path}")
                print(f"   {issue.message}")
                if issue.suggestion:
                    print(f"   💡 Suggestion: {issue.suggestion}")
                print()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
