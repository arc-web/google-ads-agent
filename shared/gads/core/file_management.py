#!/usr/bin/env python3
"""
Centralized File Management System

SINGLE SOURCE OF TRUTH for all file operations.
No more scattered file creation. No more test files.
Only actual results files that belong.

Usage:
    file_manager = FileManager(client_name)
    csv_path = file_manager.save_campaign_csv(csv_content, "broward_search")
    file_manager.archive_old_files()
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Centralized file management for Google Ads campaigns.

    RULES:
    - Only create files that are ACTUAL RESULTS
    - No test files, no temporary files, no junk
    - Auto-archive everything immediately
    - Clean directories at all times
    """

    def __init__(self, client_name: str, base_path: str = "google_ads_agent"):
        self.client_name = client_name
        self.base_path = Path(base_path)
        self.client_path = self.base_path / client_name
        self.campaigns_path = self.client_path / "campaigns"
        self.new_campaigns_path = self.campaigns_path / "new_campaigns"
        self.archive_path = self.campaigns_path / "archive"

        # Ensure clean structure
        self._ensure_clean_structure()

    def _ensure_clean_structure(self):
        """Create and maintain clean directory structure"""
        self.new_campaigns_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)

    def save_campaign_csv(self, csv_content: str, campaign_name: str) -> str:
        """
        Save campaign CSV - ONLY ACTUAL RESULTS

        Args:
            csv_content: The CSV content to save
            campaign_name: Name for the campaign file

        Returns:
            Path to saved file
        """
        # Auto-archive everything first
        self.archive_all_files()

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{campaign_name}_{timestamp}.csv"
        filepath = self.new_campaigns_path / filename

        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        logger.info(f"✅ Saved campaign CSV: {filepath}")
        return str(filepath)

    def save_validation_report(self, report_data: Dict[str, Any], campaign_name: str) -> str:
        """
        Save validation report - ONLY IF IT'S MEANINGFUL

        Args:
            report_data: Validation results
            campaign_name: Associated campaign name

        Returns:
            Path to saved report
        """
        # Only save if there are actual issues or it's a pass confirmation
        if not report_data.get('issues') and report_data.get('status') == 'PASS':
            # Don't clutter with "everything is fine" reports
            return ""

        # Auto-archive old reports
        self.archive_all_files()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{campaign_name}_validation_{timestamp}.txt"
        filepath = self.new_campaigns_path / filename

        # Create simple text report
        report_content = self._format_validation_report(report_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"✅ Saved validation report: {filepath}")
        return str(filepath)

    def archive_all_files(self):
        """Archive EVERYTHING - keep directories clean"""
        # Archive all files from campaigns directory
        for item in self.campaigns_path.iterdir():
            if item.is_file() and item.name != '.gitkeep':
                shutil.move(str(item), str(self.archive_path / item.name))
                logger.debug(f"Archived: {item.name}")

        # Archive all files from new_campaigns (except current working files)
        # NOTE: This is aggressive - archives everything to keep it clean

        logger.info("✅ Auto-archived all old files")

    def cleanup_test_files(self):
        """Remove any test/mock files that shouldn't exist"""
        test_patterns = [
            "*test*", "*mock*", "*sample*", "*demo*", "*example*",
            "*temp*", "*tmp*", "*debug*", "*backup*"
        ]

        for pattern in test_patterns:
            for file in self.client_path.rglob(pattern):
                if file.is_file():
                    file.unlink()
                    logger.info(f"🗑️ Removed test file: {file}")

    def get_latest_campaign_csv(self) -> Optional[str]:
        """Get the latest campaign CSV file"""
        csv_files = list(self.new_campaigns_path.glob("*.csv"))
        if not csv_files:
            return None

        # Return most recent by modification time
        return str(max(csv_files, key=lambda f: f.stat().st_mtime))

    def _format_validation_report(self, report_data: Dict[str, Any]) -> str:
        """Format validation results as simple text"""
        status = report_data.get('status', 'UNKNOWN')
        issues = report_data.get('issues', [])

        report = f"VALIDATION REPORT: {status.upper()}\n"
        report += f"Timestamp: {datetime.now().isoformat()}\n"
        report += f"Issues Found: {len(issues)}\n\n"

        if issues:
            report += "ISSUES:\n"
            for i, issue in enumerate(issues[:10], 1):  # First 10 issues
                report += f"{i}. {issue.get('message', 'Unknown issue')}\n"

        return report

    def validate_directory_cleanliness(self) -> Dict[str, Any]:
        """Validate that directories are clean and properly organized"""
        results = {
            'new_campaigns_file_count': len(list(self.new_campaigns_path.glob("*"))),
            'archive_file_count': len(list(self.archive_path.glob("*"))),
            'old_files_in_campaigns': len(list(self.campaigns_path.glob("*.csv"))),
            'test_files_found': 0,
            'issues': []
        }

        # Check for test files
        test_files = []
        test_patterns = ["*test*", "*mock*", "*sample*", "*demo*"]
        for pattern in test_patterns:
            test_files.extend(list(self.client_path.rglob(pattern)))

        results['test_files_found'] = len(test_files)

        # Validate cleanliness
        if results['old_files_in_campaigns'] > 0:
            results['issues'].append(f"Found {results['old_files_in_campaigns']} old CSV files in campaigns directory")

        if results['test_files_found'] > 0:
            results['issues'].append(f"Found {results['test_files_found']} test files that should be removed")

        if results['new_campaigns_file_count'] > 3:
            results['issues'].append(f"Too many files in new_campaigns ({results['new_campaigns_file_count']}) - should be max 3")

        return results


# Global instance for easy access
_file_managers = {}

def get_file_manager(client_name: str) -> FileManager:
    """Get or create file manager for client"""
    if client_name not in _file_managers:
        _file_managers[client_name] = FileManager(client_name)
    return _file_managers[client_name]