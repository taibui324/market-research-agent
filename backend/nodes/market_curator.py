"""
Enhanced data curator for market research with Japanese curry market-specific relevance scoring.
Extends the existing Curator class with specialized filtering and quality assessment.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import hashlib

from langchain_core.messages import AIMessage

from ..classes import MarketResearchState
from .curator import Curator

logger = logging.getLogger(__name__)


class MarketDataCurator(Curator):
    """Enhanced curator for market research data with specialized relevance scoring."""
    
    def __init__(self):
        super().__init__()
        self.market_relevance_threshold = 0.6  # Higher threshold for market research
        
        # Japanese curry market-specific keywords
        self.japanese_curry_keywords = {
            'high_relevance': [
                'japanese curry', 'curry rice', 'karē', 'カレー', 'curry roux',
                'golden curry', 'vermont curry', 'java curry', 'kokumaro',
                'house foods', 'glico', 's&b curry', 'otafuku', 'curry udon'
            ],
            'medium_relevance': [
                'curry powder', 'curry sauce', 'japanese food', 'instant curry',
                'retort curry', 'curry restaurant', 'curry chain', 'coco ichibanya',
                'go go curry', 'curry house', 'spice level', 'japanese cuisine'
            ],
            'low_relevance': [
                'indian curry', 'thai curry', 'green curry', 'red curry',
                'curry leaves', 'masala', 'tikka', 'vindaloo', 'korma'
            ]
        }
        
        # Quality indicators for different data types
        self.quality_indicators = {
            'consumer_social': {
                'positive': ['review', 'taste', 'flavor', 'delicious', 'recommend', 'love', 'favorite'],
                'negative': ['spam', 'advertisement', 'promotion', 'sponsored']
            },
            'consumer_reviews': {
                'positive': ['purchased', 'tried', 'rating', 'stars', 'experience', 'opinion'],
                'negative': ['fake', 'bot', 'generated', 'promotional']
            },
            'market_trends': {
                'positive': ['market', 'trend', 'growth', 'forecast', 'analysis', 'report', 'data'],
                'negative': ['opinion', 'blog', 'personal', 'unverified']
            },
            'competitor_landscape': {
                'positive': ['company', 'brand', 'market share', 'revenue', 'sales', 'competition'],
                'negative': ['rumor', 'speculation', 'unconfirmed', 'gossip']
            }
        }
    
    def calculate_market_relevance_score(self, document: Dict[str, Any], target_market: str) -> float:
        """Calculate market-specific relevance score for a document."""
        content = f"{document.get('title', '')} {document.get('content', '')}".lower()
        
        if target_market == 'japanese_curry':
            return self._calculate_japanese_curry_relevance(content)
        
        # Default scoring for other markets
        return self._calculate_generic_market_relevance(content, target_market)
    
    def _calculate_japanese_curry_relevance(self, content: str) -> float:
        """Calculate relevance score specifically for Japanese curry market."""
        score = 0.0
        matches = 0
        
        # High relevance keywords (weight: 1.0)
        for keyword in self.japanese_curry_keywords['high_relevance']:
            if keyword in content:
                score += 1.0
                matches += 1
                
        # Medium relevance keywords (weight: 0.5)
        for keyword in self.japanese_curry_keywords['medium_relevance']:
            if keyword in content:
                score += 0.5
                matches += 1
                
        # Penalty for low relevance keywords (weight: -0.2)
        for keyword in self.japanese_curry_keywords['low_relevance']:
            if keyword in content:
                score -= 0.2
        
        # If no matches, return 0
        if matches == 0:
            return 0.0
        
        # Normalize score based on number of matches (more flexible scoring)
        # Base score on actual matches rather than theoretical maximum
        base_score = min(1.0, score / 2.0)  # Divide by 2 for more reasonable scaling
        
        return max(0.0, base_score)
    
    def _calculate_generic_market_relevance(self, content: str, target_market: str) -> float:
        """Calculate generic market relevance score."""
        market_terms = target_market.lower().split('_')
        score = 0.0
        
        for term in market_terms:
            if term in content:
                score += 0.5
                
        return min(1.0, score)
    
    def calculate_data_quality_score(self, document: Dict[str, Any]) -> float:
        """Calculate data quality score based on content and source characteristics."""
        data_type = document.get('data_type', 'unknown')
        content = f"{document.get('title', '')} {document.get('content', '')}".lower()
        url = document.get('url', '')
        
        quality_score = 0.5  # Base score
        
        # Get quality indicators for this data type
        indicators = self.quality_indicators.get(data_type, {})
        
        # Positive quality indicators
        positive_indicators = indicators.get('positive', [])
        for indicator in positive_indicators:
            if indicator in content:
                quality_score += 0.1
                
        # Negative quality indicators
        negative_indicators = indicators.get('negative', [])
        for indicator in negative_indicators:
            if indicator in content:
                quality_score -= 0.2
        
        # Source credibility scoring
        quality_score += self._calculate_source_credibility(url)
        
        # Content length and structure scoring
        quality_score += self._calculate_content_quality(document)
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_source_credibility(self, url: str) -> float:
        """Calculate source credibility based on domain and URL characteristics."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # High credibility sources
            high_credibility_domains = [
                'nikkei.com', 'reuters.com', 'bloomberg.com', 'wsj.com',
                'mintel.com', 'euromonitor.com', 'statista.com',
                'amazon.com', 'rakuten.co.jp', 'tabelog.com'
            ]
            
            # Medium credibility sources
            medium_credibility_domains = [
                'foodbusinessmagazine.com', 'qsrmagazine.com',
                'restaurantbusinessonline.com', 'foodnavigator.com',
                'yelp.com', 'tripadvisor.com', 'google.com'
            ]
            
            # Low credibility indicators
            low_credibility_indicators = [
                'blogspot', 'wordpress', 'tumblr', 'medium.com',
                'personal', 'blog', 'forum'
            ]
            
            for high_domain in high_credibility_domains:
                if high_domain in domain:
                    return 0.3
                    
            for medium_domain in medium_credibility_domains:
                if medium_domain in domain:
                    return 0.2
                    
            for low_indicator in low_credibility_indicators:
                if low_indicator in domain:
                    return -0.1
                    
            return 0.1  # Default for unknown sources
            
        except Exception:
            return 0.0
    
    def _calculate_content_quality(self, document: Dict[str, Any]) -> float:
        """Calculate content quality based on length, structure, and completeness."""
        content = document.get('content', '')
        title = document.get('title', '')
        
        quality_score = 0.0
        
        # Content length scoring
        content_length = len(content)
        if content_length > 500:
            quality_score += 0.1
        elif content_length > 200:
            quality_score += 0.05
        elif content_length < 50:
            quality_score -= 0.1
            
        # Title quality
        if len(title) > 10 and len(title) < 200:
            quality_score += 0.05
            
        # Structure indicators
        if any(indicator in content.lower() for indicator in ['analysis', 'report', 'study', 'research']):
            quality_score += 0.1
            
        return quality_score
    
    def calculate_confidence_score(self, document: Dict[str, Any], market_relevance: float, quality_score: float) -> float:
        """Calculate overall confidence score combining relevance, quality, and source attribution."""
        tavily_score = float(document.get('score', 0.0))
        
        # Weighted combination of scores
        confidence = (
            market_relevance * 0.4 +  # Market relevance: 40%
            quality_score * 0.3 +     # Data quality: 30%
            tavily_score * 0.3        # Tavily score: 30%
        )
        
        return min(1.0, max(0.0, confidence))
    
    def remove_duplicates(self, documents: Dict[str, Any]) -> Dict[str, Any]:
        """Remove duplicate documents based on content similarity and URL normalization."""
        if not documents:
            return documents
            
        unique_docs = {}
        content_hashes = set()
        
        for doc_id, doc in documents.items():
            # Create content hash for duplicate detection
            content = f"{doc.get('title', '')} {doc.get('content', '')}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Skip if we've seen this content before
            if content_hash in content_hashes:
                logger.debug(f"Removing duplicate document: {doc.get('title', 'No title')}")
                continue
                
            content_hashes.add(content_hash)
            unique_docs[doc_id] = doc
            
        logger.info(f"Removed {len(documents) - len(unique_docs)} duplicate documents")
        return unique_docs
    
    async def curate_market_data(self, state: MarketResearchState) -> MarketResearchState:
        """Curate market research data with specialized scoring and filtering."""
        target_market = state.get('target_market', 'japanese_curry')
        logger.info(f"Starting market data curation for {target_market}")
        
        # Send WebSocket update
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Curating market research data for {target_market}",
                    result={"step": "Market Data Curation"}
                )
        
        msg = [f"🔍 Curating market research data for {target_market}"]
        
        # Data types to curate
        data_types = {
            'consumer_raw_data': ('👥 Consumer', 'consumer'),
            'trend_raw_data': ('📈 Trends', 'trends'),
            'competitor_raw_data': ('🏢 Competitors', 'competitors')
        }
        
        curated_counts = {}
        
        for data_field, (emoji, category) in data_types.items():
            raw_data = state.get(data_field, {})
            if not raw_data:
                msg.append(f"{emoji}: No data to curate")
                curated_counts[category] = {"initial": 0, "kept": 0}
                # Still create empty curated data field
                state[f'curated_{data_field}'] = {}
                continue
                
            msg.append(f"\n{emoji}: Processing {len(raw_data)} documents")
            
            # Remove duplicates first
            unique_data = self.remove_duplicates(raw_data)
            
            # Score and filter documents
            curated_data = {}
            for doc_id, doc in unique_data.items():
                try:
                    # Calculate market relevance
                    market_relevance = self.calculate_market_relevance_score(doc, target_market)
                    
                    # Calculate data quality
                    quality_score = self.calculate_data_quality_score(doc)
                    
                    # Calculate overall confidence
                    confidence_score = self.calculate_confidence_score(doc, market_relevance, quality_score)
                    
                    # Apply threshold filtering
                    if confidence_score >= self.market_relevance_threshold:
                        # Add scoring metadata
                        doc['market_curation'] = {
                            'market_relevance': market_relevance,
                            'quality_score': quality_score,
                            'confidence_score': confidence_score,
                            'curated_at': datetime.now().isoformat()
                        }
                        curated_data[doc_id] = doc
                        
                except Exception as e:
                    logger.warning(f"Error curating document {doc_id}: {e}")
                    continue
            
            # Sort by confidence score
            sorted_items = sorted(
                curated_data.items(),
                key=lambda x: x[1]['market_curation']['confidence_score'],
                reverse=True
            )
            
            # Limit to top documents per category
            max_docs_per_category = 25
            if len(sorted_items) > max_docs_per_category:
                sorted_items = sorted_items[:max_docs_per_category]
                
            final_curated_data = dict(sorted_items)
            
            # Store curated data (always store, even if empty)
            state[f'curated_{data_field}'] = final_curated_data
            
            curated_counts[category] = {
                "initial": len(raw_data),
                "kept": len(final_curated_data)
            }
            
            msg.append(f"  ✓ Kept {len(final_curated_data)} high-quality documents")
            logger.info(f"Curated {category} data: {len(raw_data)} -> {len(final_curated_data)} documents")
        
        # Update messages
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        state['messages'] = messages
        
        # Send final curation stats
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="curation_complete",
                    message="Market data curation complete",
                    result={
                        "step": "Market Data Curation",
                        "curated_counts": curated_counts
                    }
                )
        
        logger.info("Market data curation complete")
        return state
    
    async def run(self, state: MarketResearchState) -> MarketResearchState:
        """Run the enhanced market data curation."""
        # First run standard curation if needed
        if hasattr(state, 'financial_data') and state.get('financial_data'):
            state = await super().curate_data(state)
        
        # Then run market-specific curation
        return await self.curate_market_data(state)