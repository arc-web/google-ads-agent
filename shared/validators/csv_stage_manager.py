#!/usr/bin/env python3
"""
CSV Stage Manager

Manages CSV lifecycle stages (initial, analyzed, final) to prevent infinite validation loops
and coordinate between campaign builder and validation system.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import csv
from datetime import datetime


class CSVStageManager:
    """
    Manages CSV file stages and workflow coordination.

    Stages:
    - initial: Freshly built by campaign builder (triggers validation)
    - analyzed: Validation completed, analysis report generated
    - final: Optimized CSV created, no further processing needed
    """

    def __init__(self, base_path: str = "google_ads_agent"):
        self.base_path = Path(base_path)
        self.new_campaigns_dir = None

    def get_csv_stage(self, csv_path: str) -> str:
        """
        Determine the stage of a CSV file.

        CRITICAL: NEVER read CSV content for stage detection to preserve row 1 headers.
        Only use filename patterns and metadata files.

        Args:
            csv_path: Path to the CSV file

        Returns:
            Stage: 'initial', 'analyzed', 'final', or 'unknown'
        """
        path = Path(csv_path)
        filename = path.name.lower()

        # Check filename patterns (most reliable method)
        if '_final' in filename or '_optimized' in filename or '_complete' in filename:
            return 'final'
        elif '_analyzed' in filename or '_validated' in filename or '_checked' in filename:
            return 'analyzed'
        elif '_initial' in filename or '_draft' in filename or '_raw' in filename:
            return 'initial'

        # Check for metadata file
        metadata_file = path.parent / f"{path.stem}_metadata.txt"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('Stage:'):
                            stage = line.split(':')[1].strip().lower()
                            if stage in ['initial', 'analyzed', 'final']:
                                return stage
            except Exception:
                pass

        # Default to initial for new files in new_campaigns directory
        if 'new_campaigns' in str(path):
            return 'initial'

        return 'unknown'

    def mark_csv_stage(self, csv_path: str, stage: str, reason: str = "") -> bool:
        """
        Mark a CSV file with its current stage.

        CRITICAL: NEVER modify the CSV content itself to preserve row 1 as headers.
        Stage information is stored in filenames and separate metadata files only.

        Args:
            csv_path: Path to the CSV file
            stage: New stage ('initial', 'analyzed', 'final')
            reason: Optional reason for stage change

        Returns:
            Success status
        """
        valid_stages = ['initial', 'analyzed', 'final']
        if stage not in valid_stages:
            return False

        path = Path(csv_path)

        try:
            # NEVER modify the CSV content - this would break row 1 headers
            # Instead, use filename-based stage indication

            current_name = path.name
            base_name = current_name

            # Remove any existing stage indicators from filename
            for s in valid_stages:
                base_name = base_name.replace(f'_{s}', '').replace(f'_{s.capitalize()}', '')

            # Add new stage to filename
            name_parts = base_name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{stage}.{name_parts[1]}"
            else:
                new_name = f"{base_name}_{stage}"

            new_path = path.parent / new_name

            # Rename file to include stage
            path.rename(new_path)

            # Create separate metadata file for additional info
            if reason:
                metadata_file = new_path.parent / f"{new_path.stem}_metadata.txt"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    f.write(f"Stage: {stage}\n")
                    f.write(f"Reason: {reason}\n")
                    from datetime import datetime
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")

            return True

        except Exception as e:
            print(f"Error marking CSV stage: {e}")
            return False

    def should_trigger_validation(self, csv_path: str) -> bool:
        """
        Determine if validation should be triggered for a CSV file.

        Args:
            csv_path: Path to the CSV file

        Returns:
            True if validation should be triggered
        """
        stage = self.get_csv_stage(csv_path)

        # Only trigger validation on initial stage CSVs
        return stage == 'initial'

    def get_campaign_workflow_files(self, campaign_dir: str) -> Dict[str, str]:
        """
        Get all files related to a campaign workflow.

        Args:
            campaign_dir: Campaign directory path

        Returns:
            Dictionary mapping file types to file paths
        """
        campaign_path = Path(campaign_dir)
        workflow_files = {
            'initial_csv': None,
            'analysis_report': None,
            'final_csv': None,
            'optimization_log': None
        }

        if not campaign_path.exists():
            return workflow_files

        for file_path in campaign_path.glob('*.csv'):
            stage = self.get_csv_stage(str(file_path))
            filename = file_path.name.lower()

            if stage == 'initial' or '_initial' in filename or '_draft' in filename:
                workflow_files['initial_csv'] = str(file_path)
            elif stage == 'final' or '_final' in filename or '_optimized' in filename:
                workflow_files['final_csv'] = str(file_path)

        # Look for analysis reports
        for file_path in campaign_path.glob('*.json'):
            if 'analysis' in file_path.name.lower() or 'validation' in file_path.name.lower():
                workflow_files['analysis_report'] = str(file_path)

        for file_path in campaign_path.glob('*.log'):
            if 'optimization' in file_path.name.lower():
                workflow_files['optimization_log'] = str(file_path)

        return workflow_files

    def create_analysis_feedback(self, csv_path: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create feedback for the campaign builder based on analysis results.

        Args:
            csv_path: Path to the analyzed CSV
            analysis_results: Validation analysis results

        Returns:
            Feedback dictionary for campaign builder
        """
        feedback = {
            'csv_path': csv_path,
            'timestamp': datetime.now().isoformat(),
            'stage': 'analyzed',
            'overall_status': analysis_results.get('final_status', 'UNKNOWN'),
            'critical_issues': 0,
            'warnings': 0,
            'recommendations': [],
            'optimization_suggestions': []
        }

        # Count issues by severity
        issues = analysis_results.get('issues', [])
        for issue in issues:
            severity = issue.get('severity', 'info')
            if severity == 'critical' or severity == 'error':
                feedback['critical_issues'] += 1
            elif severity == 'warning':
                feedback['warnings'] += 1

        # Extract recommendations
        feedback['recommendations'] = [
            issue.get('message', '')[:100] + '...' if len(issue.get('message', '')) > 100 else issue.get('message', '')
            for issue in issues[:10]  # Top 10 recommendations
        ]

        # Generate optimization suggestions based on issue patterns
        feedback['optimization_suggestions'] = self._generate_optimization_suggestions(issues)

        return feedback

    def _generate_optimization_suggestions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization suggestions based on issue patterns"""
        suggestions = []
        issue_types = {}

        # Count issue types
        for issue in issues:
            issue_type = issue.get('issue_type', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        # Generate suggestions based on common issues
        if issue_types.get('missing_positioning_headlines', 0) > 0:
            suggestions.append("Add #1 positioning headlines to establish authority")

        if issue_types.get('missing_brand_recognition', 0) > 0:
            suggestions.append("Include Wright's brand names in headlines")

        if issue_types.get('missing_value_impact_messaging', 0) > 0:
            suggestions.append("Add value impact messaging about hurricane protection")

        if issue_types.get('headline_too_short', 0) > 0:
            suggestions.append("Expand headlines to meet 25-30 character recommendations")

        if issue_types.get('description_too_short', 0) > 0:
            suggestions.append("Expand descriptions to meet 70-90 character optimal length")

        if not suggestions:
            suggestions.append("Review and optimize ad copy for better performance")

        return suggestions

    def save_feedback_to_campaign_builder(self, feedback: Dict[str, Any], campaign_dir: str) -> str:
        """
        Save feedback for campaign builder to consume.

        Args:
            feedback: Feedback dictionary
            campaign_dir: Campaign directory

        Returns:
            Path to feedback file
        """
        campaign_path = Path(campaign_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        feedback_file = campaign_path / f"validation_feedback_{timestamp}.json"

        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback, f, indent=2, ensure_ascii=False)

            return str(feedback_file)

        except Exception as e:
            print(f"Error saving feedback: {e}")
            return ""

    def monitor_new_campaigns_directory(self, client_dir: str) -> List[str]:
        """
        Monitor new campaigns directory for CSVs that need validation.

        Args:
            client_dir: Client directory path

        Returns:
            List of CSV paths that need validation
        """
        new_campaigns_dir = Path(client_dir) / "campaigns" / "new_campaigns"

        if not new_campaigns_dir.exists():
            return []

        csvs_needing_validation = []

        for csv_file in new_campaigns_dir.glob('*.csv'):
            if self.should_trigger_validation(str(csv_file)):
                csvs_needing_validation.append(str(csv_file))

        return csvs_needing_validation

    def get_workflow_status(self, campaign_dir: str) -> Dict[str, Any]:
        """
        Get the current workflow status for a campaign directory.

        Args:
            campaign_dir: Campaign directory path

        Returns:
            Workflow status dictionary
        """
        workflow_files = self.get_campaign_workflow_files(campaign_dir)

        status = {
            'directory': campaign_dir,
            'has_initial_csv': workflow_files['initial_csv'] is not None,
            'has_analysis_report': workflow_files['analysis_report'] is not None,
            'has_final_csv': workflow_files['final_csv'] is not None,
            'workflow_complete': all(workflow_files.values()),
            'next_action': None,
            'files': workflow_files
        }

        # Determine next action
        if not status['has_initial_csv']:
            status['next_action'] = 'Wait for campaign builder to create initial CSV'
        elif not status['has_analysis_report']:
            status['next_action'] = 'Run validation analysis'
        elif not status['has_final_csv']:
            status['next_action'] = 'Wait for campaign builder to create optimized CSV'
        else:
            status['next_action'] = 'Workflow complete - ready for upload'

        return status


# Convenience functions
def mark_csv_final(csv_path: str, reason: str = "Optimization complete") -> bool:
    """Mark a CSV as final to prevent further validation triggers"""
    manager = CSVStageManager()
    return manager.mark_csv_stage(csv_path, 'final', reason)


def should_validate_csv(csv_path: str) -> bool:
    """Check if a CSV should be validated"""
    manager = CSVStageManager()
    return manager.should_trigger_validation(csv_path)


def get_csv_workflow_status(campaign_dir: str) -> Dict[str, Any]:
    """Get workflow status for a campaign directory"""
    manager = CSVStageManager()
    return manager.get_workflow_status(campaign_dir)