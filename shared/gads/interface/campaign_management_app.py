"""
Google Ads Campaign Management GUI

Systematic campaign creation interface with step-by-step validation.
Provides visual progress tracking and error handling for each phase.
"""

import streamlit as st
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from ..core.google_ads_api_service import GoogleAdsAPIService
from ..core.models import (
    get_session_factory, create_database_engine,
    record_campaign_creation_step, get_campaign_creation_progress
)

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state for campaign creation workflow"""
    if 'current_phase' not in st.session_state:
        st.session_state.current_phase = 0
    if 'phases_completed' not in st.session_state:
        st.session_state.phases_completed = []
    if 'api_service' not in st.session_state:
        st.session_state.api_service = None
    if 'customer_id' not in st.session_state:
        st.session_state.customer_id = ""
    if 'campaign_config' not in st.session_state:
        st.session_state.campaign_config = {}
    if 'creation_results' not in st.session_state:
        st.session_state.creation_results = {}

# ============================================================================
# PHASE DEFINITIONS
# ============================================================================

PHASES = [
    {
        "id": "account_validation",
        "title": "Phase 1: Account Validation",
        "description": "Validate Google Ads account access and permissions",
        "steps": ["validate_account_access"],
        "required_before": []
    },
    {
        "id": "budget_creation",
        "title": "Phase 2: Budget Management",
        "description": "Create and configure campaign budget",
        "steps": ["create_campaign_budget"],
        "required_before": ["account_validation"]
    },
    {
        "id": "campaign_creation",
        "title": "Phase 3: Campaign Creation",
        "description": "Create the main campaign structure",
        "steps": ["create_campaign"],
        "required_before": ["budget_creation"]
    },
    {
        "id": "asset_group_setup",
        "title": "Phase 4: Asset Group Configuration",
        "description": "Configure asset groups for Performance Max campaigns",
        "steps": ["create_asset_groups", "link_asset_groups"],
        "required_before": ["campaign_creation"]
    },
    {
        "id": "ad_group_setup",
        "title": "Phase 5: Ad Group & Ad Creation",
        "description": "Create ad groups, keywords, and ads for Search campaigns",
        "steps": ["create_ad_group", "add_keywords", "create_ads"],
        "required_before": ["campaign_creation"]
    }
]

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_phase_progress():
    """Render visual progress indicator for all phases"""
    st.header("📊 Campaign Creation Progress")

    cols = st.columns(len(PHASES))

    for i, phase in enumerate(PHASES):
        with cols[i]:
            # Determine phase status
            if phase["id"] in st.session_state.phases_completed:
                status_icon = "✅"
                status_color = "green"
            elif st.session_state.current_phase == i:
                status_icon = "🔄"
                status_color = "blue"
            elif all(req in st.session_state.phases_completed for req in phase["required_before"]):
                status_icon = "⏳"
                status_color = "orange"
            else:
                status_icon = "⏸️"
                status_color = "gray"

            st.markdown(f"""
            <div style='text-align: center; padding: 10px; border: 2px solid {status_color}; border-radius: 10px; margin: 5px;'>
                <div style='font-size: 24px;'>{status_icon}</div>
                <div style='font-size: 12px; font-weight: bold;'>{phase["title"].split(": ")[1]}</div>
            </div>
            """, unsafe_allow_html=True)

def render_phase_content(phase_idx: int):
    """Render the content for the current phase"""
    phase = PHASES[phase_idx]

    st.header(f"🎯 {phase['title']}")
    st.markdown(f"**{phase['description']}**")

    # Check prerequisites
    missing_prereqs = [req for req in phase["required_before"] if req not in st.session_state.phases_completed]
    if missing_prereqs:
        st.error(f"⚠️ Complete these phases first: {', '.join(missing_prereqs)}")
        return

    # Render phase-specific content
    if phase["id"] == "account_validation":
        render_account_validation_phase()
    elif phase["id"] == "budget_creation":
        render_budget_creation_phase()
    elif phase["id"] == "campaign_creation":
        render_campaign_creation_phase()
    elif phase["id"] == "asset_group_setup":
        render_asset_group_phase()
    elif phase["id"] == "ad_group_setup":
        render_ad_group_phase()

def render_account_validation_phase():
    """Phase 1: Account validation"""
    st.subheader("🔐 Account Access Validation")

    customer_id = st.text_input(
        "Google Ads Customer ID",
        value=st.session_state.customer_id,
        placeholder="123-456-7890",
        help="Your Google Ads customer ID (with or without dashes)"
    )

    config_path = st.text_input(
        "Google Ads Config Path",
        value="path/to/google-ads.yaml",
        help="Path to your google-ads.yaml configuration file"
    )

    if st.button("🔍 Validate Account Access", type="primary"):
        if not customer_id:
            st.error("Please enter a Customer ID")
            return

        try:
            with st.spinner("Validating account access..."):
                # Initialize API service
                api_service = GoogleAdsAPIService(config_path)
                result = api_service.validate_account_access(customer_id.replace('-', ''))

                st.success(f"✅ Account access validated: {result['account_name']}")

                # Update session state
                st.session_state.api_service = api_service
                st.session_state.customer_id = customer_id.replace('-', '')
                st.session_state.phases_completed.append("account_validation")
                st.session_state.current_phase = 1

                st.rerun()

        except Exception as e:
            st.error(f"❌ Account validation failed: {str(e)}")

def render_budget_creation_phase():
    """Phase 2: Budget creation"""
    st.subheader("💰 Campaign Budget Setup")

    col1, col2 = st.columns(2)

    with col1:
        budget_name = st.text_input(
            "Budget Name",
            value=f"Budget - {datetime.now().strftime('%Y-%m-%d')}",
            help="Descriptive name for the budget"
        )

        budget_amount = st.number_input(
            "Daily Budget ($)",
            min_value=5.0,
            max_value=10000.0,
            value=89.99,
            step=1.0,
            help="Daily budget amount in USD"
        )

    with col2:
        budget_period = st.selectbox(
            "Budget Period",
            ["daily", "monthly"],
            help="Budget delivery period"
        )

        budget_delivery = st.selectbox(
            "Delivery Method",
            ["STANDARD", "ACCELERATED"],
            help="How quickly to spend the budget"
        )

    if st.button("💰 Create Budget", type="primary"):
        if not budget_name or budget_amount <= 0:
            st.error("Please provide a budget name and valid amount")
            return

        try:
            with st.spinner("Creating campaign budget..."):
                budget_data = {
                    'name': budget_name,
                    'amount_micros': int(budget_amount * 1000000),  # Convert to micros
                    'period': budget_period
                }

                result = st.session_state.api_service.create_campaign_budget(budget_data)

                st.success(f"✅ Budget created: {result['budget_id']} (${budget_amount}/{budget_period})")

                # Store budget info for next phase
                st.session_state.campaign_config['budget'] = budget_data
                st.session_state.campaign_config['budget_id'] = result['budget_id']

                # Update progress
                st.session_state.phases_completed.append("budget_creation")
                st.session_state.current_phase = 2

                st.rerun()

        except Exception as e:
            st.error(f"❌ Budget creation failed: {str(e)}")

def render_campaign_creation_phase():
    """Phase 3: Campaign creation"""
    st.subheader("🚀 Campaign Creation")

    col1, col2 = st.columns(2)

    with col1:
        campaign_name = st.text_input(
            "Campaign Name",
            value=f"Campaign - {datetime.now().strftime('%Y-%m-%d')}",
            help="Descriptive campaign name"
        )

        campaign_type = st.selectbox(
            "Campaign Type",
            ["SEARCH", "PERFORMANCE_MAX", "DISPLAY"],
            help="Type of Google Ads campaign"
        )

    with col2:
        target_cpa = st.number_input(
            "Target CPA ($)",
            min_value=0.1,
            max_value=1000.0,
            value=25.0,
            step=1.0,
            help="Target cost per acquisition (optional)"
        )

        status = st.selectbox(
            "Initial Status",
            ["PAUSED", "ENABLED"],
            help="Campaign status after creation"
        )

    # Geographic targeting
    st.subheader("📍 Geographic Targeting")
    col1, col2 = st.columns(2)

    with col1:
        use_national = st.checkbox("Target United States (National)", value=True)
        florida_radius = st.number_input(
            "Florida Radius (miles)",
            min_value=0,
            max_value=500,
            value=25,
            help="Radius around Florida for targeting"
        )

    if st.button("🚀 Create Campaign", type="primary"):
        if not campaign_name:
            st.error("Please provide a campaign name")
            return

        try:
            with st.spinner("Creating campaign..."):
                campaign_data = {
                    'name': campaign_name,
                    'type': campaign_type,
                    'status': status
                }

                if target_cpa > 0:
                    campaign_data['target_cpa'] = target_cpa

                # Geographic targeting
                locations = []
                if use_national:
                    locations.append("2840")  # United States
                if florida_radius > 0:
                    # Would need to implement Florida city targeting
                    pass

                campaign_data['locations'] = locations

                result = st.session_state.api_service.create_campaign(
                    campaign_data,
                    st.session_state.campaign_config['budget_id']
                )

                st.success(f"✅ Campaign created: {result['campaign_id']} ({campaign_type})")

                # Store campaign info
                st.session_state.campaign_config['campaign'] = campaign_data
                st.session_state.campaign_config['campaign_id'] = result['campaign_id']

                # Update progress
                st.session_state.phases_completed.append("campaign_creation")

                # Determine next phase based on campaign type
                if campaign_type == "PERFORMANCE_MAX":
                    st.session_state.current_phase = 3  # Asset groups
                else:
                    st.session_state.current_phase = 4  # Ad groups

                st.rerun()

        except Exception as e:
            st.error(f"❌ Campaign creation failed: {str(e)}")

def render_asset_group_phase():
    """Phase 4: Asset group configuration for Performance Max"""
    st.subheader("🎨 Asset Group Configuration")

    campaign_type = st.session_state.campaign_config.get('campaign', {}).get('type')
    if campaign_type != "PERFORMANCE_MAX":
        st.info("Asset groups are only needed for Performance Max campaigns. Skipping to next phase.")
        st.session_state.current_phase = 4  # Skip to ad groups
        st.rerun()
        return

    st.markdown("**Performance Max campaigns use asset groups instead of traditional ad groups.**")

    # Asset group configuration
    num_asset_groups = st.number_input(
        "Number of Asset Groups",
        min_value=1,
        max_value=10,
        value=1,
        help="How many asset groups to create"
    )

    asset_groups = []
    for i in range(num_asset_groups):
        st.markdown(f"### Asset Group {i+1}")

        col1, col2 = st.columns(2)
        with col1:
            ag_name = st.text_input(
                f"Asset Group {i+1} Name",
                value=f"Asset Group {i+1}",
                key=f"ag_name_{i}"
            )

        with col2:
            target_audience = st.selectbox(
                f"Target Audience {i+1}",
                ["General", "High Intent", "Remarketing", "Competitors"],
                key=f"audience_{i}"
            )

        # Headlines
        st.markdown("**Headlines** (3-5 recommended)")
        headlines = []
        for j in range(5):
            headline = st.text_input(
                f"Headline {j+1}",
                value="",
                max_chars=30,
                key=f"headline_{i}_{j}",
                placeholder=f"Compelling headline {j+1}"
            )
            if headline.strip():
                headlines.append(headline)

        # Descriptions
        st.markdown("**Descriptions** (2-3 recommended)")
        descriptions = []
        for j in range(3):
            desc = st.text_area(
                f"Description {j+1}",
                value="",
                max_chars=80,
                key=f"desc_{i}_{j}",
                placeholder=f"Persuasive description {j+1}"
            )
            if desc.strip():
                descriptions.append(desc)

        if headlines and descriptions:
            asset_groups.append({
                'name': ag_name,
                'headlines': headlines,
                'descriptions': descriptions,
                'target_audience': target_audience
            })

    if st.button("🎨 Create Asset Groups", type="primary"):
        if not asset_groups:
            st.error("Please configure at least one asset group with headlines and descriptions")
            return

        try:
            with st.spinner("Creating asset groups..."):
                created_groups = []

                for ag_data in asset_groups:
                    result = st.session_state.api_service.create_asset_group(
                        st.session_state.campaign_config['campaign_id'],
                        ag_data
                    )
                    created_groups.append(result)

                st.success(f"✅ Created {len(created_groups)} asset groups")

                # Store asset groups
                st.session_state.campaign_config['asset_groups'] = asset_groups

                # Update progress
                st.session_state.phases_completed.append("asset_group_setup")
                st.session_state.current_phase = 5  # Complete

                st.rerun()

        except Exception as e:
            st.error(f"❌ Asset group creation failed: {str(e)}")

def render_ad_group_phase():
    """Phase 5: Ad group creation for Search campaigns"""
    st.subheader("📢 Ad Group & Ad Creation")

    campaign_type = st.session_state.campaign_config.get('campaign', {}).get('type')
    if campaign_type == "PERFORMANCE_MAX":
        st.info("Search campaigns use ad groups. Performance Max campaigns use asset groups.")
        st.session_state.current_phase = 5  # Complete
        st.rerun()
        return

    # Ad group configuration
    ad_group_name = st.text_input(
        "Ad Group Name",
        value="Main Ad Group",
        help="Name for the ad group"
    )

    cpc_bid = st.number_input(
        "Default CPC Bid ($)",
        min_value=0.01,
        max_value=50.0,
        value=2.0,
        step=0.1,
        help="Default cost-per-click bid"
    )

    # Keywords
    st.markdown("**Keywords**")
    keywords_input = st.text_area(
        "Keywords (one per line)",
        value="",
        height=100,
        help="Enter keywords, one per line. Use quotes for phrase match."
    )

    # Ad configuration
    st.markdown("**Ad Configuration**")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Headlines** (3-5 recommended)")
        ad_headlines = []
        for i in range(5):
            headline = st.text_input(
                f"Headline {i+1}",
                value="",
                max_chars=30,
                key=f"ad_headline_{i}",
                placeholder=f"Compelling headline {i+1}"
            )
            if headline.strip():
                ad_headlines.append(headline)

    with col2:
        st.markdown("**Descriptions** (2-3 recommended)")
        ad_descriptions = []
        for i in range(3):
            desc = st.text_area(
                f"Description {i+1}",
                value="",
                max_chars=80,
                key=f"ad_desc_{i}",
                placeholder=f"Persuasive description {i+1}"
            )
            if desc.strip():
                ad_descriptions.append(desc)

    # URL paths
    col1, col2 = st.columns(2)
    with col1:
        path1 = st.text_input("Path 1", value="", placeholder="resume-services")
    with col2:
        path2 = st.text_input("Path 2", value="", placeholder="executive")

    if st.button("📢 Create Ad Group & Ads", type="primary"):
        if not ad_group_name:
            st.error("Please provide an ad group name")
            return

        if not ad_headlines or not ad_descriptions:
            st.error("Please provide at least one headline and one description")
            return

        keywords_list = [k.strip() for k in keywords_input.split('\n') if k.strip()]
        if not keywords_list:
            st.error("Please provide at least one keyword")
            return

        try:
            with st.spinner("Creating ad group, keywords, and ads..."):
                # Create ad group
                ad_group_data = {
                    'name': ad_group_name,
                    'cpc_bid': cpc_bid
                }

                ad_group_result = st.session_state.api_service.create_ad_group(
                    st.session_state.campaign_config['campaign_id'],
                    ad_group_data
                )

                # Add keywords
                keywords_result = st.session_state.api_service.create_keywords(
                    ad_group_result['ad_group_id'],
                    keywords_list
                )

                # Create ad
                ad_data = {
                    'headlines': ad_headlines,
                    'descriptions': ad_descriptions,
                    'path1': path1 if path1 else None,
                    'path2': path2 if path2 else None
                }

                ad_result = st.session_state.api_service.create_responsive_search_ad(
                    ad_group_result['ad_group_id'],
                    ad_data
                )

                st.success("✅ Complete ad setup created!"                st.markdown(f"""
                - **Ad Group**: {ad_group_result['ad_group_id']}
                - **Keywords**: {keywords_result['keywords_created']} added
                - **Ad**: {ad_result['ad_id']} created
                """)

                # Store configuration
                st.session_state.campaign_config['ad_group'] = ad_group_data
                st.session_state.campaign_config['keywords'] = keywords_list
                st.session_state.campaign_config['ad'] = ad_data

                # Update progress
                st.session_state.phases_completed.append("ad_group_setup")
                st.session_state.current_phase = 5  # Complete

                st.rerun()

        except Exception as e:
            st.error(f"❌ Ad setup failed: {str(e)}")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Google Ads Campaign Manager",
        page_icon="🚀",
        layout="wide"
    )

    st.title("🚀 Google Ads Systematic Campaign Manager")
    st.markdown("""
    Create Google Ads campaigns systematically with step-by-step validation.
    Each phase must be completed successfully before proceeding to the next.
    """)

    # Initialize session state
    init_session_state()

    # Render progress indicator
    render_phase_progress()

    # Render current phase content
    if st.session_state.current_phase < len(PHASES):
        render_phase_content(st.session_state.current_phase)
    else:
        # Campaign creation complete
        render_completion_summary()

    # Sidebar with campaign summary
    render_sidebar_summary()

def render_completion_summary():
    """Render completion summary when all phases are done"""
    st.header("🎉 Campaign Creation Complete!")

    st.success("✅ Your Google Ads campaign has been created successfully!")

    # Display results
    config = st.session_state.campaign_config

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Campaign Summary")
        st.markdown(f"""
        - **Customer ID**: {st.session_state.customer_id}
        - **Campaign ID**: {config.get('campaign_id', 'N/A')}
        - **Budget ID**: {config.get('budget_id', 'N/A')}
        - **Type**: {config.get('campaign', {}).get('type', 'N/A')}
        - **Status**: Active
        """)

    with col2:
        st.subheader("📈 Next Steps")
        st.markdown("""
        1. **Review in Google Ads** - Check your campaign in the Google Ads interface
        2. **Monitor Performance** - Track impressions, clicks, and conversions
        3. **Optimize Bids** - Adjust bids based on performance data
        4. **Add More Assets** - Expand with additional headlines/descriptions
        5. **Scale Budget** - Increase budget as performance improves
        """)

    if st.button("🔄 Create Another Campaign"):
        # Reset session state for new campaign
        for key in list(st.session_state.keys()):
            if key != 'api_service':  # Keep API service initialized
                del st.session_state[key]
        init_session_state()
        st.rerun()

def render_sidebar_summary():
    """Render sidebar with current campaign summary"""
    with st.sidebar:
        st.header("📋 Current Campaign")

        if st.session_state.customer_id:
            st.markdown(f"**Customer ID**: {st.session_state.customer_id}")

        config = st.session_state.campaign_config

        if config.get('budget'):
            budget = config['budget']
            st.markdown(f"**Budget**: ${budget['amount_micros']/1000000:.2f}/{budget['period']}")

        if config.get('campaign'):
            campaign = config['campaign']
            st.markdown(f"**Campaign**: {campaign['name']}")
            st.markdown(f"**Type**: {campaign['type']}")

        if config.get('campaign_id'):
            st.markdown(f"**Campaign ID**: {config['campaign_id']}")

        # Phase completion status
        st.markdown("---")
        st.markdown("**Phase Status**")
        for phase in PHASES:
            status = "✅" if phase["id"] in st.session_state.phases_completed else "⏳"
            st.markdown(f"{status} {phase['title'].split(': ')[1]}")

if __name__ == "__main__":
    main()
