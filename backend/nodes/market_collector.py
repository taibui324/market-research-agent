"""
Enhanced data collector for market research data sources.
Extends the existing Collector class to handle specialized market research data.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import hashlib

from langchain_core.messages import AIMessage, HumanMessage
from langchain_perplexity import ChatPerplexity
from tavily import AsyncTavilyClient

from ..classes import MarketResearchState
from .collector import Collector
from ..services.mongodb import MongoDBService

logger = logging.getLogger(__name__)


class MarketDataCollector(Collector):
    """Enhanced collector for market research data sources."""

    def __init__(self):
        super().__init__()

        # Disable Perplexity due to API issues, use Tavily only
        logger.info("Using Tavily as primary search provider (Perplexity disabled)")
        self.perplexity_llm = None

        # Initialize Tavily client as fallback
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            raise ValueError("Missing TAVILY_API_KEY environment variable")
        
        self.tavily_client = AsyncTavilyClient(api_key=self.tavily_api_key)

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

    async def check_existing_market_data(self, job_id: str, target_market: str) -> Optional[Dict[str, Any]]:
        """Check if market data already exists in MongoDB and is recent (within 24 hours)."""
        try:
            mongodb = MongoDBService()
            
            # Check if market_research collection exists
            if not hasattr(mongodb, 'market_research'):
                mongodb.market_research = mongodb.db.market_research
            
            # Get today's date range
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # Look for existing data for this job_id and target_market created today
            existing_data = mongodb.market_research.find_one({                
                "target_market": target_market,
                "created_at": {
                    "$gte": start_of_day,
                    "$lte": end_of_day
                }
            })
            
            if existing_data:
                logger.info(f"Found market data for job {job_id} and market {target_market} created today")
                return existing_data
            else:
                logger.info(f"No existing market data found for job {job_id} and market {target_market} created today")
                return None
                
        except Exception as e:
            logger.error(f"Error checking existing market data for job {job_id}: {e}")
            return None

    async def save_market_data_to_mongodb(self, job_id: str, target_market: str, consumer_data: Dict[str, Any], 
                                       trend_data: Dict[str, Any], competitor_data: Dict[str, Any]) -> None:
        """Save collected market research data to MongoDB."""
        try:
            mongodb = MongoDBService()
            
            # Create market research data document
            market_data_doc = {
                "job_id": job_id,
                "target_market": target_market,
                "consumer_data": consumer_data,
                "trend_data": trend_data,
                "competitor_data": competitor_data,
                "total_documents": len(consumer_data) + len(trend_data) + len(competitor_data),
                "created_at": datetime.utcnow(),
                "data_types": {
                    "consumer_social": len([d for d in consumer_data.values() if d.get('data_type') == 'consumer_social']),
                    "consumer_reviews": len([d for d in consumer_data.values() if d.get('data_type') == 'consumer_reviews']),
                    "market_trends": len([d for d in trend_data.values() if d.get('data_type') == 'market_trends']),
                    "market_reports": len([d for d in trend_data.values() if d.get('data_type') == 'market_reports']),
                    "competitor_landscape": len([d for d in competitor_data.values() if d.get('data_type') == 'competitor_landscape']),
                    "product_comparison": len([d for d in competitor_data.values() if d.get('data_type') == 'product_comparison'])
                }
            }
            
            # Insert into market_research collection
            if not hasattr(mongodb, 'market_research'):
                mongodb.market_research = mongodb.db.market_research
            
            # Use upsert to update existing data or insert new
            mongodb.market_research.update_one(
                {"job_id": job_id, "target_market": target_market},
                {"$set": market_data_doc},
                upsert=True
            )
            
            # Update job record with market data completion status
            mongodb.jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "market_data_collected": True,
                    "market_data_documents": market_data_doc["total_documents"],
                    "updated_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Saved market research data to MongoDB for job {job_id}: {market_data_doc['total_documents']} documents")
            
        except Exception as e:
            logger.error(f"Failed to save market data to MongoDB for job {job_id}: {e}")

    async def collect_consumer_data(self, state: MarketResearchState, queries: List[str]) -> Dict[str, Any]:
        """Collect consumer insights from social media, reviews, and forums."""
        logger.info(f"Collecting consumer data for {len(queries)} queries")

        consumer_data = {}

        for index, query in enumerate(queries):
            if index == 0:                
                try:
                    # Create enhanced queries for social media and reviews
                    social_query = (
                        f"{query} site:({' OR site:'.join(self.social_media_sources)})"
                    )
                    review_query = (
                        f"{query} reviews site:({' OR site:'.join(self.review_sources)})"
                    )

                    # Collect from social media using Perplexity
                    social_results = await self._search_with_perplexity_enhanced(social_query, max_results=10)
                    if social_results:
                        for i, result in enumerate(social_results):
                            url_hash = hashlib.md5(f"social_{query}_{i}".encode()).hexdigest()
                            consumer_data[f"social_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Social Media Insights: {query}",
                                'data_type': 'consumer_social',
                                'query': query,
                                'source_category': 'social_media',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
                            }

                    # Collect from review sites using Perplexity
                    review_results = await self._search_with_perplexity_enhanced(review_query, max_results=10)
                    if review_results:
                        for i, result in enumerate(review_results):
                            url_hash = hashlib.md5(f"review_{query}_{i}".encode()).hexdigest()
                            consumer_data[f"review_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Customer Reviews: {query}",
                                'data_type': 'consumer_reviews',
                                'query': query,
                                'source_category': 'reviews',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
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

        for index, query in enumerate(queries):
            if index == 0:
                try:
                    # Create enhanced queries for industry trends and reports
                    industry_query = f"{query} trends market analysis site:({' OR site:'.join(self.industry_sources)})"
                    report_query = f"{query} market report forecast 2024 2025"

                    # Collect from industry sources using Perplexity
                    industry_results = await self._search_with_perplexity_enhanced(industry_query, max_results=8)
                    if industry_results:
                        for i, result in enumerate(industry_results):
                            url_hash = hashlib.md5(f"industry_{query}_{i}".encode()).hexdigest()
                            trend_data[f"industry_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Industry Trends: {query}",
                                'data_type': 'market_trends',
                                'query': query,
                                'source_category': 'industry_publications',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
                            }

                    # Collect market reports using Perplexity
                    report_results = await self._search_with_perplexity_enhanced(report_query, max_results=5)
                    if report_results:
                        for i, result in enumerate(report_results):
                            url_hash = hashlib.md5(f"report_{query}_{i}".encode()).hexdigest()
                            trend_data[f"report_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Market Report: {query}",
                                'data_type': 'market_reports',
                                'query': query,
                                'source_category': 'market_reports',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
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

        for index, query in enumerate(queries):
            if index == 0:
                try:
                    # Create enhanced queries for competitor analysis
                    competitor_query = f"Find information about competitors, competing brands, and companies in the {query} market. Include market share data, competitive positioning, and key players in the industry."
                    product_query = f"Find detailed product comparisons, features, pricing, and competitive analysis for {query}. Include product specifications, pricing strategies, and competitive advantages."

                    # Collect competitor landscape data using Perplexity
                    competitor_results = await self._search_with_perplexity_enhanced(competitor_query, max_results=10)
                    if competitor_results:
                        for i, result in enumerate(competitor_results):
                            url_hash = hashlib.md5(f"competitor_{query}_{i}".encode()).hexdigest()
                            competitor_data[f"competitor_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Competitor Analysis: {query}",
                                'data_type': 'competitor_landscape',
                                'query': query,
                                'source_category': 'competitor_analysis',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
                            }

                    # Collect product comparison data using Perplexity
                    product_results = await self._search_with_perplexity_enhanced(product_query, max_results=8)
                    if product_results:
                        for i, result in enumerate(product_results):
                            url_hash = hashlib.md5(f"product_{query}_{i}".encode()).hexdigest()
                            competitor_data[f"product_{url_hash}"] = {
                                'content': result.get('content', ''),
                                'url': result.get('url', f"perplexity_search_{url_hash}"),
                                'title': f"Product Comparison: {query}",
                                'data_type': 'product_comparison',
                                'query': query,
                                'source_category': 'product_analysis',
                                'collected_at': datetime.now().isoformat(),
                                # Enhanced metadata from Perplexity
                                'citations': result.get('citations', []),
                                'search_results': result.get('search_results', []),
                                'usage_metadata': result.get('usage_metadata', {}),
                                'response_metadata': result.get('response_metadata', {}),
                                'generation_info': result.get('generation_info'),
                                'raw_response': result.get('raw_response', {})
                            }

                except Exception as e:
                    logger.error(f"Error collecting competitor data for query '{query}': {e}")
                    continue

            logger.info(f"Collected {len(competitor_data)} competitor data points")
            return competitor_data

    async def _search_with_perplexity_enhanced(self, query: str, max_results: int = 10, max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:
        """Enhanced search using Perplexity with full metadata capture."""
        for attempt in range(max_retries):
            try:
                # Create a message for Perplexity
                message = HumanMessage(content=query)

                # Get response from Perplexity
                response = await self.perplexity_llm.ainvoke([message])

                if response and hasattr(response, 'content'):
                    # Extract all metadata from the response
                    content = response.content
                    
                    # Extract citations if available
                    citations = []
                    if hasattr(response, 'additional_kwargs') and 'citations' in response.additional_kwargs:
                        citations = response.additional_kwargs['citations']
                    
                    # Extract search results if available
                    search_results = []
                    if hasattr(response, 'additional_kwargs') and 'search_results' in response.additional_kwargs:
                        search_results = response.additional_kwargs['search_results']
                    
                    # Extract usage metadata
                    usage_metadata = {}
                    if hasattr(response, 'usage_metadata'):
                        usage_metadata = response.usage_metadata
                    
                    # Extract response metadata
                    response_metadata = {}
                    if hasattr(response, 'response_metadata'):
                        response_metadata = response.response_metadata
                    
                    # Extract generation info
                    generation_info = None
                    if hasattr(response, 'generation_info'):
                        generation_info = response.generation_info
                    
                    # Split content into chunks for multiple results
                    content_chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
                    
                    # Create enhanced results with all metadata
                    results = []
                    for i, chunk in enumerate(content_chunks[:max_results]):
                        # Extract URL from search results if available
                        url = f"perplexity_search_{hashlib.md5(f'{query}_{i}'.encode()).hexdigest()}"
                        if i < len(search_results) and 'url' in search_results[i]:
                            url = search_results[i]['url']
                        
                        results.append({
                            'content': chunk,
                            'url': url,
                            'citations': citations,
                            'search_results': search_results,
                            'usage_metadata': usage_metadata,
                            'response_metadata': response_metadata,
                            'generation_info': generation_info,
                            'raw_response': {
                                'content': content,
                                'additional_kwargs': getattr(response, 'additional_kwargs', {}),
                                'response_metadata': getattr(response, 'response_metadata', {}),
                                'usage_metadata': getattr(response, 'usage_metadata', {}),
                                'generation_info': getattr(response, 'generation_info', None)
                            }
                        })
                    
                    return results

            except Exception as e:
                logger.warning(f"Perplexity search attempt {attempt + 1} failed for query '{query}': {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All Perplexity search attempts failed for query '{query}'")

        return None

    # Keep the old method for backward compatibility
    async def _search_with_perplexity(self, query: str, max_results: int = 10, max_retries: int = 3) -> Optional[List[str]]:
        """Search using Perplexity with retry logic and Tavily fallback."""
        
        # First try Perplexity if available
        if self.perplexity_llm:
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
                        logger.info(f"Perplexity search successful: {len(results)} results for query '{query}'")
                        return results[:max_results]

                except Exception as e:
                    logger.warning(f"Perplexity search attempt {attempt + 1} failed for query '{query}': {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # If Perplexity fails or is not available, fall back to Tavily
        logger.info(f"Using Tavily for query: {query}")
        try:
            tavily_results = await self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            if tavily_results and 'results' in tavily_results:
                # Extract content from Tavily results
                results = []
                for result in tavily_results['results'][:max_results]:
                    content = result.get('content', '')
                    if content:
                        results.append(content)
                
                logger.info(f"Tavily search successful: {len(results)} results for query '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Tavily search also failed for query '{query}': {e}")

        # If both fail, return empty list to allow workflow to continue
        logger.warning(f"All search methods failed for query '{query}', returning empty results")
        return []

    async def collect_market_research_data(self, state: MarketResearchState) -> MarketResearchState:
        """Main method to collect all market research data with caching."""
        target_market = state.get('target_market', 'japanese_curry')
        market_segment = state.get('market_segment', 'food_beverage')
        job_id = state.get('job_id')

        logger.info(f"Starting market research data collection for {target_market}")

        # Check if data already exists and is recent
        existing_data = await self.check_existing_market_data(job_id, target_market)
        if existing_data:
            logger.info(f"Using cached market data for {target_market} (saved {existing_data.get('created_at')})")
            
            # Extract data from existing document
            consumer_data = existing_data.get('consumer_data', {})
            trend_data = existing_data.get('trend_data', {})
            competitor_data = existing_data.get('competitor_data', {})
            
            # Update messages
            msg = [
                f"📊 Using cached market research data for {target_market}:",
                f"• Consumer insights: {len(consumer_data)} documents",
                f"• Market trends: {len(trend_data)} documents", 
                f"• Competitor analysis: {len(competitor_data)} documents",
                f"• Data age: {datetime.utcnow() - existing_data.get('created_at', datetime.utcnow())}"
            ]

            messages = state.get('messages', [])
            messages.append(AIMessage(content="\n".join(msg)))
            state['messages'] = messages

            return state

        # Send WebSocket update
        if websocket_manager := state.get('websocket_manager'):
            if job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Collecting fresh market research data for {target_market}",
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

        # Save to MongoDB
        if job_id:
            await self.save_market_data_to_mongodb(job_id, target_market, consumer_data, trend_data, competitor_data)

        # Update messages
        msg = [
            f"📊 Market research data collection complete for {target_market}:",
            f"• Consumer insights: {len(consumer_data)} documents",
            f"• Market trends: {len(trend_data)} documents", 
            f"• Competitor analysis: {len(competitor_data)} documents",
            f"• Data saved to MongoDB with job_id: {job_id}"
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
