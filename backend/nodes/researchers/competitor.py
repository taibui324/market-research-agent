"""
CompetitorAnalysisAgent for market research workflow.
Integrates with MarketResearchState to provide comprehensive competitive analysis.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.classes.state import MarketResearchState
from .base import BaseResearcher

logger = logging.getLogger(__name__)


class CompetitorAnalysisAgent(BaseResearcher):
    """
    Specialized agent for competitor analysis within the 3C framework.
    Analyzes competitor landscape, positioning, and feature comparisons.
    """
    
    def __init__(self):
        super().__init__()
        self.analyst_type = "competitor_analysis"
        
    async def analyze_competitor_landscape(self, state: MarketResearchState) -> Dict[str, Any]:
        """Analyze the competitive landscape for the target market."""
        target_market = state.get('target_market', 'japanese_curry')
        market_segment = state.get('market_segment', 'general')
        
        logger.info(f"Analyzing competitor landscape for {target_market} market")
        
        try:
            # Get curated competitor data from the market data pipeline
            competitor_data = state.get('curated_competitor_raw_data', {})
            
            if not competitor_data:
                logger.warning("No curated competitor data available for analysis")
                return self._create_empty_competitor_landscape()
            
            # Generate competitor-focused queries
            queries = await self.generate_competitor_queries(state)
            
            # If we have market data from the pipeline, use it; otherwise search
            if competitor_data:
                landscape_data = competitor_data
            else:
                # Search for additional competitor data
                landscape_data = await self.search_documents(state, queries)
            
            # Analyze competitor landscape
            landscape_analysis = await self._analyze_landscape_data(landscape_data, state)
            
            logger.info("Competitor landscape analysis completed successfully")
            return landscape_analysis
            
        except Exception as e:
            logger.error(f"Error in competitor landscape analysis: {e}")
            return self._create_empty_competitor_landscape()
    
    async def generate_competitor_queries(self, state: MarketResearchState) -> List[str]:
        """Generate targeted queries for competitor analysis."""
        target_market = state.get('target_market', 'japanese_curry')
        market_segment = state.get('market_segment', 'general')
        
        base_queries = [
            f"{target_market} competitors brands market share",
            f"{target_market} leading companies analysis",
            f"{target_market} competitive landscape overview",
            f"{target_market} market leaders comparison",
            f"{target_market} brand positioning strategies"
        ]
        
        # Add market focus keywords if available
        focus_keywords = state.get('market_focus_keywords', [])
        for keyword in focus_keywords[:3]:  # Limit to avoid too many queries
            base_queries.append(f"{target_market} {keyword} competitors")
        
        return base_queries
    
    async def analyze_competitive_positioning(self, state: MarketResearchState) -> Dict[str, Any]:
        """Analyze competitive positioning and differentiation strategies."""
        target_market = state.get('target_market', 'japanese_curry')
        
        logger.info(f"Analyzing competitive positioning for {target_market} market")
        
        try:
            # Get competitor landscape data
            landscape_data = state.get('competitor_landscape', {})
            
            if not landscape_data or landscape_data.get('status') == 'failed':
                logger.warning("No competitor landscape data available for positioning analysis")
                return self._create_empty_positioning_analysis()
            
            # Analyze positioning strategies
            positioning_analysis = await self._analyze_positioning_strategies(landscape_data, state)
            
            logger.info("Competitive positioning analysis completed successfully")
            return positioning_analysis
            
        except Exception as e:
            logger.error(f"Error in competitive positioning analysis: {e}")
            return self._create_empty_positioning_analysis()
    
    async def generate_feature_comparisons(self, state: MarketResearchState) -> List[Dict[str, Any]]:
        """Generate feature comparison matrices for competitors."""
        target_market = state.get('target_market', 'japanese_curry')
        
        logger.info(f"Generating feature comparisons for {target_market} market")
        
        try:
            # Get competitor data
            competitor_landscape = state.get('competitor_landscape', {})
            
            if not competitor_landscape or competitor_landscape.get('status') == 'failed':
                logger.warning("No competitor data available for feature comparison")
                return []
            
            # Generate feature comparison matrix
            feature_comparisons = await self._create_feature_matrix(competitor_landscape, state)
            
            logger.info(f"Generated {len(feature_comparisons)} feature comparison entries")
            return feature_comparisons
            
        except Exception as e:
            logger.error(f"Error in feature comparison generation: {e}")
            return []
    
    async def identify_market_gaps(self, state: MarketResearchState) -> List[str]:
        """Identify market gaps and white space opportunities."""
        target_market = state.get('target_market', 'japanese_curry')
        
        logger.info(f"Identifying market gaps for {target_market} market")
        
        try:
            # Get analysis data
            competitor_landscape = state.get('competitor_landscape', {})
            consumer_insights = state.get('consumer_insights', {})
            pain_points = state.get('pain_points', [])
            
            # Identify gaps by comparing consumer needs with competitor offerings
            market_gaps = await self._analyze_market_gaps(
                competitor_landscape, consumer_insights, pain_points, state
            )
            
            logger.info(f"Identified {len(market_gaps)} market gaps")
            return market_gaps
            
        except Exception as e:
            logger.error(f"Error in market gap identification: {e}")
            return []
    
    async def _analyze_landscape_data(self, landscape_data: Dict[str, Any], state: MarketResearchState) -> Dict[str, Any]:
        """Analyze competitor landscape data to extract key insights."""
        target_market = state.get('target_market', 'japanese_curry')
        
        # Extract competitor information from the data
        competitors = []
        market_share_data = {}
        key_players = []
        
        # Process each document in the landscape data
        for doc_id, doc in landscape_data.items():
            content = doc.get('content', '')
            title = doc.get('title', '')
            
            # Extract competitor names and market information
            extracted_competitors = self._extract_competitor_names(content, title, target_market)
            competitors.extend(extracted_competitors)
            
            # Extract market share information
            market_shares = self._extract_market_share_data(content)
            market_share_data.update(market_shares)
            
            # Extract key players
            players = self._extract_key_players(content, target_market)
            key_players.extend(players)
        
        # Remove duplicates and structure data
        unique_competitors = list(set(competitors))
        unique_key_players = list(set(key_players))
        
        return {
            'competitors': unique_competitors[:10],  # Limit to top 10
            'key_players': unique_key_players[:5],   # Limit to top 5
            'market_share_data': market_share_data,
            'total_competitors_found': len(unique_competitors),
            'analysis_timestamp': datetime.now().isoformat(),
            'target_market': target_market,
            'data_sources': len(landscape_data)
        }
    
    async def _analyze_positioning_strategies(self, landscape_data: Dict[str, Any], state: MarketResearchState) -> Dict[str, Any]:
        """Analyze competitive positioning strategies."""
        target_market = state.get('target_market', 'japanese_curry')
        
        positioning_strategies = {}
        brand_positions = {}
        differentiation_factors = []
        
        competitors = landscape_data.get('competitors', [])
        
        # Analyze positioning for each competitor
        for competitor in competitors[:5]:  # Analyze top 5 competitors
            positioning_strategies[competitor] = {
                'market_position': self._determine_market_position(competitor, target_market),
                'key_differentiators': self._identify_differentiators(competitor, target_market),
                'target_segments': self._identify_target_segments(competitor, target_market)
            }
        
        return {
            'positioning_strategies': positioning_strategies,
            'market_positioning_map': self._create_positioning_map(competitors),
            'differentiation_factors': list(set(differentiation_factors)),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def _create_feature_matrix(self, competitor_landscape: Dict[str, Any], state: MarketResearchState) -> List[Dict[str, Any]]:
        """Create feature comparison matrix."""
        competitors = competitor_landscape.get('competitors', [])
        target_market = state.get('target_market', 'japanese_curry')
        
        # Define key features to compare (market-specific)
        if target_market == 'japanese_curry':
            key_features = [
                'spice_levels', 'price_range', 'product_variety', 'availability',
                'brand_recognition', 'product_quality', 'packaging', 'convenience'
            ]
        else:
            key_features = [
                'price_range', 'product_variety', 'quality', 'availability',
                'brand_recognition', 'innovation', 'customer_service'
            ]
        
        feature_comparisons = []
        
        for competitor in competitors[:5]:  # Limit to top 5 competitors
            comparison = {
                'competitor': competitor,
                'features': {},
                'overall_rating': 'medium',  # Placeholder
                'strengths': [],
                'weaknesses': []
            }
            
            # Analyze each feature (placeholder implementation)
            for feature in key_features:
                comparison['features'][feature] = {
                    'rating': 'medium',  # Placeholder
                    'notes': f"Analysis of {competitor}'s {feature}"
                }
            
            feature_comparisons.append(comparison)
        
        return feature_comparisons
    
    async def _analyze_market_gaps(self, competitor_landscape: Dict[str, Any], 
                                 consumer_insights: Dict[str, Any], 
                                 pain_points: List[str], 
                                 state: MarketResearchState) -> List[str]:
        """Analyze market gaps by comparing consumer needs with competitor offerings."""
        target_market = state.get('target_market', 'japanese_curry')
        
        market_gaps = []
        
        # Analyze pain points not addressed by competitors
        for pain_point in pain_points[:5]:  # Analyze top 5 pain points
            if not self._is_pain_point_addressed_by_competitors(pain_point, competitor_landscape):
                market_gaps.append(f"Unaddressed consumer pain point: {pain_point}")
        
        # Identify feature gaps
        competitors = competitor_landscape.get('competitors', [])
        if len(competitors) > 0:
            market_gaps.extend([
                "Premium product positioning gap",
                "Convenience-focused product gap",
                "Health-conscious product options gap",
                "Digital-first brand experience gap"
            ])
        
        return market_gaps
    
    def _extract_competitor_names(self, content: str, title: str, target_market: str) -> List[str]:
        """Extract competitor names from content."""
        competitors = []
        
        # Market-specific competitor patterns
        if target_market == 'japanese_curry':
            patterns = [
                r'(?:house\s+foods?|golden\s+curry|vermont\s+curry|java\s+curry)',
                r'(?:s&b|s\s*&\s*b|glico|kokumaro|otafuku)',
                r'(?:coco\s+ichibanya|go\s+go\s+curry|curry\s+house)',
            ]
        else:
            # Generic patterns for other markets
            patterns = [
                r'\b[A-Z][a-zA-Z]+\s+(?:Inc|Corp|Company|Ltd)\b',
                r'\b[A-Z][a-zA-Z]+\s+Foods?\b',
                r'\b[A-Z][a-zA-Z]+\s+Brands?\b'
            ]
        
        text = f"{title} {content}".lower()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            competitors.extend(matches)
        
        return competitors
    
    def _extract_market_share_data(self, content: str) -> Dict[str, str]:
        """Extract market share data from content."""
        market_shares = {}
        
        # Look for market share patterns
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:holds?|has|commands?)\s+(\d+(?:\.\d+)?%)',
            r'(\d+(?:\.\d+)?%)\s+market\s+share\s+(?:by|of)\s+(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    company, share = match
                    market_shares[company.strip()] = share.strip()
        
        return market_shares
    
    def _extract_key_players(self, content: str, target_market: str) -> List[str]:
        """Extract key market players from content."""
        key_players = []
        
        # Look for key player indicators
        indicators = ['leading', 'major', 'key', 'top', 'dominant', 'market leader']
        
        for indicator in indicators:
            pattern = f'{indicator}\\s+(?:companies?|brands?|players?)\\s+(?:include|are)\\s+([^.]+)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract company names from the match
                companies = [name.strip() for name in re.split(r'[,;]', match) if name.strip()]
                key_players.extend(companies)
        
        return key_players
    
    def _determine_market_position(self, competitor: str, target_market: str) -> str:
        """Determine market position for a competitor."""
        # Placeholder implementation
        positions = ['premium', 'mid-market', 'budget', 'niche', 'mass-market']
        return 'mid-market'  # Default position
    
    def _identify_differentiators(self, competitor: str, target_market: str) -> List[str]:
        """Identify key differentiators for a competitor."""
        # Placeholder implementation
        differentiators = ['quality', 'price', 'convenience', 'variety', 'brand']
        return differentiators[:2]  # Return 2 differentiators
    
    def _identify_target_segments(self, competitor: str, target_market: str) -> List[str]:
        """Identify target market segments for a competitor."""
        # Placeholder implementation
        segments = ['families', 'young adults', 'professionals', 'students']
        return segments[:2]  # Return 2 segments
    
    def _create_positioning_map(self, competitors: List[str]) -> Dict[str, Any]:
        """Create a competitive positioning map."""
        return {
            'axes': ['price', 'quality'],
            'competitor_positions': {
                competitor: {'x': 0.5, 'y': 0.5} for competitor in competitors[:5]
            },
            'market_segments': ['premium', 'mid-market', 'budget', 'niche']
        }
    
    def _is_pain_point_addressed_by_competitors(self, pain_point: str, competitor_landscape: Dict[str, Any]) -> bool:
        """Check if a pain point is addressed by existing competitors."""
        # Placeholder implementation - in a real scenario, this would analyze
        # competitor offerings against the specific pain point
        return False
    
    def _create_empty_competitor_landscape(self) -> Dict[str, Any]:
        """Create empty competitor landscape structure."""
        return {
            'competitors': [],
            'key_players': [],
            'market_share_data': {},
            'total_competitors_found': 0,
            'analysis_timestamp': datetime.now().isoformat(),
            'status': 'no_data_available'
        }
    
    def _create_empty_positioning_analysis(self) -> Dict[str, Any]:
        """Create empty positioning analysis structure."""
        return {
            'positioning_strategies': {},
            'market_positioning_map': {},
            'differentiation_factors': [],
            'analysis_timestamp': datetime.now().isoformat(),
            'status': 'no_data_available'
        }
    
    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Execute comprehensive competitor analysis."""
        logger.info("Starting comprehensive competitor analysis")
        
        # Analyze competitor landscape
        competitor_landscape = await self.analyze_competitor_landscape(state)
        
        # Analyze competitive positioning
        competitive_positioning = await self.analyze_competitive_positioning(state)
        
        # Generate feature comparisons
        feature_comparisons = await self.generate_feature_comparisons(state)
        
        # Identify market gaps
        market_gaps = await self.identify_market_gaps(state)
        
        # Compile results
        results = {
            'competitor_landscape': competitor_landscape,
            'competitive_positioning': competitive_positioning,
            'feature_comparisons': feature_comparisons,
            'market_gaps': market_gaps,
            'analysis_timestamp': datetime.now().isoformat(),
            'target_market': state.get('target_market', 'unknown')
        }
        
        logger.info("Competitor analysis completed successfully")
        return results
