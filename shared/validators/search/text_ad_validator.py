#!/usr/bin/env python3
"""
Text Ad Validator for Search Campaigns

Validates text ad format, content, and compliance for Search campaigns.
Includes Wright's Impact Window & Door specific ad copy requirements.
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class TextAdValidator:
    """Validates text ad content and format for Search campaigns"""

    def __init__(self):
        # Updated Text ad limits (Google Ads specifications - 2026)
        self.headline_limits = {
            'max_length': 30,
            'min_length': 25,  # Recommended for better performance
            'max_headlines': 3
        }

        self.description_limits = {
            'max_length': 90,
            'min_length': 70,  # Updated minimum for optimal performance
            'max_descriptions': 2
        }

        # Character patterns that can cause issues
        self.problematic_chars = ['|', '\t', '\n', '\r']

        # Punctuation that might be flagged
        self.excessive_punctuation = r'[!?]{2,}'

        # Wright's Impact Window & Door specific requirements
        self.wrights_brand_patterns = [
            r"Wright'?s\s+Impact\s+Windows?",
            r"Wright'?s\s+Impact\s+Doors?",
            r"Wright'?s\s+Window\s+&\s+Door",
            r"Wright'?s\s+Impact\s+Specialists",
            r"Wright'?s\s+Florida\s+Protection",
            r"Wright'?s\s+Lifetime\s+Guarantee"
        ]

        # Required headline categories for Wright's
        self.required_headline_categories = {
            'positioning': {
                'required': True,
                'min_count': 1,
                'patterns': [r'^#1\s+', r'#1\s+.*Expert', r'#1\s+.*Protection'],
                'examples': ['#1 Impact Windows Expert', '#1 Hurricane Protection', '#1 Energy Efficient Solutions']
            },
            'brand_recognition': {
                'required': True,
                'min_count': 2,
                'patterns': self.wrights_brand_patterns,
                'examples': ['Wright\'s Impact Windows', 'Wright\'s Window & Door']
            },
            'service_excellence': {
                'required': True,
                'min_count': 5,
                'patterns': [
                    r'Premium\s+Impact\s+Windows', r'Hurricane\s+Impact\s+Glass', r'Storm-Resistant\s+Windows',
                    r'Impact\s+Entry\s+Doors', r'Hurricane\s+Door\s+Systems', r'Security\s+Impact\s+Doors',
                    r'Energy-Efficient\s+Windows', r'Utility\s+Bill\s+Savings', r'Commercial\s+Impact\s+Windows'
                ],
                'examples': ['Premium Impact Windows', 'Hurricane Impact Glass', 'Energy-Efficient Windows']
            },
            'regional_authority': {
                'required': True,
                'min_count': 5,
                'patterns': [
                    r'Florida\s+Hurricane\s+Protection', r'Florida\s+Impact\s+Windows',
                    r'Lee\s+County\s+Impact\s+Windows', r'Broward\s+County\s+Protection',
                    r'Fort\s+Myers\s+Impact\s+Doors', r'Naples\s+Storm\s+Protection'
                ],
                'examples': ['Florida Hurricane Protection', 'Lee County Impact Windows']
            }
        }

        # Required value impact messaging for Wright's
        self.required_value_messaging = {
            'catastrophic_loss_prevention': [
                r'Protect.*home.*total.*hurricane.*destruction',
                r'Avoid.*catastrophic.*storm.*damage',
                r'Prevent.*complete.*loss.*major.*hurricanes'
            ],
            'family_safety_peace_of_mind': [
                r'Keep.*family.*safe.*Florida.*storms',
                r'Sleep.*soundly.*knowing.*protected',
                r'Peace.*mind.*hurricane-ready.*protection'
            ],
            'financial_protection': [
                r'Safeguard.*largest.*financial.*investment',
                r'Insurance-approved.*products.*premium.*discounts',
                r'Increase.*home.*value.*premium.*protection'
            ],
            'emergency_preparedness': [
                r'Don\'?t\s+wait.*storm.*season.*protect.*now',
                r'Year-round.*hurricane.*readiness',
                r'Emergency.*impact.*solutions.*need.*most'
            ]
        }

        # Trust signals required for Wright's
        self.required_trust_signals = [
            r'50\+\s*Years?\s+(?:Florida\s+)?Hurricane\s+Protection\s+(?:Experience)?',
            r'Lifetime\s+Manufacturer\s+Guarantee',
            r'(?:State-Certified|Licensed)\s+(?:Installation|Service)',
            r'(?:Licensed|Fully)\s+(?:Insured|&?\s*Insured)\s+(?:Contractors?|Installation)',
            r'Professional\s+(?:Measurements?|Installation|Service)'
        ]

        # Common ad policy violations to check
        self.policy_violations = [
            r'\b(?:free|cheap|discount)\b.*\b(?:trial|sample)\b',  # Free trials
            r'\bguarantee\b.*\b(?:100%|full)\b',  # Unrealistic guarantees
            r'\b(?:best|worst|top|leading|#1)\b',  # Unsubstantiated claims (except Wright's #1 positioning)
            r'\b(?:click here|visit|go to)\b',  # Command language
        ]

    def validate_text_ad(self, csv_path: str, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate text ad content in a Search campaign row"""
        issues = []

        campaign_type = row.get("Campaign Type", "").strip()
        if campaign_type != "Search":
            return issues

        # Validate headlines (1-3)
        headline_issues = self._validate_headlines(row, row_num)
        issues.extend(headline_issues)

        # Validate descriptions (1-2)
        description_issues = self._validate_descriptions(row, row_num)
        issues.extend(description_issues)

        # Validate ad structure and consistency
        structure_issues = self._validate_ad_structure(row, row_num)
        issues.extend(structure_issues)

        # Check for Wright's specific content requirements
        wrights_issues = self._validate_wrights_content_requirements(row, row_num)
        issues.extend(wrights_issues)

        # Check for policy violations
        policy_issues = self._check_policy_compliance(row, row_num)
        issues.extend(policy_issues)

        return issues

    def _validate_headlines(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate headline content and format"""
        issues = []

        headlines = []
        for i in range(1, 4):  # Headlines 1-3
            headline_col = f"Headline {i}"
            headline = row.get(headline_col, "").strip()

            if headline:  # Only validate if headline exists
                headlines.append(headline)

                # Check length
                length = len(headline)
                if length > self.headline_limits['max_length']:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_too_long',
                        'message': f'Headline {i} too long: {length} chars (max: {self.headline_limits["max_length"]})',
                        'auto_fixable': False
                    })
                elif length < self.headline_limits['min_length']:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_too_short',
                        'message': f'Headline {i} too short: {length} chars (recommended: {self.headline_limits["min_length"]}-{self.headline_limits["max_length"]})',
                        'suggestion': f'Expand to at least {self.headline_limits["min_length"]} characters for better performance',
                        'auto_fixable': False
                    })

                # Check for problematic characters
                for char in self.problematic_chars:
                    if char in headline:
                        issues.append({
                            'level': 'text_ad',
                            'severity': 'error',
                            'row_number': row_num,
                            'column': headline_col,
                            'issue_type': 'headline_problematic_chars',
                            'message': f'Headline {i} contains problematic character: {repr(char)}',
                            'auto_fixable': False
                        })

                # Check for excessive punctuation
                if re.search(self.excessive_punctuation, headline):
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_excessive_punctuation',
                        'message': f'Headline {i} has excessive punctuation: "{headline}"',
                            'suggestion': 'Use punctuation sparingly for better ad approval',
                        'auto_fixable': False
                    })

                # Check for all caps (shouting)
                if headline.isupper() and len(headline) > 5:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': headline_col,
                        'issue_type': 'headline_all_caps',
                        'message': f'Headline {i} is all caps: "{headline}"',
                        'suggestion': 'Use mixed case for better readability',
                        'auto_fixable': True,
                        'original_value': headline,
                        'fixed_value': headline.capitalize()
                    })

        # Check for missing headlines
        if not headlines:
            issues.append({
                'level': 'text_ad',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Headline 1',
                'issue_type': 'no_headlines',
                'message': 'Search ad has no headlines',
                'auto_fixable': False
            })

        return issues

    def _validate_descriptions(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate description content and format"""
        issues = []

        descriptions = []
        for i in range(1, 3):  # Descriptions 1-2
            desc_col = f"Description {i}"
            description = row.get(desc_col, "").strip()

            if description:  # Only validate if description exists
                descriptions.append(description)

                # Check length
                length = len(description)
                if length > self.description_limits['max_length']:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_too_long',
                        'message': f'Description {i} too long: {length} chars (max: {self.description_limits["max_length"]})',
                        'auto_fixable': False
                    })
                elif length < self.description_limits['min_length']:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_too_short',
                        'message': f'Description {i} too short: {length} chars (recommended: {self.description_limits["min_length"]}-{self.description_limits["max_length"]})',
                        'suggestion': f'Expand to at least {self.description_limits["min_length"]} characters for better performance',
                        'auto_fixable': False
                    })

                # Check for problematic characters
                for char in self.problematic_chars:
                    if char in description:
                        issues.append({
                            'level': 'text_ad',
                            'severity': 'error',
                            'row_number': row_num,
                            'column': desc_col,
                            'issue_type': 'description_problematic_chars',
                            'message': f'Description {i} contains problematic character: {repr(char)}',
                            'auto_fixable': False
                        })

                # Check for excessive punctuation
                if re.search(self.excessive_punctuation, description):
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': desc_col,
                        'issue_type': 'description_excessive_punctuation',
                        'message': f'Description {i} has excessive punctuation',
                        'suggestion': 'Use punctuation sparingly for better ad approval',
                        'auto_fixable': False
                    })

        # Check for missing descriptions
        if not descriptions:
            issues.append({
                'level': 'text_ad',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Description 1',
                'issue_type': 'no_descriptions',
                'message': 'Search ad has no descriptions',
                'auto_fixable': False
            })

        return issues

    def _validate_ad_structure(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate overall ad structure and consistency"""
        issues = []

        # Check for business name consistency
        business_name = row.get("Business name", "").strip()
        if business_name and len(business_name) > 20:  # Gmail ads limit
            issues.append({
                'level': 'text_ad',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Business name',
                'issue_type': 'business_name_too_long',
                'message': f'Business name too long for Gmail ads: "{business_name}" ({len(business_name)} chars > 20 limit)',
                'suggestion': 'Shorten business name for Gmail ad compatibility',
                'auto_fixable': False
            })

        # Check for callout text length
        callout_text = row.get("Callout text", "").strip()
        if callout_text and len(callout_text) > 25:
            issues.append({
                'level': 'text_ad',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Callout text',
                'issue_type': 'callout_text_too_long',
                'message': f'Callout text too long: {len(callout_text)} chars (max: 25)',
                'auto_fixable': False
            })

        # Validate final URL
        final_url = row.get("Final URL", "").strip()
        if final_url:
            if not final_url.startswith(('http://', 'https://')):
                issues.append({
                    'level': 'text_ad',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Final URL',
                    'issue_type': 'invalid_final_url',
                    'message': f'Final URL must start with http:// or https://: {final_url}',
                    'auto_fixable': True,
                    'original_value': final_url,
                    'fixed_value': f'https://{final_url}' if not final_url.startswith('http') else final_url
                })

        # Check tracking template format (if present)
        tracking_template = row.get("Tracking template", "").strip()
        if tracking_template and not tracking_template.startswith(('http', '{')):
            issues.append({
                'level': 'text_ad',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Tracking template',
                'issue_type': 'invalid_tracking_template',
                'message': f'Tracking template format may be invalid: {tracking_template}',
                'suggestion': 'Tracking templates should start with http or use ValueTrack parameters',
                'auto_fixable': False
            })

        return issues

    def _validate_wrights_content_requirements(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate Wright's Impact Window & Door specific content requirements"""
        issues = []

        # Combine all headline text for analysis
        all_headlines = []
        for i in range(1, 4):
            headline = row.get(f"Headline {i}", "").strip()
            if headline:
                all_headlines.append(headline)

        # Combine all description text for analysis
        all_descriptions = []
        for i in range(1, 3):
            description = row.get(f"Description {i}", "").strip()
            if description:
                all_descriptions.append(description)

        full_ad_text = ' '.join(all_headlines + all_descriptions).lower()

        # Validate required headline categories
        category_counts = self._analyze_headline_categories(all_headlines)

        for category_name, category_config in self.required_headline_categories.items():
            if category_config['required']:
                count = category_counts.get(category_name, 0)
                min_required = category_config['min_count']

                if count < min_required:
                    issues.append({
                        'level': 'text_ad',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Headline 1',
                        'issue_type': f'missing_{category_name}_headlines',
                        'message': f'Missing required {category_name} headlines: {count}/{min_required} found',
                        'suggestion': f'Add at least {min_required} {category_name} headlines from approved list',
                        'auto_fixable': False,
                        'examples': category_config['examples'][:3]  # Show first 3 examples
                    })

        # Validate value impact messaging
        value_messaging_found = self._analyze_value_messaging(all_descriptions)

        if not any(value_messaging_found.values()):
            issues.append({
                'level': 'text_ad',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Description 1',
                'issue_type': 'missing_value_impact_messaging',
                'message': 'Ad missing required value impact messaging (catastrophic loss prevention, family safety, etc.)',
                'suggestion': 'Include value impact messaging about hurricane protection, family safety, or financial benefits',
                'auto_fixable': False
            })

        # Validate trust signals
        trust_signals_found = self._analyze_trust_signals(all_descriptions)

        if not trust_signals_found:
            issues.append({
                'level': 'text_ad',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Description 1',
                'issue_type': 'missing_trust_signals',
                'message': 'Ad missing trust signals (experience, guarantees, certifications)',
                'suggestion': 'Include trust signals like "50+ Years Experience" or "Lifetime Guarantee"',
                'auto_fixable': False
            })

        # Validate regional focus for Florida market
        florida_references = len(re.findall(r'\bflorida\b', full_ad_text, re.IGNORECASE))
        if florida_references == 0:
            issues.append({
                'level': 'text_ad',
                'severity': 'info',
                'row_number': row_num,
                'column': 'Headline 1',
                'issue_type': 'missing_florida_reference',
                'message': 'Ad does not reference Florida - consider adding regional relevance',
                'suggestion': 'Include Florida-specific references for local targeting',
                'auto_fixable': False
            })

        return issues

    def _analyze_headline_categories(self, headlines: List[str]) -> Dict[str, int]:
        """Analyze headlines to count categories present"""
        category_counts = {
            'positioning': 0,
            'brand_recognition': 0,
            'service_excellence': 0,
            'regional_authority': 0
        }

        for headline in headlines:
            headline_lower = headline.lower()

            # Check positioning headlines (#1 positioning)
            if self.required_headline_categories['positioning']['required']:
                for pattern in self.required_headline_categories['positioning']['patterns']:
                    if re.search(pattern, headline_lower, re.IGNORECASE):
                        category_counts['positioning'] += 1
                        break

            # Check brand recognition
            if self.required_headline_categories['brand_recognition']['required']:
                for pattern in self.required_headline_categories['brand_recognition']['patterns']:
                    if re.search(pattern, headline, re.IGNORECASE):  # Case sensitive for brand
                        category_counts['brand_recognition'] += 1
                        break

            # Check service excellence
            if self.required_headline_categories['service_excellence']['required']:
                for pattern in self.required_headline_categories['service_excellence']['patterns']:
                    if re.search(pattern, headline_lower, re.IGNORECASE):
                        category_counts['service_excellence'] += 1
                        break

            # Check regional authority
            if self.required_headline_categories['regional_authority']['required']:
                for pattern in self.required_headline_categories['regional_authority']['patterns']:
                    if re.search(pattern, headline_lower, re.IGNORECASE):
                        category_counts['regional_authority'] += 1
                        break

        return category_counts

    def _analyze_value_messaging(self, descriptions: List[str]) -> Dict[str, bool]:
        """Analyze descriptions for required value impact messaging"""
        value_messaging_found = {
            'catastrophic_loss_prevention': False,
            'family_safety_peace_of_mind': False,
            'financial_protection': False,
            'emergency_preparedness': False
        }

        full_description_text = ' '.join(descriptions).lower()

        for category, patterns in self.required_value_messaging.items():
            for pattern in patterns:
                if re.search(pattern, full_description_text, re.IGNORECASE):
                    value_messaging_found[category] = True
                    break

        return value_messaging_found

    def _analyze_trust_signals(self, descriptions: List[str]) -> bool:
        """Analyze descriptions for trust signals"""
        full_description_text = ' '.join(descriptions)

        for pattern in self.required_trust_signals:
            if re.search(pattern, full_description_text, re.IGNORECASE):
                return True

        return False

    def _check_policy_compliance(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Check for potential Google Ads policy violations"""
        issues = []

        # Combine all ad text for policy checking
        ad_text_parts = []

        # Add headlines
        for i in range(1, 4):
            headline = row.get(f"Headline {i}", "").strip()
            if headline:
                ad_text_parts.append(headline)

        # Add descriptions
        for i in range(1, 3):
            description = row.get(f"Description {i}", "").strip()
            if description:
                ad_text_parts.append(description)

        full_ad_text = ' '.join(ad_text_parts).lower()

        # Check for policy violations (skip #1 claims for Wright's positioning)
        for pattern in self.policy_violations:
            # Skip the #1/best/top pattern since Wright's requires #1 positioning
            if '#1' in pattern and 'best' in pattern:
                continue

            if re.search(pattern, full_ad_text, re.IGNORECASE):
                issues.append({
                    'level': 'text_ad',
                    'severity': 'warning',
                    'row_number': row_num,
                    'column': 'Headline 1',  # Point to first headline
                    'issue_type': 'potential_policy_violation',
                    'message': f'Ad text may violate Google Ads policies: {pattern}',
                    'suggestion': 'Review Google Ads policies and modify ad text if needed',
                    'auto_fixable': False
                })

        # Check for misleading pricing
        if re.search(r'\$\d+', full_ad_text) and 'from' not in full_ad_text:
            issues.append({
                'level': 'text_ad',
                'severity': 'info',
                'row_number': row_num,
                'column': 'Headline 1',
                'issue_type': 'pricing_display',
                'message': 'Ad contains pricing - ensure it complies with pricing policies',
                'suggestion': 'Consider using "from" or "starting at" with prices',
                'auto_fixable': False
            })

        return issues

    def assess_ad_quality(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Assess overall ad quality and provide recommendations.

        Args:
            row: CSV row data

        Returns:
            Quality assessment dictionary
        """
        quality_score = 0
        recommendations = []

        # Headline assessment
        headline_count = 0
        total_headline_length = 0
        category_compliance = 0

        headlines = []
        for i in range(1, 4):
            headline = row.get(f"Headline {i}", "").strip()
            if headline:
                headlines.append(headline)
                headline_count += 1
                total_headline_length += len(headline)

                # Length quality
                if 25 <= len(headline) <= 30:
                    quality_score += 1

        # Check category compliance
        if headlines:
            category_counts = self._analyze_headline_categories(headlines)
            for category, config in self.required_headline_categories.items():
                if category_counts.get(category, 0) >= config['min_count']:
                    category_compliance += 1

            if category_compliance >= 3:  # 3 out of 4 categories met
                quality_score += 2

        # Description assessment
        description_count = 0
        total_description_length = 0
        value_messaging_score = 0

        descriptions = []
        for i in range(1, 3):
            description = row.get(f"Description {i}", "").strip()
            if description:
                descriptions.append(description)
                description_count += 1
                total_description_length += len(description)

                # Length quality
                if 70 <= len(description) <= 90:
                    quality_score += 1

        # Check value messaging compliance
        if descriptions:
            value_messaging_found = self._analyze_value_messaging(descriptions)
            value_messaging_score = sum(value_messaging_found.values())

            if value_messaging_score >= 2:  # At least 2 value messaging types
                quality_score += 1

        # Trust signals
        if self._analyze_trust_signals(descriptions):
            quality_score += 1

        # Diversity assessment
        if headline_count >= 2:
            quality_score += 1
        if description_count >= 2:
            quality_score += 1

        # Final URL presence
        if row.get("Final URL", "").strip():
            quality_score += 1

        # Generate recommendations
        if headline_count < 3:
            recommendations.append("Add more headlines for better ad testing")
        if category_compliance < 3:
            recommendations.append("Include all required headline categories (#1 positioning, brand, service, regional)")
        if description_count < 2:
            recommendations.append("Add a second description for better performance")
        if value_messaging_score < 2:
            recommendations.append("Include more value impact messaging (protection, safety, savings)")
        if not self._analyze_trust_signals(descriptions):
            recommendations.append("Add trust signals (experience, guarantees, certifications)")
        if total_headline_length < 75:  # 25 * 3
            recommendations.append("Expand headline content for better messaging")

        return {
            'quality_score': quality_score,
            'max_score': 12,  # Updated for Wright's specific requirements
            'quality_rating': 'High' if quality_score >= 9 else 'Medium' if quality_score >= 6 else 'Low',
            'recommendations': recommendations,
            'headline_count': headline_count,
            'description_count': description_count,
            'category_compliance': f"{category_compliance}/4",
            'value_messaging_score': f"{value_messaging_score}/4",
            'wrights_compliance': 'Good' if category_compliance >= 3 and value_messaging_score >= 2 else 'Needs Work'
        }