#!/usr/bin/env python3
"""
Website Content Analyzer for MyExpertResume.com

Analyzes website content to extract value propositions, messaging, and ad copy strategies
for integration into Google Ads campaigns.

Usage:
    python3 website_content_analyzer.py [--url URL] [--focus executive|general] [--output format]
"""

import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import json
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse
import argparse
import sys

class WebsiteContentAnalyzer:
    """Analyzes website content for ad copy strategy and value propositions"""

    def __init__(self, base_url: str = "https://myexpertresume.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_page_content(self, url: str) -> str:
        """Fetch and extract text content from a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def extract_key_phrases(self, text: str) -> Dict[str, List[str]]:
        """Extract key value propositions and messaging patterns"""

        # Convert to lowercase for pattern matching
        text_lower = text.lower()

        # Define patterns for different types of value propositions
        patterns = {
            'success_metrics': [
                r'(\d+(?:\.\d+)?%?\s+(?:success|land|get|find|secure|win)\s+\w+\s+\w+)',  # "74% success rate"
                r'(\d+,?\d*\+\s+(?:careers?|resumes?|clients?|customers?))',  # "10,000+ careers"
                r'(over\s+\d+,?\d*\+\s+\w+)',  # "over 10,000+ clients"
            ],
            'awards_recognition': [
                r'(\d+x?\s+award)',  # "9x award"
                r'(award[-\s]winning)',  # "award-winning"
                r'(as\s+seen\s+on)',  # "as seen on"
                r'(featured\s+(?:on|in))',  # "featured on"
            ],
            'expertise_credentials': [
                r'(since\s+\d{4})',  # "since 2005"
                r'(\d+\+\s+years?\s+(?:of\s+)?experience)',  # "15+ years experience"
                r'(certified|accredited|licensed)',  # certifications
            ],
            'guarantees': [
                r'(money[-\s]back\s+guarantee)',  # "money-back guarantee"
                r'(30[-\s]day\s+guarantee)',  # "30-day guarantee"
                r'(we\s+guarantee)',  # "we guarantee"
                r'(guaranteed\s+(?:results?|success))',  # "guaranteed results"
            ],
            'unique_selling_points': [
                r'(all[-\s]inclusive)',  # "all-inclusive"
                r'(comprehensive\s+(?:service|approach))',  # "comprehensive service"
                r'(professional\s+(?:writers?|services?))',  # "professional writers"
                r'(expert\s+(?:advice|guidance|help))',  # "expert advice"
            ],
            'location_branding': [
                r'(fort\s+lauderdale)',  # "Fort Lauderdale"
                r'(florida|fl)',  # location
                r'(usa\s+based)',  # "USA based"
            ],
            'service_benefits': [
                r'(get\s+hired\s+faster)',  # "get hired faster"
                r'(more\s+offers)',  # "more offers"
                r'(better\s+jobs?)',  # "better jobs"
                r'(career\s+(?:advancement|success|growth))',  # "career success"
            ]
        }

        results = {}
        for category, pattern_list in patterns.items():
            matches = []
            for pattern in pattern_list:
                found = re.findall(pattern, text_lower, re.IGNORECASE)
                matches.extend(found)

            # Clean and deduplicate
            cleaned_matches = []
            for match in matches:
                # Clean up the match
                cleaned = re.sub(r'\s+', ' ', match.strip())
                if len(cleaned) > 5 and cleaned not in cleaned_matches:
                    cleaned_matches.append(cleaned)

            results[category] = cleaned_matches

        return results

    def analyze_headline_opportunities(self, content: Dict[str, List[str]]) -> List[str]:
        """Generate potential headline ideas based on website content"""

        headlines = []

        # Success metrics headlines
        for metric in content.get('success_metrics', []):
            headlines.extend([
                f"{metric.title()} Today",
                f"{metric.title()} Guaranteed",
                f"Join {metric.title()}",
            ])

        # Award-based headlines
        for award in content.get('awards_recognition', []):
            headlines.extend([
                f"{award.title()} Resume Experts",
                f"{award.title()} Service",
                f"{award.title()} Since 2005",
            ])

        # Guarantee headlines
        for guarantee in content.get('guarantees', []):
            headlines.extend([
                f"{guarantee.title()} Included",
                f"{guarantee.title()} Protection",
                f"Risk-Free {guarantee.title()}",
            ])

        # Service benefit headlines
        for benefit in content.get('service_benefits', []):
            headlines.extend([
                f"{benefit.title()} Now",
                f"Get {benefit.title()}",
                f"{benefit.title()} Results",
            ])

        return headlines[:20]  # Limit to top 20

    def analyze_website(self, focus_pages: List[str] = None) -> Dict:
        """Comprehensive website analysis"""

        if focus_pages is None:
            focus_pages = [
                "/",  # Homepage
                "/executive-resume/",  # Executive page
                "/about-us/",  # About page
                "/guarantee/",  # Guarantee page
                "/resume-services-guarantee/",  # Services guarantee
            ]

        all_content = ""
        page_analyses = {}

        for page in focus_pages:
            url = urljoin(self.base_url, page)
            print(f"Analyzing: {url}")

            content = self.get_page_content(url)
            if content:
                all_content += " " + content
                page_analyses[page] = {
                    'url': url,
                    'content_length': len(content),
                    'key_phrases': self.extract_key_phrases(content)
                }

        # Overall analysis
        overall_patterns = self.extract_key_phrases(all_content)
        headline_suggestions = self.analyze_headline_opportunities(overall_patterns)

        return {
            'base_url': self.base_url,
            'pages_analyzed': len(page_analyses),
            'total_content_length': len(all_content),
            'page_analyses': page_analyses,
            'overall_value_propositions': overall_patterns,
            'headline_suggestions': headline_suggestions,
            'top_metrics': self._get_top_metrics(overall_patterns)
        }

    def _get_top_metrics(self, patterns: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Extract the most compelling metrics and claims"""

        top_metrics = {}

        # Prioritize success metrics
        success = patterns.get('success_metrics', [])
        if success:
            top_metrics['success_metrics'] = success[:5]

        # Awards and recognition
        awards = patterns.get('awards_recognition', [])
        if awards:
            top_metrics['awards_recognition'] = awards[:3]

        # Guarantees
        guarantees = patterns.get('guarantees', [])
        if guarantees:
            top_metrics['guarantees'] = guarantees[:3]

        # Experience/credentials
        credentials = patterns.get('expertise_credentials', [])
        if credentials:
            top_metrics['expertise_credentials'] = credentials[:3]

        return top_metrics

    def generate_ad_copy_recommendations(self, analysis: Dict) -> Dict:
        """Generate ad copy recommendations based on analysis"""

        recommendations = {
            'headlines': [],
            'descriptions': [],
            'callouts': [],
            'sitelinks': []
        }

        patterns = analysis['overall_value_propositions']

        # Headline recommendations (23-30 chars)
        headline_templates = [
            "{metric} Today",
            "{metric} Guaranteed",
            "{award} Experts",
            "{award} Service",
            "Get {benefit} Now",
            "{guarantee} Included",
        ]

        for template in headline_templates:
            if '{metric}' in template and patterns.get('success_metrics'):
                for metric in patterns['success_metrics'][:2]:
                    headline = template.format(metric=metric.title())
                    if 23 <= len(headline) <= 30:
                        recommendations['headlines'].append(headline)

            if '{award}' in template and patterns.get('awards_recognition'):
                for award in patterns['awards_recognition'][:2]:
                    headline = template.format(award=award.title())
                    if 23 <= len(headline) <= 30:
                        recommendations['headlines'].append(headline)

            if '{benefit}' in template and patterns.get('service_benefits'):
                for benefit in patterns['service_benefits'][:2]:
                    headline = template.format(benefit=benefit.title())
                    if 23 <= len(headline) <= 30:
                        recommendations['headlines'].append(headline)

            if '{guarantee}' in template and patterns.get('guarantees'):
                for guarantee in patterns['guarantees'][:2]:
                    headline = template.format(guarantee=guarantee.title())
                    if 23 <= len(headline) <= 30:
                        recommendations['headlines'].append(headline)

        # Callout recommendations (15-25 chars)
        callout_templates = [
            "{success}",
            "{award}",
            "{guarantee}",
            "{benefit}",
            "{expertise}"
        ]

        category_map = {
            'success_metrics': 'success',
            'awards_recognition': 'award',
            'guarantees': 'guarantee',
            'service_benefits': 'benefit',
            'expertise_credentials': 'expertise'
        }

        for template in callout_templates:
            for category in ['success_metrics', 'awards_recognition', 'guarantees', 'service_benefits', 'expertise_credentials']:
                if patterns.get(category):
                    template_key = category_map[category]
                    for item in patterns[category][:3]:
                        try:
                            callout = template.format(**{template_key: item.title()})
                            if 15 <= len(callout) <= 25:
                                recommendations['callouts'].append(callout)
                        except KeyError:
                            continue

        # Deduplicate and limit
        recommendations['headlines'] = list(set(recommendations['headlines']))[:15]
        recommendations['callouts'] = list(set(recommendations['callouts']))[:10]

        return recommendations


def main():
    parser = argparse.ArgumentParser(description='Analyze MyExpertResume website for ad copy strategy')
    parser.add_argument('--url', default='https://myexpertresume.com',
                       help='Base URL to analyze')
    parser.add_argument('--focus', choices=['executive', 'general'], default='general',
                       help='Focus area for analysis')
    parser.add_argument('--output', choices=['json', 'text', 'markdown'], default='text',
                       help='Output format')

    args = parser.parse_args()

    analyzer = WebsiteContentAnalyzer(args.url)

    # Customize pages based on focus
    focus_pages = {
        'executive': ['/', '/executive-resume/', '/about-us/', '/guarantee/'],
        'general': ['/', '/executive-resume/', '/about-us/', '/guarantee/', '/resume-services-guarantee/']
    }

    pages_to_analyze = focus_pages.get(args.focus, focus_pages['general'])

    print(f"🔍 Analyzing {args.url} for {args.focus} focus...")
    print(f"📄 Pages to analyze: {len(pages_to_analyze)}")
    print("-" * 50)

    analysis = analyzer.analyze_website(pages_to_analyze)
    recommendations = analyzer.generate_ad_copy_recommendations(analysis)

    if args.output == 'json':
        output = {
            'analysis': analysis,
            'recommendations': recommendations
        }
        print(json.dumps(output, indent=2))

    elif args.output == 'markdown':
        print(f"# Website Analysis: {args.url}")
        print(f"**Focus:** {args.focus}")
        print(f"**Pages Analyzed:** {analysis['pages_analyzed']}")
        print()

        print("## Top Value Propositions")
        for category, items in analysis['top_metrics'].items():
            print(f"### {category.replace('_', ' ').title()}")
            for item in items:
                print(f"- {item}")
            print()

        print("## Ad Copy Recommendations")
        for ad_type, items in recommendations.items():
            print(f"### {ad_type.title()}")
            for item in items:
                print(f"- {item}")
            print()

    else:  # text output
        print("🎯 WEBSITE ANALYSIS RESULTS")
        print("=" * 50)
        print(f"URL: {args.url}")
        print(f"Focus: {args.focus}")
        print(f"Pages Analyzed: {analysis['pages_analyzed']}")
        print(f"Total Content Length: {analysis['total_content_length']:,} characters")
        print()

        print("📊 TOP VALUE PROPOSITIONS FOUND:")
        for category, items in analysis['top_metrics'].items():
            if items:
                print(f"  • {category.replace('_', ' ').title()}:")
                for item in items:
                    print(f"    - {item}")
                print()

        print("💡 AD COPY RECOMMENDATIONS:")
        print("  Headlines (23-30 chars):")
        for headline in recommendations['headlines'][:10]:
            print(f"    - \"{headline}\"")
        print()

        print("  Callouts (15-25 chars):")
        for callout in recommendations['callouts'][:8]:
            print(f"    - \"{callout}\"")
        print()

        print("📈 HEADLINE SUGGESTIONS:")
        for suggestion in analysis['headline_suggestions'][:10]:
            char_count = len(suggestion)
            status = "✅" if 23 <= char_count <= 30 else "❌"
            print(f"    {status} \"{suggestion}\" ({char_count} chars)")


if __name__ == "__main__":
    main()
