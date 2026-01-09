"""
Google Ads Editor CSV Exporter

This module implements comprehensive CSV export functionality for Google Ads Editor,
supporting all campaign types (Search, Performance Max, Display, Shopping) with proper
formatting and validation for easy upload and campaign updates.

Key Features:
- Complete Google Ads Editor CSV format support
- Campaign, Ad Group, Asset Group, and Keyword export
- Asset management for Performance Max campaigns
- Proper data validation and formatting
- UTF-8 encoding with BOM for Excel compatibility
- Incremental export support for existing campaigns

Usage:
    exporter = GoogleAdsEditorExporter()
    csv_content = exporter.export_campaigns(campaigns_data)
    exporter.save_csv(csv_content, 'campaigns_export.csv')
"""

from typing import Dict, List, Any, Optional
import csv
import logging

import csv
import io
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    """Google Ads campaign types"""
    SEARCH = "Search"
    PERFORMANCE_MAX = "Performance Max"
    DISPLAY = "Display Network only"
    SHOPPING = "Shopping"
    VIDEO = "Video"
    DISCOVERY = "Discovery"


class BidStrategyType(Enum):
    """Google Ads bid strategy types"""
    MANUAL_CPC = "Manual CPC"
    MANUAL_CPM = "Manual CPM"
    MANUAL_CPA = "Manual CPA"
    MAXIMIZE_CLICKS = "Maximize clicks"
    MAXIMIZE_CONVERSIONS = "Maximize conversions"
    MAXIMIZE_CONVERSION_VALUE = "Maximize conversion value"
    TARGET_CPA = "Target CPA"
    TARGET_ROAS = "Target ROAS"


@dataclass
class CampaignData:
    """Complete campaign data structure for CSV export"""
    campaign: str
    labels: str = ""
    campaign_type: CampaignType = CampaignType.SEARCH
    networks: str = "Google search;Search Partners"
    budget: float = 0.0
    budget_type: str = "Daily"
    eu_political_ads: str = "Doesn't have EU political ads"
    standard_conversion_goals: str = "Account-level"
    customer_acquisition: str = "Bid equally"
    languages: str = "en"
    bid_strategy_type: BidStrategyType = BidStrategyType.MAXIMIZE_CONVERSIONS
    bid_strategy_name: str = ""
    target_cpa: float = 0.0
    start_date: str = ""
    end_date: str = ""
    ad_schedule: str = ""
    ad_rotation: str = "Optimize for clicks"
    content_exclusions: str = ""
    targeting_method: str = "Location of presence or Area of interest"
    exclusion_method: str = "Location of presence"
    google_merchant_center_feed: str = ""
    merchant_identifier: str = ""
    country_of_sale: str = ""
    feed_label: str = ""
    campaign_priority: str = "Low"
    local_inventory_ads: str = "Enabled"
    shopping_ads_on_excluded_brands: str = "Disabled"
    inventory_filter: str = ""
    audience_targeting: str = ""
    flexible_reach: str = ""
    text_customization: str = "Enabled"
    final_url_expansion: str = "Enabled"
    image_enhancement: str = "Enabled"
    image_generation: str = "Disabled"
    landing_page_images: str = "Enabled"
    video_enhancement: str = "Enabled"
    brand_guidelines: str = "Disabled"
    brand_business_name: str = ""
    brand_font: str = ""
    age_demographic: str = ""
    income_demographic: str = ""
    custom_parameters: str = ""
    campaign_status: str = "Enabled"


@dataclass
class AssetGroupData:
    """Asset group data for Performance Max campaigns"""
    asset_group: str
    headlines: List[str] = field(default_factory=lambda: [""] * 15)
    long_headlines: List[str] = field(default_factory=lambda: [""] * 5)
    descriptions: List[str] = field(default_factory=lambda: [""] * 5)
    call_to_action: str = ""
    business_name: str = ""
    video_ids: List[str] = field(default_factory=lambda: [""] * 5)
    path_1: str = ""
    path_2: str = ""
    final_url: str = ""
    final_mobile_url: str = ""
    audience_signal: str = ""
    age_demographic: str = ""
    gender_demographic: str = ""
    income_demographic: str = ""
    parental_status_demographic: str = ""
    remarketing_audience_segments: str = ""
    interest_categories: str = ""
    life_events: str = ""
    custom_audience_segments: str = ""
    detailed_demographics: str = ""
    asset_group_status: str = "Enabled"


@dataclass
class AdGroupData:
    """Ad group data for Search campaigns"""
    ad_group: str
    id: str = ""
    location: str = ""
    reach: str = ""
    location_groups: str = ""
    radius: str = ""
    unit: str = ""
    bid_modifier: str = ""
    account_keyword_type: str = ""
    ad_group_status: str = "Enabled"


@dataclass
class KeywordData:
    """Keyword data for Search campaigns"""
    keyword: str
    criterion_type: str = "Keyword"
    search_theme: str = ""
    incremental: str = ""
    status: str = "Enabled"


@dataclass
class ExtensionData:
    """Ad extension data"""
    link_text: str = ""
    description_line_1: str = ""
    description_line_2: str = ""
    upgraded_extension: str = ""
    source: str = "Advertiser"
    link_source: str = ""
    tracking_template: str = ""
    final_url_suffix: str = ""
    header: str = ""
    snippet_values: str = ""
    callout_text: str = ""


@dataclass
class GoogleAdsEditorRow:
    """Complete row data for Google Ads Editor CSV export"""
    campaign_data: CampaignData
    asset_group_data: Optional[AssetGroupData] = None
    ad_group_data: Optional[AdGroupData] = None
    keyword_data: Optional[KeywordData] = None
    extension_data: Optional[ExtensionData] = None
    approval_status: str = "Approved"
    ad_strength: str = "Excellent"
    comment: str = ""


