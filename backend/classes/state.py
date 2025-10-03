from typing import TypedDict, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from typing import NotRequired, Required
except ImportError:
    # For Python < 3.11 compatibility
    from typing_extensions import NotRequired, Required

from typing_extensions import Annotated

from backend.services.websocket_manager import WebSocketManager

# Competitor data structure
class CompetitorData(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    hq_location: NotRequired[str]
    industry: NotRequired[str]
    product_category: NotRequired[str]

# Main company with competitors structure
class CompanyWithCompetitors(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    industry: NotRequired[str]
    hq_location: NotRequired[str]
    product_category: NotRequired[str]
    competitors: NotRequired[List[CompetitorData]]

# Define the input state for main company with competitors
class InputState(TypedDict, total=False):
    company: Required[str]  # Keep as simple str to avoid concurrent update issues
    company_url: NotRequired[str]
    hq_location: NotRequired[str]
    industry: NotRequired[str]
    product_category: NotRequired[str]
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


class CustomerMappingResult(TypedDict):
    """Individual consumer need/trend mapping result with cluster analysis."""
    
    cluster: Annotated[str, ..., "Consumer behavior cluster category (e.g., Quality, Convenience, Price, Sustainability, Digital)"]
    key_insights: Annotated[str, ..., "Key insights and implications about this consumer behavior or trend"]
    frequency: Annotated[int, ..., "Number of posts/mentions found for this consumer need or trend"]
    notes: Annotated[str, ..., "Notes about this consumer need or trend"]

class CustomerMappingTrendSummary(TypedDict):
    """Monthly or periodic trend summary for consumer behavior analysis."""
    
    start_date: Annotated[datetime, ..., "Start date of the trend analysis period"]
    end_date: Annotated[datetime, ..., "End date of the trend analysis period"]
    trend_highlights: Annotated[str, ..., "Key trend highlights and developments during this period"]

class CustomerMappingResults(TypedDict):
    """Complete customer mapping analysis results with trends and consumer insights."""
    
    start_date: Annotated[datetime, ..., "Start date of the trend analysis period"]
    end_date: Annotated[datetime, ..., "End date of the trend analysis period"]
    trend_summaries: Annotated[List[CustomerMappingTrendSummary], ..., "List of trend summaries covering different time periods"]
    consumer_insights: Annotated[List[CustomerMappingResult], ..., "List of clustered consumer needs and trends with frequency analysis"]

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
    customer_mapping_results: CustomerMappingResults
    financial_briefing: str
    news_briefing: str
    industry_briefing: str
    company_briefing: str
    references: List[str]
    briefings: Dict[str, Any]
    companies_data: Dict[str, Any]  # Processed company data for SWOT analysis
    swot_analyses: Dict[str, Any]  # SWOT analysis results
    competitor_analyses: Dict[str, Any]  # Competitor analysis results
    competitor_analysis_content: str  # Raw competitor analysis content
    competitor_analysis_structured: Dict[str, Any]  # Structured competitor analysis data
    competitor_analysis_metrics: Dict[str, Any]  # Competitor analysis metrics
    report: str
    consumer_insights_data: Dict[str, Any]
    customer_mapping_integration: Dict[str, Any]

class MarketResearchState(ResearchState):
    """Enhanced state management for 3C analysis extending existing ResearchState"""
    
    # Consumer Analysis Data
    consumer_insights: Annotated[Dict[str, Any], "Consumer insights and analysis results"]
    customer_personas: Annotated[List[Dict[str, Any]], "Customer persona profiles"]
    pain_points: Annotated[List[str], "Identified consumer pain points"]
    purchase_journey: Annotated[Dict[str, Any], "Consumer purchase journey mapping"]
    
    # Trend Analysis Data
    market_trends: Annotated[Dict[str, Any], "Market trends and patterns"]
    trend_predictions: Annotated[List[Dict[str, Any]], "Future trend predictions"]
    adoption_curves: Annotated[Dict[str, Any], "Technology adoption curves"]
    
    # Competitor Analysis Data
    competitor_landscape: Annotated[Dict[str, Any], "Competitive landscape analysis"]
    competitive_positioning: Annotated[Dict[str, Any], "Competitive positioning data"]
    feature_comparisons: Annotated[List[Dict[str, Any]], "Feature comparison matrices"]
    market_gaps: Annotated[List[str], "Identified market gaps"]
    
    # Opportunity Analysis Data
    opportunities: Annotated[List[Dict[str, Any]], "Market opportunities identified"]
    white_spaces: Annotated[List[Dict[str, Any]], "White space opportunities"]
    recommendations: Annotated[List[str], "Strategic recommendations"]
    
    # Market Focus and Segmentation Fields
    target_market: Annotated[str, "Target market for analysis"]  # "japanese_curry" for initial implementation
    market_segment: Annotated[str, "Specific market segment"]
    analysis_type: Annotated[str, "Type of analysis being performed"]  # "3c_analysis"
    market_focus_keywords: Annotated[List[str], "Keywords for market focus"]