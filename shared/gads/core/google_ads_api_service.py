"""
Google Ads API Service - Systematic Implementation
Core service for Google Ads API operations with MCP integration
"""

from typing import Dict, List, Any, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import logging
import json
import os

logger = logging.getLogger(__name__)


class GoogleAdsAPIService:
    """
    Systematic Google Ads API service with MCP integration.

    Provides step-by-step Google Ads account management:
    1. Account validation and access
    2. Campaign budget setup
    3. Campaign creation
    4. Asset group configuration
    5. Ad creation and optimization
    """

    def __init__(self, config_path: str):
        self.client = GoogleAdsClient.load_from_storage(config_path)
        self.customer_id = None
        self.use_parent_mcp = False
        self.parent_mcp_config = None
        self._load_mcp_config()

    def _load_mcp_config(self):
        """Load MCP configuration to determine if parent directory MCP should be used"""
        try:
            # Look for gads_client_config.json in the same directory
            config_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to gads/core/
            config_file = os.path.join(config_dir, 'gads_client_config.json')

            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)

                google_ads_config = config.get('platforms', {}).get('google_ads', {})
                mcp_server_config = google_ads_config.get('mcp_server', {})

                if mcp_server_config.get('use_parent_directory', False):
                    self.use_parent_mcp = True
                    self.parent_mcp_config = mcp_server_config
                    logger.info("Configured to use parent directory MCP server")
                else:
                    logger.info("Using local MCP implementation")
            else:
                logger.warning("gads_client_config.json not found, using local MCP implementation")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            self.use_parent_mcp = False

    async def _call_parent_mcp(self, method_name: str, **kwargs) -> Any:
        """Call parent directory MCP server for Google Ads operations"""
        if not self.use_parent_mcp:
            raise ValueError("Parent MCP not configured")

        try:
            # Import here to avoid circular imports
            import sys
            import os

            # Add parent directory to path temporarily
            parent_dir = "/Users/home/aimacpro/4_agents/platform_agents"
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            # Import the MCP registry from parent directory
            from admin.shared.mcp_registry import get_mcp_registry

            registry = get_mcp_registry()
            server_name = self.parent_mcp_config.get('server_name', 'google-ads')

            # Call the tool
            result = await registry.execute_tool(server_name, method_name, kwargs)
            return result

        except Exception as e:
            logger.error(f"Failed to call parent MCP: {e}")
            raise

    async def validate_account_access_via_mcp(self, customer_id: str) -> Dict[str, Any]:
        """Validate account access using parent MCP server"""
        return await self._call_parent_mcp("google_ads_validate_account_access",
                                         customer_id=customer_id)

    async def create_campaign_budget_via_mcp(self, customer_id: str, budget_name: str,
                                           amount_micros: int, period: str) -> Dict[str, Any]:
        """Create campaign budget using parent MCP server"""
        return await self._call_parent_mcp("google_ads_create_campaign_budget",
                                         customer_id=customer_id,
                                         budget_name=budget_name,
                                         amount_micros=amount_micros,
                                         period=period)

    # ============================================================================
    # PHASE 1: ACCOUNT VALIDATION & ACCESS
    # ============================================================================

    def validate_account_access(self, customer_id: str) -> Dict[str, Any]:
        """
        Step 1.1: Validate Google Ads account access and permissions
        Required before any other operations
        """
        try:
            # Test basic account access
            ga_service = self.client.get_service("GoogleAdsService")
            query = f"SELECT customer.id, customer.descriptive_name FROM customer WHERE customer.id = '{customer_id}'"

            response = ga_service.search(customer_id=customer_id, query=query)
            account_info = None

            for row in response:
                account_info = {
                    'customer_id': row.customer.id,
                    'account_name': row.customer.descriptive_name,
                    'access_granted': True
                }
                break

            if not account_info:
                raise ValueError(f"No access to customer ID: {customer_id}")

            self.customer_id = customer_id
            logger.info(f"✓ Account access validated: {account_info['account_name']}")
            return account_info

        except GoogleAdsException as e:
            logger.error(f"✗ Account access failed: {e}")
            raise

    def check_account_structure(self, customer_id: str) -> Dict[str, Any]:
        """
        Step 1.2: Check existing account structure
        Required to understand current setup before modifications
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Check existing campaigns
        campaign_query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.status != 'REMOVED'
        """

        campaigns = []
        for row in ga_service.search(customer_id=customer_id, query=campaign_query):
            campaigns.append({
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status,
                'budget': row.campaign_budget.amount_micros / 1000000 if hasattr(row, 'campaign_budget') else 0
            })

        return {
            'campaigns': campaigns,
            'total_campaigns': len(campaigns),
            'account_ready': len(campaigns) >= 0  # Basic validation
        }

    # ============================================================================
    # PHASE 2: BUDGET MANAGEMENT
    # ============================================================================

    def create_campaign_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2.1: Create campaign budget
        Must be done before campaign creation
        """
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        # Create budget operation
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create

        budget.name = budget_data['name']
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.amount_micros = int(budget_data['amount_micros'])
        budget.explicitly_shared = True  # Context7: Budgets should be explicitly shared

        # Set budget period
        if budget_data['period'] == 'daily':
            budget.period = self.client.enums.BudgetPeriodEnum.DAILY
        elif budget_data['period'] == 'monthly':
            budget.period = self.client.enums.BudgetPeriodEnum.MONTHLY

        try:
            response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[budget_operation]
            )

            budget_id = response.results[0].resource_name.split('/')[-1]
            logger.info(f"✓ Campaign budget created: {budget_id}")

            return {
                'budget_id': budget_id,
                'resource_name': response.results[0].resource_name,
                'status': 'created'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Budget creation failed: {e}")
            raise

    # ============================================================================
    # PHASE 3: CAMPAIGN CREATION
    # ============================================================================

    def create_campaign(self, campaign_data: Dict[str, Any], budget_id: str) -> Dict[str, Any]:
        """
        Step 3.1: Create campaign
        Requires budget_id from previous step
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        # Basic campaign settings
        campaign.name = campaign_data['name']
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED  # Start paused for safety

        # Campaign type specific settings
        if campaign_data['type'] == 'SEARCH':
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH
            campaign.advertising_channel_sub_type = self.client.enums.AdvertisingChannelSubTypeEnum.SEARCH_MOBILE_APP
        elif campaign_data['type'] == 'PERFORMANCE_MAX':
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        elif campaign_data['type'] == 'DISPLAY':
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.DISPLAY

        # Link to budget
        campaign.campaign_budget = f"customers/{self.customer_id}/campaignBudgets/{budget_id}"

        # Bid strategy
        if 'target_cpa' in campaign_data:
            campaign.manual_cpc.enhanced_cpc_enabled = False
            campaign.target_cpa.target_cpa_micros = int(campaign_data['target_cpa'] * 1000000)

        # Geographic targeting
        if 'locations' in campaign_data:
            for location_id in campaign_data['locations']:
                location = self.client.get_type("CampaignCriterion")
                location.location.geo_target_constant = f"geoTargetConstants/{location_id}"
                campaign.criteria.append(location)

        try:
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )

            campaign_id = response.results[0].resource_name.split('/')[-1]
            logger.info(f"✓ Campaign created: {campaign_id}")

            return {
                'campaign_id': campaign_id,
                'resource_name': response.results[0].resource_name,
                'status': 'created'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Campaign creation failed: {e}")
            raise

    # ============================================================================
    # PHASE 4: ASSET GROUP MANAGEMENT (PERFORMANCE MAX)
    # ============================================================================

    def create_asset_group(self, campaign_id: str, asset_group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4.1: Create asset group for Performance Max campaigns
        Requires campaign_id from previous step
        """
        asset_group_service = self.client.get_service("AssetGroupService")

        operation = self.client.get_type("AssetGroupOperation")
        asset_group = operation.create

        asset_group.name = asset_group_data['name']
        asset_group.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        asset_group.status = self.client.enums.AssetGroupStatusEnum.ENABLED

        # Add headlines
        for headline in asset_group_data.get('headlines', []):
            text_asset = self.client.get_type("TextAsset")
            text_asset.text = headline
            asset_group.text_assets.append(text_asset)

        # Add descriptions
        for description in asset_group_data.get('descriptions', []):
            text_asset = self.client.get_type("TextAsset")
            text_asset.text = description
            asset_group.text_assets.append(text_asset)

        try:
            response = asset_group_service.mutate_asset_groups(
                customer_id=self.customer_id,
                operations=[operation]
            )

            asset_group_id = response.results[0].resource_name.split('/')[-1]
            logger.info(f"✓ Asset group created: {asset_group_id}")

            return {
                'asset_group_id': asset_group_id,
                'resource_name': response.results[0].resource_name,
                'status': 'created'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Asset group creation failed: {e}")
            raise

    def link_asset_group_to_campaign(self, campaign_id: str, asset_group_id: str) -> bool:
        """
        Step 4.2: Link asset group to campaign
        Required for Performance Max campaigns
        """
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = operation.create

        campaign_asset.asset = f"customers/{self.customer_id}/assetGroups/{asset_group_id}/assets/HEADLINE"
        campaign_asset.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        campaign_asset.status = self.client.enums.CampaignAssetStatusEnum.ENABLED

        try:
            response = campaign_asset_service.mutate_campaign_assets(
                customer_id=self.customer_id,
                operations=[operation]
            )
            logger.info(f"✓ Asset group linked to campaign")
            return True

        except GoogleAdsException as e:
            logger.error(f"✗ Asset group linking failed: {e}")
            raise

    # ============================================================================
    # PHASE 5: AD CREATION AND MANAGEMENT
    # ============================================================================

    def create_ad_group(self, campaign_id: str, ad_group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5.1: Create ad group (for Search campaigns)
        Requires campaign_id from campaign creation
        """
        ad_group_service = self.client.get_service("AdGroupService")

        operation = self.client.get_type("AdGroupOperation")
        ad_group = operation.create

        ad_group.name = ad_group_data['name']
        ad_group.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
        ad_group.type = self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD

        # CPC bid
        if 'cpc_bid' in ad_group_data:
            ad_group.cpc_bid_micros = int(ad_group_data['cpc_bid'] * 1000000)

        try:
            response = ad_group_service.mutate_ad_groups(
                customer_id=self.customer_id,
                operations=[operation]
            )

            ad_group_id = response.results[0].resource_name.split('/')[-1]
            logger.info(f"✓ Ad group created: {ad_group_id}")

            return {
                'ad_group_id': ad_group_id,
                'resource_name': response.results[0].resource_name,
                'status': 'created'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Ad group creation failed: {e}")
            raise

    def create_keywords(self, ad_group_id: str, keywords: List[str]) -> Dict[str, Any]:
        """
        Step 5.2: Add keywords to ad group
        Requires ad_group_id from ad group creation
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")

        operations = []
        for keyword_text in keywords:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.create

            criterion.ad_group = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
            criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED

            # Keyword setup
            criterion.keyword.text = keyword_text
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum.EXACT

            # CPC bid
            criterion.cpc_bid_micros = 2000000  # $2.00 default

            operations.append(operation)

        try:
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=operations
            )

            created_keywords = len(response.results)
            logger.info(f"✓ Keywords created: {created_keywords}")

            return {
                'keywords_created': created_keywords,
                'status': 'completed'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Keyword creation failed: {e}")
            raise

    def create_responsive_search_ad(self, ad_group_id: str, ad_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5.3: Create Responsive Search Ad
        Requires ad_group_id from ad group creation
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")

        operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create

        ad_group_ad.ad_group = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED

        # Responsive Search Ad setup
        rsa = ad_group_ad.ad.responsive_search_ad

        # Headlines
        for headline in ad_data.get('headlines', []):
            text_asset = self.client.get_type("AdTextAsset")
            text_asset.text = headline
            rsa.headlines.append(text_asset)

        # Descriptions
        for description in ad_data.get('descriptions', []):
            text_asset = self.client.get_type("AdTextAsset")
            text_asset.text = description
            rsa.descriptions.append(text_asset)

        # Path settings
        if 'path1' in ad_data:
            rsa.path1 = ad_data['path1']
        if 'path2' in ad_data:
            rsa.path2 = ad_data['path2']

        try:
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=self.customer_id,
                operations=[operation]
            )

            ad_id = response.results[0].resource_name.split('/')[-1]
            logger.info(f"✓ Responsive Search Ad created: {ad_id}")

            return {
                'ad_id': ad_id,
                'resource_name': response.results[0].resource_name,
                'status': 'created'
            }

        except GoogleAdsException as e:
            logger.error(f"✗ Ad creation failed: {e}")
            raise

    # ============================================================================
    # SYSTEMATIC EXECUTION WORKFLOW
    # ============================================================================

    def execute_systematic_campaign_creation(self, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete systematic campaign creation workflow
        Follows the step-by-step process for reliable campaign setup
        """
        results = {
            'steps_completed': [],
            'resources_created': {},
            'errors': [],
            'status': 'in_progress'
        }

        try:
            # Step 1: Account validation
            customer_id = campaign_config['customer_id']
            account_check = self.validate_account_access(customer_id)
            results['steps_completed'].append('account_validation')
            results['resources_created']['account'] = account_check

            # Step 2: Budget creation
            budget_data = campaign_config['budget']
            budget_result = self.create_campaign_budget(budget_data)
            results['steps_completed'].append('budget_creation')
            results['resources_created']['budget'] = budget_result

            # Step 3: Campaign creation
            campaign_data = campaign_config['campaign']
            campaign_result = self.create_campaign(campaign_data, budget_result['budget_id'])
            results['steps_completed'].append('campaign_creation')
            results['resources_created']['campaign'] = campaign_result

            # Step 4: Asset groups (Performance Max) or Ad groups (Search)
            if campaign_data['type'] == 'PERFORMANCE_MAX':
                for asset_group_data in campaign_config.get('asset_groups', []):
                    ag_result = self.create_asset_group(campaign_result['campaign_id'], asset_group_data)
                    self.link_asset_group_to_campaign(campaign_result['campaign_id'], ag_result['asset_group_id'])
                    results['steps_completed'].append('asset_group_creation')
                    results['resources_created'].setdefault('asset_groups', []).append(ag_result)

            elif campaign_data['type'] == 'SEARCH':
                ad_group_data = campaign_config['ad_group']
                ad_group_result = self.create_ad_group(campaign_result['campaign_id'], ad_group_data)
                results['steps_completed'].append('ad_group_creation')
                results['resources_created']['ad_group'] = ad_group_result

                # Keywords
                keywords_result = self.create_keywords(ad_group_result['ad_group_id'], campaign_config['keywords'])
                results['steps_completed'].append('keyword_creation')
                results['resources_created']['keywords'] = keywords_result

                # Ads
                ad_result = self.create_responsive_search_ad(ad_group_result['ad_group_id'], campaign_config['ad'])
                results['steps_completed'].append('ad_creation')
                results['resources_created']['ad'] = ad_result

            results['status'] = 'completed'
            logger.info(f"✓ Systematic campaign creation completed: {campaign_result['campaign_id']}")

        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
            logger.error(f"✗ Campaign creation failed: {e}")

        return results