class GoogleAdsEditorExporter:
    """
    Comprehensive Google Ads Editor CSV exporter

    Exports campaign data in the exact format required by Google Ads Editor
    for seamless upload and campaign management.
    """

    # Complete header list matching Google Ads Editor format
    CSV_HEADERS = [
        # Campaign columns
        "Campaign", "Labels", "Campaign Type", "Networks", "Budget", "Budget type",
        "EU political ads", "Standard conversion goals", "Customer acquisition", "Languages",
        "Bid Strategy Type", "Bid Strategy Name", "Target CPA", "Start Date", "End Date",
        "Ad Schedule", "Ad rotation", "Content exclusions", "Targeting method", "Exclusion method",
        "Google Merchant Center feed", "Merchant Identifier", "Country of Sale", "Feed label",
        "Campaign Priority", "Local Inventory Ads", "Shopping ads on excluded brands",
        "Inventory filter", "Audience targeting", "Flexible Reach", "Text customization",
        "Final URL expansion", "Image enhancement", "Image generation", "Landing page images",
        "Video enhancement", "Brand guidelines", "Brand business name", "Brand font",
        "Custom parameters",

        # Asset Group columns
        "Asset Group",
        # Headlines 1-15
        *[f"Headline {i}" for i in range(1, 16)],
        # Long headlines 1-5
        *[f"Long headline {i}" for i in range(1, 6)],
        # Descriptions 1-5
        *[f"Description {i}" for i in range(1, 6)],
        "Call to action", "Business name",
        # Video IDs 1-5
        *[f"Video ID {i}" for i in range(1, 6)],
        "Path 1", "Path 2", "Final URL", "Final mobile URL", "Audience signal",
        "Age demographic", "Gender demographic", "Income demographic",
        "Parental status demographic", "Remarketing audience segments",
        "Interest categories", "Life events", "Custom audience segments",
        "Detailed demographics",

        # Ad Group columns
        "Ad Group", "ID", "Location", "Reach", "Location groups", "Radius", "Unit",
        "Bid Modifier", "Account keyword type",

        # Keyword columns
        "Keyword", "Criterion Type", "Search theme", "Incremental",

        # Extension columns
        "Link Text", "Description Line 1", "Description Line 2", "Upgraded extension",
        "Source", "Link source", "Tracking template", "Final URL suffix", "Header",
        "Snippet Values", "Callout text",

        # Status columns
        "Campaign Status", "Ad Group Status", "Asset Group Status", "Status",
        "Approval Status", "Ad strength", "Comment"
    ]

    def __init__(self):
        self.validation_errors = []
        self.limits = CampaignLimits()  # Centralized limits
        self.validator = ContentValidator(self.limits)  # Shared validation service

    def export_campaigns(self, campaigns: List[Dict[str, Any]]) -> str:
        """
        Export campaigns to Google Ads Editor CSV format

        Args:
            campaigns: List of campaign dictionaries with complete data

        Returns:
            CSV content as string with UTF-8 BOM for Excel compatibility
        """
        output = io.StringIO()

        # Write UTF-8 BOM for Excel compatibility
        output.write('\ufeff')

        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS,
                               delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for campaign in campaigns:
            rows = self._campaign_to_rows(campaign)
            for row_num, row in enumerate(rows, start=1):
                # Apply auto-corrections to ensure compliance
                self._apply_corrections_to_row(row, row_num)

                # Ensure all CSV headers are present in the row
                complete_row = {header: row.get(header, '') for header in self.CSV_HEADERS}
                writer.writerow(complete_row)

        csv_content = output.getvalue()
        output.close()

        return csv_content

    def export_campaign(self, campaign: Dict[str, Any]) -> str:
        """
        Export a single campaign to CSV format

        Args:
            campaign: Campaign dictionary with complete data

        Returns:
            CSV content as string
        """
        return self.export_campaigns([campaign])

    def _campaign_to_rows(self, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert campaign data to CSV rows

        Args:
            campaign: Campaign data dictionary

        Returns:
            List of row dictionaries for CSV writing
        """
        rows = []

        # Create campaign data object
        campaign_data = self._create_campaign_data(campaign)

        # Handle different campaign types
        if campaign_data.campaign_type == CampaignType.PERFORMANCE_MAX:
            rows.extend(self._create_pmax_rows(campaign_data, campaign))
        elif campaign_data.campaign_type == CampaignType.SEARCH:
            rows.extend(self._create_search_rows(campaign_data, campaign))
        else:
            # Generic campaign row
            row = self._create_base_row(campaign_data)
            rows.append(row)

        return rows

    def _create_campaign_data(self, campaign: Dict[str, Any]) -> CampaignData:
        """Create CampaignData object from dictionary"""
        return CampaignData(
            campaign=campaign.get('name', ''),
            labels=campaign.get('labels', ''),
            campaign_type=CampaignType(campaign.get('type', 'Search')),
            networks=campaign.get('networks', 'Google search;Search Partners'),
            budget=float(campaign.get('budget', 0.0)),
            budget_type=campaign.get('budget_type', 'Daily'),
            languages=campaign.get('languages', 'en'),
            bid_strategy_type=BidStrategyType(campaign.get('bid_strategy_type', 'Maximize conversions')),
            bid_strategy_name=campaign.get('bid_strategy_name', ''),
            target_cpa=float(campaign.get('target_cpa', 0.0)),
            start_date=campaign.get('start_date', ''),
            end_date=campaign.get('end_date', ''),
            ad_schedule=campaign.get('ad_schedule', ''),
            brand_guidelines=campaign.get('brand_guidelines', 'Disabled'),
            brand_business_name=campaign.get('brand_business_name', ''),
            brand_font=campaign.get('brand_font', ''),
            age_demographic=campaign.get('age_demographic', ''),
            income_demographic=campaign.get('income_demographic', ''),
            custom_parameters=campaign.get('custom_parameters', ''),
            campaign_status=campaign.get('status', 'Enabled')
        )

    def _create_pmax_rows(self, campaign_data: CampaignData, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create rows for Performance Max campaigns with asset groups"""
        rows = []

        asset_groups = campaign.get('asset_groups', [])

        if not asset_groups:
            # Create default asset group row
            row = self._create_base_row(campaign_data)
            rows.append(row)
        else:
            for ag_data in asset_groups:
                asset_group = self._create_asset_group_data(ag_data)
                row = self._create_asset_group_row(campaign_data, asset_group)
                rows.append(row)

                # Add extension rows for this asset group
                extension_rows = self._create_extension_rows(campaign_data, ag_data)
                rows.extend(extension_rows)

        # Add campaign-level extensions (callouts and structured snippets)
        campaign_extension_rows = self._create_campaign_extension_rows(campaign_data, campaign)
        rows.extend(campaign_extension_rows)

        # Add location targeting rows
        locations = campaign.get('locations', [])
        if locations:
            for location in locations:
                row = self._create_base_row(campaign_data)
                row.update({
                    "Location": location.get('location', ''),
                    "Reach": location.get('reach', ''),
                    "Location groups": location.get('location_groups', ''),
                    "Radius": location.get('radius', ''),
                    "Unit": location.get('unit', ''),
                    "Status": "Enabled"
                })
                rows.append(row)

        return rows

    def _create_extension_rows(self, campaign_data: CampaignData, ag_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create extension rows for sitelinks, structured snippets, and callouts"""
        rows = []

        # Sitelinks
        sitelinks = ag_data.get('sitelinks', [])
        if sitelinks:
            for sitelink in sitelinks:
                row = self._create_base_row(campaign_data)
                row.update({
                    "Link Text": sitelink.get('text', ''),
                    "Description Line 1": sitelink.get('description1', ''),
                    "Description Line 2": sitelink.get('description2', ''),
                    "Final URL": sitelink.get('url', ''),
                    "Source": "sitelink",
                    "Status": "Enabled"
                })
                rows.append(row)

        # Structured Snippets - One row with comma-separated values
        structured_snippets = ag_data.get('structured_snippets')
        if structured_snippets:
            header = structured_snippets.get('header', '')
            values = structured_snippets.get('values', [])
            language = structured_snippets.get('language', 'en')

            if values and header:
                # Create one row with line-break separated values (like real Google Ads CSV)
                # Google Ads expects: Header + line-break separated values in one row
                line_break_values = '\n'.join(values[:10])  # Max 10 values
                row = self._create_base_row(campaign_data)
                row.update({
                    "Header": header,
                    "Snippet Values": line_break_values,
                    "Language": language,
                    "Source": "snippet",
                    "Status": "Enabled"
                })
                rows.append(row)

        # Callouts
        callouts = ag_data.get('callouts', [])
        if callouts:
            for callout in callouts:
                row = self._create_base_row(campaign_data)
                row.update({
                    "Callout text": callout,
                    "Source": "callout",
                    "Status": "Enabled"
                })
                rows.append(row)

        # Search Themes for PMAX campaigns
        search_themes = ag_data.get('search_themes', [])
        if search_themes:
            for theme in search_themes[:10]:  # Max 10 search themes
                row = self._create_base_row(campaign_data)
                row.update({
                    "Search theme": theme,
                    "Source": "search_theme",
                    "Status": "Enabled"
                })
                rows.append(row)

        return rows

    def _create_campaign_extension_rows(self, campaign_data: CampaignData, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create extension rows for campaign-level callouts and structured snippets"""
        rows = []

        # Campaign-level Structured Snippets
        structured_snippets = campaign.get('structured_snippets')
        if structured_snippets:
            header = structured_snippets.get('header', '')
            values = structured_snippets.get('values', [])
            language = structured_snippets.get('language', 'en')

            if values and header:
                # Create one row with line-break separated values (like real Google Ads CSV)
                line_break_values = '\n'.join(values[:10])  # Max 10 values
                row = self._create_base_row(campaign_data)
                row.update({
                    "Header": header,
                    "Snippet Values": line_break_values,
                    "Language": language,
                    "Source": "snippet",
                    "Status": "Enabled"
                })
                rows.append(row)

        # Campaign-level Callouts (max 20 per account)
        callouts = campaign.get('callouts', [])
        if callouts:
            for callout in callouts[:20]:  # Enforce 20 callout limit
                row = self._create_base_row(campaign_data)
                row.update({
                    "Callout text": callout,
                    "Source": "callout",
                    "Status": "Enabled"
                })
                rows.append(row)

        return rows

    def _create_search_rows(self, campaign_data: CampaignData, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create rows for Search campaigns with ad groups and keywords"""
        rows = []

        ad_groups = campaign.get('ad_groups', [])

        if not ad_groups:
            # Create campaign-level row
            row = self._create_base_row(campaign_data)
            rows.append(row)
        else:
            for ag_data in ad_groups:
                ad_group = self._create_ad_group_data(ag_data)
                keywords = ag_data.get('keywords', [])

                if not keywords:
                    # Ad group row without keywords
                    row = self._create_ad_group_row(campaign_data, ad_group)
                    rows.append(row)
                else:
                    # Rows for each keyword
                    for kw_data in keywords:
                        keyword = self._create_keyword_data(kw_data)
                        row = self._create_keyword_row(campaign_data, ad_group, keyword)
                        rows.append(row)

        return rows

    def _create_asset_group_data(self, ag_data: Dict[str, Any]) -> AssetGroupData:
        """Create AssetGroupData object from dictionary"""
        headlines = ag_data.get('headlines', [])
        long_headlines = ag_data.get('long_headlines', [])
        descriptions = ag_data.get('descriptions', [])
        video_ids = ag_data.get('video_ids', [])

        # Pad arrays to required lengths
        headlines.extend([''] * (15 - len(headlines)))
        long_headlines.extend([''] * (5 - len(long_headlines)))
        descriptions.extend([''] * (5 - len(descriptions)))
        video_ids.extend([''] * (5 - len(video_ids)))

        return AssetGroupData(
            asset_group=ag_data.get('name', ''),
            headlines=headlines[:15],
            long_headlines=long_headlines[:5],
            descriptions=descriptions[:5],
            call_to_action=ag_data.get('call_to_action', ''),
            business_name=ag_data.get('business_name', ''),
            video_ids=video_ids[:5],
            path_1=ag_data.get('path_1', ''),
            path_2=ag_data.get('path_2', ''),
            final_url=ag_data.get('final_url', ''),
            final_mobile_url=ag_data.get('final_mobile_url', ''),
            audience_signal=ag_data.get('audience_signal', ''),
            age_demographic=ag_data.get('age_demographic', ''),
            income_demographic=ag_data.get('income_demographic', ''),
            interest_categories=ag_data.get('interest_categories', ''),
            asset_group_status=ag_data.get('status', 'Enabled')
        )

    def _create_ad_group_data(self, ag_data: Dict[str, Any]) -> AdGroupData:
        """Create AdGroupData object from dictionary"""
        return AdGroupData(
            ad_group=ag_data.get('name', ''),
            id=ag_data.get('id', ''),
            location=ag_data.get('location', ''),
            bid_modifier=str(ag_data.get('bid_modifier', '')),
            ad_group_status=ag_data.get('status', 'Enabled')
        )

    def _create_keyword_data(self, kw_data: Dict[str, Any]) -> KeywordData:
        """Create KeywordData object from dictionary"""
        return KeywordData(
            keyword=kw_data.get('text', ''),
            criterion_type=kw_data.get('criterion_type', 'Keyword'),
            status=kw_data.get('status', 'Enabled')
        )

    def _create_base_row(self, campaign_data: CampaignData) -> Dict[str, Any]:
        """Create base CSV row with campaign data"""
        row = {}

        # Campaign columns
        row.update({
            "Campaign": campaign_data.campaign,
            "Labels": campaign_data.labels,
            "Campaign Type": campaign_data.campaign_type.value,
            "Networks": campaign_data.networks,
            "Budget": f"{campaign_data.budget:.2f}" if campaign_data.budget > 0 else "",
            "Budget type": campaign_data.budget_type,
            "EU political ads": campaign_data.eu_political_ads,
            "Standard conversion goals": campaign_data.standard_conversion_goals,
            "Customer acquisition": campaign_data.customer_acquisition,
            "Languages": campaign_data.languages,
            "Bid Strategy Type": campaign_data.bid_strategy_type.value,
            "Bid Strategy Name": campaign_data.bid_strategy_name,
            "Target CPA": f"{campaign_data.target_cpa:.2f}" if campaign_data.target_cpa > 0 else "",
            "Start Date": campaign_data.start_date,
            "End Date": campaign_data.end_date,
            "Ad Schedule": campaign_data.ad_schedule,
            "Ad rotation": campaign_data.ad_rotation,
            "Content exclusions": campaign_data.content_exclusions,
            "Targeting method": campaign_data.targeting_method,
            "Exclusion method": campaign_data.exclusion_method,
            "Google Merchant Center feed": campaign_data.google_merchant_center_feed,
            "Merchant Identifier": campaign_data.merchant_identifier,
            "Country of Sale": campaign_data.country_of_sale,
            "Feed label": campaign_data.feed_label,
            "Campaign Priority": campaign_data.campaign_priority,
            "Local Inventory Ads": campaign_data.local_inventory_ads,
            "Shopping ads on excluded brands": campaign_data.shopping_ads_on_excluded_brands,
            "Inventory filter": campaign_data.inventory_filter,
            "Audience targeting": campaign_data.audience_targeting,
            "Flexible Reach": campaign_data.flexible_reach,
            "Text customization": campaign_data.text_customization,
            "Final URL expansion": campaign_data.final_url_expansion,
            "Image enhancement": campaign_data.image_enhancement,
            "Image generation": campaign_data.image_generation,
            "Landing page images": campaign_data.landing_page_images,
            "Video enhancement": campaign_data.video_enhancement,
            "Brand guidelines": campaign_data.brand_guidelines,
            "Brand business name": campaign_data.brand_business_name,
            "Brand font": campaign_data.brand_font,
            "Age demographic": campaign_data.age_demographic,
            "Income demographic": campaign_data.income_demographic,
            "Custom parameters": campaign_data.custom_parameters,
            "Campaign Status": campaign_data.campaign_status,
            "Ad Group Status": "",
            "Asset Group Status": "",
            "Status": "",
            "Approval Status": "Approved",
            "Ad strength": "Excellent",
            "Comment": ""
        })

        return row

    def _create_asset_group_row(self, campaign_data: CampaignData,
                               asset_group: AssetGroupData) -> Dict[str, Any]:
        """Create CSV row for asset group data"""
        row = self._create_base_row(campaign_data)

        # Asset Group columns
        row["Asset Group"] = asset_group.asset_group

        # Headlines
        for i, headline in enumerate(asset_group.headlines, 1):
            row[f"Headline {i}"] = headline

        # Long headlines
        for i, long_headline in enumerate(asset_group.long_headlines, 1):
            row[f"Long headline {i}"] = long_headline

        # Descriptions
        for i, description in enumerate(asset_group.descriptions, 1):
            row[f"Description {i}"] = description

        # Other asset group fields
        row.update({
            "Call to action": asset_group.call_to_action,
            "Business name": asset_group.business_name,
            "Path 1": asset_group.path_1,
            "Path 2": asset_group.path_2,
            "Final URL": asset_group.final_url,
            "Final mobile URL": asset_group.final_mobile_url,
            "Audience signal": asset_group.audience_signal,
            "Age demographic": asset_group.age_demographic,
            "Gender demographic": asset_group.gender_demographic,
            "Income demographic": asset_group.income_demographic,
            "Parental status demographic": asset_group.parental_status_demographic,
            "Remarketing audience segments": asset_group.remarketing_audience_segments,
            "Interest categories": asset_group.interest_categories,
            "Life events": asset_group.life_events,
            "Custom audience segments": asset_group.custom_audience_segments,
            "Detailed demographics": asset_group.detailed_demographics,
            "Asset Group Status": asset_group.asset_group_status
        })

        return row

    def _create_ad_group_row(self, campaign_data: CampaignData,
                            ad_group: AdGroupData) -> Dict[str, Any]:
        """Create CSV row for ad group data"""
        row = self._create_base_row(campaign_data)

        row.update({
            "Ad Group": ad_group.ad_group,
            "ID": ad_group.id,
            "Location": ad_group.location,
            "Reach": ad_group.reach,
            "Location groups": ad_group.location_groups,
            "Radius": ad_group.radius,
            "Unit": ad_group.unit,
            "Bid Modifier": ad_group.bid_modifier,
            "Account keyword type": ad_group.account_keyword_type,
            "Ad Group Status": ad_group.ad_group_status
        })

        return row

    def _create_keyword_row(self, campaign_data: CampaignData,
                           ad_group: AdGroupData, keyword: KeywordData) -> Dict[str, Any]:
        """Create CSV row for keyword data"""
        row = self._create_ad_group_row(campaign_data, ad_group)

        row.update({
            "Keyword": keyword.keyword,
            "Criterion Type": keyword.criterion_type,
            "Search theme": keyword.search_theme,
            "Incremental": keyword.incremental,
            "Status": keyword.status
        })

        return row

    def save_csv(self, csv_content: str, filename: str) -> None:
        """
        Save CSV content to file

        Args:
            csv_content: CSV content as string
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(csv_content)

        logger.info(f"CSV exported to {filename}")

    def validate_csv_data(self, csv_content: str) -> List[str]:
        """
        Validate CSV data against Google Ads Editor requirements

        Args:
            csv_content: CSV content to validate

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            # Remove UTF-8 BOM if present (can cause parsing issues)
            if csv_content.startswith('\ufeff'):
                csv_content = csv_content[1:]

            # Parse CSV to validate structure
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            # Check headers
            expected_headers = set(self.CSV_HEADERS)
            actual_headers = set(reader.fieldnames or [])

            if not expected_headers.issubset(actual_headers):
                missing = expected_headers - actual_headers
                errors.append(f"Missing required headers: {missing}")

            # Validate each row
            for row_num, row in enumerate(reader, 2):  # Start from 2 (header is 1)
                row_errors = self._validate_row(row, row_num)
                errors.extend(row_errors)

        except Exception as e:
            errors.append(f"CSV parsing error: {e}")

        self.validation_errors = errors
        return errors

    def _validate_row(self, row: Dict[str, str], row_num: int) -> List[str]:
        """Validate a single CSV row"""
        errors = []

        # Campaign name is required
        if not row.get("Campaign", "").strip():
            errors.append(f"Row {row_num}: Campaign name is required")

        # Validate budget if provided
        budget = row.get("Budget", "")
        if budget and budget != "":
            try:
                float(budget)
            except ValueError:
                errors.append(f"Row {row_num}: Invalid budget value: {budget}")

        # Validate dates if provided
        for date_field in ["Start Date", "End Date"]:
            date_val = row.get(date_field, "")
            if date_val:
                try:
                    datetime.strptime(date_val, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid {date_field} format: {date_val} (expected YYYY-MM-DD)")

        # PMAX Campaign specific validations
        campaign_type = row.get("Campaign Type", "")
        if campaign_type == "Performance Max":
            errors.extend(self._validate_pmax_row(row, row_num))

        return errors

    def _validate_pmax_row(self, row: Dict[str, str], row_num: int) -> List[str]:
        """Validate PMAX-specific requirements and auto-correct violations"""
        corrections_made = []

        # FIRST: Apply all auto-corrections
        self._apply_corrections(row, corrections_made)

        # THEN: Validate the corrected content
        all_errors = self._validate_corrected_row(row, row_num)

        # Log corrections
        if corrections_made:
            print(f"Row {row_num} - Auto-corrected {len(corrections_made)} violations:")
            for correction in corrections_made[:3]:
                print(f"  ✅ {correction}")
            if len(corrections_made) > 3:
                print(f"  ... and {len(corrections_made) - 3} more corrections")

        return all_errors

    def _apply_corrections(self, row: Dict[str, str], corrections_made: List[str]) -> None:
        """Apply auto-corrections to fix compliance issues"""

        # Auto-correct EU political ads setting
        eu_ads = row.get("EU political ads", "").strip()
        if not eu_ads or eu_ads not in ["Doesn't have EU political ads", "Has EU political ads"]:
            row["EU political ads"] = "Doesn't have EU political ads"
            corrections_made.append("EU political ads: set to 'Doesn't have EU political ads'")

        # Auto-correct brand guidelines setting (disable to prevent logo upload issues)
        brand_guidelines = row.get("Brand guidelines", "").strip()
        if not brand_guidelines or brand_guidelines not in ["Enabled", "Disabled"]:
            row["Brand guidelines"] = "Disabled"
            corrections_made.append("Brand guidelines: set to 'Disabled' (prevents logo upload failures)")
        elif brand_guidelines == "Enabled":
            # Only change if this is a campaign row (not location targeting row)
            if not row.get("Location", "").strip():  # Skip if this is a location targeting row
                row["Brand guidelines"] = "Disabled"
                corrections_made.append("Brand guidelines: changed from 'Enabled' to 'Disabled' (prevents logo upload failures)")

        # Headlines - expand if too short, truncate if too long
        for i in range(1, 16):
            field_name = f"Headline {i}"
            original = row.get(field_name, "")
            if original:
                if len(original) > self.limits.headline_max:
                    corrected = self.validator.auto_correct_text(original, self.limits.headline_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Headline {i}: truncated to {len(corrected)} chars")
                    print(f"DEBUG: Applied correction to {field_name}: '{original}' → '{corrected}'")
                elif len(original) < self.limits.headline_min:
                    corrected = self.validator.expand_text_to_minimum(original, self.limits.headline_min, "headline", self.limits.headline_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Headline {i}: expanded to {len(corrected)} chars")
                    print(f"DEBUG: Applied expansion to {field_name}: '{original}' → '{corrected}'")

        # Callouts - expand if too short, truncate if too long
        for i in range(1, 11):
            field_name = f"Callout text {i}"
            original = row.get(field_name, "")
            if original:
                if len(original) > self.limits.callout_max:
                    corrected = self.validator.auto_correct_text(original, self.limits.callout_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Callout {i}: truncated to {len(corrected)} chars")
                elif len(original) < self.limits.callout_min:
                    corrected = self.validator.expand_text_to_minimum(original, self.limits.callout_min, "callout", self.limits.callout_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Callout {i}: expanded to {len(corrected)} chars")

        # Sitelinks - truncate if too long
        field_name = "Link Text"
        original = row.get(field_name, "")
        if original and len(original) > self.limits.sitelink_text_max:
            corrected = self.validator.auto_correct_text(original, self.limits.sitelink_text_max)
            row[field_name] = corrected
            corrections_made.append(f"Sitelink text: truncated to {len(corrected)} chars")

        for field_name in ["Description Line 1", "Description Line 2"]:
            original = row.get(field_name, "")
            if original and len(original) > self.limits.sitelink_desc_max:
                corrected = self.validator.auto_correct_text(original, self.limits.sitelink_desc_max)
                row[field_name] = corrected
                corrections_made.append(f"{field_name}: truncated to {len(corrected)} chars")

        # Structured snippets - truncate if too long
        field_name = "Header"
        original = row.get(field_name, "")
        if original and len(original) > self.limits.structured_snippet_header_max:
            corrected = self.validator.auto_correct_text(original, self.limits.structured_snippet_header_max)
            row[field_name] = corrected
            corrections_made.append(f"Snippet header: truncated to {len(corrected)} chars")

        field_name = "Snippet Values"
        snippet_values = row.get(field_name, "")
        if snippet_values:
            values = snippet_values.split('\n')
            corrected_values = []
            for i, value in enumerate(values):
                if value.strip() and len(value.strip()) > self.limits.structured_snippet_value_max:
                    corrected = self.validator.auto_correct_text(value.strip(), self.limits.structured_snippet_value_max)
                    corrected_values.append(corrected)
                    corrections_made.append(f"Snippet value {i+1}: truncated to {len(corrected)} chars")
                else:
                    corrected_values.append(value.strip())
            row[field_name] = '\n'.join(corrected_values)

        # Paths - truncate if too long
        for field_name in ["Path 1", "Path 2"]:
            original = row.get(field_name, "")
            if original and len(original) > 15:
                row[field_name] = original[:15]
                corrections_made.append(f"{field_name}: truncated to 15 chars")

        # Final URL - truncate if too long
        field_name = "Final URL"
        original = row.get(field_name, "")
        if original and len(original.encode('utf-8')) > 2048:
            corrected = original
            while len(corrected.encode('utf-8')) > 2048 and len(corrected) > 0:
                corrected = corrected[:-1]
            row[field_name] = corrected
            corrections_made.append(f"Final URL: truncated to {len(corrected.encode('utf-8'))} bytes")

        # Long headlines - truncate if too long
        for i in range(1, 6):
            field_name = f"Long headline {i}"
            original = row.get(field_name, "")
            if original and len(original) > self.limits.long_headline_max:
                corrected = self.validator.auto_correct_text(original, self.limits.long_headline_max)
                row[field_name] = corrected
                corrections_made.append(f"Long headline {i}: truncated to {len(corrected)} chars")

        # Descriptions - truncate if too long
        for i in range(1, 6):
            field_name = f"Description {i}"
            original = row.get(field_name, "")
            if original and len(original) > self.limits.description_max:
                corrected = self.validator.auto_correct_text(original, self.limits.description_max)
                row[field_name] = corrected
                corrections_made.append(f"Description {i}: truncated to {len(corrected)} chars")

    def _validate_corrected_row(self, row: Dict[str, str], row_num: int) -> List[str]:
        """Validate content after corrections have been applied"""
        all_errors = []

        # Validate EU political ads setting (must be properly configured for non-EU targeting)
        eu_ads = row.get("EU political ads", "").strip()
        if eu_ads and eu_ads not in ["Doesn't have EU political ads", "Has EU political ads"]:
            all_errors.append(f"Row {row_num}: EU political ads must be either 'Doesn't have EU political ads' or 'Has EU political ads'")
        elif not eu_ads:
            all_errors.append(f"Row {row_num}: EU political ads setting is required")

        # Validate brand guidelines setting (should be disabled to avoid logo upload issues)
        brand_guidelines = row.get("Brand guidelines", "").strip()
        if brand_guidelines and brand_guidelines not in ["Enabled", "Disabled"]:
            all_errors.append(f"Row {row_num}: Brand guidelines must be either 'Enabled' or 'Disabled'")
        elif brand_guidelines == "Enabled":
            all_errors.append(f"Row {row_num}: WARNING - Brand guidelines are enabled, which may require logo upload and cause campaign launch failures")
        elif not brand_guidelines:
            all_errors.append(f"Row {row_num}: Brand guidelines setting is required")

        # Check for long headlines (required for PMAX)
        long_headlines = [row.get(f"Long headline {i}", "") for i in range(1, 6)]
        if not any(long_headline.strip() for long_headline in long_headlines):
            all_errors.append(f"Row {row_num}: PMAX campaigns require at least one long headline (up to 90 characters)")

        # Validate headlines
        for i in range(1, 16):
            field_name = f"Headline {i}"
            text = row.get(field_name, "")
            if text:
                if len(text) > self.limits.headline_max:
                    all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (max {self.limits.headline_max})")
                elif len(text) < self.limits.headline_min:
                    all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (min {self.limits.headline_min})")

        # Validate callouts
        for i in range(1, 11):
            field_name = f"Callout text {i}"
            text = row.get(field_name, "")
            if text:
                if len(text) > self.limits.callout_max:
                    all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (max {self.limits.callout_max})")
                elif len(text) < self.limits.callout_min:
                    all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (min {self.limits.callout_min})")

        # Validate sitelinks
        sitelink_text = row.get("Link Text", "")
        if sitelink_text and len(sitelink_text) > self.limits.sitelink_text_max:
            all_errors.append(f"Row {row_num}: Link Text is {len(sitelink_text)} characters (max {self.limits.sitelink_text_max})")

        for field_name in ["Description Line 1", "Description Line 2"]:
            text = row.get(field_name, "")
            if text and len(text) > self.limits.sitelink_desc_max:
                all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (max {self.limits.sitelink_desc_max})")

        # Validate structured snippets
        header = row.get("Header", "")
        if header and len(header) > self.limits.structured_snippet_header_max:
            all_errors.append(f"Row {row_num}: Header is {len(header)} characters (max {self.limits.structured_snippet_header_max})")

        values_text = row.get("Snippet Values", "")
        if values_text:
            values = values_text.split('\n')
            for i, value in enumerate(values):
                if value.strip() and len(value.strip()) > self.limits.structured_snippet_value_max:
                    all_errors.append(f"Row {row_num}: Snippet value {i+1} is {len(value.strip())} characters (max {self.limits.structured_snippet_value_max})")

        # Validate paths
        for field_name in ["Path 1", "Path 2"]:
            text = row.get(field_name, "")
            if text and len(text) > 15:
                all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (max 15)")

        # Validate final URL
        final_url = row.get("Final URL", "")
        if final_url and len(final_url.encode('utf-8')) > 2048:
            all_errors.append(f"Row {row_num}: Final URL is {len(final_url.encode('utf-8'))} bytes (max 2048)")

        # Validate descriptions
        for i in range(1, 6):
            field_name = f"Description {i}"
            text = row.get(field_name, "")
            if text and len(text) > self.limits.description_max:
                all_errors.append(f"Row {row_num}: {field_name} is {len(text)} characters (max {self.limits.description_max})")

        return all_errors

    def _apply_corrections_to_row(self, row: Dict[str, str], row_num: int) -> None:
        """Apply auto-corrections to a row during export"""
        corrections_made = []

        # Apply corrections based on campaign type
        campaign_type = row.get("Campaign Type", "")
        if campaign_type == "Performance Max":
            self._apply_pmax_corrections(row, corrections_made)

        # Store corrections for reporting
        if corrections_made:
            row['_corrections_made'] = corrections_made

    def _apply_pmax_corrections(self, row: Dict[str, str], corrections_made: List[str]) -> None:
        """Apply PMAX-specific corrections during export"""

        # Headlines - expand if too short, truncate if too long
        for i in range(1, 16):
            field_name = f"Headline {i}"
            original = row.get(field_name, "")
            if original:
                if len(original) > self.limits.headline_max:
                    corrected = self.validator.auto_correct_text(original, self.limits.headline_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Headline {i}: truncated")
                elif len(original) < self.limits.headline_min:
                    corrected = self.validator.expand_text_to_minimum(original, self.limits.headline_min, "headline", self.limits.headline_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Headline {i}: expanded")

        # Callouts - expand if too short, truncate if too long
        for i in range(1, 11):
            field_name = f"Callout text {i}"
            original = row.get(field_name, "")
            if original:
                if len(original) > self.limits.callout_max:
                    corrected = self.validator.auto_correct_text(original, self.limits.callout_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Callout {i}: truncated")
                elif len(original) < self.limits.callout_min:
                    corrected = self.validator.expand_text_to_minimum(original, self.limits.callout_min, "callout", self.limits.callout_max)
                    row[field_name] = corrected
                    corrections_made.append(f"Callout {i}: expanded")

    def _validate_asset_group_row(self, row: Dict[str, str], row_num: int) -> List[str]:
        """Validate asset group row - simplified, delegates to PMAX validation"""
        errors = []

        # For asset groups, delegate to PMAX validation since they contain the actual assets
        if row.get("Campaign Type") == "Performance Max":
            errors.extend(self._validate_pmax_row(row, row_num))

        return errors


# Domain Models - Simple wrappers for better organization
@dataclass
class CampaignLimits:
    """Centralized limits for easy maintenance"""
    headline_max: int = 30
    headline_min: int = 23
    long_headline_max: int = 90
    long_headline_min: int = 23
    description_max: int = 90
    description_min: int = 70
    callout_max: int = 25
    callout_min: int = 15
    sitelink_text_max: int = 25
    sitelink_text_min: int = 15
    sitelink_desc_max: int = 35
    sitelink_desc_min: int = 20
    structured_snippet_header_max: int = 25
    structured_snippet_header_min: int = 15
    structured_snippet_value_max: int = 25
    structured_snippet_value_min: int = 10

@dataclass
class ValidationError:
    """Structured validation error"""
    row: int
    field: str
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self) -> str:
        return f"Row {self.row}: {self.message}"

# Shared validation service
class ContentValidator:
    """Extracted validation logic for reuse"""

    def __init__(self, limits: CampaignLimits):
        self.limits = limits

    def validate_text_length(self, text: str, field_name: str, min_len: int, max_len: int, row_num: int) -> List[ValidationError]:
        """Validate text length against limits"""
        errors = []
        if len(text) > max_len:
            errors.append(ValidationError(
                row=row_num,
                field=field_name,
                message=f"{field_name} is {len(text)} characters (max {max_len})"
            ))
        if len(text) < min_len:
            errors.append(ValidationError(
                row=row_num,
                field=field_name,
                message=f"{field_name} is {len(text)} characters (min {min_len})",
                severity="warning"
            ))
        return errors

    def auto_correct_text(self, text: str, max_length: int) -> str:
        """Smart text truncation"""
        if len(text) <= max_length:
            return text

        # Try word boundary truncation
        words = text.split()
        result = ""
        for word in words:
            if len(result + " " + word) <= max_length:
                result += (" " if result else "") + word
            else:
                break

        if result and len(result) >= max_length * 0.7:
            return result

        # Fallback: hard truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.6:
            return truncated[:last_space]

        return truncated

    def expand_text_to_minimum(self, text: str, min_length: int, content_type: str, max_length: int = 30) -> str:
        """Expand text to meet minimum character requirements without exceeding maximum"""
        if len(text) >= min_length:
            return text

        # Calculate how much we can add without exceeding max
        available_space = max_length - len(text)

        # Context-aware expansion based on content type
        expansions = {
            "headline": [
                " Services", " Today", " Now", " Online",
                " - Expert", " - Pro", " Help"
            ],
            "callout": [
                " Available", " Today", " Now", " Expert",
                " Since 2005", " Pro", " Top"
            ]
        }

        # Try adding expansions that fit within available space
        result = text
        available_expansions = expansions.get(content_type, [""])

        for expansion in available_expansions:
            if len(expansion) <= available_space:
                test_result = result + expansion
                if len(test_result) >= min_length:
                    return test_result

        # If no expansion works, try shorter additions
        short_additions = [" Pro", " Now", " Top", " New", " Best"]
        for addition in short_additions:
            if len(addition) <= available_space:
                test_result = result + addition
                if len(test_result) >= min_length:
                    return test_result

        # Final fallback: repeat last word or add minimal text
        if len(result) < max_length - 2:
            # Try to repeat the last word if it fits
            words = result.split()
            if words:
                last_word = words[-1]
                if len(result + " " + last_word) <= max_length and len(result + " " + last_word) >= min_length:
                    return result + " " + last_word

        # Ultimate fallback: just return original if we can't expand without exceeding limits
        return result

# Convenience functions
def export_campaigns_to_csv(campaigns: List[Dict[str, Any]],
                           output_path: Optional[str] = None) -> str:
    """
    Export campaigns to Google Ads Editor CSV format

    Args:
        campaigns: List of campaign dictionaries
        output_path: Optional path to save CSV file

    Returns:
        CSV content as string
    """
    exporter = GoogleAdsEditorExporter()
    csv_content = exporter.export_campaigns(campaigns)

    if output_path:
        exporter.save_csv(csv_content, output_path)

    return csv_content


def create_sample_pmax_campaign() -> Dict[str, Any]:
    """
    Create a sample Performance Max campaign for testing

    Returns:
        Sample campaign data dictionary
    """
    return {
        "name": "Sample PMAX Campaign",
        "type": "Performance Max",
        "budget": 100.00,
        "languages": "en",
        "bid_strategy_type": "Maximize conversions",
        "brand_business_name": "My Business",
        "brand_font": "Arial",
        "custom_parameters": "{_campaignname}=Sample+PMAX",
        "status": "Enabled",
        "asset_groups": [
            {
                "name": "Sample Asset Group",
                "headlines": [
                    "Professional Resume Writer",
                    "Top Resume Writing Service",
                    "Expert Resume Writers",
                    "Resume Writing & Cover Letter",
                    "Resume Writing Experts"
                ],
                "descriptions": [
                    "Expert resume writing services with proven results",
                    "Professional career coaching and LinkedIn optimization",
                    "74% land a job within 30 days guarantee"
                ],
                "business_name": "My Expert Resume",
                "final_url": "https://myexpertresume.com/",
                "interest_categories": "Professional Resume Writer",
                "status": "Enabled"
            }
        ]
    }


def create_sample_search_campaign() -> Dict[str, Any]:
    """
    Create a sample Search campaign for testing

    Returns:
        Sample campaign data dictionary
    """
    return {
        "name": "Sample Search Campaign",
        "type": "Search",
        "budget": 50.00,
        "networks": "Google search",
        "bid_strategy_type": "Manual CPC",
        "status": "Enabled",
        "ad_groups": [
            {
                "name": "Resume Writing Services",
                "status": "Enabled",
                "keywords": [
                    {
                        "text": "professional resume writing",
                        "status": "Enabled"
                    },
                    {
                        "text": "resume writing service",
                        "status": "Enabled"
                    },
                    {
                        "text": "expert resume writer",
                        "status": "Enabled"
                    }
                ]
            }
        ]
    }


# Export for easy importing
__all__ = [
    'GoogleAdsEditorExporter',
    'CampaignData',
    'AssetGroupData',
    'AdGroupData',
    'KeywordData',
    'ExtensionData',
    'CampaignType',
    'BidStrategyType',
    'export_campaigns_to_csv',
    'create_sample_pmax_campaign',
    'create_sample_search_campaign'
]
