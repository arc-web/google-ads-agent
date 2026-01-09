#!/usr/bin/env python3
"""
Master CSV Validator

Coordinates all hierarchical validators and generates comprehensive reports.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .account_validator import AccountValidator
from .campaign_validator import CampaignValidator
from .asset_group_validator import AssetGroupValidator
from .asset_validator import AssetValidator
from .targeting_validator import TargetingValidator

# Import search validators for enhanced validation
from .search.search_campaign_validator import SearchCampaignValidator
from .search.search_keyword_validator import SearchKeywordValidator
from .search.search_adgroup_validator import SearchAdGroupValidator
from .search.search_budget_validator import SearchBudgetValidator
from .search.search_location_validator import SearchLocationValidator

logger = logging.getLogger(__name__)


class MasterValidator:
    """
    Master validator that coordinates all hierarchical validation levels.
    """

    def __init__(self):
        # Core validators
        self.account_validator = AccountValidator()
        self.campaign_validator = CampaignValidator()
        self.asset_group_validator = AssetGroupValidator()
        self.asset_validator = AssetValidator()
        self.targeting_validator = TargetingValidator()

        # Enhanced search validators - UPDATED based on Context7 and our analysis
        self.search_campaign_validator = SearchCampaignValidator()
        self.search_keyword_validator = SearchKeywordValidator()
        self.search_adgroup_validator = SearchAdGroupValidator()
        self.search_budget_validator = SearchBudgetValidator()
        self.search_location_validator = SearchLocationValidator()

    def validate_csv_file(self, csv_path: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Validate a single CSV file through all hierarchical levels.

        Args:
            csv_path: Path to the CSV file
            auto_fix: Whether to auto-fix issues where possible

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting hierarchical validation of: {csv_path}")

        # Read CSV content
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                csv_content = f.read()
        except Exception as e:
            return {
                'csv_file': csv_path,
                'success': False,
                'error': f'Failed to read CSV file: {e}',
                'validation_report': None
            }

        # Collect all issues from all validators
        all_issues = []

        # Level 1: Account validation
        logger.info("Running account-level validation...")
        account_issues = self.account_validator.validate_csv_structure(csv_path, csv_content)
        account_issues.extend(self.account_validator.validate_account_settings(csv_path, csv_content))
        all_issues.extend(account_issues)

        # Level 2: Campaign validation - ENHANCED with search-specific validation
        logger.info("Running campaign-level validation...")
        campaign_issues = self.campaign_validator.validate_campaign_settings(csv_path, csv_content)

        # Add search campaign validation if this appears to be a search campaign
        if self._is_search_campaign_csv(csv_content):
            logger.info("Running enhanced search campaign validation...")
            search_campaign_issues = self._validate_search_campaign_data(csv_content)
            campaign_issues.extend(search_campaign_issues)

        all_issues.extend(campaign_issues)

        # Level 3: Asset group validation
        logger.info("Running asset group validation...")
        asset_group_issues = self.asset_group_validator.validate_asset_groups(csv_path, csv_content)
        all_issues.extend(asset_group_issues)

        # Level 4: Asset validation
        logger.info("Running asset validation...")
        asset_issues = self.asset_validator.validate_assets(csv_path, csv_content)
        all_issues.extend(asset_issues)

        # Level 5: Targeting validation
        logger.info("Running targeting validation...")
        targeting_issues = self.targeting_validator.validate_targeting(csv_path, csv_content)
        all_issues.extend(targeting_issues)

        # Apply auto-fixes if requested
        fixed_issues = []
        if auto_fix:
            logger.info("Applying auto-fixes...")
            csv_content, fixed_issues = self._apply_auto_fixes(csv_content, all_issues)

            # Save fixed CSV if any fixes were applied
            if fixed_issues:
                backup_path = f"{csv_path}.backup"
                try:
                    # Create backup
                    with open(backup_path, 'w', encoding='utf-8-sig') as f:
                        with open(csv_path, 'r', encoding='utf-8-sig') as orig:
                            f.write(orig.read())

                    # Save fixed version
                    with open(csv_path, 'w', encoding='utf-8-sig') as f:
                        f.write(csv_content)

                    logger.info(f"Applied {len(fixed_issues)} fixes and created backup: {backup_path}")
                except Exception as e:
                    logger.error(f"Failed to apply fixes: {e}")

        # Convert ValidationIssue objects to dicts for report generation
        all_issues_dicts = []
        for issue in all_issues:
            if hasattr(issue, '__dict__'):
                all_issues_dicts.append(issue.__dict__)
            else:
                all_issues_dicts.append(issue)

        fixed_issues_dicts = []
        for issue in fixed_issues:
            if hasattr(issue, '__dict__'):
                fixed_issues_dicts.append(issue.__dict__)
            else:
                fixed_issues_dicts.append(issue)

        # Generate validation report
        report = self._generate_validation_report(csv_path, all_issues_dicts, fixed_issues_dicts)

        return {
            'csv_file': csv_path,
            'success': True,
            'error': None,
            'validation_report': report
        }

    def validate_client_directory(self, client_dir: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Validate all CSV files in a client directory.

        Args:
            client_dir: Path to client directory
            auto_fix: Whether to auto-fix issues

        Returns:
            Client-level validation report
        """
        client_path = Path(client_dir)
        if not client_path.exists():
            return {
                'client_directory': client_dir,
                'success': False,
                'error': f'Client directory not found: {client_dir}',
                'validation_results': []
            }

        logger.info(f"Validating all CSVs in client directory: {client_dir}")

        # Find all CSV files (excluding reports)
        csv_files = self._find_csv_files(client_path)

        validation_results = []
        for csv_file in csv_files:
            result = self.validate_csv_file(str(csv_file), auto_fix)
            validation_results.append(result)

        # Generate client summary report
        client_report = self._generate_client_report(client_dir, validation_results)

        return {
            'client_directory': client_dir,
            'success': True,
            'error': None,
            'validation_results': validation_results,
            'client_summary': client_report
        }

    def validate_all_clients(self, base_dir: str = "google_ads_agent", auto_fix: bool = False) -> Dict[str, Any]:
        """
        Validate all client directories.

        Args:
            base_dir: Base directory containing client folders
            auto_fix: Whether to auto-fix issues

        Returns:
            Global validation report
        """
        base_path = Path(base_dir)
        if not base_path.exists():
            return {
                'base_directory': base_dir,
                'success': False,
                'error': f'Base directory not found: {base_dir}',
                'client_results': []
            }

        # Find all client directories
        client_dirs = [d for d in base_path.iterdir() if d.is_dir() and not d.name.startswith('_')]

        logger.info(f"Found {len(client_dirs)} client directories to validate")

        client_results = []
        for client_dir in client_dirs:
            result = self.validate_client_directory(str(client_dir), auto_fix)
            client_results.append(result)

        # Generate global summary
        global_report = self._generate_global_report(base_dir, client_results)

        return {
            'base_directory': base_dir,
            'success': True,
            'error': None,
            'client_results': client_results,
            'global_summary': global_report
        }

    def _find_csv_files(self, client_path: Path) -> List[Path]:
        """Find all campaign CSV files for a client"""
        csv_files = []

        # Look in campaigns directory
        campaigns_dir = client_path / 'campaigns'
        if campaigns_dir.exists():
            for csv_file in campaigns_dir.glob('*.csv'):
                # Skip archived files and imports
                if 'archive' not in str(csv_file.parent) and 'import' not in str(csv_file.parent):
                    csv_files.append(csv_file)

        # Also check root level campaign files
        for csv_file in client_path.glob('*.csv'):
            if 'campaign' in csv_file.name.lower() and 'report' not in csv_file.name.lower():
                csv_files.append(csv_file)

        return csv_files

    def _apply_auto_fixes(self, csv_content: str, all_issues: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Apply auto-fixes to CSV content"""
        fixed_issues = []

        # Group fixable issues by row and column
        fixes_by_location = {}
        for issue in all_issues:
            if issue.get('auto_fixable', False) and issue.get('fixed_value') is not None:
                key = (issue['row_number'], issue['column'])
                if key not in fixes_by_location:
                    fixes_by_location[key] = issue
                    fixed_issues.append(issue)

        if not fixed_issues:
            return csv_content, fixed_issues

        # Parse and fix CSV
        lines = csv_content.split('\n')
        if len(lines) < 2:
            return csv_content, fixed_issues

        # Parse header to get column indices
        header_line = lines[0]
        headers = header_line.split('\t')
        col_indices = {header: i for i, header in enumerate(headers)}

        # Apply fixes
        for (row_num, column), issue in fixes_by_location.items():
            if row_num < len(lines) and column in col_indices:
                fields = lines[row_num - 1].split('\t')  # -1 because row_num is 1-indexed
                col_idx = col_indices[column]
                if col_idx < len(fields):
                    fields[col_idx] = str(issue['fixed_value'])
                    lines[row_num - 1] = '\t'.join(fields)

        return '\n'.join(lines), fixed_issues

    def _generate_validation_report(self, csv_path: str, all_issues: List[Dict[str, Any]],
                                  fixed_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed validation report for a single CSV"""

        # Count issues by severity and level
        severity_counts = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        level_counts = {'account': 0, 'campaign': 0, 'asset_group': 0, 'asset': 0, 'targeting': 0, 'keyword': 0, 'adgroup': 0, 'budget': 0, 'location': 0}

        for issue in all_issues:
            severity = issue.get('severity', 'warning')
            level = issue.get('level', 'unknown')

            # Normalize severity values
            if severity == 'error':
                severity_counts['error'] += 1
            elif severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts['warning'] += 1

            # Normalize level values
            if level in level_counts:
                level_counts[level] += 1
            else:
                level_counts['unknown'] = level_counts.get('unknown', 0) + 1

        # Determine final status
        if severity_counts['critical'] > 0 or severity_counts['error'] > 0:
            final_status = 'FAIL'
        elif fixed_issues:
            final_status = 'PASS_WITH_FIXES'
        else:
            final_status = 'PASS'

        return {
            'csv_file': csv_path,
            'timestamp': datetime.now().isoformat(),
            'total_issues': len(all_issues),
            'issues_fixed': len(fixed_issues),
            'severity_breakdown': severity_counts,
            'level_breakdown': level_counts,
            'final_status': final_status,
            'issues': all_issues,
            'fixes_applied': fixed_issues
        }

    def _generate_client_report(self, client_dir: str, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate client-level summary report"""
        total_csvs = len(validation_results)
        successful_validations = sum(1 for r in validation_results if r['success'])
        total_issues = sum(r['validation_report']['total_issues'] for r in validation_results if r['success'] and r['validation_report'])
        total_fixes = sum(r['validation_report']['issues_fixed'] for r in validation_results if r['success'] and r['validation_report'])

        # Count final statuses
        status_counts = {'PASS': 0, 'PASS_WITH_FIXES': 0, 'FAIL': 0}
        for result in validation_results:
            if result['success'] and result['validation_report']:
                status = result['validation_report']['final_status']
                status_counts[status] += 1

        return {
            'client_directory': client_dir,
            'timestamp': datetime.now().isoformat(),
            'csv_files_processed': total_csvs,
            'successful_validations': successful_validations,
            'total_issues_found': total_issues,
            'total_fixes_applied': total_fixes,
            'status_breakdown': status_counts,
            'overall_status': 'PASS' if status_counts['FAIL'] == 0 else 'FAIL'
        }

    def _generate_global_report(self, base_dir: str, client_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate global summary report"""
        total_clients = len(client_results)
        successful_clients = sum(1 for r in client_results if r['success'])
        total_issues = sum(r['client_summary']['total_issues_found'] for r in client_results if r['success'] and r['client_summary'])
        total_fixes = sum(r['client_summary']['total_fixes_applied'] for r in client_results if r['success'] and r['client_summary'])

        # Count client statuses
        client_status_counts = {'PASS': 0, 'FAIL': 0}
        for result in client_results:
            if result['success'] and result['client_summary']:
                status = result['client_summary']['overall_status']
                client_status_counts[status] += 1

        return {
            'base_directory': base_dir,
            'timestamp': datetime.now().isoformat(),
            'clients_processed': total_clients,
            'successful_clients': successful_clients,
            'total_issues_found': total_issues,
            'total_fixes_applied': total_fixes,
            'client_status_breakdown': client_status_counts,
            'overall_status': 'PASS' if client_status_counts['FAIL'] == 0 else 'FAIL'
        }

    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save validation report to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to: {output_path}")

    def print_summary_report(self, report: Dict[str, Any]):
        """Print a human-readable summary of validation results"""
        print("\n" + "="*80)
        print("GOOGLE ADS CSV VALIDATION REPORT")
        print("="*80)

        if 'global_summary' in report:
            # Global report
            gs = report['global_summary']
            print(f"Directory: {gs['base_directory']}")
            print(f"Clients Processed: {gs['clients_processed']}")
            print(f"Successful: {gs['successful_clients']}")
            print(f"Total Issues Found: {gs['total_issues_found']}")
            print(f"Total Fixes Applied: {gs['total_fixes_applied']}")
            print(f"Overall Status: {gs['overall_status']}")

            if gs['client_status_breakdown']['PASS'] > 0:
                print(f"✅ Clients Passing: {gs['client_status_breakdown']['PASS']}")
            if gs['client_status_breakdown']['FAIL'] > 0:
                print(f"❌ Clients Failing: {gs['client_status_breakdown']['FAIL']}")

        elif 'client_summary' in report:
            # Client report
            cs = report['client_summary']
            print(f"Client Directory: {cs['client_directory']}")
            print(f"CSV Files Processed: {cs['csv_files_processed']}")
            print(f"Successful Validations: {cs['successful_validations']}")
            print(f"Total Issues Found: {cs['total_issues_found']}")
            print(f"Total Fixes Applied: {cs['total_fixes_applied']}")
            print(f"Overall Status: {cs['overall_status']}")

            status = cs['status_breakdown']
            if status['PASS'] > 0:
                print(f"✅ CSVs Passing: {status['PASS']}")
            if status['PASS_WITH_FIXES'] > 0:
                print(f"⚠️  CSVs Fixed: {status['PASS_WITH_FIXES']}")
            if status['FAIL'] > 0:
                print(f"❌ CSVs Failing: {status['FAIL']}")

        elif 'validation_report' in report:
            # Single CSV report
            vr = report['validation_report']
            print(f"CSV File: {vr['csv_file']}")
            print(f"Status: {vr['final_status']}")
            print(f"Total Issues: {vr['total_issues']}")
            print(f"Issues Fixed: {vr['issues_fixed']}")

            severity = vr['severity_breakdown']
            if severity['critical'] > 0:
                print(f"🚨 Critical: {severity['critical']}")
            if severity['error'] > 0:
                print(f"❌ Errors: {severity['error']}")
            if severity['warning'] > 0:
                print(f"⚠️  Warnings: {severity['warning']}")
            if severity['info'] > 0:
                print(f"ℹ️  Info: {severity['info']}")

        print("="*80 + "\n")

    def _is_search_campaign_csv(self, csv_content: str) -> bool:
        """Determine if CSV contains search campaign data"""
        lines = csv_content.split('\n')
        if len(lines) < 2:
            return False

        # Check headers for search campaign indicators
        header_line = lines[0].lower()
        search_indicators = ['campaign type', 'networks', 'keywords', 'ad group']

        return any(indicator in header_line for indicator in search_indicators)

    def _validate_search_campaign_data(self, csv_content: str) -> List[Dict[str, Any]]:
        """Validate search-specific campaign data with enhanced rules"""
        issues = []

        try:
            # Parse CSV content
            lines = csv_content.split('\n')
            if len(lines) < 2:
                return issues

            headers = [h.strip() for h in lines[0].split('\t')]
            rows = []

            for line_num, line in enumerate(lines[1:], 1):
                if line.strip():
                    fields = line.split('\t')
                    if len(fields) >= len(headers):
                        row_dict = dict(zip(headers, fields))
                        row_dict['_line_number'] = line_num + 1
                        rows.append(row_dict)

            # Extract different row types
            campaign_rows = [r for r in rows if r.get('Campaign') and not r.get('Ad Group') and not r.get('Keyword')]
            adgroup_rows = [r for r in rows if r.get('Ad Group') and not r.get('Keyword')]
            keyword_rows = [r for r in rows if r.get('Keyword')]

            # Validate campaigns
            for row in campaign_rows:
                campaign_issues = self.search_campaign_validator.validate_campaign_row(
                    {k: v for k, v in row.items() if k != '_line_number'},
                    row['_line_number']
                )
                issues.extend(campaign_issues)

            # Validate ad groups
            for row in adgroup_rows:
                adgroup_issues = self.search_adgroup_validator.validate_adgroup_row(
                    {k: v for k, v in row.items() if k != '_line_number'},
                    row['_line_number']
                )
                issues.extend(adgroup_issues)

            # Validate keywords
            for row in keyword_rows:
                keyword_issues = self.search_keyword_validator.validate_keyword_row(
                    {k: v for k, v in row.items() if k != '_line_number'},
                    row['_line_number']
                )
                issues.extend(keyword_issues)

            # Cross-validation
            if campaign_rows:
                campaign_issues = self.search_campaign_validator.validate_campaign_data(campaign_rows)
                issues.extend(campaign_issues)

            if adgroup_rows:
                adgroup_issues = self.search_adgroup_validator.validate_adgroup_data(adgroup_rows)
                issues.extend(adgroup_issues)

            if keyword_rows:
                keyword_issues = self.search_keyword_validator.validate_keyword_data(keyword_rows)
                issues.extend(keyword_issues)

            # Location validation
            if any('Location' in row or 'ZIP Code Targeting' in row for row in rows):
                location_issues = self.search_location_validator.validate_location_data(rows)
                issues.extend(location_issues)

        except Exception as e:
            logger.error(f"Error during search campaign validation: {e}")

        return issues