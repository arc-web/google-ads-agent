#!/usr/bin/env python3
"""
Search Location Validator

Validates geographic targeting for Search campaigns.
Ensures location IDs, types, and radius settings are valid for Search network.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search location validation."""
    level: str
    severity: str  # 'critical', 'warning', 'info'
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchLocationValidator:
    """
    Validates geographic targeting for Search campaigns.

    Focuses on Search-specific location validation including:
    - Location ID validation
    - Location type verification
    - Radius targeting parameters
    - Geographic exclusions
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize SearchLocationValidator with validation rules."""
        self.validation_rules = validation_rules or self._get_default_rules()

        # Valid location types
        self.valid_location_types = [
            'Country', 'State', 'City', 'Postal code', 'DMA region',
            'Location group', 'Proximity', 'Radius'
        ]

        # Location ID patterns (Google uses numeric IDs)
        self.location_id_pattern = re.compile(r'^\d+$')

        # Valid radius ranges (in miles/kilometers)
        self.min_radius_miles = 0.1
        self.max_radius_miles = 500
        self.min_radius_km = 0.1
        self.max_radius_km = 800

        # Common location status values
        self.valid_location_statuses = ['Enabled', 'Removed']

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules for Search location targeting."""
        return {
            'location': {
                'required_fields': ['Location'],
                'valid_types': [
                    'Country', 'State', 'City', 'Postal code', 'DMA region',
                    'Location group', 'Proximity', 'Radius'
                ],
                'id_validation': {
                    'pattern': r'^\d+$',
                    'description': 'Location IDs should be numeric'
                },
                'radius_limits': {
                    'min_miles': 0.1,
                    'max_miles': 500,
                    'min_km': 0.1,
                    'max_km': 800
                }
            }
        }

    def _parse_location_targeting(self, location_str: str) -> Dict[str, Any]:
        """
        Parse location targeting string into components.

        Args:
            location_str: Location targeting string from CSV

        Returns:
            Dictionary with parsed location components
        """
        if not location_str or not location_str.strip():
            return {}

        location_str = location_str.strip()

        # Handle multiple locations separated by semicolons or pipes
        locations = re.split(r'[;|]', location_str)

        parsed_locations = []
        for loc in locations:
            loc = loc.strip()
            if not loc:
                continue

            # Try to parse location format: "Name, State - ZIP codes: 12345, 67890 | Region"
            parsed = {
                'full_text': loc,
                'name': '',
                'type': '',
                'zip_codes': [],
                'region': '',
                'radius': None,
                'unit': 'miles'
            }

            # Check for ZIP codes
            zip_match = re.search(r'ZIP codes:\s*([0-9,\s]+)', loc, re.IGNORECASE)
            if zip_match:
                zip_str = zip_match.group(1)
                parsed['zip_codes'] = [z.strip() for z in zip_str.split(',') if z.strip()]

            # Check for radius
            radius_match = re.search(r'(\d+(?:\.\d+)?)\s*(miles?|km|kilometers?)\s*radius', loc, re.IGNORECASE)
            if radius_match:
                parsed['radius'] = float(radius_match.group(1))
                parsed['unit'] = 'km' if 'km' in radius_match.group(2).lower() else 'miles'

            # Extract region info
            region_match = re.search(r'\|\s*(.+)$', loc)
            if region_match:
                parsed['region'] = region_match.group(1).strip()

            # Try to determine location type
            if parsed['zip_codes']:
                parsed['type'] = 'Postal code'
            elif parsed['radius']:
                parsed['type'] = 'Radius'
            elif 'county' in loc.lower():
                parsed['type'] = 'County'
            elif any(state in loc for state in ['FL', 'CA', 'TX', 'NY']):
                parsed['type'] = 'State'
            else:
                parsed['type'] = 'City'  # Default assumption

            parsed_locations.append(parsed)

        return {
            'locations': parsed_locations,
            'location_count': len(parsed_locations)
        }

    def validate_location_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        """
        Validate a single location row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row
            row_number: Row number in the CSV (for error reporting)

        Returns:
            List of validation issues found
        """
        issues = []

        # Validate Location field
        location = row.get('Location', '').strip()
        if not location:
            issues.append(ValidationIssue(
                level='location',
                severity='warning',
                row_number=row_number,
                column='Location',
                issue_type='missing_location',
                message='Location targeting not specified',
                suggestion='Add geographic targeting to control where ads appear'
            ))
            return issues

        # Parse location targeting
        parsed_location = self._parse_location_targeting(location)

        if not parsed_location.get('locations'):
            issues.append(ValidationIssue(
                level='location',
                severity='critical',
                row_number=row_number,
                column='Location',
                issue_type='invalid_location_format',
                message=f'Unable to parse location format: "{location}"',
                suggestion='Use format: "City, State" or "ZIP codes: 12345" or "Location | Region"'
            ))
            return issues

        # Validate each location
        for i, loc_data in enumerate(parsed_location['locations']):
            loc_prefix = f'Location {i+1}' if len(parsed_location['locations']) > 1 else 'Location'

            # Validate location type
            loc_type = loc_data.get('type', '')
            if loc_type and loc_type not in self.valid_location_types:
                issues.append(ValidationIssue(
                    level='location',
                    severity='warning',
                    row_number=row_number,
                    column='Location',
                    issue_type='unknown_location_type',
                    message=f'{loc_prefix} type "{loc_type}" is not standard',
                    suggestion=f'Consider: {", ".join(self.valid_location_types[:4])}'
                ))

            # Validate ZIP codes
            zip_codes = loc_data.get('zip_codes', [])
            for zip_code in zip_codes:
                if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
                    issues.append(ValidationIssue(
                        level='location',
                        severity='critical',
                        row_number=row_number,
                        column='Location',
                        issue_type='invalid_zip_format',
                        message=f'Invalid ZIP code format: "{zip_code}"',
                        suggestion='Use 5-digit (12345) or 9-digit (12345-6789) ZIP codes'
                    ))

            # Validate radius
            radius = loc_data.get('radius')
            if radius is not None:
                unit = loc_data.get('unit', 'miles')
                min_radius = self.min_radius_km if unit == 'km' else self.min_radius_miles
                max_radius = self.max_radius_km if unit == 'km' else self.max_radius_miles

                if radius < min_radius:
                    issues.append(ValidationIssue(
                        level='location',
                        severity='critical',
                        row_number=row_number,
                        column='Location',
                        issue_type='radius_too_small',
                        message=f'Radius {radius} {unit} is below minimum {min_radius} {unit}',
                        suggestion=f'Increase radius to at least {min_radius} {unit}'
                    ))
                elif radius > max_radius:
                    issues.append(ValidationIssue(
                        level='location',
                        severity='critical',
                        row_number=row_number,
                        column='Location',
                        issue_type='radius_too_large',
                        message=f'Radius {radius} {unit} exceeds maximum {max_radius} {unit}',
                        suggestion=f'Reduce radius to {max_radius} {unit} or less'
                    ))

        # Validate Location id field (if present)
        location_id = row.get('Location id', '').strip()
        if location_id:
            if not self.location_id_pattern.match(location_id):
                issues.append(ValidationIssue(
                    level='location',
                    severity='critical',
                    row_number=row_number,
                    column='Location id',
                    issue_type='invalid_location_id_format',
                    message=f'Location ID "{location_id}" should be numeric',
                    suggestion='Use Google\'s numeric location ID'
                ))

        # Validate Location type field (if present)
        location_type = row.get('Location type', '').strip()
        if location_type and location_type not in self.valid_location_types:
            issues.append(ValidationIssue(
                level='location',
                severity='warning',
                row_number=row_number,
                column='Location type',
                issue_type='invalid_location_type',
                message=f'Location type "{location_type}" is not standard',
                suggestion=f'Use one of: {", ".join(self.valid_location_types)}'
            ))

        # Validate Radius field (if present)
        radius_str = row.get('Radius', '').strip()
        if radius_str:
            try:
                radius_val = float(radius_str)
                # Assume miles if no unit specified
                if radius_val < self.min_radius_miles:
                    issues.append(ValidationIssue(
                        level='location',
                        severity='critical',
                        row_number=row_number,
                        column='Radius',
                        issue_type='radius_too_small',
                        message=f'Radius {radius_val} miles is below minimum {self.min_radius_miles} miles',
                        suggestion=f'Increase radius to at least {self.min_radius_miles} miles'
                    ))
                elif radius_val > self.max_radius_miles:
                    issues.append(ValidationIssue(
                        level='location',
                        severity='critical',
                        row_number=row_number,
                        column='Radius',
                        issue_type='radius_too_large',
                        message=f'Radius {radius_val} miles exceeds maximum {self.max_radius_miles} miles',
                        suggestion=f'Reduce radius to {self.max_radius_miles} miles or less'
                    ))
            except ValueError:
                issues.append(ValidationIssue(
                    level='location',
                    severity='critical',
                    row_number=row_number,
                    column='Radius',
                    issue_type='invalid_radius_format',
                    message=f'Invalid radius format: "{radius_str}"',
                    suggestion='Use numeric format (e.g., 25.5)'
                ))

        return issues

    def validate_location_data(self, location_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate location-level data across multiple rows.

        Args:
            location_rows: List of location row dictionaries

        Returns:
            List of validation issues found
        """
        issues = []

        if not location_rows:
            return issues

        # Validate each location row
        for i, row in enumerate(location_rows):
            row_issues = self.validate_location_row(row, i + 2)  # +2 because row 1 is headers
            issues.extend(row_issues)

        # Cross-location validation
        location_coverage = {}

        for row in location_rows:
            campaign = row.get('Campaign', 'unknown')
            location = row.get('Location', '').strip()

            if campaign not in location_coverage:
                location_coverage[campaign] = set()

            # Add location to coverage set
            if location:
                location_coverage[campaign].add(location)

        # Validate campaign location coverage
        for campaign, locations in location_coverage.items():
            location_count = len(locations)

            if location_count == 0:
                issues.append(ValidationIssue(
                    level='location',
                    severity='critical',
                    row_number=0,
                    column='Location',
                    issue_type='no_location_targeting',
                    message=f'Campaign "{campaign}" has no location targeting',
                    suggestion='Add location targeting to control ad delivery'
                ))
            elif location_count > 1000:
                issues.append(ValidationIssue(
                    level='location',
                    severity='warning',
                    row_number=0,
                    column='Location',
                    issue_type='excessive_location_targeting',
                    message=f'Campaign "{campaign}" targets {location_count} locations',
                    suggestion='Consider reducing location targets for better management'
                ))

        # Check for overlapping or redundant locations
        for campaign, locations in location_coverage.items():
            location_list = list(locations)

            # Look for potential duplicates or overlaps
            for i, loc1 in enumerate(location_list):
                for j, loc2 in enumerate(location_list[i+1:], i+1):
                    # Simple overlap detection (same ZIP codes, etc.)
                    if loc1 != loc2:
                        # Check if both contain same ZIP codes
                        loc1_zips = set(re.findall(r'\b\d{5}\b', loc1))
                        loc2_zips = set(re.findall(r'\b\d{5}\b', loc2))

                        if loc1_zips and loc2_zips and loc1_zips & loc2_zips:
                            issues.append(ValidationIssue(
                                level='location',
                                severity='info',
                                row_number=0,
                                column='Location',
                                issue_type='potential_location_overlap',
                                message=f'Campaign "{campaign}" may have overlapping location targets',
                                suggestion='Review location targeting to avoid redundancy'
                            ))
                            break
                else:
                    continue
                break

        return issues