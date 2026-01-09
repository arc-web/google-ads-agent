#!/usr/bin/env python3
"""
Search Campaign Master Validator

Integrates Search campaign validation into the main validation system.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import csv
import io

# Import existing master validator
from .master_validator import MasterValidator
# Import search validators
from .search import SearchValidator

logger = logging.getLogger(__name__)


class SearchMasterValidator(MasterValidator):
    """
    Extended master validator with Search campaign specialization.

    Inherits all functionality from MasterValidator and adds
    Search-specific validation capabilities.
    """

    def __init__(self, base_path: str = "google_ads_agent"):
        super().__init__()
        self.base_path = Path(base_path)
        self.search_validator = SearchValidator()

    def validate_search_campaign_csv(self, csv_path: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Validate a Search campaign CSV with specialized Search validation.

        Args:
            csv_path: Path to the CSV file
            auto_fix: Whether to auto-fix issues where possible

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting Search campaign validation of: {csv_path}")

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

        # Check if this is actually a Search campaign
        is_search_campaign = self._is_search_campaign_csv(csv_content)

        if not is_search_campaign:
            # Fall back to regular validation
            logger.info("CSV is not a Search campaign, using standard validation")
            return self.validate_csv_file(csv_path, auto_fix)

        # Perform Search-specific validation
        search_issues = self.search_validator.validate_search_csv(csv_path, csv_content)

        # Also run standard validation for account/campaign level issues
        standard_result = self.validate_csv_file(csv_path, False)  # Don't auto-fix yet
        standard_issues = standard_result['validation_report']['issues']

        # Combine issues, prioritizing Search-specific ones
        all_issues = search_issues + standard_issues

        # Remove duplicates (same issue from both validators)
        unique_issues = self._deduplicate_issues(all_issues)

        # Apply auto-fixes if requested
        if auto_fix:
            csv_content, fixed_issues = self._apply_search_auto_fixes(csv_content, unique_issues)
            if fixed_issues:
                # Save fixed version
                self._save_fixed_csv(csv_path, csv_content, fixed_issues)

        # Generate comprehensive report
        report = self._generate_search_validation_report(csv_path, unique_issues, fixed_issues if auto_fix else [])

        return {
            'csv_file': csv_path,
            'success': True,
            'error': None,
            'validation_report': report,
            'campaign_type': 'Search'
        }

    def _is_search_campaign_csv(self, csv_content: str) -> bool:
        """Determine if CSV contains Search campaigns"""
        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            for row in reader:
                campaign_type = row.get("Campaign Type", "").strip()
                if campaign_type == "Search":
                    return True

                # Also check for Search-specific columns
                if any(col for col in row.keys() if 'keyword' in col.lower() or 'criterion' in col.lower()):
                    return True

            return False

        except Exception:
            return False

    def _deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate issues from combined validation"""
        seen = set()
        unique_issues = []

        for issue in issues:
            # Create a unique key based on level, row, column, and issue type
            key = (
                issue['level'],
                issue['row_number'],
                issue['column'],
                issue['issue_type']
            )

            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        return unique_issues

    def _apply_search_auto_fixes(self, csv_content: str, issues: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Apply Search-specific auto-fixes"""
        fixed_issues = []

        # First apply standard auto-fixes
        csv_content, standard_fixed = self._apply_auto_fixes_to_csv(csv_content, issues)

        # Then apply Search-specific fixes
        lines = csv_content.split('\n')
        if len(lines) < 2:
            return csv_content, standard_fixed

        # Parse header
        header_line = lines[0]
        headers = header_line.split('\t')
        col_indices = {header: i for i, header in enumerate(headers)}

        # Apply Search-specific fixes
        for issue in issues:
            if issue.get('auto_fixable', False) and issue.get('fixed_value') is not None:
                row_num = issue['row_number']
                column = issue['column']

                if row_num < len(lines) and column in col_indices:
                    fields = lines[row_num - 1].split('\t')
                    col_idx = col_indices[column]

                    if col_idx < len(fields):
                        # Apply Search-specific logic
                        if column == 'Criterion Type' and not fields[col_idx].strip():
                            fields[col_idx] = 'Exact'  # Default Search match type
                            fixed_issues.append(issue)
                        elif issue['issue_type'] == 'headline_all_caps':
                            # Title case for headlines
                            fields[col_idx] = fields[col_idx].capitalize()
                            fixed_issues.append(issue)
                        else:
                            # Apply standard fix
                            fields[col_idx] = str(issue['fixed_value'])
                            fixed_issues.append(issue)

                        lines[row_num - 1] = '\t'.join(fields)

        return '\n'.join(lines), fixed_issues

    def _save_fixed_csv(self, csv_path: str, csv_content: str, fixed_issues: List[Dict[str, Any]]):
        """Save fixed CSV with backup"""
        backup_path = f"{csv_path}.backup"
        try:
            # Create backup
            with open(backup_path, 'w', encoding='utf-8-sig') as f:
                with open(csv_path, 'r', encoding='utf-8-sig') as orig:
                    f.write(orig.read())

            # Save fixed version
            with open(csv_path, 'w', encoding='utf-8-sig') as f:
                f.write(csv_content)

            logger.info(f"Applied {len(fixed_issues)} Search-specific fixes and created backup: {backup_path}")

        except Exception as e:
            logger.error(f"Failed to apply Search fixes: {e}")

    def _generate_search_validation_report(self, csv_path: str, issues: List[Dict[str, Any]],
                                        fixed_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate Search-specific validation report"""

        # Count issues by severity and level
        severity_counts = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        level_counts = {
            'account': 0, 'campaign': 0, 'asset_group': 0, 'asset': 0, 'targeting': 0,
            'search_campaign': 0, 'ad_group': 0, 'keyword': 0, 'text_ad': 0
        }

        for issue in issues:
            severity_counts[issue['severity']] += 1
            level_counts[issue['level']] += 1

        # Determine final status
        if severity_counts['critical'] > 0 or severity_counts['error'] > 0:
            final_status = 'FAIL'
        elif fixed_issues:
            final_status = 'PASS_WITH_FIXES'
        else:
            final_status = 'PASS'

        # Search-specific recommendations
        recommendations = []
        if level_counts['keyword'] > 0:
            recommendations.append("Review keyword match types and targeting strategy")
        if level_counts['text_ad'] > 0:
            recommendations.append("Optimize text ad length and content for better performance")
        if level_counts['ad_group'] > 0:
            recommendations.append("Consider ad group structure and keyword organization")

        return {
            'csv_file': csv_path,
            'timestamp': self._get_timestamp(),
            'campaign_type': 'Search',
            'total_issues': len(issues),
            'issues_fixed': len(fixed_issues),
            'severity_breakdown': severity_counts,
            'level_breakdown': level_counts,
            'final_status': final_status,
            'issues': issues,
            'fixes_applied': fixed_issues,
            'search_recommendations': recommendations,
            'quality_metrics': self._calculate_search_quality_metrics(issues)
        }

    def _calculate_search_quality_metrics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Search campaign quality metrics"""
        total_issues = len(issues)

        # Calculate quality score (inverse of issues, normalized)
        quality_score = max(0, 100 - (total_issues * 5))
        quality_score = min(100, quality_score)

        # Determine quality rating
        if quality_score >= 80:
            rating = 'Excellent'
        elif quality_score >= 60:
            rating = 'Good'
        elif quality_score >= 40:
            rating = 'Fair'
        else:
            rating = 'Poor'

        return {
            'quality_score': quality_score,
            'quality_rating': rating,
            'issues_per_100_rows': total_issues,  # Simplified metric
            'search_readiness': 'Ready' if quality_score >= 60 else 'Needs Work'
        }

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


def validate_search_campaign_file(csv_path: str, auto_fix: bool = False) -> Dict[str, Any]:
    """
    Convenience function to validate a single Search campaign CSV.

    Args:
        csv_path: Path to the CSV file
        auto_fix: Whether to auto-fix issues

    Returns:
        Validation report
    """
    validator = SearchMasterValidator()
    return validator.validate_search_campaign_csv(csv_path, auto_fix)


def validate_search_client_directory(client_dir: str, auto_fix: bool = False) -> Dict[str, Any]:
    """
    Validate all Search campaign CSVs in a client directory.

    Args:
        client_dir: Client directory path
        auto_fix: Whether to auto-fix issues

    Returns:
        Client-level validation report
    """
    validator = SearchMasterValidator()
    return validator.validate_client_directory(client_dir, auto_fix)


# CLI integration
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Search Campaign CSV Validator')
    parser.add_argument('--csv', help='Path to Search campaign CSV file')
    parser.add_argument('--client', help='Client directory containing Search CSVs')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues where possible')
    parser.add_argument('--output', help='Output JSON report file')

    args = parser.parse_args()

    validator = SearchMasterValidator()

    if args.csv:
        result = validator.validate_search_campaign_csv(args.csv, args.fix)
        validator.print_summary_report(result)

        if args.output:
            validator.save_report(result, args.output)

    elif args.client:
        result = validator.validate_client_directory(args.client, args.fix)
        validator.print_summary_report(result)

        if args.output:
            validator.save_report(result, args.output)
    else:
        parser.print_help()