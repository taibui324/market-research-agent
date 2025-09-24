from typing import TypedDict, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from typing import NotRequired, Required
except ImportError:
    # For Python < 3.11 compatibility
    from typing_extensions import NotRequired, Required

from backend.services.websocket_manager import WebSocketManager

# Competitor data structure
class CompetitorData(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    hq_location: NotRequired[str]

# Main company with competitors structure
class CompanyWithCompetitors(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    industry: NotRequired[str]
    hq_location: NotRequired[str]
    competitors: NotRequired[List[CompetitorData]]

# Define the input state for main company with competitors
class InputState(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    hq_location: NotRequired[str]
    industry: NotRequired[str]
    competitors: NotRequired[List[CompetitorData]]
    websocket_manager: NotRequired[WebSocketManager]
    job_id: NotRequired[str]

# Data models for 3C analysis
@dataclass
class ConsumerInsight:
    """Data model for consumer insights from social media, reviews, and forums"""
    insight_id: str
    source: str
    content: str
    sentiment: float
    pain_point: Optional[str]
    need_category: str
    confidence_score: float
    timestamp: datetime

@dataclass
class MarketTrend:
    """Data model for market trends and consumer behavior patterns"""
    trend_id: str
    trend_name: str
    description: str
    growth_rate: Optional[float]
    adoption_stage: str  # emerging, growing, mature, declining
    impact_level: str    # high, medium, low
    time_horizon: str    # short, medium, long
    sources: List[str]

@dataclass
class CompetitorProfile:
    """Data model for competitor analysis and market positioning"""
    competitor_id: str
    company_name: str
    market_share: Optional[float]
    key_products: List[str]
    strengths: List[str]
    weaknesses: List[str]
    positioning: str
    target_segments: List[str]

@dataclass
class MarketOpportunity:
    """Data model for identified market opportunities and white spaces"""
    opportunity_id: str
    title: str
    description: str
    market_size: Optional[str]
    competition_level: str  # low, medium, high
    consumer_demand: str    # low, medium, high
    alignment_score: float  # how well it aligns with company capabilities
    priority: str           # high, medium, low
    recommendations: List[str]

class ResearchState(InputState):
    site_scrape: Dict[str, Any]
    messages: List[Any]
    financial_data: Dict[str, Any]
    news_data: Dict[str, Any]
    industry_data: Dict[str, Any]
    company_data: Dict[str, Any]
    curated_financial_data: Dict[str, Any]
    curated_news_data: Dict[str, Any]
    curated_industry_data: Dict[str, Any]
    curated_company_data: Dict[str, Any]
    financial_briefing: str
    news_briefing: str
    industry_briefing: str
    company_briefing: str
    references: List[str]
    briefings: Dict[str, Any]
    companies_data: Dict[str, Any]  # Processed company data for SWOT analysis
    swot_analyses: Dict[str, Any]  # SWOT analysis results
    report: str

class MarketResearchState(ResearchState):
    """Enhanced state management for 3C analysis extending existing ResearchState"""
    
    # Consumer Analysis Data
    consumer_insights: Dict[str, Any]
    customer_personas: List[Dict[str, Any]]
    pain_points: List[str]
    purchase_journey: Dict[str, Any]
    
    # Trend Analysis Data
    market_trends: Dict[str, Any]
    trend_predictions: List[Dict[str, Any]]
    adoption_curves: Dict[str, Any]
    
    # Competitor Analysis Data
    competitor_landscape: Dict[str, Any]
    competitive_positioning: Dict[str, Any]
    feature_comparisons: List[Dict[str, Any]]
    market_gaps: List[str]
    
    # Opportunity Analysis Data
    opportunities: List[Dict[str, Any]]
    white_spaces: List[Dict[str, Any]]
    recommendations: List[str]
    
    # Market Focus and Segmentation Fields
    target_market: str  # "japanese_curry" for initial implementation
    market_segment: str
    analysis_type: str  # "3c_analysis"
    market_focus_keywords: List[str]