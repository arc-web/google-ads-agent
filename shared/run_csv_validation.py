#!/usr/bin/env python3
"""
Google Ads CSV Validation Runner

Comprehensive validation of Google Ads CSVs across all client directories.
Validates hierarchically: Account → Campaign → Asset Group → Asset → Targeting.

NEW WORKFLOW: Integrates with campaign builder workflow
- Monitors new_campaigns directory for initial CSVs
- Only validates CSVs marked as 'initial' stage
- Saves analysis reports in same directory as CSVs
- Creates feedback for campaign builder
- Prevents infinite loops by marking CSVs as 'analyzed'

Usage:
    python run_csv_validation.py --client <client_name>
    python run_csv_validation.py --all
    python run_csv_validation.py --client <client_name> --fix
    python run_csv_validation.py --client <client_name> --output report.json

    # NEW: Monitor new campaigns directory
    python run_csv_validation.py --monitor-new <client_name>
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append('validators')
sys.path.append('gads/core/business_logic')

from validators import MasterValidator
from validators.csv_stage_manager import CSVStageManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Google Ads CSV Validation Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single client
  python run_csv_validation.py --client wrights_impact_window_and_door

  # Validate all clients
  python run_csv_validation.py --all

  # Validate with auto-fixing
  python run_csv_validation.py --client collab_med_spa --fix

  # Validate and save detailed report
  python run_csv_validation.py --client evolution_restoration_and_renovation --output validation_report.json

  # Validate all clients and save reports
  python run_csv_validation.py --all --output-dir reports/

  # NEW WORKFLOW: Monitor new campaigns directory
  python run_csv_validation.py --monitor-new wrights_impact_window_and_door

  # Validate specific CSV (respects stage checking)
  python run_csv_validation.py --csv google_ads_agent/wrights_impact_window_and_door/campaigns/new_campaigns/campaign.csv

  # Check workflow status for a client
  python run_csv_validation.py --workflow-status wrights_impact_window_and_door

  # Mark a CSV as final (prevents further validation)
  python run_csv_validation.py --mark-final path/to/campaign_final.csv
        """
    )

    parser.add_argument('--client', help='Client directory name to validate')
    parser.add_argument('--all', action='store_true', help='Validate all client directories')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues where possible')
    parser.add_argument('--output', help='Output file for single client report (JSON)')
    parser.add_argument('--output-dir', help='Output directory for multiple reports')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # NEW: Campaign builder workflow options
    parser.add_argument('--monitor-new', help='Monitor new_campaigns directory and validate initial CSVs')
    parser.add_argument('--csv', help='Validate specific CSV file (respects stage checking)')
    parser.add_argument('--mark-final', help='Mark a CSV as final (prevents further validation)')
    parser.add_argument('--workflow-status', help='Show workflow status for a client directory')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize validators
    validator = MasterValidator()
    stage_manager = CSVStageManager()

    try:
        # NEW: Handle workflow status check
        if args.workflow_status:
            client_dir = f"google_ads_agent/{args.workflow_status}"
            status = stage_manager.get_workflow_status(client_dir)
            print(f"\n📊 WORKFLOW STATUS: {args.workflow_status}")
            print("=" * 60)
            print(f"Directory: {status['directory']}")
            print(f"Initial CSV: {'✅' if status['has_initial_csv'] else '❌'} {status['files']['initial_csv'] or 'Not found'}")
            print(f"Analysis Report: {'✅' if status['has_analysis_report'] else '❌'} {status['files']['analysis_report'] or 'Not found'}")
            print(f"Final CSV: {'✅' if status['has_final_csv'] else '❌'} {status['files']['final_csv'] or 'Not found'}")
            print(f"Workflow Complete: {'✅' if status['workflow_complete'] else '❌'}")
            print(f"Next Action: {status['next_action']}")
            return 0

        # NEW: Handle mark final
        if args.mark_final:
            success = stage_manager.mark_csv_stage(args.mark_final, 'final', 'Manual override')
            if success:
                logger.info(f"✅ Marked CSV as final: {args.mark_final}")
                return 0
            else:
                logger.error(f"❌ Failed to mark CSV as final: {args.mark_final}")
                return 1

        # NEW: Handle specific CSV validation
        if args.csv:
            csv_path = args.csv
            if not stage_manager.should_trigger_validation(csv_path):
                stage = stage_manager.get_csv_stage(csv_path)
                logger.info(f"⏭️  Skipping validation - CSV stage: {stage} (path: {csv_path})")
                return 0

            logger.info(f"🔍 Validating CSV: {csv_path}")
            results = validator.validate_csv_file(csv_path, auto_fix=args.fix)

            if not results['success']:
                logger.error(f"❌ Validation failed: {results['error']}")
                return 1

            # Mark as analyzed
            stage_manager.mark_csv_stage(csv_path, 'analyzed', 'Validation completed')

            # Save report in same directory as CSV
            csv_dir = Path(csv_path).parent
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_name = Path(csv_path).stem
            report_file = csv_dir / f"{csv_name}_analysis_{timestamp}.json"

            validator.save_report(results, str(report_file))
            logger.info(f"📁 Analysis report saved: {report_file}")

            # Create feedback for campaign builder
            feedback = stage_manager.create_analysis_feedback(csv_path, results)
            feedback_file = stage_manager.save_feedback_to_campaign_builder(feedback, str(csv_dir))
            if feedback_file:
                logger.info(f"📁 Feedback for campaign builder: {feedback_file}")

            # Print summary
            validator.print_summary_report(results)

            # Return appropriate exit code
            status = results.get('final_status', 'UNKNOWN')
            return 0 if status in ['PASS', 'PASS_WITH_FIXES'] else 1

        # NEW: Handle monitoring new campaigns directory
        if args.monitor_new:
            client_dir = f"google_ads_agent/{args.monitor_new}"
            csvs_to_validate = stage_manager.monitor_new_campaigns_directory(client_dir)

            if not csvs_to_validate:
                logger.info(f"ℹ️  No initial CSVs found in new_campaigns directory for: {args.monitor_new}")
                return 0

            logger.info(f"🔍 Found {len(csvs_to_validate)} CSV(s) needing validation in new_campaigns")

            all_passed = True
            for csv_path in csvs_to_validate:
                logger.info(f"🔍 Processing: {Path(csv_path).name}")

                # Validate CSV
                results = validator.validate_csv_file(csv_path, auto_fix=args.fix)

                if not results['success']:
                    logger.error(f"❌ Validation failed for {csv_path}: {results['error']}")
                    all_passed = False
                    continue

                # Mark as analyzed
                stage_manager.mark_csv_stage(csv_path, 'analyzed', 'Automated validation')

                # Save report in same directory
                csv_dir = Path(csv_path).parent
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_name = Path(csv_path).stem
                report_file = csv_dir / f"{csv_name}_analysis_{timestamp}.json"

                validator.save_report(results, str(report_file))
                logger.info(f"📁 Analysis saved: {report_file}")

                # Create feedback for campaign builder
                feedback = stage_manager.create_analysis_feedback(csv_path, results)
                feedback_file = stage_manager.save_feedback_to_campaign_builder(feedback, str(csv_dir))
                if feedback_file:
                    logger.info(f"📁 Feedback created: {feedback_file}")

                # Print brief summary for this CSV
                status = results.get('final_status', 'UNKNOWN')
                issue_count = len(results.get('issues', []))
                logger.info(f"   Status: {status} | Issues: {issue_count}")

                if status not in ['PASS', 'PASS_WITH_FIXES']:
                    all_passed = False

            return 0 if all_passed else 1

        if args.all:
            # Validate all clients
            logger.info("🔍 Starting validation of all client directories...")
            results = validator.validate_all_clients(auto_fix=args.fix)

            if not results['success']:
                logger.error(f"❌ Validation failed: {results['error']}")
                return 1

            # Print global summary
            validator.print_summary_report(results)

            # Save individual client reports if requested
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                global_report_file = output_dir / f"global_validation_report_{timestamp}.json"

                # Save global report
                validator.save_report(results, str(global_report_file))
                logger.info(f"📁 Global report saved to: {global_report_file}")

                # Save individual client reports
                for client_result in results['client_results']:
                    if client_result['success']:
                        client_name = Path(client_result['client_directory']).name
                        client_report_file = output_dir / f"{client_name}_validation_report_{timestamp}.json"
                        validator.save_report(client_result, str(client_report_file))
                        logger.info(f"📁 Client report saved to: {client_report_file}")

            # Return appropriate exit code
            global_status = results['global_summary']['overall_status']
            return 0 if global_status == 'PASS' else 1

        elif args.client:
            # Validate single client
            logger.info(f"🔍 Starting validation of client: {args.client}")
            results = validator.validate_client_directory(args.client, auto_fix=args.fix)

            if not results['success']:
                logger.error(f"❌ Validation failed: {results['error']}")
                return 1

            # Print client summary
            validator.print_summary_report(results)

            # Save report if requested
            if args.output:
                validator.save_report(results, args.output)
                logger.info(f"📁 Report saved to: {args.output}")

            # Return appropriate exit code
            client_status = results['client_summary']['overall_status']
            return 0 if client_status == 'PASS' else 1

        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)