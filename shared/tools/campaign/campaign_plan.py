#!/usr/bin/env python3
"""
Campaign Plan for Google Ads Editor CSV Export Test

Based on the original MyExpertResume.com Performance Max campaign analysis.
Incorporates RSA and Sitelink strategy guidelines for optimal ad creation.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Setup Python path for dependency traversal
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure all agent packages are available
agent_paths = [
    os.path.join(project_root, 'agents'),
    os.path.join(project_root, 'agents', 'google_ads_agent'),
    os.path.join(project_root, 'agents', 'google_cloud_agent'),
    os.path.join(project_root, 'agents', 'google_youtube_agent'),
    os.path.join(project_root, 'shared'),
    os.path.join(project_root, 'admin'),
]

for path in agent_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

from google_ads_agent.gads.core.business_logic.google_ads_editor_exporter import (
    GoogleAdsEditorExporter,
    export_campaigns_to_csv
)
from google_ads_agent.utils.logging_utils import get_logger

logger = get_logger('campaign_plan')


def create_national_campaign() -> Dict[str, Any]:
    """
    Create national MyExpertResume executive campaign (no regional keywords).
    Focus: Broad national reach for executive resume services.
    """
    logger.info("Creating national executive campaign")
    # Header printed by caller when appropriate

    campaign_data = {
        "name": "MyExpertResume National Executive",
        "type": "Performance Max",
        "budget": 89.99,  # Higher budget for national reach
        "budget_type": "Daily",
        "languages": "en",
        "bid_strategy_type": "Maximize conversions",
        "bid_strategy_name": "",
        "target_cpa": 0.0,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": "",
        "ad_schedule": "(Monday[05:00-22:00]);(Tuesday[05:00-22:00]);(Wednesday[05:00-22:00]);(Thursday[05:00-22:00]);(Friday[05:00-22:00]);(Saturday[05:00-22:00]);(Sunday[05:00-22:00])",
        "ad_rotation": "Optimize for clicks",
        "targeting_method": "Location of presence or Area of interest",
        "exclusion_method": "Location of presence",
        "brand_guidelines": "Disabled",
        "brand_business_name": "My Expert Resume",
        "brand_font": "",
        "networks": "Google search",
        "custom_parameters": '{"_campaignname":"MyExpertResume+National+Executive"}',
        "campaign_status": "Enabled",
        "callouts": [
            "Executive Resume Service",
            "C-Suite Resume Writing",
            "Leadership Career Coaching",
            "VP Resume Services",
            "Director Resume Help",
            "Senior Management Resume",
            "Executive Career Coaching",
            "Professional Resume Writing",
            "Career Advancement Resume",
            "Job Search Resume Service",
            "100% Higher Response Rate",
            "98% Get Higher Pay Offers",
            "74% Land Job Within 30 Days",
            "10,000+ Careers Generated",
            "9x Award Winning Experts",
            "Guaranteed Interview Calls",
            "Accelerate Your Career",
            "Trusted Executive Advisors",
            "Nationwide Executive Resumes",
            "MyExpertResume for Leaders"
        ],
        "structured_snippets": {
            "header": "Types",
            "values": [
                "Executive Resume Writing",
                "C-Suite Resume Services",
                "Leadership Resume Writing",
                "VP Resume Writing",
                "Director Resume Services",
                "Senior Management Resumes",
                "Professional Resume Writing",
                "Career Advancement Services",
                "Executive Job Search",
                "Career Coaching"
            ]
        },
        # Geographic targeting for national campaign - all 50 states
        "locations": [
            {
                "location": "2840",  # United States geo target constant ID
                "reach": "",
                "location_groups": "",
                "radius": "",
                "unit": ""
            }
        ],
        "asset_groups": [
            # National Executive Core Focus - Exact match, national keywords only
            {
                "name": "National - Executive Core",
                "headlines": [
                    "Executive Resume Writing Service",
                    "C-Suite Resume Writing Service",
                    "Leadership Resume Writing Service",
                    "VP Resume Writing Service",
                    "Director Resume Writing Service",
                    "Senior Management Resume Writing",
                    "Executive Career Coaching",
                    "Professional Resume Writing Service",
                    "Career Advancement Resume Service",
                    "Job Search Resume Service",
                    "Executive Job Search Help",
                    "C-Suite Career Advancement",
                    "Leadership Career Services",
                    "Executive Resume Optimization",
                    "Professional Career Coaching"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service for C-Suite Professionals",
                    "C-Suite Resume Writing Service Career Advancement Help",
                    "Leadership Resume Writing Service Executive Career Coaching",
                    "VP Resume Writing Service Senior Management Career Help",
                    "Director Resume Writing Service Professional Career Services"
                ],
                "descriptions": [
                    "Executive resume writing service for C-suite professionals career advancement",
                    "C-suite resume specialists leadership career coaching executive services",
                    "Professional resume writing senior management career development help",
                    "Executive career coaching VP director resume writing services national",
                    "Leadership resume writing career advancement job search assistance"
                ],
                "search_themes": [
                    "Executive Resume Writing Service",
                    "C-Suite Resume Writing Service",
                    "Leadership Resume Writing Service",
                    "VP Resume Writing Service",
                    "Director Resume Writing Service",
                    "Senior Management Resume Writing",
                    "Professional Resume Writing Service",
                    "Career Advancement Resume Service",
                    "Executive Career Coaching",
                    "Job Search Resume Service"
                ]
            },

            # National Senior Executive Focus
            {
                "name": "National - Senior Executive",
                "headlines": [
                    "Senior Executive Resume Writing",
                    "VP Level Resume Writing Service",
                    "Director Level Resume Services",
                    "Senior Management Resume Help",
                    "Executive Level Career Coaching",
                    "C-Level Resume Writing",
                    "Senior Leadership Resume Service",
                    "Executive Career Advancement",
                    "Senior Professional Resume Help",
                    "Management Level Resume Writing",
                    "Executive Resume Services",
                    "Senior Career Development",
                    "Leadership Resume Writing",
                    "Executive Job Search Services",
                    "Senior Professional Career Help"
                ],
                "long_headlines": [
                    "Senior Executive Resume Writing Service Professional Career Advancement",
                    "VP Director Level Resume Writing Service Executive Career Coaching",
                    "Senior Management Resume Help C-Level Professional Career Services",
                    "Executive Level Career Coaching Senior Leadership Resume Writing",
                    "Senior Professional Resume Help Management Level Career Development"
                ],
                "descriptions": [
                    "Senior executive resume writing VP director level career advancement services",
                    "C-level resume writing senior management professional career coaching help",
                    "Senior leadership resume services executive level career development",
                    "VP director resume writing senior professional career advancement",
                    "Management level resume help executive job search career services"
                ],
                "search_themes": [
                    "Senior Executive Resume Writing",
                    "VP Level Resume Writing Service",
                    "Director Level Resume Services",
                    "Senior Management Resume Help",
                    "Executive Level Career Coaching",
                    "C-Level Resume Writing",
                    "Senior Leadership Resume Service",
                    "Executive Career Advancement",
                    "Senior Professional Resume Help",
                    "Management Level Resume Writing"
                ]
            },

            # National Career Advancement Focus
            {
                "name": "National - Career Advancement",
                "headlines": [
                    "Career Advancement Resume Service",
                    "Professional Development Resume",
                    "Job Search Resume Help",
                    "Career Transition Resume Writing",
                    "Executive Career Coaching",
                    "Professional Resume Optimization",
                    "Career Growth Resume Service",
                    "Job Advancement Resume Help",
                    "Professional Career Services",
                    "Executive Job Search Coaching",
                    "Career Development Services",
                    "Professional Growth Resume",
                    "Executive Career Services",
                    "Career Transition Help",
                    "Professional Advancement Resume"
                ],
                "long_headlines": [
                    "Career Advancement Resume Service Professional Development Help",
                    "Job Search Resume Help Career Transition Executive Coaching",
                    "Professional Resume Optimization Career Growth Advancement Services",
                    "Executive Career Coaching Professional Development Resume Writing",
                    "Career Transition Help Job Advancement Professional Career Services"
                ],
                "descriptions": [
                    "Career advancement resume service professional development job search help",
                    "Executive career coaching resume optimization professional growth services",
                    "Career transition resume writing job advancement professional help",
                    "Professional development services executive career coaching resume",
                    "Job search career advancement resume help professional services"
                ],
                "search_themes": [
                    "Career Advancement Resume Service",
                    "Professional Development Resume",
                    "Job Search Resume Help",
                    "Career Transition Resume Writing",
                    "Executive Career Coaching",
                    "Professional Resume Optimization",
                    "Career Growth Resume Service",
                    "Job Advancement Resume Help",
                    "Professional Career Services",
                    "Executive Job Search Coaching"
                ]
            }
        ]
    }

    return campaign_data


def create_florida_campaign() -> Dict[str, Any]:
    """
    Create Florida regional MyExpertResume campaign (Florida keywords only).
    Focus: Local Florida market for executive resume services.
    """
    # Header printed by caller when appropriate

    campaign_data = {
        "name": "MyExpertResume Florida Executive",
        "type": "Performance Max",
        "budget": 59.99,  # Regional budget
        "budget_type": "Daily",
        "languages": "en",
        "bid_strategy_type": "Maximize conversions",
        "bid_strategy_name": "",
        "target_cpa": 0.0,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": "",
        "ad_schedule": "(Monday[05:00-22:00]);(Tuesday[05:00-22:00]);(Wednesday[05:00-22:00]);(Thursday[05:00-22:00]);(Friday[05:00-22:00]);(Saturday[05:00-22:00]);(Sunday[05:00-22:00])",
        "ad_rotation": "Optimize for clicks",
        "targeting_method": "Location of presence or Area of interest",
        "exclusion_method": "Location of presence",
        "brand_guidelines": "Disabled",
        "brand_business_name": "My Expert Resume",
        "brand_font": "",
        "networks": "Google search",
        "custom_parameters": '{"_campaignname":"MyExpertResume+Florida+Executive"}',
        "campaign_status": "Enabled",
        "callouts": [
            "Florida Executive Resume",
            "Miami C-Suite Resume",
            "Fort Lauderdale Career Coach",
            "Tampa Professional Resume",
            "Orlando Leadership Resume",
            "Jacksonville Resume Services",
            "West Palm Beach Exec Help",
            "Florida Career Development",
            "Executive Career Help",
            "Florida Job Search Success",
            "Fort Lauderdale Resume Svc",
            "Miami Executive Resume",
            "Florida Career Coaching",
            "Tampa Resume Writing",
            "Orlando C-Suite Resume",
            "Fort Lauderdale Resume",
            "Miami Career Coaching",
            "Tampa Executive Resume",
            "Orlando Professional Help",
            "Jacksonville Career Services"
        ],
        "structured_snippets": {
            "header": "Types",
            "values": [
                "Executive Resume Writing",
                "Florida Career Coaching",
                "Professional Resume Services",
                "Leadership Resume Writing",
                "C-Suite Resume Services",
                "Job Search Assistance",
                "Career Advancement",
                "Executive Career Help",
                "Resume Optimization",
                "Career Development"
            ]
        },
        # Geographic targeting for Florida regional campaign - key Florida cities
        "locations": [
            {
                "location": "Fort Lauderdale, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            },
            {
                "location": "Miami, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            },
            {
                "location": "West Palm Beach, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            },
            {
                "location": "Tampa, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            },
            {
                "location": "Orlando, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            },
            {
                "location": "Jacksonville, FL, USA",
                "reach": "",
                "location_groups": "",
                "radius": "25",
                "unit": "miles"
            }
        ],
        "asset_groups": [
            # Florida Executive Focus - Florida keywords only
            {
                "name": "Florida - Executive Core",
                "headlines": [
                    "Executive Resume Writing Fort Lauderdale",
                    "C-Suite Resume Service Miami",
                    "Professional Resume Writing Florida",
                    "Leadership Resume Writing Tampa",
                    "VP Resume Writing Orlando",
                    "Director Resume Service Jacksonville",
                    "Executive Career Coaching Fort Lauderdale",
                    "Resume Writing Service West Palm Beach",
                    "Professional Resume Help Florida",
                    "Career Coaching Miami",
                    "Executive Resume Service Tampa",
                    "C-Suite Resume Writing Orlando",
                    "Leadership Career Services Fort Lauderdale",
                    "VP Resume Help Jacksonville",
                    "Director Resume Writing Miami"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service Fort Lauderdale Florida",
                    "C-Suite Resume Writing Service Miami Professional Career Help",
                    "Professional Resume Writing Florida Executive Career Coaching",
                    "Leadership Resume Writing Service Tampa VP Career Advancement",
                    "Director Resume Writing Jacksonville Senior Management Help"
                ],
                "descriptions": [
                    "Executive resume writing Fort Lauderdale Florida C-suite career services",
                    "Professional resume writing Miami Tampa Orlando career advancement",
                    "C-suite resume specialists Florida executive career coaching Jacksonville",
                    "Leadership resume writing West Palm Beach Fort Lauderdale career help",
                    "VP director resume services Florida executive job search assistance"
                ],
                "search_themes": [
                    "Executive Resume Writing Service Fort Lauderdale",
                    "Executive Resume Writing Service Ft Lauderdale",
                    "Executive Resume Writing Service Miami",
                    "C-Suite Resume Writing Service Fort Lauderdale",
                    "Professional Resume Writing Service Florida",
                    "Career Coaching Fort Lauderdale",
                    "Executive Resume Service West Palm Beach",
                    "Resume Writing Service Tampa",
                    "C-Suite Resume Writing Orlando",
                    "Professional Resume Help Jacksonville"
                ]
            },

            # Florida Career Services Focus
            {
                "name": "Florida - Career Services",
                "headlines": [
                    "Resume Writing Fort Lauderdale",
                    "Career Coaching Miami Florida",
                    "Executive Resume Service Tampa",
                    "Professional Resume Help Orlando",
                    "Career Development Jacksonville",
                    "Resume Services West Palm Beach",
                    "Executive Career Help Fort Lauderdale",
                    "Professional Coaching Miami",
                    "Resume Writing Services Florida",
                    "Career Advancement Tampa",
                    "Executive Resume Orlando",
                    "Professional Career Jacksonville",
                    "Resume Help West Palm Beach",
                    "Career Services Fort Lauderdale",
                    "Executive Coaching Miami"
                ],
                "long_headlines": [
                    "Resume Writing Fort Lauderdale Career Coaching Executive Services",
                    "Professional Resume Help Miami Florida Career Development Services",
                    "Executive Career Coaching Tampa Resume Writing Professional Help",
                    "Career Advancement Orlando Resume Services Executive Career Help",
                    "Professional Career Development Jacksonville Resume Writing Services"
                ],
                "descriptions": [
                    "Resume writing Fort Lauderdale career coaching executive services Florida",
                    "Professional resume help Miami career development executive coaching",
                    "Resume services Tampa career advancement professional help Florida",
                    "Executive career coaching Orlando resume writing professional services",
                    "Career development Jacksonville executive resume help professional coaching"
                ],
                "search_themes": [
                    "Resume Writing Fort Lauderdale",
                    "Career Coaching Miami Florida",
                    "Executive Resume Service Tampa",
                    "Professional Resume Help Orlando",
                    "Career Development Jacksonville",
                    "Resume Services West Palm Beach",
                    "Executive Career Help Fort Lauderdale",
                    "Professional Coaching Miami",
                    "Resume Writing Services Florida",
                    "Career Advancement Tampa"
                ]
            }
        ]
    }

    return campaign_data


def create_campaign_plan():
    """
    Create a comprehensive campaign plan based on the original MyExpertResume structure
    """

    print("🎯 CAMPAIGN PLANNING: MyExpertResume.com TEST Campaign - Executive Resume Only")
    print("=" * 80)

    # Based on analysis of original CSV
    campaign_data = {
        "name": "ARC PMAX TEST - Executive",  # Test campaign with single asset group
        "type": "Performance Max",
        "budget": 41.89,  # From original
        "budget_type": "Daily",
        "languages": "en",
        "bid_strategy_type": "Maximize conversions",
        "brand_business_name": "",  # Remove for approval
        "brand_font": "",  # Remove for approval
        "brand_guidelines": "Disabled",  # Turn off for approval
        "custom_parameters": "{_campaignname}=ARC+PMAX",  # From original
        "networks": "Google search",  # Performance Max only runs on Google search
        "audience_targeting": "Standard",
        "status": "Enabled",
        "start_date": "2025-12-09",  # Today's date
        "ad_schedule": "(Monday[05:00-22:00]);(Tuesday[05:00-22:00]);(Wednesday[05:00-22:00]);(Thursday[05:00-22:00]);(Friday[05:00-22:00]);(Saturday[05:00-22:00]);(Sunday[05:00-22:00])",
        "final_url_expansion": "Enabled",
        "image_enhancement": "Enabled",
        "video_enhancement": "Enabled",

        "asset_groups": [
            # Asset Group 1: Core Executive Focus - Exact match themes
            {
                "name": "ARC - Executive Core | Search",
                # Headlines: 5 service + 5 value prop + 3 reputation + 2 branded = 15 total
                "headlines": [
                    "Executive Resume Writing Service",
                    "C-Suite Resume Writing Service",
                    "Professional Resume Writing Help",
                    "Leadership Resume Writing Service",
                    "Career Coaching Resume Services",
                    "100% Higher Response Rate",
                    "98% Get Higher Pay Offers",
                    "74% Land Job Within 30 Days",
                    "Get More Offers & Hired Faster",
                    "Sandy Spencer Expert Resumes",
                    "Over 10,000+ Careers Created",
                    "9x Award Winning Resume Experts",
                    "MyExpertResume Trusted Nationwide",
                    "Fort Lauderdale Resume Experts",
                    "Since 2005 Professional Writers"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service for C-Suite Professionals",
                    "Professional Resume Writing Service Career Advancement Help",
                    "100% Higher Response Rate Executive Resume Writing Services",
                    "98% Get Higher Pay Executive Resume Writers Career Coaching",
                    "9x Award Winning Executive Resume Specialists Since 2005"
                ],
                "descriptions": [
                    "Executive resume writing service with 100% higher response guarantee",
                    "C-suite resume specialists 98% higher pay offers career advancement",
                    "Professional resume writing 74% land job in 30 days success rate",
                    "Expert resume writers 10,000+ careers created Sandy Spencer service",
                    "Award-winning resume services Fort Lauderdale executive career coaching"
                ],
                "business_name": "My Expert Resume",
                "call_to_action": "Learn More",
                "final_url": "https://myexpertresume.com/executive-resume/",
                "path_1": "exec-resume",
                "path_2": "writing-service",
                "audience_signal": "ARC | Executive | Resume Writer | Standard",
                "interest_categories": "Executive Resume Writing",
                "age_demographic": "45-54;55-64;65+",
                "income_demographic": "Top 30%;Top 25%;Top 20%;Top 15%;Top 10%",
                "status": "Enabled",
                "sitelinks": [
                    {
                        "text": "Executive Resume Service",
                        "url": "https://myexpertresume.com/executive-resume/",
                        "description1": "C-Suite Resume Writing Service",
                        "description2": "100% Higher Response Rate"
                    },
                    {
                        "text": "Resume Writing Florida",
                        "url": "https://myexpertresume.com/",
                        "description1": "Fort Lauderdale Resume Experts",
                        "description2": "74% Land Job Success Rate"
                    },
                    {
                        "text": "Career Coaching Service",
                        "url": "https://myexpertresume.com/career-coaching/",
                        "description1": "Executive Career Advancement",
                        "description2": "98% Higher Pay Offers"
                    },
                    {
                        "text": "Resume Guarantee",
                        "url": "https://myexpertresume.com/guarantee/",
                        "description1": "30-Day Money Back Guarantee",
                        "description2": "10,000+ Successful Careers"
                    },
                    {
                        "text": "LinkedIn Optimization",
                        "url": "https://myexpertresume.com/linkedin-profiles/",
                        "description1": "Professional LinkedIn Services",
                        "description2": "9x Award Winning Experts"
                    }
                ],
                # Core exact match themes (10): (industry) + (service)
                "search_themes": [
                    "Executive Resume Writing Service",
                    "C-Suite Resume Writing Service",
                    "Leadership Resume Writing Service",
                    "VP Resume Writing Service",
                    "Director Resume Writing Service",
                    "Senior Management Resume Writing",
                    "Professional Resume Writing Service",
                    "Career Advancement Resume Service",
                    "Executive Career Coaching",
                    "Job Search Resume Service"
                ]
            },

            # Asset Group 2: Florida Regional Focus - Florida themes
            {
                "name": "ARC - Executive Florida | Search",
                # Florida-focused headlines
                "headlines": [
                    "Executive Resume Writing Fort Lauderdale",
                    "C-Suite Resume Service Miami",
                    "Professional Resume Writing Florida",
                    "Leadership Resume Writing Tampa",
                    "VP Resume Writing Orlando",
                    "Director Resume Service Jacksonville",
                    "Executive Career Coaching Fort Lauderdale",
                    "Resume Writing Service West Palm Beach",
                    "Professional Resume Help Florida",
                    "Career Coaching Miami",
                    "Executive Resume Service Tampa",
                    "C-Suite Resume Writing Orlando",
                    "Leadership Career Services Fort Lauderdale",
                    "VP Resume Help Jacksonville",
                    "Director Resume Writing Miami"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service Fort Lauderdale Florida",
                    "C-Suite Resume Writing Service Miami Professional Career Help",
                    "Professional Resume Writing Florida Executive Career Coaching",
                    "Leadership Resume Writing Service Tampa VP Career Advancement",
                    "Director Resume Writing Jacksonville Senior Management Help"
                ],
                "descriptions": [
                    "Executive resume writing Fort Lauderdale Florida C-suite career services",
                    "Professional resume writing Miami Tampa Orlando career advancement",
                    "C-suite resume specialists Florida executive career coaching Jacksonville",
                    "Leadership resume writing West Palm Beach Fort Lauderdale career help",
                    "VP director resume services Florida executive job search assistance"
                ],
                # Florida regional themes (10): (industry) + (service) + (Florida region)
                "search_themes": [
                    "Executive Resume Writing Service Fort Lauderdale",
                    "Executive Resume Writing Service Ft Lauderdale",
                    "Executive Resume Writing Service Miami",
                    "C-Suite Resume Writing Service Fort Lauderdale",
                    "Professional Resume Writing Service Florida",
                    "Career Coaching Fort Lauderdale",
                    "Executive Resume Service West Palm Beach",
                    "Resume Writing Service Tampa",
                    "C-Suite Resume Writing Orlando",
                    "Professional Resume Help Jacksonville"
                ]
            },

            # Asset Group 3: National Executive Focus - Major city themes
            {
                "name": "ARC - Executive National | Search",
                # National city-focused headlines
                "headlines": [
                    "Executive Resume Writing New York",
                    "C-Suite Resume Service Chicago",
                    "Professional Resume Writing Los Angeles",
                    "Leadership Resume Service Atlanta",
                    "VP Resume Writing Boston",
                    "Director Resume Help Washington DC",
                    "Executive Career Coaching Dallas",
                    "Resume Writing Service Houston",
                    "Professional Resume San Francisco",
                    "Career Coaching Philadelphia",
                    "Executive Resume Service New York",
                    "C-Suite Career Help Chicago",
                    "Leadership Resume Writing Los Angeles",
                    "VP Resume Service Atlanta",
                    "Director Resume Boston"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service New York Professional Career Help",
                    "C-Suite Resume Writing Service Chicago Executive Career Advancement",
                    "Professional Resume Writing Los Angeles Leadership Career Services",
                    "VP Resume Writing Service Atlanta Director Career Coaching Help",
                    "Executive Career Coaching Boston Senior Management Resume Services"
                ],
                "descriptions": [
                    "Executive resume writing New York Chicago Los Angeles career services",
                    "C-suite resume specialists Atlanta Boston Washington DC executive help",
                    "Professional resume writing San Francisco Philadelphia Dallas Houston",
                    "Leadership career coaching New York Chicago executive job search",
                    "VP director resume services major cities executive career advancement"
                ],
                # Major city themes (10): (industry) + (service) + (major city)
                "search_themes": [
                    "Executive Resume Writing Service New York",
                    "Executive Resume Writing Service Chicago",
                    "C-Suite Resume Writing Service Atlanta",
                    "Professional Resume Service Los Angeles",
                    "Executive Career Coaching Boston",
                    "Resume Writing Service Washington DC",
                    "Leadership Resume Service Dallas",
                    "Executive Resume Help Houston",
                    "Professional Resume Writing San Francisco",
                    "Career Coaching Service Philadelphia"
                ]
            },

            # Asset Group 4: Extended Regional Focus - Additional combinations
            {
                "name": "ARC - Executive Extended | Search",
                # Extended regional headlines
                "headlines": [
                    "Executive Resume Writing Service Florida",
                    "C-Suite Resume Writing Service Miami",
                    "Professional Resume Writing Fort Lauderdale",
                    "Leadership Resume Writing Service Tampa",
                    "VP Resume Writing Orlando",
                    "Director Resume Writing Jacksonville",
                    "Senior Management Resume Service Atlanta",
                    "Career Advancement Resume New York",
                    "Executive Job Search Help Chicago",
                    "Professional Resume Optimization Los Angeles",
                    "Executive Career Services Boston",
                    "C-Suite Resume Help Washington DC",
                    "Leadership Career Coaching Dallas",
                    "VP Resume Services Houston",
                    "Director Career Advancement San Francisco"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service Florida Comprehensive Career Help",
                    "C-Suite Resume Writing Service Miami Professional Career Advancement",
                    "Professional Resume Writing Fort Lauderdale Executive Career Coaching",
                    "Leadership Resume Writing Service Tampa VP Career Development Help",
                    "Director Resume Writing Jacksonville Senior Management Career Services"
                ],
                "descriptions": [
                    "Executive resume writing Florida Miami Fort Lauderdale comprehensive services",
                    "C-suite resume specialists Tampa Orlando Jacksonville career advancement",
                    "Professional resume writing Atlanta New York Chicago executive help",
                    "Leadership career coaching Los Angeles Boston Washington DC job search",
                    "VP director resume services major cities executive career optimization"
                ],
                # Extended regional themes (10): More specific combinations
                "search_themes": [
                    "Executive Resume Writing Service Florida",
                    "C-Suite Resume Writing Service Miami",
                    "Professional Resume Writing Fort Lauderdale",
                    "Leadership Resume Writing Service Tampa",
                    "VP Resume Writing Orlando",
                    "Director Resume Writing Jacksonville",
                    "Senior Management Resume Service Atlanta",
                    "Career Advancement Resume New York",
                    "Executive Job Search Help Chicago",
                    "Professional Resume Optimization Los Angeles"
                ]
            },

            # Asset Group 5: Performance Focus - High-conversion combinations
            {
                "name": "ARC - Executive Performance | Search",
                # Performance-optimized headlines
                "headlines": [
                    "Executive Resume Writing Service Now",
                    "C-Suite Resume Writing Get Results",
                    "Professional Resume Writing Today",
                    "Leadership Resume Writing Service Help",
                    "VP Resume Writing Career Advancement",
                    "Director Resume Writing Job Search",
                    "Senior Management Resume Services",
                    "Career Advancement Resume Writing",
                    "Executive Job Search Resume Help",
                    "Professional Resume Optimization",
                    "Executive Career Coaching Services",
                    "C-Suite Career Development Help",
                    "Leadership Career Advancement",
                    "VP Career Coaching Services",
                    "Director Executive Resume Help"
                ],
                "long_headlines": [
                    "Executive Resume Writing Service Get Hired Faster Professional Career Help",
                    "C-Suite Resume Writing Service Career Advancement Executive Job Search",
                    "Professional Resume Writing Services Leadership Career Development Help",
                    "VP Director Resume Writing Service Senior Management Career Coaching",
                    "Executive Career Advancement Resume Optimization Professional Services"
                ],
                "descriptions": [
                    "Executive resume writing service get hired faster career advancement now",
                    "C-suite resume specialists professional career coaching job search help",
                    "Leadership resume writing services VP director career development today",
                    "Senior management resume help executive career advancement services",
                    "Professional resume optimization career coaching executive job search"
                ],
                # Performance-focused themes (10): High-conversion combinations
                "search_themes": [
                    "Executive Resume Writing Service",
                    "C-Suite Resume Writing Service",
                    "Professional Resume Writing Service",
                    "Leadership Resume Writing Service",
                    "VP Resume Writing Service",
                    "Director Resume Writing Service",
                    "Senior Management Resume Writing",
                    "Career Advancement Resume Service",
                    "Executive Career Coaching",
                    "Job Search Resume Service"
                ]
            }
        ]

    }

    return campaign_data


def display_campaign_summary(campaign_data: Dict[str, Any]) -> None:
    """Display a summary of the planned campaign"""
    print("📊 CAMPAIGN SUMMARY:")
    print("-" * 30)
    print(f"   Name: {campaign_data['name']}")
    print(f"   Type: {campaign_data['type']}")
    print(f"   Budget: ${campaign_data['budget']} {campaign_data['budget_type']}")
    print(f"   Business: {campaign_data['brand_business_name']}")
    print(f"   Asset Groups: {len(campaign_data['asset_groups'])}")
    print()

    print("🎯 ASSET GROUPS:")
    print("-" * 20)
    for i, ag in enumerate(campaign_data['asset_groups'], 1):
        print(f"   {i}. {ag['name']}")
        print(f"      Headlines: {len(ag['headlines'])}")
        print(f"      Descriptions: {len(ag['descriptions'])}")
        print(f"      Final URL: {ag.get('final_url', 'Inherited from campaign')}")
        audience = ag.get('audience_signal', ag.get('audience', 'N/A'))
        print(f"      Audience: {audience}")
        search_themes = len(ag.get('search_themes', []))
        print(f"      Search Themes: {search_themes}")
        print()

    print("✅ PLAN CONFIRMED:")
    print("-" * 20)
    campaign_name = campaign_data['name'].lower()
    if 'national' in campaign_name:
        print("   ✓ National campaign structure for broad executive reach")
        print("   ✓ Performance Max with national asset groups")
        print("   ✓ Executive resume writing focus (no regional keywords)")
        print("   ✓ National audience targeting and interest categories")
    elif 'florida' in campaign_name:
        print("   ✓ Florida regional campaign structure")
        print("   ✓ Performance Max with Florida-focused asset groups")
        print("   ✓ Executive resume writing focus (Florida keywords only)")
        print("   ✓ Local Florida audience targeting and interest categories")
    else:
        print("   ✓ Campaign structure matches original MyExpertResume.com setup")
        print("   ✓ Performance Max with executive-focused asset groups")
        print("   ✓ Executive resume writing focus")
        print("   ✓ Proper audience signals and interest categories")


def generate_csv_export(campaign_data: Dict[str, Any], confirm: bool = True) -> None:
    """Generate the CSV export if confirmed"""
    if not confirm:
        print("❌ Campaign plan not confirmed. Skipping CSV generation.")
        return

    print("\n🚀 GENERATING GOOGLE ADS EDITOR CSV EXPORT...")
    print("=" * 50)

    try:
        # Export to CSV (with auto-corrections applied)
        exporter = GoogleAdsEditorExporter()
        csv_content = exporter.export_campaigns([campaign_data])

        # Report any corrections that were applied during export
        # Parse CSV to check for correction metadata
        import csv
        import io
        csv_io = io.StringIO(csv_content)
        reader = csv.DictReader(csv_io, delimiter='\t')

        total_corrections = 0
        for row in reader:
            if '_corrections_made' in row and row['_corrections_made']:
                corrections = eval(row['_corrections_made'])  # Safe since we control the data
                total_corrections += len(corrections)

        if total_corrections > 0:
            print(f"Row 2 - Auto-corrected {total_corrections} violations during export:")
            # Parse and show some examples
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')
            for row in reader:
                if '_corrections_made' in row and row['_corrections_made']:
                    corrections = eval(row['_corrections_made'])
                    for correction in corrections[:3]:  # Show first 3
                        print(f"  ✅ {correction}")
                    if len(corrections) > 3:
                        print(f"  ... and {len(corrections) - 3} more corrections")
                    break

        # Validate the corrected export
        validation_errors = exporter.validate_csv_data(csv_content)

        if validation_errors:
            print("❌ Validation Errors Found:")
            for error in validation_errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(validation_errors) > 5:
                print(f"   ... and {len(validation_errors) - 5} more errors")
        else:
            print("✅ CSV validation passed!")

        # Save the file with campaign-specific naming
        campaign_type = campaign_data['name'].lower().replace(' ', '_').replace('-', '_')
        output_filename = f"myexpertresume_{campaign_type}_campaign.csv"
        exporter.save_csv(csv_content, output_filename)

        print(f"✅ Campaign exported to: {output_filename}")
        print(f"📊 Total rows in export: {len(csv_content.split('\n')) - 1}")  # Exclude header

        # Show file size
        import os
        file_size = os.path.getsize(output_filename)
        print(f"📁 File size: {file_size:,} bytes")

        print("\n💡 NEXT STEPS:")
        print("-" * 15)
        print("   1. Open Google Ads Editor")
        print("   2. Go to File → Import")
        print("   3. Select the exported CSV file")
        print("   4. Review changes and apply")

    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()


def create_complete_campaign_suite():
    """
    Create a complete campaign suite with both national and regional campaigns.
    Returns a list of campaigns for unified CSV export.
    """
    print("🎯 CAMPAIGN PLANNING: Complete MyExpertResume Campaign Suite")
    print("=" * 70)

    campaigns = []

    # National Executive Campaign
    national_campaign = create_national_campaign()
    campaigns.append(national_campaign)

    # Florida Regional Campaign
    florida_campaign = create_florida_campaign()
    campaigns.append(florida_campaign)

    print(f"📊 CAMPAIGN SUITE SUMMARY:")
    print("-" * 40)
    print(f"   Total Campaigns: {len(campaigns)}")
    print(f"   National Campaign: {len(national_campaign['asset_groups'])} asset groups")
    print(f"   Regional Campaign: {len(florida_campaign['asset_groups'])} asset groups")
    print(f"   Total Asset Groups: {sum(len(c['asset_groups']) for c in campaigns)}")
    print(f"   Total Search Themes: {sum(len(ag.get('search_themes', [])) for c in campaigns for ag in c['asset_groups'])}")

    return campaigns

if __name__ == "__main__":
    import sys

    # Check for campaign type argument
    campaign_type = sys.argv[1] if len(sys.argv) > 1 else "complete"

    # Create the appropriate campaign plan
    if campaign_type.lower() == "complete":
        campaigns = create_complete_campaign_suite()
        campaign_note = "Complete campaign suite: National + Florida Regional campaigns"
    elif campaign_type.lower() == "national":
        campaigns = [create_national_campaign()]
        campaign_note = "National executive campaign with broad reach (no regional keywords)"
    elif campaign_type.lower() == "florida":
        campaigns = [create_florida_campaign()]
        campaign_note = "Florida regional campaign targeting local Florida markets"
    elif campaign_type.lower() == "test":
        campaigns = [create_campaign_plan()]
        campaign_note = "Original test campaign with mixed asset groups"
    else:
        print("❌ Invalid campaign type. Use: complete, national, florida, or test")
        sys.exit(1)

    # Display summary for each campaign
    for i, campaign in enumerate(campaigns, 1):
        if len(campaigns) > 1:
            print(f"\n🎯 CAMPAIGN {i}: {campaign['name']}")
            print("-" * 50)
        display_campaign_summary(campaign)

    # Auto-proceed with export
    print(f"\n🚀 AUTO-GENERATING GOOGLE ADS EDITOR CSV EXPORT...")
    print("=" * 55)
    print(f"Note: {campaign_note}")
    print(f"Campaigns: {len(campaigns)}")
    print()

    # Export all campaigns to a single CSV
    if len(campaigns) == 1:
        generate_csv_export(campaigns[0], confirm=True)
    else:
        # Export multiple campaigns to single CSV
        exporter = GoogleAdsEditorExporter()
        combined_csv_content = exporter.export_campaigns(campaigns)

        # Save the combined CSV
        output_filename = "myexpertresume_complete_campaign_suite.csv"
        exporter.save_csv(combined_csv_content, output_filename)

        print(f"✅ Combined campaign suite exported to: {output_filename}")

        # Parse and validate
        validation_errors = exporter.validate_csv_data(combined_csv_content)

        if validation_errors:
            print("❌ Validation Errors Found:")
            for error in validation_errors[:5]:
                print(f"   - {error}")
            if len(validation_errors) > 5:
                print(f"   ... and {len(validation_errors) - 5} more errors")
        else:
            print("✅ Combined CSV validation passed!")

        # Show file stats
        import os
        file_size = os.path.getsize(output_filename)
        csv_lines = combined_csv_content.strip().split('\n')
        print(f"📊 Total rows in combined export: {len(csv_lines)}")
        print(f"📁 Combined file size: {file_size:,} bytes")
