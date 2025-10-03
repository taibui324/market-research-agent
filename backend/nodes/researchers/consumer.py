import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage

from ...classes import MarketResearchState, ConsumerInsight
from ...services.mongodb import MongoDBService
from .base import BaseResearcher
from .customer_mapping import CustomerMappingResearcher

logger = logging.getLogger(__name__)


class ConsumerAnalysisAgent(BaseResearcher):
    """
    Consumer Analysis Agent for 3C market research focusing on Japanese curry market.
    Uses existing database data as context to generate new consumer insights via LLM.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "consumer_analyst"
        
        # Initialize customer mapping researcher for enhanced consumer analysis
        self.customer_mapping_researcher = CustomerMappingResearcher()
        
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
        Uses existing database data as context to generate new insights via LLM.
        """
        try:
            # Add overall timeout for the entire process
            return await asyncio.wait_for(
                self._analyze_consumer_insights_internal(state),
                timeout=150  # 2.5 minutes total timeout
            )
        except asyncio.TimeoutError:
            logger.error("Consumer analysis timed out after 150 seconds")
            return {
                'consumer_insights': {
                    'raw_data': {},
                    'structured_insights': [],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'market_focus': state.get('target_market', 'japanese_curry'),
                    'customer_mapping_integration': {},
                    'error': 'Analysis timed out after 150 seconds'
                },
                'pain_points': [],
                'customer_personas': [],
                'purchase_journey': {},
                'customer_mapping_results': {}
            }
        except Exception as e:
            logger.error(f"Consumer analysis failed: {e}")
            return {
                'consumer_insights': {
                    'raw_data': {},
                    'structured_insights': [],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'market_focus': state.get('target_market', 'japanese_curry'),
                    'customer_mapping_integration': {},
                    'error': str(e)
                },
                'pain_points': [],
                'customer_personas': [],
                'purchase_journey': {},
                'customer_mapping_results': {}
            }

    async def _analyze_consumer_insights_internal(self, state: MarketResearchState) -> Dict[str, Any]:
        """
        Internal method to analyze consumer insights.
        """
        target_market = state.get('target_market', 'japanese_curry')
        company = state.get('company', 'Unknown Company')
        job_id = state.get('job_id')
        
        msg = [f"👥 Consumer Analysis Agent analyzing {target_market} market for {company}"]
        
        # Send initial status update
        if websocket_manager := state.get('websocket_manager'):
            if job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Querying existing consumer data from database",
                    result={
                        "step": "Consumer Analysis",
                        "analyst_type": "Consumer Analyst",
                        "target_market": target_market
                    }
                )
        
        # Query existing consumer analysis data from MongoDB using new structure
        try:
            existing_data = await self.query_existing_consumer_data(job_id, target_market)
        except Exception as e:
            logger.error(f"Error querying consumer analysis data: {e}")
            msg.append(f"\n❌ Error querying consumer analysis data: {str(e)}")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="error",
                    message=f"Failed to query consumer data: {str(e)}",
                    result={
                        "step": "Consumer Analysis",
                        "error": str(e)
                    }
                )
            
            # Return empty structure if query fails
            return {
                'consumer_insights': {
                    'raw_data': {},
                    'structured_insights': [],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'market_focus': target_market,
                    'customer_mapping_integration': {},
                    'error': str(e)
                },
                'pain_points': [],
                'customer_personas': [],
                'purchase_journey': {},
                'customer_mapping_results': {}
            }
        
        if not existing_data:
            msg.append(f"\n⚠️ No existing consumer analysis data found for job {job_id}")
            
            # Return empty structure if no data found
            return {
                'consumer_insights': {
                    'raw_data': {},
                    'structured_insights': [],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'market_focus': target_market,
                    'customer_mapping_integration': {}
                },
                'pain_points': [],
                'customer_personas': [],
                'purchase_journey': {},
                'customer_mapping_results': {}
            }
        
        # Extract consumer insights data from the new MongoDB structure
        consumer_insights = existing_data.get('consumer_insights', {})
        raw_data = consumer_insights.get('raw_data', {})
        msg.append(f"\n✓ Found existing consumer analysis data with {len(raw_data)} raw data entries")
        
        # Log the consumer analysis data being returned
        logger.info(f"Returning consumer analysis data for job {job_id}")
        logger.info(f"Consumer insights keys: {list(consumer_insights.keys()) if consumer_insights else 'None'}")
        logger.info(f"Pain points count: {len(existing_data.get('pain_points', []))}")
        logger.info(f"Customer personas count: {len(existing_data.get('customer_personas', []))}")
        logger.info(f"Purchase journey keys: {list(existing_data.get('purchase_journey', {}).keys())}")
        logger.info(f"Customer mapping results keys: {list(existing_data.get('customer_mapping_results', {}).keys())}")
        
        # Prepare the result data
        result_data = {
            'consumer_insights': consumer_insights,
            'pain_points': existing_data.get('pain_points', []),
            'customer_personas': existing_data.get('customer_personas', []),
            'purchase_journey': existing_data.get('purchase_journey', {}),
            'customer_mapping_results': existing_data.get('customer_mapping_results', {})
        }
        
        # Save the consumer analysis results to MongoDB and update state
        try:
            # # Save to MongoDB
            # await self.save_consumer_analysis_results(
            #     job_id=job_id,
            #     target_market=target_market,
            #     consumer_insights_data=consumer_insights,
            #     pain_points=existing_data.get('pain_points', []),
            #     customer_personas=existing_data.get('customer_personas', []),
            #     purchase_journey=existing_data.get('purchase_journey', {}),
            #     customer_mapping_results=existing_data.get('customer_mapping_results', {})
            # )
            # logger.info(f"Successfully saved consumer analysis results to MongoDB for job {job_id}")
            
            # Update the state with the consumer analysis data
            state.update({
                'consumer_insights': consumer_insights,
                'pain_points': existing_data.get('pain_points', []),
                'customer_personas': existing_data.get('customer_personas', []),
                'purchase_journey': existing_data.get('purchase_journey', {}),
                'customer_mapping_results': existing_data.get('customer_mapping_results', {})
            })
            logger.info(f"Updated state with consumer analysis data for job {job_id}")
            
            # Create detailed log file
            log_filepath = await self.create_detailed_log_file(
                job_id=job_id,
                target_market=target_market,
                consumer_insights_data=consumer_insights,
                pain_points=existing_data.get('pain_points', []),
                customer_personas=existing_data.get('customer_personas', []),
                purchase_journey=existing_data.get('purchase_journey', {}),
                customer_mapping_results=existing_data.get('customer_mapping_results', {})
            )
            
            if log_filepath:
                logger.info(f"Detailed log file created: {log_filepath}")
                # Add log file path to state for reference
                state['consumer_analysis_log_file'] = log_filepath
            
            # Send websocket update about successful save
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Consumer analysis data saved to database, state, and log file",
                    result={
                        "step": "Consumer Analysis",
                        "status": "Data Saved",
                        "consumer_insights_count": len(consumer_insights.get('structured_insights', [])),
                        "pain_points_count": len(existing_data.get('pain_points', [])),
                        "personas_count": len(existing_data.get('customer_personas', [])),
                        "state_updated": True,
                        "log_file_created": bool(log_filepath),
                        "log_file_path": log_filepath if log_filepath else None
                    }
                )
        except Exception as e:
            logger.error(f"Failed to save consumer analysis results: {e}")
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="warning",
                    message=f"Failed to save consumer analysis data: {str(e)}",
                    result={
                        "step": "Consumer Analysis",
                        "status": "Save Failed",
                        "error": str(e)
                    }
                )
        
        # Return the existing consumer analysis data in the expected format
        return result_data

    async def generate_insights_from_context(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Use existing consumer data as context to generate new insights via LLM.
        """
        if not consumer_data:
            return []
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Prepare context from existing data
            context_data = []
            for data_key, data_entry in consumer_data.items():
                context_item = {
                    'title': data_entry.get('title', ''),
                    'content': data_entry.get('content', ''),
                    'data_type': data_entry.get('data_type', ''),
                    'source_category': data_entry.get('source_category', ''),
                    'query': data_entry.get('query', ''),
                    'citations': data_entry.get('citations', [])[:3]  # Limit citations
                }
                context_data.append(context_item)
            
            # Create context summary
            context_summary = "\n\n".join([
                f"**{item['title']}** ({item['data_type']})\n"
                f"Query: {item['query']}\n"
                f"Content: {item['content'][:500]}...\n"
                f"Citations: {len(item['citations'])} sources"
                for item in context_data[:10]  # Limit to top 10 for context
            ])
            
            # Generate new insights using LLM with context
            insight_prompt = f"""
            Based on the following consumer data context about Japanese curry market, generate new consumer insights:
            
            CONTEXT DATA:
            {context_summary}
            
            Generate 5-8 new consumer insights focusing on:
            1. Emerging consumer trends and preferences
            2. Pain points and challenges consumers face
            3. Purchase behavior patterns and decision factors
            4. Brand preferences and loyalty factors
            5. Usage occasions and consumption patterns
            6. Demographic and psychographic insights
            7. Market opportunities and gaps
            8. Competitive landscape insights
            
            For each insight, provide:
            - insight_text: The specific consumer insight
            - category: One of {self.insight_categories}
            - sentiment: positive/negative/neutral
            - confidence: 0.0-1.0 score
            - evidence: Supporting evidence from the context
            - implications: Business implications for the market
            
            Format as JSON array with insight objects.
            """
            
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a consumer insights analyst specializing in Japanese curry market research. Generate new insights based on existing data context."},
                        {"role": "user", "content": insight_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500  # Reduced to speed up response
                ),
                timeout=30  # 30 second timeout per LLM call
            )
            
            # Parse LLM response to extract insights
            insight_text = response.choices[0].message.content
            
            # Create structured insight objects
            insights = []
            try:
                import json
                import re
                
                # Try to extract JSON from the response
                json_match = re.search(r'\[.*\]', insight_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_insights = json.loads(json_str)
                    
                    for insight_data in parsed_insights:
                        insight = {
                            'insight_id': str(uuid.uuid4()),
                            'insight_text': insight_data.get('insight_text', ''),
                            'category': insight_data.get('category', 'general'),
                            'sentiment': insight_data.get('sentiment', 'neutral'),
                            'confidence': float(insight_data.get('confidence', 0.7)),
                            'evidence': insight_data.get('evidence', ''),
                            'implications': insight_data.get('implications', ''),
                            'source': 'context_analysis',
                            'timestamp': datetime.now().isoformat(),
                            'confidence_score': float(insight_data.get('confidence', 0.7))
                        }
                        insights.append(insight)
                else:
                    # Fallback: parse line by line for structured text
                    lines = insight_text.split('\n')
                    current_insight = {}
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('{') or line.startswith('"insight_text"'):
                            if current_insight:
                                insights.append(current_insight)
                            current_insight = {
                                'insight_id': str(uuid.uuid4()),
                                'source': 'context_analysis',
                                'timestamp': datetime.now().isoformat(),
                                'confidence_score': 0.8
                            }
                        elif ':' in line and current_insight:
                            key, value = line.split(':', 1)
                            key = key.strip().strip('"').strip(',')
                            value = value.strip().strip('"').strip(',')
                            current_insight[key] = value
                    
                    # Add the last insight
                    if current_insight:
                        insights.append(current_insight)
                
                # If no insights were parsed, create a fallback
                if not insights:
                    insights = [
                        {
                            'insight_id': str(uuid.uuid4()),
                            'insight_text': insight_text[:200] + "...",
                            'category': 'general',
                            'sentiment': 'neutral',
                            'confidence': 0.7,
                            'source': 'context_analysis',
                            'timestamp': datetime.now().isoformat(),
                            'confidence_score': 0.7
                        }
                    ]
                
            except Exception as e:
                logger.error(f"Error parsing insights: {e}")
                # Fallback: create basic insights
                insights = [
                    {
                        'insight_id': str(uuid.uuid4()),
                        'insight_text': insight_text[:200] + "...",
                        'category': 'general',
                        'sentiment': 'neutral',
                        'confidence': 0.7,
                        'source': 'context_analysis',
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': 0.7
                    }
                ]
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Generated {len(insights)} new insights from context",
                    result={
                        "step": "Context Analysis",
                        "insights_generated": len(insights)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating insights from context: {e}")
            insights = []
        
        return insights

    async def generate_pain_points_from_context(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> List[str]:
        """
        Generate pain points from existing consumer data context.
        """
        if not consumer_data:
            return []
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Prepare context for pain point analysis
            context_content = []
            for data_entry in consumer_data.values():
                content = data_entry.get('content', '')
                if content:
                    context_content.append(content[:300])  # Limit content length
            
            context_text = "\n\n".join(context_content[:5])  # Limit to 5 items
            
            # Generate pain points using LLM with context
            pain_point_prompt = f"""
            Based on the following consumer data context about Japanese curry, identify key consumer pain points:
            
            CONTEXT:
            {context_text}
            
            Identify 5-8 specific consumer pain points related to:
            - Product quality and authenticity issues
            - Convenience and preparation challenges
            - Pricing and value concerns
            - Availability and accessibility issues
            - Health and dietary restrictions
            - Packaging and storage problems
            - Brand and product selection challenges
            
            List each pain point as a clear, actionable statement.
            Focus on insights that could inform product development and marketing strategies.
            """
            
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a consumer research analyst identifying pain points in the Japanese curry market based on existing data context."},
                        {"role": "user", "content": pain_point_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=600  # Reduced for faster response
                ),
                timeout=30  # 30 second timeout
            )
            
            # Parse pain points from response
            pain_point_text = response.choices[0].message.content
            
            # Extract individual pain points
            pain_points = []
            lines = pain_point_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                    pain_point = line.lstrip('-•*0123456789. ').strip()
                    if pain_point:
                        pain_points.append(pain_point)
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Generated {len(pain_points)} pain points from context",
                    result={
                        "step": "Pain Point Analysis",
                        "pain_points_generated": len(pain_points)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating pain points from context: {e}")
            pain_points = []
        
        return pain_points

    async def generate_personas_from_context(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Generate customer personas from existing consumer data context.
        """
        if not consumer_data:
            return []
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Prepare context for persona generation
            context_summary = []
            for data_entry in consumer_data.values():
                content = data_entry.get('content', '')
                if content:
                    context_summary.append(content[:200])
            
            context_text = "\n\n".join(context_summary[:8])  # Limit context
            
            # Generate personas using LLM with context
            persona_prompt = f"""
            Based on the following consumer data context about Japanese curry, create 3-4 distinct customer personas:
            
            CONTEXT:
            {context_text}
            
            For each persona, provide:
            - Name and basic demographics
            - Japanese curry consumption behavior
            - Key motivations and preferences
            - Main pain points and challenges
            - Purchase decision factors
            - Preferred product attributes
            - Usage occasions and frequency
            
            Create personas that represent different consumer segments in the Japanese curry market.
            """
            
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a consumer research analyst creating customer personas for the Japanese curry market based on existing data context."},
                        {"role": "user", "content": persona_prompt}
                    ],
                    temperature=0.4,
                    max_tokens=1000  # Reduced for faster response
                ),
                timeout=30  # 30 second timeout
            )
            
            # Parse personas from response
            persona_text = response.choices[0].message.content
            
            # Create structured persona objects
            personas = []
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
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Generated {len(personas)} customer personas from context",
                    result={
                        "step": "Persona Generation",
                        "personas_generated": len(personas)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating personas from context: {e}")
            personas = []
        
        return personas

    async def generate_journey_from_context(self, consumer_data: Dict[str, Any], state: MarketResearchState) -> Dict[str, Any]:
        """
        Generate purchase journey from existing consumer data context.
        """
        if not consumer_data:
            return {}
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Prepare context for journey mapping
            context_summary = []
            for data_entry in consumer_data.values():
                content = data_entry.get('content', '')
                if content:
                    context_summary.append(content[:150])
            
            context_text = "\n\n".join(context_summary[:10])  # Limit context
            
            # Generate journey using LLM with context
            journey_prompt = f"""
            Based on the following consumer data context about Japanese curry, map the customer purchase journey:
            
            CONTEXT:
            {context_text}
            
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
            
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a customer journey analyst specializing in Japanese curry market research based on existing data context."},
                        {"role": "user", "content": journey_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800  # Reduced for faster response
                ),
                timeout=30  # 30 second timeout
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
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Generated purchase journey from context",
                    result={
                        "step": "Journey Mapping",
                        "journey_stages": len(purchase_journey['stages'])
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating journey from context: {e}")
            purchase_journey = {
                'journey_id': str(uuid.uuid4()),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
        
        return purchase_journey

    async def query_existing_consumer_data(self, job_id: str, target_market: str) -> Optional[Dict[str, Any]]:
        """
        Query existing consumer data from MongoDB.
        Returns the most recent consumer analysis data for the given job and market.
        """
        try:
            mongodb = MongoDBService()
            
            # Query the market_research collection for existing consumer data
            # WE DONT NEED THE JOB_ID
            query_filter = {
                "target_market": target_market
            }
                        
            # Find the most recent record - use async pattern with timeout
            existing_record = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: mongodb.market_research.find_one(
                        query_filter,
                        sort=[("created_at", -1)],  # Sort by creation date, most recent first
                        projection={"_id": 1, "consumer_data": 1, "created_at": 1}  # Only get needed fields
                    )
                ),
                timeout=10  # 10 second timeout for database query
            )
            
            if existing_record:
                logger.info(f"Found existing consumer data for job {job_id} and market {target_market}")
                logger.info(f"Existing consumer data: {existing_record}")
                return existing_record
            else:
                logger.info(f"No existing consumer data found for job {job_id} and market {target_market}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying existing consumer data for job {job_id}: {e}")
            return None


    async def integrate_customer_mapping(self, state: MarketResearchState, target_market: str) -> Dict[str, Any]:
        """
        Integrate customer mapping analysis to enhance consumer insights.
        Uses CustomerMappingResearcher to provide additional consumer behavior data.
        """
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Integrating customer mapping analysis",
                    result={
                        "step": "Customer Mapping Integration",
                        "analyst_type": "Consumer Analyst",
                        "target_market": target_market
                    }
                )
            
            # Map target market to industry for customer mapping
            industry_mapping = {
                'japanese_curry': 'Packaged curry products (Curry roux & ready-to-eat/retort curry)',
                'curry': 'Packaged curry products (Curry roux & ready-to-eat/retort curry)',
                'food': 'Food and beverage industry',
                'restaurant': 'Restaurant and food service industry'
            }
            
            industry = industry_mapping.get(target_market.lower(), f"{target_market} industry")
            
            # Create customer mapping state
            customer_mapping_state = {
                'industry': industry,
                'websocket_manager': websocket_manager,
                'job_id': job_id
            }
            
            # Execute customer mapping research
            logger.info(f"Executing customer mapping research for {industry}")
            customer_mapping_results = await self.customer_mapping_researcher.research_customer_mapping(
                customer_mapping_state
            )
            
            # Extract key insights from customer mapping for integration
            integration_summary = await self.synthesize_customer_mapping_insights(
                customer_mapping_results, target_market, state
            )
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Customer mapping integration completed",
                    result={
                        "step": "Customer Mapping Integration",
                        "status": "Completed",
                        "consumer_insights_count": len(customer_mapping_results.get('consumer_insights', [])),
                        "trend_summaries_count": len(customer_mapping_results.get('trend_summaries', []))
                    }
                )
            
            return {
                'raw_results': customer_mapping_results,
                'integration_summary': integration_summary,
                'industry_analyzed': industry,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error integrating customer mapping: {e}")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="warning",
                    message=f"Customer mapping integration failed: {str(e)}",
                    result={
                        "step": "Customer Mapping Integration",
                        "status": "Failed",
                        "error": str(e)
                    }
                )
            
            return {
                'error': str(e),
                'status': 'failed',
                'analysis_timestamp': datetime.now().isoformat()
            }

    async def synthesize_customer_mapping_insights(self, customer_mapping_results: Dict[str, Any], target_market: str, state: MarketResearchState) -> Dict[str, Any]:
        """
        Synthesize customer mapping results into actionable insights for consumer analysis.
        Extracts key consumer behavior patterns and trends.
        """
        try:
            consumer_insights = customer_mapping_results.get('consumer_insights', [])
            trend_summaries = customer_mapping_results.get('trend_summaries', [])
            
            # Extract key consumer behavior clusters
            behavior_clusters = []
            for insight in consumer_insights:
                cluster_info = {
                    'cluster': insight.get('cluster', 'Unknown'),
                    'consumer_need_trend': insight.get('consumer_need_trend', ''),
                    'frequency': insight.get('frequency', 0),
                    'key_insights': insight.get('key_insights', '')
                }
                behavior_clusters.append(cluster_info)
            
            # Extract trend evolution patterns
            trend_evolution = []
            for trend in trend_summaries:
                trend_info = {
                    'period': f"{trend.get('start_date', '')} to {trend.get('end_date', '')}",
                    'highlights': trend.get('trend_highlights', ''),
                    'behavior_changes': trend.get('consumer_behavior_changes', ''),
                    'demographic_shifts': trend.get('demographic_trends', '')
                }
                trend_evolution.append(trend_info)
            
            # Generate synthesis using LLM
            synthesis_prompt = f"""
            Synthesize customer mapping insights for {target_market} market consumer analysis:
            
            Consumer Behavior Clusters:
            {behavior_clusters[:5]}  # Top 5 clusters
            
            Trend Evolution:
            {trend_evolution[:3]}  # Recent 3 trends
            
            Provide a synthesis focusing on:
            1. Key consumer behavior patterns relevant to {target_market}
            2. Emerging consumer needs and preferences
            3. Demographic and psychographic insights
            4. Purchase journey implications
            5. Market opportunities based on consumer behavior
            
            Format as structured insights for integration with consumer analysis.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a consumer insights analyst synthesizing customer mapping data for {target_market} market research."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            synthesis_text = response.choices[0].message.content
            
            return {
                'behavior_clusters': behavior_clusters,
                'trend_evolution': trend_evolution,
                'synthesis': synthesis_text,
                'key_insights': [
                    f"Analyzed {len(consumer_insights)} consumer behavior clusters",
                    f"Tracked {len(trend_summaries)} trend evolution periods",
                    f"Focused on {target_market} market consumer patterns"
                ],
                'integration_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing customer mapping insights: {e}")
            return {
                'error': str(e),
                'synthesis': 'Failed to synthesize customer mapping insights',
                'integration_timestamp': datetime.now().isoformat()
            }

    async def save_consumer_analysis_results(self, job_id: str, target_market: str, 
                                           consumer_insights_data: Dict[str, Any],
                                           pain_points: List[str], 
                                           customer_personas: List[Dict[str, Any]],
                                           purchase_journey: Dict[str, Any],
                                           customer_mapping_results: Dict[str, Any]) -> None:
        """
        Save consumer analysis results to MongoDB with comprehensive logging.
        """
        try:
            logger.info(f"Starting to save consumer analysis results for job {job_id}")
            logger.info(f"Target market: {target_market}")
            logger.info(f"Consumer insights data keys: {list(consumer_insights_data.keys()) if consumer_insights_data else 'None'}")
            logger.info(f"Pain points count: {len(pain_points)}")
            logger.info(f"Customer personas count: {len(customer_personas)}")
            logger.info(f"Purchase journey keys: {list(purchase_journey.keys()) if purchase_journey else 'None'}")
            logger.info(f"Customer mapping results keys: {list(customer_mapping_results.keys()) if customer_mapping_results else 'None'}")
            
            mongodb = MongoDBService()
            
            # Create consumer analysis document with detailed metadata
            consumer_analysis_doc = {
                "job_id": job_id,
                "target_market": target_market,
                "consumer_insights": consumer_insights_data,
                "pain_points": pain_points,
                "customer_personas": customer_personas,
                "purchase_journey": purchase_journey,
                "customer_mapping_results": customer_mapping_results,
                "analysis_type": "consumer_analysis_report",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "data_summary": {
                    "consumer_insights_count": len(consumer_insights_data.get('structured_insights', [])),
                    "pain_points_count": len(pain_points),
                    "personas_count": len(customer_personas),
                    "journey_stages_count": len(purchase_journey.get('stages', {})),
                    "mapping_results_count": len(customer_mapping_results.get('consumer_insights', []))
                }
            }
            
            logger.info(f"Prepared consumer analysis document with {len(consumer_analysis_doc)} fields")
            
            # Save to market_research collection with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: mongodb.market_research.insert_one(consumer_analysis_doc)
                ),
                timeout=15  # 15 second timeout for database save
            )
            
            logger.info(f"Successfully saved consumer analysis results to MongoDB")
            logger.info(f"Document ID: {result.inserted_id}")
            logger.info(f"Job ID: {job_id}, Target Market: {target_market}")
            
            # Log summary of saved data
            logger.info(f"Data summary - Pain points: {len(pain_points)}")
            logger.info(f"Data summary - Personas: {len(customer_personas)}")
            logger.info(f"Data summary - Journey stages: {len(purchase_journey.get('stages', {}))}")
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout saving consumer analysis results for job {job_id} after 15 seconds")
            raise Exception(f"Database save timeout for job {job_id}")
        except Exception as e:
            logger.error(f"Error saving consumer analysis results for job {job_id}: {e}")
            logger.error(f"Target market: {target_market}")
            logger.error(f"Consumer insights data type: {type(consumer_insights_data)}")
            logger.error(f"Pain points type: {type(pain_points)}")
            logger.error(f"Customer personas type: {type(customer_personas)}")
            raise

    async def create_detailed_log_file(self, job_id: str, target_market: str, 
                                     consumer_insights_data: Dict[str, Any],
                                     pain_points: List[str], 
                                     customer_personas: List[Dict[str, Any]],
                                     purchase_journey: Dict[str, Any],
                                     customer_mapping_results: Dict[str, Any]) -> str:
        """
        Create a detailed log file for consumer analysis data.
        Returns the path to the created log file.
        """
        try:
            # Create log file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"consumer_analysis_log_{job_id}_{timestamp}.json"
            log_filepath = f"./backend/tmp/{log_filename}"  # You can change this path as needed
            
            # Prepare detailed log data
            log_data = {
                "job_id": job_id,
                "target_market": target_market,
                "timestamp": datetime.now().isoformat(),
                "consumer_insights": {
                    "raw_data_count": len(consumer_insights_data.get('raw_data', {})),
                    "structured_insights_count": len(consumer_insights_data.get('structured_insights', [])),
                    "analysis_timestamp": consumer_insights_data.get('analysis_timestamp'),
                    "market_focus": consumer_insights_data.get('market_focus'),
                    "insights_sample": consumer_insights_data.get('structured_insights', [])[:3]  # First 3 insights
                },
                "pain_points": {
                    "count": len(pain_points),
                    "sample": pain_points[:5]  # First 5 pain points
                },
                "customer_personas": {
                    "count": len(customer_personas),
                    "personas": customer_personas[:2]  # First 2 personas
                },
                "purchase_journey": {
                    "journey_id": purchase_journey.get('journey_id'),
                    "stages_count": len(purchase_journey.get('stages', {})),
                    "stages": list(purchase_journey.get('stages', {}).keys())
                },
                "customer_mapping_results": {
                    "consumer_insights_count": len(customer_mapping_results.get('consumer_insights', [])),
                    "trend_summaries_count": len(customer_mapping_results.get('trend_summaries', [])),
                    "start_date": customer_mapping_results.get('start_date'),
                    "end_date": customer_mapping_results.get('end_date')
                },
                "data_summary": {
                    "total_insights": len(consumer_insights_data.get('structured_insights', [])),
                    "total_pain_points": len(pain_points),
                    "total_personas": len(customer_personas),
                    "total_journey_stages": len(purchase_journey.get('stages', {})),
                    "total_mapping_insights": len(customer_mapping_results.get('consumer_insights', []))
                }
            }
            
            # Write log file
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Created detailed log file: {log_filepath}")
            logger.info(f"Log file contains data for job {job_id} with {log_data['data_summary']['total_insights']} insights")
            
            return log_filepath
            
        except Exception as e:
            logger.error(f"Error creating detailed log file for job {job_id}: {e}")
            return ""

    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Main entry point for the Consumer Analysis Agent."""
        return await self.analyze_consumer_insights(state)