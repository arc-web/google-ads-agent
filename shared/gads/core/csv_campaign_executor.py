"""
CSV Campaign Executor

Reads Google Ads Editor CSV files and executes them via Google Ads API.
CSV becomes the canonical source of truth for campaign specifications.
"""

import csv
import io
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from .google_ads_api_service import GoogleAdsAPIService

logger = logging.getLogger(__name__)


class CSVParseError(Exception):
    """CSV parsing or validation error"""
    pass


class CSVCampaignExecutor:
    """
    Executes Google Ads campaigns from CSV specifications.

    Strategy: CSV is canonical source of truth, API executes it.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.api_service = GoogleAdsAPIService(config_path)

    def execute_csv_campaign(self, csv_path: str, customer_id: str) -> Dict[str, Any]:
        """
        Execute a complete campaign from CSV file.

        Args:
            csv_path: Path to Google Ads Editor CSV file
            customer_id: Google Ads customer ID

        Returns:
            Execution results with created resources and errors
        """
        # Parse CSV into structured data
        campaign_specs = self._parse_csv_file(csv_path)

        # Validate campaign structure
        validation_errors = self._validate_campaign_specs(campaign_specs)
        if validation_errors:
            raise CSVParseError(f"CSV validation failed: {validation_errors}")

        # Execute campaign creation
        return self._execute_campaign_specs(campaign_specs, customer_id)

    def _parse_csv_file(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parse Google Ads Editor CSV into structured campaign specifications.

        CRITICAL ISSUE: CSV parsing is error-prone and complex due to:
        - 100+ columns with complex relationships
        - Multiple row types (campaign, asset group, ad group, keywords, ads)
        - Hierarchical dependencies between rows
        - String formatting requirements for schedules, targeting, etc.
        """
        campaign_specs = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                # Handle BOM and detect delimiter
                sample = f.read(1024)
                f.seek(0)
                delimiter = '\t' if '\t' in sample else ','

                reader = csv.DictReader(f, delimiter=delimiter)

                current_campaign = None
                current_asset_group = None
                current_ad_group = None

                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header offset
                    try:
                        row_type = self._classify_row_type(row)

                        if row_type == 'campaign':
                            # New campaign specification
                            campaign_spec = self._parse_campaign_row(row)
                            campaign_specs.append(campaign_spec)
                            current_campaign = campaign_spec
                            current_asset_group = None
                            current_ad_group = None

                        elif row_type == 'asset_group' and current_campaign:
                            # Asset group for Performance Max
                            asset_group_spec = self._parse_asset_group_row(row)
                            current_campaign.setdefault('asset_groups', []).append(asset_group_spec)
                            current_asset_group = asset_group_spec

                        elif row_type == 'ad_group' and current_campaign:
                            # Ad group for Search campaigns
                            ad_group_spec = self._parse_ad_group_row(row)
                            current_campaign.setdefault('ad_groups', []).append(ad_group_spec)
                            current_ad_group = ad_group_spec

                        elif row_type == 'keyword' and current_ad_group:
                            # Keyword for ad group
                            keyword_spec = self._parse_keyword_row(row)
                            current_ad_group.setdefault('keywords', []).append(keyword_spec)

                        elif row_type == 'ad' and current_ad_group:
                            # Ad for ad group
                            ad_spec = self._parse_ad_row(row)
                            current_ad_group.setdefault('ads', []).append(ad_spec)

                    except Exception as e:
                        logger.warning(f"Failed to parse row {row_num}: {e}")
                        continue

        except FileNotFoundError:
            raise CSVParseError(f"CSV file not found: {csv_path}")
        except Exception as e:
            raise CSVParseError(f"CSV parsing failed: {e}")

        return campaign_specs

    def _classify_row_type(self, row: Dict[str, str]) -> str:
        """
        Classify CSV row type based on filled columns.

        CRITICAL ISSUE: Brittle classification logic
        - Depends on specific column patterns
        - Breaks if CSV format changes
        - No validation of required vs optional fields
        """
        # Campaign row: Has Campaign column filled
        if row.get('Campaign', '').strip():
            return 'campaign'

        # Asset Group row: Has Asset Group column filled (Performance Max)
        if row.get('Asset Group', '').strip():
            return 'asset_group'

        # Ad Group row: Has Ad Group column filled (Search)
        if row.get('Ad Group', '').strip():
            return 'ad_group'

        # Keyword row: Has Keyword column filled
        if row.get('Keyword', '').strip():
            return 'keyword'

        # Ad row: Has Headline 1 or Description 1 filled
        if (row.get('Headline 1', '').strip() or
            row.get('Description 1', '').strip()):
            return 'ad'

        return 'unknown'

    def _parse_campaign_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse campaign row into structured data"""
        # CRITICAL ISSUE: Complex string parsing for structured data
        # Ad schedules, targeting, etc. are encoded as strings
        return {
            'name': row.get('Campaign', ''),
            'type': row.get('Campaign Type', 'Search'),
            'budget': float(row.get('Budget', 0) or 0),
            'budget_type': row.get('Budget type', 'Daily'),
            'bid_strategy_type': row.get('Bid Strategy Type', ''),
            'target_cpa': float(row.get('Target CPA', 0) or 0),
            'languages': row.get('Languages', 'en'),
            'ad_schedule': row.get('Ad Schedule', ''),
            'networks': row.get('Networks', ''),
            # ... many more fields
        }

    def _parse_asset_group_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse asset group row"""
        headlines = []
        descriptions = []

        # Extract headlines (1-15)
        for i in range(1, 16):
            headline = row.get(f'Headline {i}', '').strip()
            if headline:
                headlines.append(headline)

        # Extract descriptions (1-5)
        for i in range(1, 6):
            desc = row.get(f'Description {i}', '').strip()
            if desc:
                descriptions.append(desc)

        return {
            'name': row.get('Asset Group', ''),
            'headlines': headlines,
            'descriptions': descriptions,
            'final_url': row.get('Final URL', ''),
            'path1': row.get('Path 1', ''),
            'path2': row.get('Path 2', ''),
        }

    def _validate_campaign_specs(self, campaign_specs: List[Dict[str, Any]]) -> List[str]:
        """
        Validate campaign specifications.

        CRITICAL ISSUE: Validation happens too late
        - Errors discovered only at execution time
        - No early feedback during CSV creation
        - Hard to debug CSV formatting issues
        """
        errors = []

        for i, campaign in enumerate(campaign_specs):
            # Required fields
            if not campaign.get('name'):
                errors.append(f"Campaign {i+1}: Missing campaign name")

            if campaign.get('budget', 0) <= 0:
                errors.append(f"Campaign {i+1}: Invalid budget amount")

            # Campaign type validation
            campaign_type = campaign.get('type', '').upper()
            if campaign_type not in ['SEARCH', 'PERFORMANCE_MAX', 'DISPLAY', 'SHOPPING']:
                errors.append(f"Campaign {i+1}: Invalid campaign type '{campaign_type}'")

            # Type-specific validation
            if campaign_type == 'PERFORMANCE_MAX':
                if not campaign.get('asset_groups'):
                    errors.append(f"Campaign {i+1}: Performance Max requires asset groups")

            elif campaign_type == 'SEARCH':
                if not campaign.get('ad_groups'):
                    errors.append(f"Campaign {i+1}: Search campaigns require ad groups")

        return errors

    def _execute_campaign_specs(self, campaign_specs: List[Dict[str, Any]],
                               customer_id: str) -> Dict[str, Any]:
        """
        Execute campaign creation from specifications.

        CRITICAL ISSUE: Complex execution dependencies
        - Budget must be created before campaign
        - Campaign must exist before asset groups/ad groups
        - Asset groups must exist before ads
        - Failures in middle break entire process
        """
        results = {
            'campaigns_created': [],
            'errors': [],
            'warnings': []
        }

        # Set customer ID for API service
        self.api_service.customer_id = customer_id

        for campaign_spec in campaign_specs:
            try:
                # Execute single campaign
                campaign_result = self._execute_single_campaign(campaign_spec)
                results['campaigns_created'].append(campaign_result)

            except Exception as e:
                results['errors'].append({
                    'campaign': campaign_spec.get('name'),
                    'error': str(e)
                })
                logger.error(f"Failed to create campaign '{campaign_spec.get('name')}': {e}")

        return results

    def _execute_single_campaign(self, campaign_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute single campaign with all its components.

        CRITICAL ISSUE: Transactional integrity
        - Partial failures leave orphaned resources
        - No rollback mechanism for failed campaigns
        - Resource cleanup required on failures
        """
        campaign_result = {
            'name': campaign_spec['name'],
            'status': 'in_progress',
            'resources_created': {},
            'errors': []
        }

        try:
            # Step 1: Create budget (if not exists)
            budget_result = self.api_service.create_campaign_budget({
                'name': f"Budget - {campaign_spec['name']}",
                'amount_micros': int(campaign_spec['budget'] * 1000000),
                'period': campaign_spec['budget_type'].lower()
            })
            campaign_result['resources_created']['budget'] = budget_result

            # Step 2: Create campaign
            campaign_result_api = self.api_service.create_campaign(
                campaign_spec, budget_result['budget_id']
            )
            campaign_result['resources_created']['campaign'] = campaign_result_api

            # Step 3: Create asset groups or ad groups based on campaign type
            if campaign_spec.get('type') == 'PERFORMANCE_MAX':
                for asset_group_spec in campaign_spec.get('asset_groups', []):
                    ag_result = self.api_service.create_asset_group(
                        campaign_result_api['campaign_id'], asset_group_spec
                    )
                    # Link to campaign
                    self.api_service.link_asset_group_to_campaign(
                        campaign_result_api['campaign_id'], ag_result['asset_group_id']
                    )

            elif campaign_spec.get('type') == 'SEARCH':
                for ad_group_spec in campaign_spec.get('ad_groups', []):
                    ag_result = self.api_service.create_ad_group(
                        campaign_result_api['campaign_id'], ad_group_spec
                    )

                    # Create keywords and ads for this ad group
                    for keyword_spec in ad_group_spec.get('keywords', []):
                        self.api_service.create_keywords(
                            ag_result['ad_group_id'], [keyword_spec['text']]
                        )

                    for ad_spec in ad_group_spec.get('ads', []):
                        self.api_service.create_responsive_search_ad(
                            ag_result['ad_group_id'], ad_spec
                        )

            campaign_result['status'] = 'completed'

        except Exception as e:
            campaign_result['status'] = 'failed'
            campaign_result['errors'].append(str(e))
            # CRITICAL ISSUE: No cleanup of partially created resources

        return campaign_result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_csv_format(csv_path: str) -> Tuple[bool, List[str]]:
    """
    Validate CSV format before execution.

    CRITICAL ISSUE: Validation is separate from execution
    - Should be integrated into CSV creation process
    - Early validation prevents execution failures
    """
    errors = []
    warnings = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(1024)
            delimiter = '\t' if '\t' in sample else ','
            f.seek(0)

            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []

            # Check required headers
            required_headers = ['Campaign', 'Campaign Type', 'Budget']
            for header in required_headers:
                if header not in headers:
                    errors.append(f"Missing required header: {header}")

            # Validate data rows
            for row_num, row in enumerate(reader, start=2):
                # Campaign row validation
                if row.get('Campaign', '').strip():
                    if not row.get('Budget'):
                        errors.append(f"Row {row_num}: Campaign missing budget")

                    campaign_type = row.get('Campaign Type', '').upper()
                    if campaign_type not in ['SEARCH', 'PERFORMANCE_MAX', 'DISPLAY', 'SHOPPING']:
                        errors.append(f"Row {row_num}: Invalid campaign type '{campaign_type}'")

    except Exception as e:
        errors.append(f"CSV validation failed: {e}")

    return len(errors) == 0, errors


def diff_csv_campaigns(csv_path1: str, csv_path2: str) -> Dict[str, Any]:
    """
    Compare two CSV campaign files for differences.

    CRITICAL ISSUE: CSV comparison is complex
    - Row ordering matters
    - Hierarchical relationships hard to compare
    - Text differences don't reflect functional differences
    """
    # Implementation would be complex and error-prone
    return {"error": "CSV diffing not implemented - too complex and error-prone"}
