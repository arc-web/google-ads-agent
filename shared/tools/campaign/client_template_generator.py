#!/usr/bin/env python3
"""
Intelligent Client Template Generator

Uses inferred patterns and AI assistance to generate client directory structures
that follow organizational best practices.

Usage:
    python client_template_generator.py --client new_client_name
    python client_template_generator.py --client new_client --infer-from collab_med_spa
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Optional
import sys

try:
    import yaml
except ImportError:
    yaml = None

# #region agent log
# #endregion

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent))
try:
    from client_structure_inference import PatternInferenceEngine
    from client_structure_validator import ClientStructureValidator
except ImportError:
    # Fallback if imports fail
    PatternInferenceEngine = None
    ClientStructureValidator = None

class ClientTemplateGenerator:
    """Generates client directory structures using inferred patterns"""
    
    # #region agent log
    def __init__(self, base_path: str = "google_ads_agent"):
        self.base_path = Path(base_path)
        self.inference_engine = PatternInferenceEngine(base_path)
        self.validator = ClientStructureValidator(base_path)
    # #endregion
    
    def generate_client_structure(
        self, 
        client_name: str, 
        reference_client: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict:
        """Generate complete client directory structure"""
        # #region agent log
        client_path = self.base_path / client_name
        
        if client_path.exists():
            return {
                'success': False,
                'error': f"Client directory already exists: {client_name}"
            }
        
        # Load patterns
        patterns = self.inference_engine.load_patterns()
        if not patterns:
            patterns = self.inference_engine.infer_patterns()
            self.inference_engine.save_patterns()
        
        # Create structure
        created = []
        
        # Create directories
        required_dirs = ['campaigns', 'docs', 'assets', 'search_themes']
        for dir_name in required_dirs:
            dir_path = client_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        
        # Create subdirectories
        (client_path / 'campaigns' / 'archive').mkdir(exist_ok=True)
        (client_path / 'campaigns' / 'imports').mkdir(exist_ok=True)
        
        # Generate files
        self._generate_readme(client_path, client_name, reference_client, website, industry)
        self._generate_config(client_path, client_name, website, industry)
        self._generate_assets_readme(client_path)
        self._generate_search_themes(client_path, client_name)
        
        # Validate
        issues = self.validator.validate_client(client_name)
        
        # #endregion
        return {
            'success': True,
            'client_path': str(client_path),
            'created': created,
            'validation_issues': len([i for i in issues if i.severity == 'error']),
            'warnings': len([i for i in issues if i.severity == 'warning'])
        }
    
    def _generate_readme(
        self, 
        client_path: Path, 
        client_name: str,
        reference_client: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None
    ):
        """Generate README.md from template"""
        # #region agent log
        display_name = client_name.replace('_', ' ').title()
        
        # Load reference README if provided
        reference_content = None
        if reference_client:
            ref_path = self.base_path / reference_client / 'README.md'
            if ref_path.exists():
                reference_content = ref_path.read_text()
        
        template = f"""# {display_name} Campaign Management

This directory contains all {display_name} campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
{client_name}/
├── campaigns/              # CSV exports for Google Ads Editor
│   ├── archive/            # Archived campaign CSVs
│   └── imports/            # Imported Google Ads Editor exports
├── docs/                   # Documentation and reports
├── assets/                 # Campaign assets (images, videos, etc.)
├── search_themes/          # Search theme configurations
├── {client_name}_client_config.yaml  # Client configuration
└── README.md              # This file

