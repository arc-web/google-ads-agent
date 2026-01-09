"""
Database Models for Google Ads Campaign Management

Tracks systematic campaign creation process and performance monitoring.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# ============================================================================
# ACCOUNT & ACCESS MODELS
# ============================================================================

class GoogleAdsAccount(Base):
    """Google Ads account information and access status"""
    __tablename__ = 'google_ads_accounts'

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(20), unique=True, nullable=False, index=True)
    account_name = Column(String(255))
    access_granted = Column(Boolean, default=False)
    access_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="account")
    account_checks = relationship("AccountAccessCheck", back_populates="account")

class AccountAccessCheck(Base):
    """Tracks account access validation attempts"""
    __tablename__ = 'account_access_checks'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('google_ads_accounts.id'))
    check_timestamp = Column(DateTime, default=datetime.utcnow)
    check_result = Column(String(50))  # 'success', 'failed', 'partial'
    error_message = Column(Text)
    permissions_verified = Column(JSON)  # List of verified permissions

    # Relationships
    account = relationship("GoogleAdsAccount", back_populates="account_checks")

# ============================================================================
# BUDGET MANAGEMENT MODELS
# ============================================================================

class CampaignBudget(Base):
    """Campaign budget tracking and management"""
    __tablename__ = 'campaign_budgets'

    id = Column(Integer, primary_key=True)
    google_ads_budget_id = Column(String(100), unique=True, index=True)
    budget_name = Column(String(255), nullable=False)
    amount_micros = Column(Integer, nullable=False)
    period = Column(String(20), nullable=False)  # 'daily', 'monthly'
    delivery_method = Column(String(20), default='STANDARD')
    status = Column(String(20), default='active')  # 'active', 'paused', 'removed'

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="budget")

# ============================================================================
# CAMPAIGN MANAGEMENT MODELS
# ============================================================================

class Campaign(Base):
    """Campaign tracking and systematic creation progress"""
    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True)
    google_ads_campaign_id = Column(String(100), unique=True, index=True)
    account_id = Column(Integer, ForeignKey('google_ads_accounts.id'))
    budget_id = Column(Integer, ForeignKey('campaign_budgets.id'))

    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # 'SEARCH', 'PERFORMANCE_MAX', 'DISPLAY'
    status = Column(String(20), default='draft')  # 'draft', 'created', 'active', 'paused', 'removed'

    # Systematic creation tracking
    creation_phase = Column(String(50), default='not_started')  # Phase in systematic process
    creation_step = Column(String(100))  # Current step being executed
    creation_progress = Column(Float, default=0.0)  # 0.0 to 1.0 progress

    # Campaign configuration (stored as JSON)
    campaign_config = Column(JSON)  # Original campaign configuration
    api_config = Column(JSON)  # Google Ads API configuration used

    # Performance tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost_micros = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("GoogleAdsAccount", back_populates="campaigns")
    budget = relationship("CampaignBudget", back_populates="campaigns")
    asset_groups = relationship("AssetGroup", back_populates="campaign")
    ad_groups = relationship("AdGroup", back_populates="campaign")
    creation_logs = relationship("CampaignCreationLog", back_populates="campaign")

class CampaignCreationLog(Base):
    """Logs each step in systematic campaign creation"""
    __tablename__ = 'campaign_creation_logs'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    step_name = Column(String(100), nullable=False)
    step_phase = Column(String(50), nullable=False)
    step_status = Column(String(20), nullable=False)  # 'started', 'completed', 'failed'
    step_started_at = Column(DateTime, default=datetime.utcnow)
    step_completed_at = Column(DateTime)
    error_message = Column(Text)
    api_response = Column(JSON)  # Raw API response if successful
    metadata = Column(JSON)  # Additional step-specific data

    # Relationships
    campaign = relationship("Campaign", back_populates="creation_logs")

# ============================================================================
# ASSET GROUP MODELS (PERFORMANCE MAX)
# ============================================================================

class AssetGroup(Base):
    """Asset groups for Performance Max campaigns"""
    __tablename__ = 'asset_groups'

    id = Column(Integer, primary_key=True)
    google_ads_asset_group_id = Column(String(100), unique=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))

    asset_group_name = Column(String(255), nullable=False)
    status = Column(String(20), default='active')

    # Asset counts
    headline_count = Column(Integer, default=0)
    description_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)

    # Performance tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost_micros = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="asset_groups")
    assets = relationship("Asset", back_populates="asset_group")

class Asset(Base):
    """Individual assets within asset groups"""
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    google_ads_asset_id = Column(String(100), unique=True, index=True)
    asset_group_id = Column(Integer, ForeignKey('asset_groups.id'))

    asset_type = Column(String(50), nullable=False)  # 'HEADLINE', 'DESCRIPTION', 'IMAGE', 'VIDEO'
    asset_text = Column(Text)  # For text assets
    asset_url = Column(String(500))  # For media assets
    status = Column(String(20), default='active')

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset_group = relationship("AssetGroup", back_populates="assets")

# ============================================================================
# AD GROUP MODELS (SEARCH CAMPAIGNS)
# ============================================================================

class AdGroup(Base):
    """Ad groups for Search campaigns"""
    __tablename__ = 'ad_groups'

    id = Column(Integer, primary_key=True)
    google_ads_ad_group_id = Column(String(100), unique=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))

    ad_group_name = Column(String(255), nullable=False)
    status = Column(String(20), default='active')
    cpc_bid_micros = Column(Integer)  # Default CPC bid

    # Performance tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost_micros = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="ad_groups")
    keywords = relationship("Keyword", back_populates="ad_group")
    ads = relationship("Ad", back_populates="ad_group")

class Keyword(Base):
    """Keywords within ad groups"""
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True)
    google_ads_keyword_id = Column(String(100), unique=True, index=True)
    ad_group_id = Column(Integer, ForeignKey('ad_groups.id'))

    keyword_text = Column(String(255), nullable=False)
    match_type = Column(String(20), nullable=False)  # 'EXACT', 'PHRASE', 'BROAD'
    status = Column(String(20), default='active')
    cpc_bid_micros = Column(Integer)

    # Performance tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost_micros = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ad_group = relationship("AdGroup", back_populates="keywords")

class Ad(Base):
    """Ads within ad groups"""
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True)
    google_ads_ad_id = Column(String(100), unique=True, index=True)
    ad_group_id = Column(Integer, ForeignKey('ad_groups.id'))

    ad_type = Column(String(50), nullable=False)  # 'RESPONSIVE_SEARCH_AD', 'TEXT_AD', etc.
    status = Column(String(20), default='active')

    # Ad content (stored as JSON for flexibility)
    headlines = Column(JSON)  # List of headline texts
    descriptions = Column(JSON)  # List of description texts
    paths = Column(JSON)  # URL paths

    # Performance tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost_micros = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ad_group = relationship("AdGroup", back_populates="ads")

# ============================================================================
# SYSTEMATIC EXECUTION TRACKING
# ============================================================================

class SystematicExecution(Base):
    """Tracks complete systematic campaign creation workflows"""
    __tablename__ = 'systematic_executions'

    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, index=True)
    customer_id = Column(String(20), nullable=False)

    execution_status = Column(String(20), default='in_progress')  # 'in_progress', 'completed', 'failed'
    current_phase = Column(String(50))
    current_step = Column(String(100))

    # Progress tracking
    steps_completed = Column(JSON)  # List of completed step names
    steps_failed = Column(JSON)  # List of failed step names
    resources_created = Column(JSON)  # Resources created during execution

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Results
    final_campaign_id = Column(String(100))
    error_messages = Column(JSON)

    # Relationships (would need to be established based on actual campaigns created)
    # campaigns_created = relationship("Campaign", backref="systematic_execution")

# ============================================================================
# DATABASE SETUP
# ============================================================================

def create_database_engine(database_url: str):
    """Create SQLAlchemy database engine"""
    return create_engine(database_url, echo=False)

def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

def get_session_factory(engine):
    """Create SQLAlchemy session factory"""
    return sessionmaker(bind=engine)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def record_campaign_creation_step(campaign_id: int, step_name: str, step_phase: str,
                                step_status: str, session, error_message: str = None,
                                api_response: Dict = None, metadata: Dict = None):
    """Record a step in campaign creation process"""
    log_entry = CampaignCreationLog(
        campaign_id=campaign_id,
        step_name=step_name,
        step_phase=step_phase,
        step_status=step_status,
        error_message=error_message,
        api_response=api_response,
        metadata=metadata
    )

    if step_status in ['completed', 'failed']:
        log_entry.step_completed_at = datetime.utcnow()

    session.add(log_entry)
    session.commit()

    return log_entry

def get_campaign_creation_progress(campaign_id: int, session) -> Dict[str, Any]:
    """Get progress summary for campaign creation"""
    logs = session.query(CampaignCreationLog).filter_by(campaign_id=campaign_id).all()

    completed_steps = [log.step_name for log in logs if log.step_status == 'completed']
    failed_steps = [log.step_name for log in logs if log.step_status == 'failed']
    in_progress_steps = [log.step_name for log in logs if log.step_status == 'started']

    total_steps = len(logs)
    completed_count = len(completed_steps)
    progress_percentage = (completed_count / total_steps) * 100 if total_steps > 0 else 0

    return {
        'campaign_id': campaign_id,
        'total_steps': total_steps,
        'completed_steps': completed_steps,
        'failed_steps': failed_steps,
        'in_progress_steps': in_progress_steps,
        'progress_percentage': progress_percentage,
        'status': 'completed' if completed_count == total_steps else 'in_progress'
    }
