#!/usr/bin/env python3
"""
Client Structure Pattern Inference System

Learns organizational patterns from existing client directories and provides
intelligent suggestions for new clients or fixing existing ones.

Usage:
    python client_structure_inference.py --analyze
    python client_structure_inference.py --suggest collab_med_spa
    python client_structure_inference.py --learn  # Update pattern database
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import re

try:
    import yaml
except ImportError:
    yaml = None

# #region agent log
import sys
# #endregion

@dataclass
class Pattern:
    """Represents a learned organizational pattern"""
    pattern_type: str  # 'directory', 'file', 'naming', 'content'
    pattern: str
    confidence: float  # 0.0 to 1.0
    examples: List[str]
    frequency: int

class PatternInferenceEngine:
    """Infers organizational patterns from existing client directories"""
    
    # #region agent log
    def __init__(self, base_path: str = "google_ads_agent"):
        self.base_path = Path(base_path)
        self.patterns: Dict[str, List[Pattern]] = defaultdict(list)
        self.learned_patterns_file = Path(".cursor/client_patterns.json")
    # #endregion
    
    def analyze_all_clients(self) -> Dict:
        """Analyze all client directories to learn patterns"""
        # #region agent log
        analysis = {
            'directory_structure': defaultdict(int),
            'file_naming': defaultdict(Counter),
            'file_content': defaultdict(set),
            'common_files': Counter(),
            'common_dirs': Counter(),
            'naming_conventions': defaultdict(list)
        }
        
        if not self.base_path.exists():
            return analysis
        
        client_dirs = [d for d in self.base_path.iterdir() 
                      if d.is_dir() and not d.name.startswith('_')]
        
        for client_dir in client_dirs:
            # #endregion
            self._analyze_client_structure(client_dir, analysis)
            self._analyze_naming_patterns(client_dir, analysis)
            self._analyze_content_patterns(client_dir, analysis)
        
        # #region agent log
        return analysis
        # #endregion
    
    def _analyze_client_structure(self, client_dir: Path, analysis: Dict):
        """Analyze directory structure patterns"""
        # #region agent log
        structure = []
        for item in client_dir.iterdir():
            if item.is_dir():
                structure.append(item.name)
                analysis['common_dirs'][item.name] += 1
        
        structure_key = '/'.join(sorted(structure))
        analysis['directory_structure'][structure_key] += 1
        # #endregion
    
    def _analyze_naming_patterns(self, client_dir: Path, analysis: Dict):
        """Analyze file naming patterns"""
        # #region agent log
        client_name = client_dir.name
        
        # Analyze CSV files
        campaigns_dir = client_dir / 'campaigns'
        if campaigns_dir.exists():
            for csv_file in campaigns_dir.rglob('*.csv'):
                if 'import' in str(csv_file.parent) or 'archive' in str(csv_file.parent):
                    continue
                
                # Extract pattern
                name = csv_file.name
                pattern = self._extract_naming_pattern(name, client_name)
                analysis['file_naming']['csv'][pattern] += 1
                analysis['naming_conventions']['csv'].append(name)
        
        # Analyze config files
        config_files = list(client_dir.glob('*_client_config.yaml'))
        for config_file in config_files:
            pattern = self._extract_naming_pattern(config_file.name, client_name)
            analysis['file_naming']['config'][pattern] += 1
        
        # Analyze doc files
        docs_dir = client_dir / 'docs'
        if docs_dir.exists():
            for doc_file in docs_dir.glob('*.md'):
                analysis['common_files'][doc_file.name] += 1
                analysis['file_content']['doc_names'].add(doc_file.name)
        # #endregion
    
    def _analyze_content_patterns(self, client_dir: Path, analysis: Dict):
        """Analyze content patterns in files"""
        # #region agent log
        readme_path = client_dir / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            sections = self._extract_readme_sections(content)
            for section in sections:
                analysis['file_content']['readme_sections'].add(section)
        
        config_files = list(client_dir.glob('*_client_config.yaml'))
        for config_file in config_files:
            try:
                if yaml:
                    with open(config_file) as f:
                        config = yaml.safe_load(f)
                        if config:
                            for key in config.keys():
                                analysis['file_content']['config_keys'].add(key)
            except:
                pass
        # #endregion
    
    def _extract_naming_pattern(self, filename: str, client_name: str) -> str:
        """Extract naming pattern from filename"""
        # #region agent log
        # Remove client name to get pattern
        pattern = filename.replace(client_name, '{client}')
        pattern = re.sub(r'\d{4}', '{year}', pattern)
        pattern = re.sub(r'[A-Z][a-z]+', '{Word}', pattern)
        return pattern
        # #endregion
    
    def _extract_readme_sections(self, content: str) -> List[str]:
        """Extract section headers from README"""
        # #region agent log
        sections = []
        for line in content.split('\n'):
            if line.startswith('##'):
                sections.append(line.strip('# ').strip())
        return sections
        # #endregion
    
    def infer_patterns(self) -> Dict[str, List[Pattern]]:
        """Infer patterns from analysis"""
        # #region agent log
        analysis = self.analyze_all_clients()
        patterns = defaultdict(list)
        
        # Infer directory patterns
        total_clients = sum(analysis['directory_structure'].values())
        for structure, count in analysis['directory_structure'].items():
            confidence = count / total_clients if total_clients > 0 else 0
            if confidence >= 0.5:  # Present in at least 50% of clients
                patterns['directory'].append(Pattern(
                    pattern_type='directory',
                    pattern=structure,
                    confidence=confidence,
                    examples=[structure],
                    frequency=count
                ))
        
        # Infer file naming patterns
        for file_type in ['csv', 'config']:
            total = sum(analysis['file_naming'][file_type].values())
            for pattern, count in analysis['file_naming'][file_type].most_common(5):
                confidence = count / total if total > 0 else 0
                if confidence >= 0.3:  # At least 30% use this pattern
                    patterns['naming'].append(Pattern(
                        pattern_type='naming',
                        pattern=pattern,
                        confidence=confidence,
                        examples=list(analysis['naming_conventions'].get(file_type, []))[:3],
                        frequency=count
                    ))
        
        # Infer common files
        total_clients = len([d for d in self.base_path.iterdir() 
                            if d.is_dir() and not d.name.startswith('_')])
        for filename, count in analysis['common_files'].most_common(10):
            confidence = count / total_clients if total_clients > 0 else 0
            if confidence >= 0.5:
                patterns['files'].append(Pattern(
                    pattern_type='file',
                    pattern=filename,
                    confidence=confidence,
                    examples=[filename],
                    frequency=count
                ))
        
        # #endregion
        return patterns
    
    def suggest_for_client(self, client_name: str) -> Dict:
        """Suggest structure for a specific client"""
        # #region agent log
        patterns = self.infer_patterns()
        client_path = self.base_path / client_name
        
        suggestions = {
            'missing_directories': [],
            'missing_files': [],
            'naming_issues': [],
            'content_suggestions': []
        }
        
        # Check directories
        required_dirs = ['campaigns', 'docs', 'assets', 'search_themes']
        for dir_name in required_dirs:
            if not (client_path / dir_name).exists():
                suggestions['missing_directories'].append({
                    'name': dir_name,
                    'confidence': 1.0,
                    'reason': 'Present in all client directories'
                })
        
        # Check files
        if not (client_path / 'README.md').exists():
            suggestions['missing_files'].append({
                'name': 'README.md',
                'confidence': 1.0,
                'reason': 'Required in all client directories'
            })
        
        config_pattern = f"{client_name}_client_config.yaml"
        if not (client_path / config_pattern).exists():
            suggestions['missing_files'].append({
                'name': config_pattern,
                'confidence': 1.0,
                'reason': 'Standard client config naming pattern'
            })
        
        # Check naming
        campaigns_dir = client_path / 'campaigns'
        if campaigns_dir.exists():
            for csv_file in campaigns_dir.glob('*.csv'):
                if 'import' not in str(csv_file.parent) and 'archive' not in str(csv_file.parent):
                    # Check if follows pattern
                    expected_pattern = f"{client_name.replace('_', '')}_*_2025.csv"
                    if not re.match(expected_pattern.replace('*', '.*'), csv_file.name, re.IGNORECASE):
                        suggestions['naming_issues'].append({
                            'file': str(csv_file),
                            'current': csv_file.name,
                            'suggested': self._suggest_csv_name(csv_file.name, client_name),
                            'confidence': 0.8
                        })
        
        # #endregion
        return suggestions
    
    def _suggest_csv_name(self, current_name: str, client_name: str) -> str:
        """Suggest proper CSV name"""
        # #region agent log
        base = ''.join(word.capitalize() for word in client_name.split('_'))
        
        # Extract description
        if 'keyword' in current_name.lower():
            desc = 'Keywords'
        elif 'campaign' in current_name.lower():
            desc = 'Campaign'
        else:
            desc = 'Campaign'
        
        return f"{base}_{desc}_2025.csv"
        # #endregion
    
    def save_patterns(self):
        """Save learned patterns to file"""
        # #region agent log
        patterns = self.infer_patterns()
        patterns_dict = {}
        for pattern_type, pattern_list in patterns.items():
            patterns_dict[pattern_type] = [
                {
                    'pattern': p.pattern,
                    'confidence': p.confidence,
                    'frequency': p.frequency,
                    'examples': p.examples[:3]
                }
                for p in pattern_list
            ]
        
        self.learned_patterns_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.learned_patterns_file, 'w') as f:
            json.dump(patterns_dict, f, indent=2)
        # #endregion
    
    def load_patterns(self) -> Dict:
        """Load learned patterns from file"""
        # #region agent log
        if self.learned_patterns_file.exists():
            with open(self.learned_patterns_file) as f:
                return json.load(f)
        return {}
        # #endregion

def main():
    parser = argparse.ArgumentParser(description='Infer client structure patterns')
    parser.add_argument('--analyze', action='store_true', help='Analyze all clients')
    parser.add_argument('--learn', action='store_true', help='Learn and save patterns')
    parser.add_argument('--suggest', help='Suggest structure for client')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    engine = PatternInferenceEngine()
    
    if args.learn:
        print("🔍 Learning patterns from existing clients...")
        patterns = engine.infer_patterns()
        engine.save_patterns()
        print(f"✅ Learned {sum(len(p) for p in patterns.values())} patterns")
        print(f"📁 Saved to: {engine.learned_patterns_file}")
    
    elif args.analyze:
        print("📊 Analyzing all client directories...")
        analysis = engine.analyze_all_clients()
        
        print(f"\n📁 Common Directories:")
        for dir_name, count in analysis['common_dirs'].most_common():
            print(f"   {dir_name}: {count} clients")
        
        print(f"\n📄 Common Files:")
        for filename, count in analysis['common_files'].most_common(10):
            print(f"   {filename}: {count} clients")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"\n💾 Saved analysis to: {args.output}")
    
    elif args.suggest:
        print(f"💡 Suggestions for: {args.suggest}")
        suggestions = engine.suggest_for_client(args.suggest)
        
        if suggestions['missing_directories']:
            print("\n📁 Missing Directories:")
            for item in suggestions['missing_directories']:
                print(f"   ❌ {item['name']} (confidence: {item['confidence']:.0%})")
        
        if suggestions['missing_files']:
            print("\n📄 Missing Files:")
            for item in suggestions['missing_files']:
                print(f"   ❌ {item['name']} (confidence: {item['confidence']:.0%})")
        
        if suggestions['naming_issues']:
            print("\n🏷️  Naming Issues:")
            for item in suggestions['naming_issues']:
                print(f"   ⚠️  {item['current']}")
                print(f"      → {item['suggested']}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(suggestions, f, indent=2)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