# Agent-level tools (../tools/)
├── campaign_plan.py        # Generate campaign CSVs
└── run_campaign_plan.sh   # Campaign planning script
```

## 🎯 Quick Access

### Current Campaign CSVs
- Check `campaigns/` directory for available CSV files

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Documentation
- Analysis reports in `docs/` directory

### Campaign Planning
```bash
cd ../tools/
python3 campaign_plan.py
```

### View Campaign Summary
```bash
cd campaigns/
ls -la *.csv
```

## 📊 Campaign Overview

- **Client**: {display_name}
{f"- **Website**: {website}" if website else "- **Website**: To be determined"}
{f"- **Industry**: {industry}" if industry else "- **Industry**: To be determined"}
- **Account Status**: To be determined

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 🔧 Tools Available

### Campaign Tools (Agent Level - `../tools/`)
- `../tools/campaign/campaign_plan.py` - Generate campaign CSVs
- `../tools/campaign/rsa_campaign_generator.py` - Generate RSA campaigns
- `../tools/campaign/search_themes_generator.py` - Generate search themes
- `../tools/campaign/website_content_analyzer.py` - Analyze website content

### Documentation
- Campaign documentation in `docs/` directory
- Implementation guides and strategy documents

## 📈 Performance Notes

- Add campaign performance notes here
"""
        
        (client_path / 'README.md').write_text(template)
        # #endregion
    
    def _generate_config(
        self, 
        client_path: Path, 
        client_name: str,
        website: Optional[str] = None,
        industry: Optional[str] = None
    ):
        """Generate client config YAML"""
        # #region agent log
        config_name = f"{client_name}_client_config.yaml"
        display_name = client_name.replace('_', ' ').title()
        
        template = f"""# {display_name} Client Configuration
# This file contains client-specific settings for {display_name} campaign management

client:
  name: "{display_name}"
  website: "{website or 'To be determined'}"
  phone: "To be determined"
  industry: "{industry or 'To be determined'}"
  account_status: "To be determined"

services:
  - "Service 1"
  - "Service 2"

campaign_settings:
  primary_goal: "lead_generation"
  conversion_types: ["phone_calls", "form_submissions"]
  target_cpa: 40.00
  target_roas: 300

budget_allocation:
  primary_campaign: 1.0

geographic_targeting:
  primary_location: "To be determined"
  radius_miles: 25
  additional_cities: []

performance_targets:
  monthly_conversions: 100
  cost_per_conversion: 40.00
  conversion_rate: 0.03
  return_on_ad_spend: 3.0

keywords:
  primary_search_terms:
    - "primary keyword 1"
    - "primary keyword 2"

  negative_keywords:
    - "cheap"
    - "free"
    - "DIY"

assets:
  required_images: 15
  required_videos: 3
  trust_badges: true
  before_after_photos: true

compliance:
  licensed: true
  insured: true
  certifications: []
  regulatory_requirements: []

notes:
  - "Add client-specific notes here"
"""
        
        (client_path / config_name).write_text(template)
        # #endregion
    
    def _generate_assets_readme(self, client_path: Path):
        """Generate assets README"""
        # #region agent log
        assets_dir = client_path / 'assets'
        template = """# Campaign Assets

This directory contains all creative assets for Google Ads campaigns.

## Directory Structure

```
assets/
├── images/          # Campaign images and graphics
├── videos/          # Video content and demonstrations
├── documents/       # Supporting documents and PDFs
└── README.md       # This file
```

## Asset Requirements

### Images
- **Format**: JPG, PNG (high quality)
- **Dimensions**: 1200x628 for carousel, 300x300 for square
- **File Size**: <5MB per image

### Videos
- **Format**: MP4 (H.264 codec)
- **Duration**: 15-60 seconds
- **Resolution**: 1920x1080 (1080p)

## File Naming Convention

Format: `ServiceType_AssetType_Descriptor_Number.Extension`

Examples:
- `Service_BeforeAfter_Example_001.jpg`
- `Video_Testimonial_CustomerStory_001.mp4`
"""
        
        (assets_dir / 'README.md').write_text(template)
        # #endregion
    
    def _generate_search_themes(self, client_path: Path, client_name: str):
        """Generate search themes files"""
        # #region agent log
        search_themes_dir = client_path / 'search_themes'
        
        # CSV
        csv_content = """Campaign,Search theme,Source,Status
Campaign Name,primary search term,search_theme,Enabled
Campaign Name,secondary search term,search_theme,Enabled
"""
        (search_themes_dir / 'search_themes.csv').write_text(csv_content)
        
        # Markdown
        md_content = f"""# {client_name.replace('_', ' ').title()} Performance Max Campaign Themes

## Overview

Performance Max campaigns utilize search themes to guide Google's AI in finding relevant audiences.

## Campaign Themes

### Campaign Name
- Primary search term
- Secondary search term

## Search Theme Strategy

- Include "near me" variations
- Include location-specific terms
- Focus on service area targeting
"""
        
        (search_themes_dir / 'pmax_campaign_themes.md').write_text(md_content)
        # #endregion

def main():
    parser = argparse.ArgumentParser(description='Generate client directory structure')
    parser.add_argument('--client', required=True, help='Client name (use underscores)')
    parser.add_argument('--infer-from', help='Reference client to infer patterns from')
    parser.add_argument('--website', help='Client website URL')
    parser.add_argument('--industry', help='Client industry')
    
    args = parser.parse_args()
    
    generator = ClientTemplateGenerator()
    
    result = generator.generate_client_structure(
        client_name=args.client,
        reference_client=args.infer_from,
        website=args.website,
        industry=args.industry
    )
    
    if result['success']:
        print(f"✅ Generated client structure for: {args.client}")
        print(f"📁 Location: {result['client_path']}")
        print(f"📊 Validation: {result['validation_issues']} errors, {result['warnings']} warnings")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
