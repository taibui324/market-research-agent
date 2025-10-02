"""
Enhanced data collector for market research data sources.
Extends the existing Collector class to handle specialized market research data.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import hashlib

from langchain_core.messages import AIMessage, HumanMessage
from langchain_perplexity import ChatPerplexity

from ..classes import MarketResearchState
from .collector import Collector

logger = logging.getLogger(__name__)


class MarketDataCollector(Collector):
    """Enhanced collector for market research data sources."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize Perplexity client
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.perplexity_api_key:
            raise ValueError("Missing PERPLEXITY_API_KEY environment variable")
        
        self.perplexity_llm = ChatPerplexity(
            model="sonar",
            api_key=self.perplexity_api_key,
            temperature=0.1,
            max_tokens=2000,
        )
        
        self.social_media_sources = [
            "twitter.com", "x.com", "instagram.com", "reddit.com", 
            "facebook.com", "linkedin.com", "youtube.com"
        ]
        self.review_sources = [
            "amazon.com", "rakuten.co.jp", "tabelog.com", "gurunavi.com",
            "yelp.com", "tripadvisor.com", "google.com/reviews"
        ]
        self.industry_sources = [
            "nikkei.com", "foodbusinessmagazine.com", "restaurantbusinessonline.com",
            "qsrmagazine.com", "foodnavigator.com", "mintel.com"
        ]
        
    async def collect_consumer_data(self, state: MarketResearchState, queries: List[str]) -> Dict[str, Any]:
        """Collect consumer insights from social media, reviews, and forums."""
        logger.info(f"Collecting consumer data for {len(queries)} queries")
        
        consumer_data = {}
        
        for query in queries:
            try:
                # Create enhanced queries for social media and reviews
                social_query = f"Find recent social media discussions and posts about {query} on platforms like Twitter, Instagram, Reddit, Facebook, LinkedIn, and YouTube. Include user opinions, reviews, and trending topics."
                review_query = f"Find customer reviews and ratings for {query} on platforms like Amazon, Rakuten, Tabelog, Gurunavi, Yelp, TripAdvisor, and Google Reviews. Include both positive and negative feedback."
                
                # Collect from social media using Perplexity
                social_results = await self._search_with_perplexity(social_query, max_results=10)
                if social_results:
                    for i, result in enumerate(social_results):
                        url_hash = hashlib.md5(f"social_{query}_{i}".encode()).hexdigest()
                        consumer_data[f"social_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Social Media Insights: {query}",
                            'data_type': 'consumer_social',
                            'query': query,
                            'source_category': 'social_media',
                            'collected_at': datetime.now().isoformat()
                        }
                
                # Collect from review sites using Perplexity
                review_results = await self._search_with_perplexity(review_query, max_results=10)
                if review_results:
                    for i, result in enumerate(review_results):
                        url_hash = hashlib.md5(f"review_{query}_{i}".encode()).hexdigest()
                        consumer_data[f"review_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Customer Reviews: {query}",
                            'data_type': 'consumer_reviews',
                            'query': query,
                            'source_category': 'reviews',
                            'collected_at': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                logger.error(f"Error collecting consumer data for query '{query}': {e}")
                continue
                
        logger.info(f"Collected {len(consumer_data)} consumer data points")
        return consumer_data
    
    async def collect_trend_data(self, state: MarketResearchState, queries: List[str]) -> Dict[str, Any]:
        """Collect market trend data from industry publications and reports."""
        logger.info(f"Collecting trend data for {len(queries)} queries")
        
        trend_data = {}
        
        for query in queries:
            try:
                # Create enhanced queries for industry trends and reports
                industry_query = f"Find recent market trends, industry analysis, and business insights about {query} from sources like Nikkei, Food Business Magazine, Restaurant Business Online, QSR Magazine, Food Navigator, and Mintel. Include market forecasts and industry reports."
                report_query = f"Find comprehensive market reports, forecasts, and analysis for {query} for 2024 and 2025. Include market size, growth projections, and industry trends."
                
                # Collect from industry sources using Perplexity
                industry_results = await self._search_with_perplexity(industry_query, max_results=8)
                if industry_results:
                    for i, result in enumerate(industry_results):
                        url_hash = hashlib.md5(f"industry_{query}_{i}".encode()).hexdigest()
                        trend_data[f"industry_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Industry Trends: {query}",
                            'data_type': 'market_trends',
                            'query': query,
                            'source_category': 'industry_publications',
                            'collected_at': datetime.now().isoformat()
                        }
                
                # Collect market reports using Perplexity
                report_results = await self._search_with_perplexity(report_query, max_results=5)
                if report_results:
                    for i, result in enumerate(report_results):
                        url_hash = hashlib.md5(f"report_{query}_{i}".encode()).hexdigest()
                        trend_data[f"report_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Market Report: {query}",
                            'data_type': 'market_reports',
                            'query': query,
                            'source_category': 'market_reports',
                            'collected_at': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                logger.error(f"Error collecting trend data for query '{query}': {e}")
                continue
                
        logger.info(f"Collected {len(trend_data)} trend data points")
        return trend_data
    
    async def collect_competitor_data(self, state: MarketResearchState, queries: List[str]) -> Dict[str, Any]:
        """Collect competitor data from company websites, press releases, and business reports."""
        logger.info(f"Collecting competitor data for {len(queries)} queries")
        
        competitor_data = {}
        
        for query in queries:
            try:
                # Create enhanced queries for competitor analysis
                competitor_query = f"Find information about competitors, competing brands, and companies in the {query} market. Include market share data, competitive positioning, and key players in the industry."
                product_query = f"Find detailed product comparisons, features, pricing, and competitive analysis for {query}. Include product specifications, pricing strategies, and competitive advantages."
                
                # Collect competitor landscape data using Perplexity
                competitor_results = await self._search_with_perplexity(competitor_query, max_results=10)
                if competitor_results:
                    for i, result in enumerate(competitor_results):
                        url_hash = hashlib.md5(f"competitor_{query}_{i}".encode()).hexdigest()
                        competitor_data[f"competitor_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Competitor Analysis: {query}",
                            'data_type': 'competitor_landscape',
                            'query': query,
                            'source_category': 'competitor_analysis',
                            'collected_at': datetime.now().isoformat()
                        }
                
                # Collect product comparison data using Perplexity
                product_results = await self._search_with_perplexity(product_query, max_results=8)
                if product_results:
                    for i, result in enumerate(product_results):
                        url_hash = hashlib.md5(f"product_{query}_{i}".encode()).hexdigest()
                        competitor_data[f"product_{url_hash}"] = {
                            'content': result,
                            'url': f"perplexity_search_{url_hash}",
                            'title': f"Product Comparison: {query}",
                            'data_type': 'product_comparison',
                            'query': query,
                            'source_category': 'product_analysis',
                            'collected_at': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                logger.error(f"Error collecting competitor data for query '{query}': {e}")
                continue
                
        logger.info(f"Collected {len(competitor_data)} competitor data points")
        return competitor_data
    
    async def _search_with_perplexity(self, query: str, max_results: int = 10, max_retries: int = 3) -> Optional[List[str]]:
        """Search using Perplexity with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                # Create a message for Perplexity
                message = HumanMessage(content=query)
                
                # Get response from Perplexity
                response = await self.perplexity_llm.ainvoke([message])
                
                if response and hasattr(response, 'content'):
                    # Split the response into chunks for better processing
                    content = response.content
                    # Split by paragraphs or sections for multiple results
                    results = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
                    
                    # Limit results to max_results
                    return results[:max_results]
                    
            except Exception as e:
                logger.warning(f"Perplexity search attempt {attempt + 1} failed for query '{query}': {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All Perplexity search attempts failed for query '{query}'")
                    
        return None
    
    async def collect_market_research_data(self, state: MarketResearchState) -> MarketResearchState:
        """Main method to collect all market research data."""
        target_market = state.get('target_market', 'japanese_curry')
        market_segment = state.get('market_segment', 'food_beverage')
        
        logger.info(f"Starting market research data collection for {target_market}")
        
        # Send WebSocket update
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Collecting market research data for {target_market}",
                    result={"step": "Market Data Collection"}
                )
        
        # Generate market-specific queries
        base_queries = [
            f"{target_market} consumer preferences",
            f"{target_market} market trends",
            f"{target_market} competitors analysis",
            f"{target_market} customer reviews",
            f"{target_market} industry report"
        ]
        
        # Add market focus keywords if available
        focus_keywords = state.get('market_focus_keywords', [])
        if focus_keywords:
            for keyword in focus_keywords:
                base_queries.append(f"{target_market} {keyword}")
        
        # Collect data in parallel
        consumer_task = self.collect_consumer_data(state, base_queries)
        trend_task = self.collect_trend_data(state, base_queries)
        competitor_task = self.collect_competitor_data(state, base_queries)
        
        consumer_data, trend_data, competitor_data = await asyncio.gather(
            consumer_task, trend_task, competitor_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(consumer_data, Exception):
            logger.error(f"Consumer data collection failed: {consumer_data}")
            consumer_data = {}
        if isinstance(trend_data, Exception):
            logger.error(f"Trend data collection failed: {trend_data}")
            trend_data = {}
        if isinstance(competitor_data, Exception):
            logger.error(f"Competitor data collection failed: {competitor_data}")
            competitor_data = {}
        
        # Store collected data in state
        state['consumer_raw_data'] = consumer_data
        state['trend_raw_data'] = trend_data
        state['competitor_raw_data'] = competitor_data
        
        # Update messages
        msg = [
            f"📊 Market research data collection complete for {target_market}:",
            f"• Consumer insights: {len(consumer_data)} documents",
            f"• Market trends: {len(trend_data)} documents", 
            f"• Competitor analysis: {len(competitor_data)} documents"
        ]
        
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        state['messages'] = messages
        
        logger.info(f"Market research data collection complete. Total documents: {len(consumer_data) + len(trend_data) + len(competitor_data)}")
        
        return state
    
    async def run(self, state: MarketResearchState) -> MarketResearchState:
        """Run the enhanced market data collection."""
        # First run the standard collection
        state = await super().collect(state)
        
        # Then run market-specific collection
        return await self.collect_market_research_data(state)
