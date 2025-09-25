import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage

from ...classes import MarketResearchState, ConsumerInsight
from .base import BaseResearcher

logger = logging.getLogger(__name__)


class ConsumerAnalysisAgent(BaseResearcher):
    """
    Consumer Analysis Agent for 3C market research focusing on Japanese curry market.
    Analyzes social media, reviews, and forums to extract consumer insights, pain points,
    and customer personas.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "consumer_analyst"
        
        # Japanese curry market specific keywords for enhanced search
        self.market_keywords = [
            "japanese curry", "curry rice", "カレー", "curry roux", "curry sauce",
            "japanese food", "curry house", "curry restaurant", "instant curry",
            "curry powder", "curry spice", "curry flavor", "curry taste"
        ]
        
        # Consumer insight categories for classification
        self.insight_categories = [
            "taste_preference", "convenience", "price_sensitivity", "health_concern",
            "authenticity", "packaging", "preparation_time", "ingredient_quality",
            "brand_loyalty", "purchase_frequency", "usage_occasion"
        ]

    async def analyze_consumer_insights(self, state: MarketResearchState) -> Dict[str, Any]:
        """
        Main method to analyze consumer insights for Japanese curry market.
        Extracts insights from social media, reviews, and forums.
        """
        target_market = state.get('target_market', 'japanese_curry')
        company = state.get('company', 'Unknown Company')
        
        msg = [f"👥 Consumer Analysis Agent analyzing {target_market} market for {company}"]
        
        # Generate consumer-focused search queries
        queries = await self.generate_consumer_queries(state)
        
        # Add message to show subqueries
        subqueries_msg = "🔍 Consumer analysis queries:\n" + "\n".join([f"• {query}" for query in queries])
        messages = state.get('messages', [])
        messages.append(AIMessage(content=subqueries_msg))
        state['messages'] = messages

        # Send queries through WebSocket
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Consumer analysis queries generated",
                    result={
                        "step": "Consumer Analysis",
                        "analyst_type": "Consumer Analyst",
                        "queries": queries,
                        "target_market": target_market
                    }
                )
        
        # Collect consumer data from multiple sources
        consumer_data = {}
        try:
            # Search for consumer insights using generated queries
            for query in queries:
                documents = await self.search_documents(state, [query])
                if documents:
                    for url, doc in documents.items():
                        doc['query'] = query
                        doc['analysis_type'] = 'consumer_insight'
                        consumer_data[url] = doc
            
            msg.append(f"\n✓ Found {len(consumer_data)} consumer insight documents")
            
            if websocket_manager := state.get('websocket_manager'):
                if job_id := state.get('job_id'):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Collected {len(consumer_data)} consumer insight documents",
                        result={
                            "step": "Data Collection",
                            "analyst_type": "Consumer Analyst",
                            "documents_found": len(consumer_data)
                        }
                    )
                    
        except Exception as e:
            msg.append(f"\n⚠️ Error during consumer data collection: {str(e)}")
            logger.error(f"Consumer data collection error: {e}")
        
        # Extract structured consumer insights
        consumer_insights = await self.extract_consumer_insights(consumer_data, state)
        
        # Identify pain points from collected data
        pain_points = await self.identify_pain_points(consumer_data, state)
        
        # Generate customer personas
        customer_personas = await self.generate_customer_personas(consumer_insights, pain_points, state)
        
        # Map purchase journey
        purchase_journey = await self.map_purchase_journey(consumer_insights, state)
        
        # Update state with consumer analysis results
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        
        # Store results in MarketResearchState format
        consumer_insights_data = {
            'raw_data': consumer_data,
            'structured_insights': consumer_insights,
            'analysis_timestamp': datetime.now().isoformat(),
            'market_focus': target_market
        }
        
        # Return state updates - avoid returning conflicting keys
        # Only return consumer-specific keys to prevent state conflicts
        return {
            'consumer_insights': consumer_insights_data,
            'pain_points': pain_points,
            'customer_personas': customer_personas,
            'purchase_journey': purchase_journey
        }

    async def generate_consumer_queries(self, state: MarketResearchState) -> List[str]:
        """Generate targeted search queries for consumer analysis of Japanese curry market."""
        target_market = state.get('target_market', 'japanese_curry')
        
        prompt = f"""
        Generate search queries to understand consumer behavior, preferences, and pain points 
        in the {target_market} market. Focus on:
        
        - Consumer reviews and feedback about Japanese curry products
        - Social media discussions about Japanese curry preferences and experiences
        - Forum discussions about Japanese curry cooking, brands, and taste preferences
        - Consumer complaints and pain points related to Japanese curry products
        - Purchase behavior and decision factors for Japanese curry products
        - Consumer preferences for curry flavors, spice levels, and preparation methods
        
        Make queries specific to consumer insights and social listening for Japanese curry market.
        """
        
        return await self.generate_queries(state, prompt)

    async def extract_consumer_insights(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Extract structured consumer insights from collected data.
        Uses LLM to analyze content and categorize insights.
        """
        if not consumer_data:
            return []
        
        insights = []
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Process documents in batches to extract insights
            for url, doc in consumer_data.items():
                content = doc.get('content', '')
                if not content or len(content.strip()) < 50:
                    continue
                
                # Use LLM to extract consumer insights from content
                insight_prompt = f"""
                Analyze the following consumer content about Japanese curry and extract key insights:
                
                Content: {content[:2000]}  # Limit content length
                
                Extract and categorize consumer insights focusing on:
                1. Taste preferences and flavor profiles
                2. Convenience and preparation concerns
                3. Price sensitivity and value perception
                4. Health and ingredient concerns
                5. Brand preferences and loyalty factors
                6. Purchase occasions and usage patterns
                
                Provide insights in JSON format with fields:
                - insight_text: The specific consumer insight
                - category: One of {self.insight_categories}
                - sentiment: positive/negative/neutral
                - confidence: 0.0-1.0 score
                - pain_point: true/false if this represents a consumer pain point
                """
                
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a consumer insights analyst specializing in Japanese curry market research."},
                            {"role": "user", "content": insight_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    # Parse LLM response to extract insights
                    insight_text = response.choices[0].message.content
                    
                    # Create structured insight object
                    insight = {
                        'insight_id': str(uuid.uuid4()),
                        'source_url': url,
                        'source_title': doc.get('title', ''),
                        'query': doc.get('query', ''),
                        'raw_content': content[:500],  # Store snippet
                        'extracted_insight': insight_text,
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': 0.8  # Default confidence
                    }
                    
                    insights.append(insight)
                    
                except Exception as e:
                    logger.error(f"Error extracting insight from {url}: {e}")
                    continue
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Extracted {len(insights)} consumer insights",
                    result={
                        "step": "Insight Extraction",
                        "insights_extracted": len(insights)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in consumer insight extraction: {e}")
        
        return insights

    async def identify_pain_points(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> List[str]:
        """
        Identify consumer pain points from collected data.
        Focuses on negative sentiment and complaint patterns.
        """
        if not consumer_data:
            return []
        
        pain_points = []
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Combine content from multiple sources for pain point analysis
            combined_content = ""
            for doc in consumer_data.values():
                content = doc.get('content', '')
                if content:
                    combined_content += content + "\n\n"
            
            if not combined_content.strip():
                return []
            
            # Use LLM to identify pain points
            pain_point_prompt = f"""
            Analyze consumer discussions about Japanese curry and identify key pain points and complaints:
            
            Content: {combined_content[:3000]}  # Limit content length
            
            Identify specific consumer pain points related to:
            - Product quality issues (taste, texture, authenticity)
            - Convenience and preparation challenges
            - Pricing and value concerns
            - Availability and accessibility issues
            - Health and dietary restrictions
            - Packaging and storage problems
            
            List the top 5-10 most significant pain points as bullet points.
            Focus on actionable insights that could inform product development.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a consumer research analyst identifying pain points in the Japanese curry market."},
                    {"role": "user", "content": pain_point_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            # Parse pain points from response
            pain_point_text = response.choices[0].message.content
            
            # Extract individual pain points (assuming bullet point format)
            lines = pain_point_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    pain_point = line.lstrip('-•* ').strip()
                    if pain_point:
                        pain_points.append(pain_point)
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Identified {len(pain_points)} consumer pain points",
                    result={
                        "step": "Pain Point Analysis",
                        "pain_points_found": len(pain_points)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error identifying pain points: {e}")
        
        return pain_points

    async def generate_customer_personas(self, insights: List[Dict[str, Any]], pain_points: List[str], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Generate customer personas based on consumer insights and pain points.
        Creates 3-5 distinct persona profiles for Japanese curry consumers.
        """
        if not insights and not pain_points:
            return []
        
        personas = []
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Prepare data for persona generation
            insights_summary = "\n".join([insight.get('extracted_insight', '')[:200] for insight in insights[:10]])
            pain_points_summary = "\n".join([f"- {pp}" for pp in pain_points[:10]])
            
            persona_prompt = f"""
            Based on consumer insights and pain points about Japanese curry, create 3-4 distinct customer personas:
            
            Consumer Insights:
            {insights_summary}
            
            Pain Points:
            {pain_points_summary}
            
            For each persona, provide:
            - Name and basic demographics
            - Japanese curry consumption behavior
            - Key motivations and preferences
            - Main pain points and challenges
            - Purchase decision factors
            - Preferred product attributes
            - Usage occasions and frequency
            
            Format as JSON array with persona objects containing these fields:
            name, age_range, lifestyle, consumption_behavior, motivations, pain_points, decision_factors, preferences
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a consumer research analyst creating customer personas for the Japanese curry market."},
                    {"role": "user", "content": persona_prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            # Parse personas from response
            persona_text = response.choices[0].message.content
            
            # Create structured persona objects (simplified parsing)
            # In a production system, you'd want more robust JSON parsing
            persona_lines = persona_text.split('\n')
            current_persona = {}
            
            for line in persona_lines:
                line = line.strip()
                if 'Name:' in line or 'Persona' in line:
                    if current_persona:
                        personas.append(current_persona)
                    current_persona = {
                        'persona_id': str(uuid.uuid4()),
                        'name': line.split(':')[-1].strip() if ':' in line else f"Persona {len(personas) + 1}",
                        'description': '',
                        'characteristics': [],
                        'pain_points': [],
                        'preferences': []
                    }
                elif current_persona and line:
                    if 'description' not in current_persona or not current_persona['description']:
                        current_persona['description'] = line
                    else:
                        current_persona['characteristics'].append(line)
            
            # Add the last persona
            if current_persona:
                personas.append(current_persona)
            
            # Ensure we have at least basic personas if parsing failed
            if not personas:
                personas = [
                    {
                        'persona_id': str(uuid.uuid4()),
                        'name': 'Convenience Seeker',
                        'description': 'Busy professional who values quick and easy Japanese curry solutions',
                        'characteristics': ['Time-constrained', 'Values convenience', 'Quality conscious'],
                        'pain_points': ['Long preparation time', 'Complex cooking process'],
                        'preferences': ['Ready-to-eat options', 'Authentic taste', 'Premium quality']
                    },
                    {
                        'persona_id': str(uuid.uuid4()),
                        'name': 'Authentic Food Enthusiast',
                        'description': 'Food lover seeking authentic Japanese curry experiences',
                        'characteristics': ['Quality focused', 'Authenticity important', 'Willing to pay premium'],
                        'pain_points': ['Lack of authentic options', 'Inconsistent quality'],
                        'preferences': ['Traditional recipes', 'High-quality ingredients', 'Restaurant-quality taste']
                    }
                ]
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Generated {len(personas)} customer personas",
                    result={
                        "step": "Persona Generation",
                        "personas_created": len(personas)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating customer personas: {e}")
        
        return personas

    async def map_purchase_journey(self, insights: List[Dict[str, Any]], state: MarketResearchState) -> Dict[str, Any]:
        """
        Map the customer purchase journey for Japanese curry products.
        Identifies key touchpoints, decision factors, and conversion barriers.
        """
        if not insights:
            return {}
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Analyze insights for purchase journey patterns
            insights_text = "\n".join([insight.get('extracted_insight', '')[:150] for insight in insights[:15]])
            
            journey_prompt = f"""
            Based on consumer insights about Japanese curry, map the typical customer purchase journey:
            
            Consumer Insights:
            {insights_text}
            
            Identify and describe each stage of the purchase journey:
            1. Awareness - How customers discover Japanese curry products
            2. Consideration - What factors they evaluate when considering purchase
            3. Purchase - Where and how they make the purchase decision
            4. Usage - How they use the product and their experience
            5. Loyalty - What drives repeat purchases or brand switching
            
            For each stage, identify:
            - Key touchpoints and channels
            - Decision factors and influences
            - Potential barriers or friction points
            - Opportunities for improvement
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a customer journey analyst specializing in Japanese curry market research."},
                    {"role": "user", "content": journey_prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            journey_text = response.choices[0].message.content
            
            # Structure the purchase journey
            purchase_journey = {
                'journey_id': str(uuid.uuid4()),
                'market_focus': state.get('target_market', 'japanese_curry'),
                'analysis_date': datetime.now().isoformat(),
                'stages': {
                    'awareness': {'description': '', 'touchpoints': [], 'barriers': []},
                    'consideration': {'description': '', 'factors': [], 'barriers': []},
                    'purchase': {'description': '', 'channels': [], 'barriers': []},
                    'usage': {'description': '', 'experience_factors': [], 'satisfaction_drivers': []},
                    'loyalty': {'description': '', 'retention_factors': [], 'switching_triggers': []}
                },
                'raw_analysis': journey_text,
                'key_insights': []
            }
            
            # Parse journey stages (simplified - in production, use more sophisticated parsing)
            lines = journey_text.split('\n')
            current_stage = None
            
            for line in lines:
                line = line.strip()
                if any(stage in line.lower() for stage in ['awareness', 'consideration', 'purchase', 'usage', 'loyalty']):
                    for stage in ['awareness', 'consideration', 'purchase', 'usage', 'loyalty']:
                        if stage in line.lower():
                            current_stage = stage
                            break
                elif current_stage and line and not line.startswith('#'):
                    if 'description' not in purchase_journey['stages'][current_stage] or not purchase_journey['stages'][current_stage]['description']:
                        purchase_journey['stages'][current_stage]['description'] = line
                    else:
                        # Add to appropriate list based on content
                        if 'barrier' in line.lower() or 'friction' in line.lower():
                            purchase_journey['stages'][current_stage].setdefault('barriers', []).append(line)
                        else:
                            purchase_journey['stages'][current_stage].setdefault('key_points', []).append(line)
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Mapped customer purchase journey",
                    result={
                        "step": "Journey Mapping",
                        "journey_stages": len(purchase_journey['stages'])
                    }
                )
                
        except Exception as e:
            logger.error(f"Error mapping purchase journey: {e}")
            purchase_journey = {
                'journey_id': str(uuid.uuid4()),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
        
        return purchase_journey

    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Main entry point for the Consumer Analysis Agent."""
        return await self.analyze_consumer_insights(state)