#!/usr/bin/env python3
"""
Targeting-level CSV Validator

Validates geographic and audience targeting settings.
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import io
import re

logger = logging.getLogger(__name__)


class TargetingValidator:
    """Validates geographic and audience targeting"""

    def __init__(self):
        # Location validation patterns
        self.zip_pattern = r'^\d{5}(-\d{4})?$'
        self.city_state_pattern = r'^[A-Za-z\s]+,\s*[A-Z]{2}$'
        self.coordinates_pattern = r'^-?\d+\.\d+,-?\d+\.\d+$'

        # Valid currencies
        self.valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF']

        # Valid countries (ISO 2-letter codes)
        self.valid_countries = [
            'US', 'CA', 'GB', 'AU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE',
            'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL'
        ]

        # Timezone pattern
        self.timezone_pattern = r'^[A-Za-z/_()+\-\s]+$'

        # Radius validation
        self.min_radius = 1
        self.max_radius = 500  # miles
        self.valid_units = ['miles', 'kilometers', 'km']

    def validate_targeting(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate all targeting settings"""
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            for row_num, row in enumerate(reader, 2):
                # Validate geographic targeting
                geo_issues = self._validate_geographic_targeting(row, row_num)
                issues.extend(geo_issues)

                # Validate audience targeting
                audience_issues = self._validate_audience_targeting(row, row_num)
                issues.extend(audience_issues)

                # Validate language settings
                language_issues = self._validate_language_targeting(row, row_num)
                issues.extend(language_issues)

                # Validate radius and location settings
                radius_issues = self._validate_radius_settings(row, row_num)
                issues.extend(radius_issues)

        except Exception as e:
            issues.append({
                'level': 'targeting',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate targeting: {e}',
                'auto_fixable': False
            })

        return issues

    def _validate_geographic_targeting(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate geographic location targeting"""
        issues = []

        location = row.get("Location", "").strip()
        if location:
            # Try different location formats
            is_valid = False

            # Check ZIP code format
            if re.match(self.zip_pattern, location):
                is_valid = True
            # Check City, State format
            elif re.match(self.city_state_pattern, location):
                is_valid = True
                # Additional validation for state codes
                state = location.split(',')[1].strip()
                if state not in self._get_us_state_codes():
                    issues.append({
                        'level': 'targeting',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Location',
                        'issue_type': 'invalid_state_code',
                        'message': f'Potentially invalid state code: {state} in location "{location}"',
                        'auto_fixable': False
                    })
            # Check coordinates format
            elif re.match(self.coordinates_pattern, location):
                is_valid = True
            # Check if it's a valid country or region name
            elif location in self._get_common_location_names():
                is_valid = True

            if not is_valid:
                issues.append({
                    'level': 'targeting',
                    'severity': 'warning',
                    'row_number': row_num,
                    'column': 'Location',
                    'issue_type': 'invalid_location_format',
                    'message': f'Location format may be invalid: "{location}"',
                    'suggestion': 'Use formats like: "City, ST", "12345", or "latitude,longitude"',
                    'auto_fixable': False
                })

        return issues

    def _validate_audience_targeting(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate audience targeting settings"""
        issues = []

        # Check for audience signals
        audience_signal = row.get("Audience signal", "").strip()
        if audience_signal:
            # Validate audience signal format (should be descriptive)
            if len(audience_signal) < 3:
                issues.append({
                    'level': 'targeting',
                    'severity': 'warning',
                    'row_number': row_num,
                    'column': 'Audience signal',
                    'issue_type': 'audience_signal_too_short',
                    'message': f'Audience signal too short: "{audience_signal}"',
                    'suggestion': 'Use more descriptive audience targeting',
                    'auto_fixable': False
                })

        # Check demographic targeting
        demographics = [
            ('Age demographic', row.get('Age demographic', '').strip()),
            ('Gender demographic', row.get('Gender demographic', '').strip()),
            ('Income demographic', row.get('Income demographic', '').strip()),
            ('Parental status demographic', row.get('Parental status demographic', '').strip())
        ]

        for demo_name, demo_value in demographics:
            if demo_value:
                # Basic validation - demographic values should be reasonable
                if len(demo_value) < 2:
                    issues.append({
                        'level': 'targeting',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': demo_name,
                        'issue_type': 'demographic_value_short',
                        'message': f'{demo_name} value seems too short: "{demo_value}"',
                        'auto_fixable': False
                    })

        # Check interest categories
        interests = row.get("Interest categories", "").strip()
        if interests:
            # Interest categories should be comma-separated
            interest_list = [i.strip() for i in interests.split(',')]
            if len(interest_list) > 10:
                issues.append({
                    'level': 'targeting',
                    'severity': 'warning',
                    'row_number': row_num,
                    'column': 'Interest categories',
                    'issue_type': 'too_many_interests',
                    'message': f'Too many interest categories ({len(interest_list)}) - may limit reach',
                    'suggestion': 'Consider using fewer, more targeted interests',
                    'auto_fixable': False
                })

        return issues

    def _validate_language_targeting(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate language targeting"""
        issues = []

        languages = row.get("Languages", "").strip()
        if languages:
            # Languages should be comma-separated language codes
            lang_list = [lang.strip() for lang in languages.split(',')]

            for lang in lang_list:
                if lang and lang not in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh-CN', 'zh-TW', 'nl', 'sv', 'no', 'da', 'fi']:
                    issues.append({
                        'level': 'targeting',
                        'severity': 'info',
                        'row_number': row_num,
                        'column': 'Languages',
                        'issue_type': 'non_standard_language',
                        'message': f'Non-standard language code: "{lang}"',
                        'suggestion': 'Use standard ISO language codes',
                        'auto_fixable': False
                    })

        return issues

    def _validate_radius_settings(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate radius and location group settings"""
        issues = []

        # Check radius
        radius_str = row.get("Radius", "").strip()
        if radius_str:
            try:
                radius = float(radius_str)
                if radius < self.min_radius:
                    issues.append({
                        'level': 'targeting',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Radius',
                        'issue_type': 'radius_too_small',
                        'message': f'Radius too small: {radius} (min: {self.min_radius})',
                        'auto_fixable': False
                    })
                elif radius > self.max_radius:
                    issues.append({
                        'level': 'targeting',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Radius',
                        'issue_type': 'radius_too_large',
                        'message': f'Radius very large: {radius} (max recommended: {self.max_radius})',
                        'suggestion': 'Large radius may reduce targeting precision',
                        'auto_fixable': False
                    })
            except ValueError:
                issues.append({
                    'level': 'targeting',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Radius',
                    'issue_type': 'invalid_radius_format',
                    'message': f'Invalid radius format: "{radius_str}"',
                    'auto_fixable': False
                })

        # Check unit
        unit = row.get("Unit", "").strip()
        if unit and unit not in self.valid_units:
            issues.append({
                'level': 'targeting',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Unit',
                'issue_type': 'invalid_unit',
                'message': f'Invalid radius unit: "{unit}". Valid units: {self.valid_units}',
                'auto_fixable': True,
                'original_value': unit,
                'fixed_value': 'miles'  # Default to miles
            })

        # Check bid modifier
        bid_modifier_str = row.get("Bid Modifier", "").strip()
        if bid_modifier_str:
            try:
                bid_modifier = float(bid_modifier_str)
                if bid_modifier < 0.1 or bid_modifier > 9.0:
                    issues.append({
                        'level': 'targeting',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Bid Modifier',
                        'issue_type': 'extreme_bid_modifier',
                        'message': f'Extreme bid modifier: {bid_modifier} (recommended range: 0.1 - 9.0)',
                        'auto_fixable': False
                    })
            except ValueError:
                issues.append({
                    'level': 'targeting',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Bid Modifier',
                    'issue_type': 'invalid_bid_modifier_format',
                    'message': f'Invalid bid modifier format: "{bid_modifier_str}"',
                    'auto_fixable': False
                })

        return issues

    def _get_us_state_codes(self) -> List[str]:
        """Get list of US state codes"""
        return [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC'  # District of Columbia
        ]

    def _get_common_location_names(self) -> List[str]:
        """Get list of common location names"""
        return [
            'United States', 'Canada', 'United Kingdom', 'Australia', 'Germany',
            'France', 'Italy', 'Spain', 'Netherlands', 'Belgium', 'Switzerland',
            'Austria', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Ireland',
            'Portugal', 'Greece', 'Poland'
        ]