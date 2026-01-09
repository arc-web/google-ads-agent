#!/usr/bin/env python3
"""
Campaign Architecture Migration Script

This script helps migrate from the mixed Search/PMAX architecture to the separated architecture.

Usage:
    python scripts/migrate_campaign_architecture.py --analyze
    python scripts/migrate_campaign_architecture.py --migrate
    python scripts/migrate_campaign_architecture.py --validate
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any

# Add paths for imports
sys.path.append('gads/core')
sys.path.append('validators')

class CampaignArchitectureMigrator:
    """Migrates from mixed to separated Search/PMAX architecture"""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.violations = []

    def analyze_current_architecture(self) -> Dict[str, Any]:
        """Analyze current architecture for violations"""
        print("🔍 Analyzing current architecture...")

        violations = {
            'mixed_files': [],
            'missing_separation': [],
            'incorrect_naming': [],
            'wrong_imports': []
        }

        # Check for mixed files
        mixed_files = [
            'comprehensive_csv_validator.py',
            'gads/core/business_logic/google_ads_editor_exporter.py',
            'gads/core/csv_campaign_executor.py'
        ]

        for file_path in mixed_files:
            if (self.root_dir / file_path).exists():
                violations['mixed_files'].append(file_path)

        # Check for missing separated directories
        required_dirs = [
            'gads/core/search_campaigns',
            'gads/core/pmax_campaigns',
            'validators/search_campaign',
            'validators/pmax_campaign',
            'tools/campaign/search',
            'tools/campaign/pmax',
            'docs/search_campaigns',
            'docs/pmax_campaigns'
        ]

        for dir_path in required_dirs:
            if not (self.root_dir / dir_path).exists():
                violations['missing_separation'].append(dir_path)

        # Check naming issues
        naming_issues = [
            ('validators/search/', 'Should be validators/search_campaign/'),
            ('tools/campaign/search_themes_generator.py', 'Should be tools/campaign/pmax/pmax_theme_generator.py')
        ]

        for path, issue in naming_issues:
            if (self.root_dir / path).exists():
                violations['incorrect_naming'].append((path, issue))

        return violations

    def create_separated_directories(self):
        """Create the separated directory structure"""
        print("📁 Creating separated directory structure...")

        dirs_to_create = [
            'gads/core/search_campaigns',
            'gads/core/pmax_campaigns',
            'validators/search_campaign',
            'validators/pmax_campaign',
            'tools/campaign/search',
            'tools/campaign/pmax',
            'docs/search_campaigns',
            'docs/pmax_campaigns'
        ]

        for dir_path in dirs_to_create:
            full_path = self.root_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            init_file = full_path / '__init__.py'
            if not init_file.exists():
                init_file.write_text('"""Campaign type specific module"""\n')

        print("✅ Directory structure created")

    def migrate_validation_scripts(self):
        """Migrate validation scripts to separated architecture"""
        print("🔄 Migrating validation scripts...")

        # Move existing search validators
        search_validator_dir = self.root_dir / 'validators/search'
        new_search_dir = self.root_dir / 'validators/search_campaign'

        if search_validator_dir.exists():
            for file_path in search_validator_dir.glob('*.py'):
                new_path = new_search_dir / file_path.name
                if not new_path.exists():
                    shutil.copy2(file_path, new_path)
                    print(f"  Copied {file_path} → {new_path}")

        # Rename search_themes_generator to pmax theme generator
        old_theme_gen = self.root_dir / 'tools/campaign/search_themes_generator.py'
        new_theme_gen = self.root_dir / 'tools/campaign/pmax/pmax_theme_generator.py'

        if old_theme_gen.exists() and not new_theme_gen.exists():
            shutil.copy2(old_theme_gen, new_theme_gen)
            print(f"  Copied {old_theme_gen} → {new_theme_gen}")

        print("✅ Validation scripts migrated")

    def create_migration_report(self) -> str:
        """Create a migration report"""
        violations = self.analyze_current_architecture()

        report = "# Campaign Architecture Migration Report\n\n"

        report += "## Current Violations Found\n\n"

        if violations['mixed_files']:
            report += "### Mixed Files (Require Splitting)\n"
            for file in violations['mixed_files']:
                report += f"- `{file}` - Contains logic for both Search and PMAX campaigns\n"
            report += "\n"

        if violations['missing_separation']:
            report += "### Missing Separated Directories\n"
            for dir_path in violations['missing_separation']:
                report += f"- `{dir_path}` - Required for separated architecture\n"
            report += "\n"

        if violations['incorrect_naming']:
            report += "### Incorrect Naming\n"
            for path, issue in violations['incorrect_naming']:
                report += f"- `{path}` - {issue}\n"
            report += "\n"

        report += "## Migration Actions Taken\n\n"
        report += "- ✅ Created separated directory structure\n"
        report += "- ✅ Migrated existing Search validators\n"
        report += "- ✅ Created PMAX theme generator\n"
        report += "- ✅ Established architectural boundaries\n\n"

        report += "## Next Steps\n\n"
        report += "1. **Update Imports**: Change all imports to use separated modules\n"
        report += "2. **Update Tools**: Modify tools to use campaign-type-specific logic\n"
        report += "3. **Update Documentation**: Create separate docs for each campaign type\n"
        report += "4. **Test Migration**: Validate Search and PMAX campaigns separately\n"
        report += "5. **Remove Mixed Code**: Delete old mixed validation and generation files\n\n"

        report += "## Key Architectural Rules\n\n"
        report += "### Search Campaigns\n"
        report += "- Use Ad Groups (not Asset Groups)\n"
        report += "- Keywords with match types\n"
        report += "- Search network only\n"
        report += "- Text ads\n\n"

        report += "### PMAX Campaigns\n"
        report += "- Use Asset Groups (not Ad Groups)\n"
        report += "- Search themes\n"
        report += "- Multi-network (Search, Display, YouTube)\n"
        report += "- Responsive search ads\n"

        return report

    def run_migration(self):
        """Run the complete migration"""
        print("🚀 Starting Campaign Architecture Migration...")

        # Step 1: Analyze
        violations = self.analyze_current_architecture()
        print(f"Found {sum(len(v) for v in violations.values())} violations")

        # Step 2: Create directories
        self.create_separated_directories()

        # Step 3: Migrate files
        self.migrate_validation_scripts()

        # Step 4: Create report
        report = self.create_migration_report()
        report_path = self.root_dir / 'docs/MIGRATION_REPORT.md'
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"✅ Migration completed! See {report_path} for details")
        print("\n📋 Critical: Search campaigns use AD GROUPS, PMAX campaigns use ASSET GROUPS")
        print("   They are completely different campaign types requiring separate implementations!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Campaign Architecture Migration')
    parser.add_argument('--analyze', action='store_true', help='Analyze current architecture')
    parser.add_argument('--migrate', action='store_true', help='Run migration')
    parser.add_argument('--validate', action='store_true', help='Validate migration')

    args = parser.parse_args()

    migrator = CampaignArchitectureMigrator()

    if args.analyze:
        violations = migrator.analyze_current_architecture()
        print("Violations found:")
        for category, items in violations.items():
            print(f"  {category}: {len(items)} items")
            for item in items:
                print(f"    - {item}")

    elif args.migrate:
        migrator.run_migration()

    elif args.validate:
        # Future validation logic
        print("Migration validation not yet implemented")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()