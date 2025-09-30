"""
SWOT Analysis Agent for market research workflow.
Integrates with MarketResearchState to provide comprehensive SWOT analysis.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.classes.state import MarketResearchState
from .swot_analysis_base import SwotAnalysis

logger = logging.getLogger(__name__)


class SwotAnalysisAgent:
    """
    Enhanced SWOT Analysis Agent that integrates with the 3C analysis workflow.
    Provides comprehensive SWOT analysis using market research data.
    """
    
    def __init__(self):
        self.swot_analyzer = SwotAnalysis()
        
    async def analyze_market_swot(self, state: MarketResearchState) -> Dict[str, Any]:
        """Perform comprehensive SWOT analysis for the target market."""
        target_market = state.get('target_market', 'japanese_curry')
        company = state.get('company', 'Market Analysis')
        industry = state.get('industry', 'Food & Beverage')
        hq_location = state.get('hq_location', 'Japan')
        
        logger.info(f"Performing SWOT analysis for {target_market} market")
        
        try:
            # Prepare context for SWOT analysis
            context = {
                "websocket_manager": state.get('websocket_manager'),
                "job_id": state.get('job_id')
            }
            
            # Gather all available market research data
            market_docs = await self._gather_market_research_data(state)
            
            if not market_docs:
                logger.warning("No market research data available for SWOT analysis")
                return self._create_empty_swot_analysis()
            
            # Generate SWOT analysis using gathered data
            swot_result = await self.swot_analyzer.generate_swot(
                docs=market_docs,
                company=company,
                industry=industry,
                hq_location=hq_location,
                context=context
            )
            
            # Parse and structure SWOT content
            structured_swot = self._parse_swot_content(swot_result.get('swot', ''))
            
            # Calculate SWOT metrics
            swot_metrics = self._calculate_swot_metrics(structured_swot)
            
            return {
                'company': company,
                'target_market': target_market,
                'raw_swot': swot_result.get('swot', ''),
                'structured_swot': structured_swot,
                'swot_metrics': swot_metrics,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_sources_used': len(market_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in SWOT analysis: {e}")
            return self._create_empty_swot_analysis()
    
    async def analyze_competitive_swot(self, state: MarketResearchState) -> Dict[str, Any]:
        """Perform competitive SWOT analysis comparing against competitors."""
        target_market = state.get('target_market', 'japanese_curry')
        
        logger.info(f"Performing competitive SWOT analysis for {target_market} market")
        
        try:
            # Get competitor landscape data
            competitor_landscape = state.get('competitor_landscape', {})
            
            if not competitor_landscape or competitor_landscape.get('status') == 'failed':
                logger.warning("No competitor data available for competitive SWOT")
                return self._create_empty_competitive_swot()
            
            # Analyze competitive position using SWOT framework
            competitive_swot = await self._analyze_competitive_position(competitor_landscape, state)
            
            return competitive_swot
            
        except Exception as e:
            logger.error(f"Error in competitive SWOT analysis: {e}")
            return self._create_empty_competitive_swot()
    
    async def _gather_market_research_data(self, state: MarketResearchState) -> Dict[str, Any]:
        """Gather all available market research data for SWOT analysis."""
        market_docs = {}
        
        # Collect consumer insights data
        consumer_data = state.get('curated_consumer_raw_data', {})
        if consumer_data:
            for doc_id, doc in consumer_data.items():
                market_docs[f"consumer_{doc_id}"] = {
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'raw_content': doc.get('content', ''),
                    'evaluation': {'overall_score': doc.get('market_curation', {}).get('confidence_score', 0.5)},
                    'data_type': 'consumer_insights'
                }
        
        # Collect trend data
        trend_data = state.get('curated_trend_raw_data', {})
        if trend_data:
            for doc_id, doc in trend_data.items():
                market_docs[f"trend_{doc_id}"] = {
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'raw_content': doc.get('content', ''),
                    'evaluation': {'overall_score': doc.get('market_curation', {}).get('confidence_score', 0.5)},
                    'data_type': 'market_trends'
                }
        
        # Collect competitor data
        competitor_data = state.get('curated_competitor_raw_data', {})
        if competitor_data:
            for doc_id, doc in competitor_data.items():
                market_docs[f"competitor_{doc_id}"] = {
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'raw_content': doc.get('content', ''),
                    'evaluation': {'overall_score': doc.get('market_curation', {}).get('confidence_score', 0.5)},
                    'data_type': 'competitor_analysis'
                }
        
        # Include any existing company data if available
        company_data = state.get('curated_company_data', {})
        if company_data:
            for doc_id, doc in company_data.items():
                market_docs[f"company_{doc_id}"] = {
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'raw_content': doc.get('raw_content', doc.get('content', '')),
                    'evaluation': {'overall_score': doc.get('evaluation', {}).get('overall_score', 0.5)},
                    'data_type': 'company_data'
                }
        
        logger.info(f"Gathered {len(market_docs)} documents for SWOT analysis")
        return market_docs
    
    async def _analyze_competitive_position(self, competitor_landscape: Dict[str, Any], state: MarketResearchState) -> Dict[str, Any]:
        """Analyze competitive position using SWOT framework."""
        target_market = state.get('target_market', 'japanese_curry')
        
        competitors = competitor_landscape.get('competitors', [])
        key_players = competitor_landscape.get('key_players', [])
        
        competitive_swot = {
            'target_market': target_market,
            'competitive_strengths': [],
            'competitive_weaknesses': [],
            'market_opportunities': [],
            'competitive_threats': [],
            'competitive_analysis': {},
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Analyze each competitor's position
        for competitor in competitors[:3]:  # Focus on top 3 competitors
            competitive_swot['competitive_analysis'][competitor] = {
                'market_position': self._assess_competitor_position(competitor, competitor_landscape),
                'threat_level': self._assess_threat_level(competitor, state),
                'opportunity_level': self._assess_opportunity_level(competitor, state)
            }
        
        # Identify market-level SWOT elements
        competitive_swot['competitive_strengths'] = [
            "Growing market demand for authentic Japanese curry",
            "Established consumer base and brand recognition",
            "Diverse product portfolio opportunities"
        ]
        
        competitive_swot['competitive_weaknesses'] = [
            "Intense competition from established players",
            "Limited differentiation in core products",
            "Price pressure from multiple competitors"
        ]
        
        competitive_swot['market_opportunities'] = [
            "Premium product positioning",
            "Health-conscious product variants",
            "Digital-first brand experience",
            "International market expansion"
        ]
        
        competitive_swot['competitive_threats'] = [
            "New entrants with innovative products",
            "Changing consumer preferences",
            "Supply chain disruptions",
            "Economic downturn affecting discretionary spending"
        ]
        
        return competitive_swot
    
    def _parse_swot_content(self, swot_text: str) -> Dict[str, Any]:
        """Parse SWOT analysis text into structured data."""
        if not swot_text:
            return {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
                "summary": {
                    "total_points": 0,
                    "strengths_count": 0,
                    "weaknesses_count": 0,
                    "opportunities_count": 0,
                    "threats_count": 0
                }
            }
        
        # Split content by SWOT headers
        sections = re.split(r'### (Strengths|Weaknesses|Opportunities|Threats)', swot_text)
        
        structured_swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "summary": {}
        }
        
        # Process each section
        current_section = None
        for i, section in enumerate(sections):
            if section.strip().lower() in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                current_section = section.strip().lower()
            elif current_section and i + 1 < len(sections):
                # Extract bullet points from this section
                bullet_points = []
                for line in section.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('• '):
                        point_text = line[2:].strip()
                        bullet_points.append({
                            "text": point_text,
                            "citation": self._extract_citation(point_text)
                        })
                
                structured_swot[current_section] = bullet_points
        
        # Calculate summary metrics
        structured_swot["summary"] = {
            "total_points": sum(len(structured_swot[key]) for key in ['strengths', 'weaknesses', 'opportunities', 'threats']),
            "strengths_count": len(structured_swot["strengths"]),
            "weaknesses_count": len(structured_swot["weaknesses"]),
            "opportunities_count": len(structured_swot["opportunities"]),
            "threats_count": len(structured_swot["threats"])
        }
        
        return structured_swot
    
    def _extract_citation(self, text: str) -> str:
        """Extract citation from text like '[Company Briefing]'"""
        citation_match = re.search(r'\[([^\]]+)\]', text)
        return citation_match.group(1) if citation_match else "Market Research Data"
    
    def _calculate_swot_metrics(self, structured_swot: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics for SWOT analysis."""
        summary = structured_swot.get("summary", {})
        
        total_points = summary.get("total_points", 0)
        strengths_count = summary.get("strengths_count", 0)
        weaknesses_count = summary.get("weaknesses_count", 0)
        opportunities_count = summary.get("opportunities_count", 0)
        threats_count = summary.get("threats_count", 0)
        
        metrics = {
            "swot_balance": "balanced",
            "strength_ratio": 0,
            "opportunity_ratio": 0,
            "analysis_depth": "medium",
            "swot_quality_score": 0.5
        }
        
        if total_points > 0:
            metrics["strength_ratio"] = strengths_count / total_points
            metrics["opportunity_ratio"] = opportunities_count / total_points
            
            # Determine SWOT balance
            internal_ratio = (strengths_count + weaknesses_count) / total_points if total_points > 0 else 0
            if internal_ratio > 0.6:
                metrics["swot_balance"] = "internal_focused"
            elif internal_ratio < 0.4:
                metrics["swot_balance"] = "external_focused"
            else:
                metrics["swot_balance"] = "balanced"
            
            # Determine analysis depth
            if total_points >= 15:
                metrics["analysis_depth"] = "high"
            elif total_points >= 8:
                metrics["analysis_depth"] = "medium"
            else:
                metrics["analysis_depth"] = "low"
            
            # Calculate quality score
            metrics["swot_quality_score"] = min(1.0, total_points / 20.0)
        
        return metrics
    
    def _assess_competitor_position(self, competitor: str, competitor_landscape: Dict[str, Any]) -> str:
        """Assess a competitor's market position."""
        # Check market share data
        market_share_data = competitor_landscape.get('market_share_data', {})
        
        if competitor in market_share_data:
            share = market_share_data[competitor]
            if any(char.isdigit() for char in share):
                # Extract percentage if available
                percentage = re.search(r'(\d+(?:\.\d+)?)', share)
                if percentage:
                    pct = float(percentage.group(1))
                    if pct > 20:
                        return "market_leader"
                    elif pct > 10:
                        return "strong_player"
                    else:
                        return "challenger"
        
        # Default assessment
        key_players = competitor_landscape.get('key_players', [])
        if competitor in key_players:
            return "key_player"
        else:
            return "emerging_player"
    
    def _assess_threat_level(self, competitor: str, state: MarketResearchState) -> str:
        """Assess threat level from a competitor."""
        # Simplified threat assessment
        competitor_landscape = state.get('competitor_landscape', {})
        key_players = competitor_landscape.get('key_players', [])
        
        if competitor in key_players:
            return "high"
        else:
            return "medium"
    
    def _assess_opportunity_level(self, competitor: str, state: MarketResearchState) -> str:
        """Assess opportunity level related to a competitor."""
        # Simplified opportunity assessment
        return "medium"  # Default
    
    def _create_empty_swot_analysis(self) -> Dict[str, Any]:
        """Create empty SWOT analysis structure."""
        return {
            'company': 'Unknown',
            'target_market': 'unknown',
            'raw_swot': '',
            'structured_swot': {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
                "summary": {
                    "total_points": 0,
                    "strengths_count": 0,
                    "weaknesses_count": 0,
                    "opportunities_count": 0,
                    "threats_count": 0
                }
            },
            'swot_metrics': {
                "swot_balance": "unknown",
                "strength_ratio": 0,
                "opportunity_ratio": 0,
                "analysis_depth": "none",
                "swot_quality_score": 0
            },
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources_used': 0,
            'status': 'no_data_available'
        }
    
    def _create_empty_competitive_swot(self) -> Dict[str, Any]:
        """Create empty competitive SWOT structure."""
        return {
            'target_market': 'unknown',
            'competitive_strengths': [],
            'competitive_weaknesses': [],
            'market_opportunities': [],
            'competitive_threats': [],
            'competitive_analysis': {},
            'analysis_timestamp': datetime.now().isoformat(),
            'status': 'no_data_available'
        }
    
    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Execute comprehensive SWOT analysis."""
        logger.info("Starting comprehensive SWOT analysis")
        
        # Perform market SWOT analysis
        market_swot = await self.analyze_market_swot(state)
        
        # Perform competitive SWOT analysis
        competitive_swot = await self.analyze_competitive_swot(state)
        
        # Compile comprehensive SWOT results
        results = {
            'market_swot_analysis': market_swot,
            'competitive_swot_analysis': competitive_swot,
            'analysis_timestamp': datetime.now().isoformat(),
            'target_market': state.get('target_market', 'unknown')
        }
        
        logger.info("SWOT analysis completed successfully")
        return results
