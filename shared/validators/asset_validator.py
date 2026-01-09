#!/usr/bin/env python3
"""
Asset-level CSV Validator

Validates individual assets (headlines, descriptions, images, videos).
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import io
import re

logger = logging.getLogger(__name__)


class AssetValidator:
    """Validates individual assets within asset groups"""

    def __init__(self):
        # Asset length limits
        self.headline_limits = {'min': 25, 'max': 30}
        self.description_limits = {'min': 80, 'max': 90}
        self.long_headline_limits = {'min': 25, 'max': 90}

        # Video validation
        self.valid_video_formats = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv']
        self.max_video_duration = 300  # 5 minutes in seconds

        # Image validation
        self.valid_image_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']
        self.min_image_dimensions = {'width': 300, 'height': 300}
        self.max_image_size_mb = 5

        # URL patterns
        self.url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'

    def validate_assets(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate all individual assets"""
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            for row_num, row in enumerate(reader, 2):
                # Validate headlines
                headline_issues = self._validate_headlines(row, row_num)
                issues.extend(headline_issues)

                # Validate descriptions
                description_issues = self._validate_descriptions(row, row_num)
                issues.extend(description_issues)

                # Validate long headlines
                long_headline_issues = self._validate_long_headlines(row, row_num)
                issues.extend(long_headline_issues)

                # Validate videos
                video_issues = self._validate_videos(row, row_num)
                issues.extend(video_issues)

                # Validate images (if present in CSV)
                image_issues = self._validate_images(row, row_num)
                issues.extend(image_issues)

                # Validate call-to-action
                cta_issues = self._validate_call_to_action(row, row_num)
                issues.extend(cta_issues)

        except Exception as e:
            issues.append({
                'level': 'asset',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate assets: {e}',
                'auto_fixable': False
            })

        return issues

    def _validate_headlines(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate headline assets"""
        issues = []

        for i in range(1, 16):  # Headlines 1-15
            headline_col = f"Headline {i}"
            headline = row.get(headline_col, "").strip()

            if headline:
                length = len(headline)

                # Check length limits
                if length < self.headline_limits['min']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_too_short',
                        'message': f'Headline {i} too short: {length} chars (min: {self.headline_limits["min"]})',
                        'suggestion': f'Expand to at least {self.headline_limits["min"]} characters',
                        'auto_fixable': False
                    })
                elif length > self.headline_limits['max']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_too_long',
                        'message': f'Headline {i} too long: {length} chars (max: {self.headline_limits["max"]})',
                        'suggestion': f'Shorten to {self.headline_limits["max"]} characters or less',
                        'auto_fixable': False
                    })

                # Check for special characters that might cause issues
                if '|' in headline or '\t' in headline:
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_special_chars',
                        'message': f'Headline {i} contains special characters that may cause CSV issues: {headline}',
                        'auto_fixable': False
                    })

                # Check for excessive caps
                if headline.isupper() and len(headline) > 10:
                    issues.append({
                        'level': 'asset',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_all_caps',
                        'message': f'Headline {i} is all caps - may appear as shouting: {headline}',
                        'suggestion': 'Use mixed case for better readability',
                        'auto_fixable': False
                    })

        return issues

    def _validate_descriptions(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate description assets"""
        issues = []

        for i in range(1, 6):  # Descriptions 1-5
            desc_col = f"Description {i}"
            description = row.get(desc_col, "").strip()

            if description:
                length = len(description)

                # Check length limits
                if length < self.description_limits['min']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_too_short',
                        'message': f'Description {i} too short: {length} chars (min: {self.description_limits["min"]})',
                        'suggestion': f'Expand to at least {self.description_limits["min"]} characters',
                        'auto_fixable': False
                    })
                elif length > self.description_limits['max']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_too_long',
                        'message': f'Description {i} too long: {length} chars (max: {self.description_limits["max"]})',
                        'suggestion': f'Shorten to {self.description_limits["max"]} characters or less',
                        'auto_fixable': False
                    })

                # Check for special characters
                if '|' in description or '\t' in description:
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_special_chars',
                        'message': f'Description {i} contains special characters that may cause CSV issues',
                        'auto_fixable': False
                    })

        return issues

    def _validate_long_headlines(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate long headline assets"""
        issues = []

        for i in range(1, 6):  # Long headlines 1-5
            long_headline_col = f"Long headline {i}"
            long_headline = row.get(long_headline_col, "").strip()

            if long_headline:
                length = len(long_headline)

                # Check length limits for long headlines
                if length < self.long_headline_limits['min']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': long_headline_col,
                        'issue_type': 'long_headline_too_short',
                        'message': f'Long headline {i} too short: {length} chars (min: {self.long_headline_limits["min"]})',
                        'auto_fixable': False
                    })
                elif length > self.long_headline_limits['max']:
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': long_headline_col,
                        'issue_type': 'long_headline_too_long',
                        'message': f'Long headline {i} too long: {length} chars (max: {self.long_headline_limits["max"]})',
                        'auto_fixable': False
                    })

        return issues

    def _validate_videos(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate video assets"""
        issues = []

        for i in range(1, 6):  # Video IDs 1-5
            video_col = f"Video ID {i}"
            video_id = row.get(video_col, "").strip()

            if video_id:
                # Basic validation - check if it looks like a YouTube ID or URL
                if not (re.match(r'^[a-zA-Z0-9_-]{11}$', video_id) or  # YouTube ID
                       re.match(self.url_pattern, video_id)):  # URL
                    issues.append({
                        'level': 'asset',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': video_col,
                        'issue_type': 'invalid_video_id',
                        'message': f'Video ID {i} format invalid: {video_id}',
                        'suggestion': 'Use YouTube video ID (11 characters) or full URL',
                        'auto_fixable': False
                    })

        return issues

    def _validate_images(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate image assets if present"""
        issues = []

        # Check for image URLs if they exist in the CSV
        image_url_cols = [col for col in row.keys() if 'image' in col.lower() and 'url' in col.lower()]

        for col in image_url_cols:
            image_url = row.get(col, "").strip()
            if image_url and not re.match(self.url_pattern, image_url):
                issues.append({
                    'level': 'asset',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': col,
                    'issue_type': 'invalid_image_url',
                    'message': f'Invalid image URL format: {image_url}',
                    'suggestion': 'URL should start with http:// or https://',
                    'auto_fixable': False
                })

        return issues

    def _validate_call_to_action(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate call-to-action text"""
        issues = []

        cta = row.get("Call to action", "").strip()
        if cta:
            # Check length
            if len(cta) > 25:
                issues.append({
                    'level': 'asset',
                    'severity': 'warning',
                    'row_number': row_num,
                    'column': 'Call to action',
                    'issue_type': 'cta_too_long',
                    'message': f'Call to action too long: {len(cta)} chars (recommended: 25 or less)',
                    'auto_fixable': False
                })

            # Check for common CTA text issues
            if cta.isupper():
                issues.append({
                    'level': 'asset',
                    'severity': 'info',
                    'row_number': row_num,
                    'column': 'Call to action',
                    'issue_type': 'cta_all_caps',
                    'message': f'Call to action is all caps: {cta}',
                    'suggestion': 'Consider using title case',
                    'auto_fixable': False
                })

        return issues