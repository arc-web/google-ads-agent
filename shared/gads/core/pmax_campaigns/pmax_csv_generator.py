"""
PMAX Campaign CSV Generator

Generates Google Ads Editor CSV files specifically for Performance Max campaigns.
PMAX campaigns use Asset Groups (not Ad Groups) and have a different column structure.

CSV Structure for PMAX Campaigns:
- Campaign, Campaign Type, Networks, Budget, Labels, Target ROAS, etc.
- Asset Group, Status, Final URL, Path 1, Path 2, Headlines, Descriptions, Images, Labels
- Search Themes (not keywords with match types)

NO Ad Groups in PMAX campaigns - that's Search only.
"""

from typing import Dict, List, Any, Optional
import csv
import io
from datetime import datetime


class PMAXCSVGenerator:
    """
    Generates CSV files specifically for PMAX campaigns.

    Key differences from Search:
    - Uses Asset Groups instead of Ad Groups
    - Different column structure
    - Search themes instead of keywords
    - Responsive search ads instead of text ads
    - Audience signals instead of geographic targeting
    """

    # PMAX campaign CSV columns (different from Search)
    PMAX_CAMPAIGN_COLUMNS = [
        'Campaign', 'Campaign Type', 'Networks', 'Budget', 'Budget type',
        'Status', 'Labels', 'Campaign Bid Strategy Type', 'Target ROAS',
        'Target CPA', 'Maximize Conversion Value', 'Attribution Model',
        'EU political ads', 'Brand guidelines', 'Conversion goals'
    ]

    PMAX_ASSET_GROUP_COLUMNS = [
        'Campaign', 'Asset Group', 'Status', 'Final URL', 'Path 1', 'Path 2',
        'Labels', 'Asset Group Bid Strategy Type', 'Target ROAS', 'Target CPA'
    ]

    PMAX_ASSET_COLUMNS = [
        'Campaign', 'Asset Group', 'Asset', 'Asset Type', 'Status',
        'Text Asset', 'Image', 'Video', 'Labels'
    ]

    PMAX_SEARCH_THEME_COLUMNS = [
        'Campaign', 'Asset Group', 'Search Theme', 'Status', 'Labels'
    ]

    def __init__(self):
        self.rows = []

    def add_pmax_campaign(self, campaign_data: Dict[str, Any]):
        """Add a PMAX campaign row"""
        row = {
            'Campaign': campaign_data['name'],
            'Campaign Type': 'Performance Max',
            'Networks': 'Search,Display,YouTube',
            'Budget': campaign_data.get('budget', '100.00'),
            'Budget type': 'Daily',
            'Status': campaign_data.get('status', 'Enabled'),
            'Labels': campaign_data.get('labels', ''),
            'Campaign Bid Strategy Type': campaign_data.get('bid_strategy', 'Maximize Conversion Value'),
            'Target ROAS': campaign_data.get('target_roas', ''),
            'Target CPA': campaign_data.get('target_cpa', ''),
            'Maximize Conversion Value': campaign_data.get('maximize_conversion_value', ''),
            'Attribution Model': campaign_data.get('attribution_model', 'Data-driven'),
            'EU political ads': "Doesn't have EU political ads",
            'Brand guidelines': 'Disabled',
            'Conversion goals': campaign_data.get('conversion_goals', '')
        }
        self.rows.append(row)

    def add_pmax_asset_group(self, campaign_name: str, asset_group_data: Dict[str, Any]):
        """Add a PMAX Asset Group row"""
        row = {
            'Campaign': campaign_name,
            'Asset Group': asset_group_data['name'],
            'Status': asset_group_data.get('status', 'Enabled'),
            'Final URL': asset_group_data.get('final_url', ''),
            'Path 1': asset_group_data.get('path_1', ''),
            'Path 2': asset_group_data.get('path_2', ''),
            'Labels': asset_group_data.get('labels', ''),
            'Asset Group Bid Strategy Type': asset_group_data.get('bid_strategy', 'Maximize Conversion Value'),
            'Target ROAS': asset_group_data.get('target_roas', ''),
            'Target CPA': asset_group_data.get('target_cpa', '')
        }
        self.rows.append(row)

    def add_pmax_asset(self, campaign_name: str, asset_group_name: str, asset_data: Dict[str, Any]):
        """Add a PMAX asset row"""
        row = {
            'Campaign': campaign_name,
            'Asset Group': asset_group_name,
            'Asset': asset_data.get('name', ''),
            'Asset Type': asset_data['type'],  # TEXT, IMAGE, VIDEO, etc.
            'Status': asset_data.get('status', 'Enabled'),
            'Text Asset': asset_data.get('text', ''),
            'Image': asset_data.get('image_url', ''),
            'Video': asset_data.get('video_url', ''),
            'Labels': asset_data.get('labels', '')
        }
        self.rows.append(row)

    def add_pmax_search_theme(self, campaign_name: str, asset_group_name: str, theme_data: Dict[str, Any]):
        """Add a PMAX search theme row"""
        row = {
            'Campaign': campaign_name,
            'Asset Group': asset_group_name,
            'Search Theme': theme_data['text'],
            'Status': theme_data.get('status', 'Enabled'),
            'Labels': theme_data.get('labels', '')
        }
        self.rows.append(row)

    def generate_csv(self) -> str:
        """Generate the complete CSV content"""
        if not self.rows:
            return ""

        # Create CSV with UTF-8 BOM for Excel compatibility
        output = io.StringIO()
        output.write('\ufeff')  # UTF-8 BOM

        # Get all unique columns from all rows
        all_columns = set()
        for row in self.rows:
            all_columns.update(row.keys())

        # Sort columns for consistency
        fieldnames = sorted(all_columns)

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in self.rows:
            writer.writerow(row)

        return output.getvalue()

    def save_csv(self, filename: str):
        """Save CSV to file"""
        csv_content = self.generate_csv()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)