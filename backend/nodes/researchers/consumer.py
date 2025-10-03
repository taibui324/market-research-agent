import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ...classes import MarketResearchState, ConsumerInsight
from ...services.mongodb import MongoDBService
from .base import BaseResearcher
from .customer_mapping import CustomerMappingResearcher
import os 
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
                timeout=600  # 2.5 minutes total timeout
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
                raise
        if not existing_data:
            msg.append(f"\n⚠️ No existing consumer analysis data found for job {job_id}")
            # Return empty structure if no data found
            raise Exception("No existing consumer analysis data found for job {job_id}")                

        # Extract consumer insights data from the new MongoDB structure
        logger.info(f"=== PARSING EXISTING DATA ===")
        logger.info(f"Existing data keys: {list(existing_data.keys())}")
        # Log the structure of each key
        for key, value in existing_data.items():
            if isinstance(value, dict):
                logger.info(f"  {key}: dict with keys {list(value.keys())}")
                if key == 'consumer_insights' and isinstance(value, dict):
                    logger.info(f"    consumer_insights keys: {list(value.keys())}")
                    if 'raw_data' in value:
                        logger.info(f"    raw_data type: {type(value['raw_data'])}, length: {len(value['raw_data']) if isinstance(value['raw_data'], (dict, list)) else 'N/A'}")
            elif isinstance(value, list):
                logger.info(f"  {key}: list with {len(value)} items")
                if value and isinstance(value[0], dict):
                    logger.info(f"    First item keys: {list(value[0].keys())}")
            else:
                logger.info(f"  {key}: {type(value)} = {str(value)[:100]}...")

        consumer_data = existing_data.get("consumer_data", {})        
        msg.append(f"\n✓ Found existing consumer analysis data with {len(consumer_data)} raw data entries")
        try:

            logger.info(f"Updated state with consumer analysis data for job {job_id}")

            # Create detailed log file
            log_filepath = await self.create_detailed_log_file(
                job_id=job_id,
                target_market=target_market,
                consumer_data=consumer_data,                
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
                        "consumer_insights_count": len(consumer_data.get('structured_insights', [])),
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
        # Integrate customer mapping analysis to enhance consumer insights
        try:
            logger.info("Starting customer mapping integration")
            customer_mapping_integration = await self.integrate_customer_mapping(state, target_market, consumer_data)

            state['customer_mapping_integration'] = customer_mapping_integration

            logger.info("Customer mapping integration completed successfully")
            return customer_mapping_integration

        except Exception as e:
            logger.error(f"Customer mapping integration failed: {e}")
            raise 

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
            # Remove projection to get all fields
            existing_record = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: mongodb.market_research.find_one(
                        query_filter,
                        sort=[("created_at", -1)],  # Sort by creation date, most recent first
                        # Remove projection to get all fields
                    )
                ),
                timeout=10  # 10 second timeout for database query
            )

            if existing_record:
                logger.info(f"Found existing consumer data for job {job_id} and market {target_market}")
                logger.info(f"Existing consumer data keys: {list(existing_record.keys())}")
                logger.info(f"Existing consumer data structure:")
                for key, value in existing_record.items():
                    if isinstance(value, dict):
                        logger.info(f"  {key}: dict with keys {list(value.keys())}")
                    elif isinstance(value, list):
                        logger.info(f"  {key}: list with {len(value)} items")
                    else:
                        logger.info(f"  {key}: {type(value)} = {str(value)[:100]}...")
                return existing_record
            else:
                logger.info(f"No existing consumer data found for job {job_id} and market {target_market}")
                return None

        except Exception as e:
            logger.error(f"Error querying existing consumer data for job {job_id}: {e}")
            return None

    ## new one and important
    async def integrate_customer_mapping(self, state: MarketResearchState, target_market: str, existing_consumer_data: Dict[str, Any]) -> Dict[str, Any]:
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

            # # Execute customer mapping research
            # logger.info(f"Executing customer mapping research for {industry}")
            # customer_mapping_results = await self.customer_mapping_researcher.research_customer_mapping(
            #     customer_mapping_state
            # )

            # Extract key insights from customer mapping for integration we may dont need this
            # integration_summary = await self.synthesize_customer_mapping_insights(
            #     existing_consumer_data, target_market
            # )

            # print(integration_summary)

            # process_consumer_insights_for_report
            consumer_insights_data = await self.process_consumer_insights_for_report(existing_consumer_data)

            # state['consumer_insights_data'] = consumer_insights_data
            # state['customer_mapping_integration'] = integration_summary

            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Customer mapping integration completed",
                    result={
                        "step": "Customer Mapping Integration",
                        "status": "Completed",
                        "consumer_insights_count": len(
                            consumer_insights_data.get("consumer_insights", [])
                        ),
                        "trend_summaries_count": len(
                            consumer_insights_data.get("trend_summaries", [])
                        ),
                    },
                )

            return consumer_insights_data

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

    async def synthesize_customer_mapping_insights(self, customer_mapping_results: Dict[str, Any], target_market: str) -> Dict[str, Any]:
        """
        Synthesize customer mapping results into actionable insights for consumer analysis.
        Uses the entire customer_mapping_results dataset with LangChain.
        """
        try:
            # Use the entire customer_mapping_results dataset
            logger.info(f"Processing complete customer mapping results with {len(customer_mapping_results)} top-level keys")
            logger.info(f"Customer mapping results keys: {list(customer_mapping_results.keys())}")

            # Log the structure of the complete dataset
            for key, value in customer_mapping_results.items():
                if isinstance(value, list):
                    logger.info(f"  {key}: list with {len(value)} items")
                elif isinstance(value, dict):
                    logger.info(f"  {key}: dict with {len(value)} keys")
                else:
                    logger.info(f"  {key}: {type(value)} = {str(value)[:100]}...")

            # Create LangChain chat model
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=10000  # Increased to handle complete dataset
            )

            # Convert the entire customer_mapping_results to properly formatted JSON string
            complete_dataset_json = json.dumps(customer_mapping_results, indent=2, ensure_ascii=False, default=str)

            # Apply intelligent truncation to prevent exceeding max token limit
            # Estimate: ~4 characters per token, so 3000 tokens = ~12,000 characters
            max_chars = 10000  # Conservative limit to account for prompt overhead
            original_length = len(complete_dataset_json)

            if original_length > max_chars:
                logger.warning(f"Dataset too large ({original_length} chars), truncating to {max_chars} chars")

                # Intelligent truncation: try to preserve complete sections
                truncated_json = complete_dataset_json[:max_chars]

                # Try to end at a complete JSON object/section
                last_complete_section = truncated_json.rfind('},')
                if last_complete_section > max_chars * 0.8:  # If we can find a good break point
                    truncated_json = truncated_json[:last_complete_section + 1]
                    # Add closing braces to maintain valid JSON structure
                    truncated_json += '}'

                # Add truncation notice
                truncated_json += f'\n\n... [TRUNCATED: Original dataset was {original_length} characters, showing first {len(truncated_json)} characters] ...'

                complete_dataset_json = truncated_json
                logger.info(f"Truncated dataset from {original_length} to {len(complete_dataset_json)} characters")
            else:
                logger.info(f"Dataset size OK: {original_length} characters (limit: {max_chars})")

            # Log data quality for debugging
            logger.info(f"Final dataset JSON length: {len(complete_dataset_json)} characters")
            logger.info(f"Dataset contains {len(customer_mapping_results)} top-level sections")

            # Create prompt template with complete dataset
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are a consumer insights analyst synthesizing customer mapping data for {target_market} market research. Analyze the complete dataset to provide comprehensive insights."),
                ("human", """
            Synthesize customer mapping insights for {target_market} market consumer analysis using the complete customer mapping dataset:
            
            Complete Customer Mapping Results:
            {complete_dataset_json}
            
            Provide a comprehensive synthesis focusing on:
            1. Key consumer behavior patterns relevant to {target_market}
            2. Emerging consumer needs and preferences
            3. Demographic and psychographic insights
            4. Purchase journey implications
            5. Market opportunities based on consumer behavior
            6. Data quality insights and patterns across the entire dataset
            7. Cross-references between different data sections
            8. Temporal patterns and trends across all data points
            
            Format as structured insights for integration with consumer analysis.
            Use the complete dataset to identify patterns, trends, and opportunities across all available data.
            
            Always must provide the citations for each of the data sections.
            """)
            ])

            # Create chain
            chain = prompt | llm

            # Generate synthesis using LangChain with complete dataset
            synthesis_response = await chain.ainvoke({
                "target_market": target_market,
                "complete_dataset_json": complete_dataset_json
            })

            synthesis_text = synthesis_response.content

            logger.info(f"Synthesis text: {synthesis_text}")

            return {
                'complete_dataset': customer_mapping_results,
                'synthesis': synthesis_text,
                'key_insights': [
                    f"Analyzed complete customer mapping dataset with {len(customer_mapping_results)} sections",
                    f"Dataset size: {len(complete_dataset_json)} characters",
                    f"Focused on {target_market} market consumer patterns",
                    f"Used entire customer mapping results for comprehensive analysis",
                    f"Truncated: {'Yes' if original_length > max_chars else 'No'} (Original: {original_length} chars)"
                ],
                'integration_timestamp': datetime.now().isoformat(),
                'data_quality_metrics': {
                    'total_sections_processed': len(customer_mapping_results),
                    'dataset_size_characters': len(complete_dataset_json),
                    'original_dataset_size': original_length,
                    'was_truncated': original_length > max_chars,
                    'truncation_ratio': len(complete_dataset_json) / original_length if original_length > 0 else 1.0,
                    'analysis_scope': 'complete_dataset',
                    'data_completeness': 'full_customer_mapping_results' if not (original_length > max_chars) else 'truncated_customer_mapping_results'
                }
            }

        except Exception as e:
            # logger.error(f"Error synthesizing customer mapping insights: {e}")
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
            # logger.info(f"Starting to save consumer analysis results for job {job_id}")
            # logger.info(f"Target market: {target_market}")
            # logger.info(f"Consumer insights data keys: {list(consumer_insights_data.keys()) if consumer_insights_data else 'None'}")
            # logger.info(f"Pain points count: {len(pain_points)}")
            # logger.info(f"Customer personas count: {len(customer_personas)}")
            # logger.info(f"Purchase journey keys: {list(purchase_journey.keys()) if purchase_journey else 'None'}")
            # logger.info(f"Customer mapping results keys: {list(customer_mapping_results.keys()) if customer_mapping_results else 'None'}")

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

            # logger.info(f"Prepared consumer analysis document with {len(consumer_analysis_doc)} fields")

            # Save to market_research collection with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: mongodb.market_research.insert_one(consumer_analysis_doc)
                ),
                timeout=15  # 15 second timeout for database save
            )

            # logger.info(f"Successfully saved consumer analysis results to MongoDB")
            # logger.info(f"Document ID: {result.inserted_id}")
            # logger.info(f"Job ID: {job_id}, Target Market: {target_market}")

            # # Log summary of saved data
            # logger.info(f"Data summary - Pain points: {len(pain_points)}")
            # logger.info(f"Data summary - Personas: {len(customer_personas)}")
            # logger.info(f"Data summary - Journey stages: {len(purchase_journey.get('stages', {}))}")

        except asyncio.TimeoutError:
            logger.error(f"Timeout saving consumer analysis results for job {job_id} after 15 seconds")
            raise Exception(f"Database save timeout for job {job_id}")
        except Exception as e:
            # logger.error(f"Error saving consumer analysis results for job {job_id}: {e}")
            # logger.error(f"Target market: {target_market}")
            # logger.error(f"Consumer insights data type: {type(consumer_insights_data)}")
            # logger.error(f"Pain points type: {type(pain_points)}")
            # logger.error(f"Customer personas type: {type(customer_personas)}")
            raise

    async def create_detailed_log_file(self, job_id: str, target_market: str, 
                                     consumer_data: Dict[str, Any],
                                     ) -> str:
        """
        Create a detailed log file for consumer analysis data.
        Returns the path to the created log file.
        """
        try:
            import os

            # Create log file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"consumer_analysis_log_{job_id}_{timestamp}.json"

            # Create tmp directory if it doesn't exist
            tmp_dir = "./backend/tmp"
            try:
                os.makedirs(tmp_dir, exist_ok=True)
                # logger.info(f"Created/verified tmp directory: {tmp_dir}")
            except Exception as e:
                # logger.error(f"Failed to create tmp directory {tmp_dir}: {e}")
                # Fallback to current directory
                tmp_dir = "."
                # logger.info(f"Using fallback directory: {tmp_dir}")

            log_filepath = os.path.join(tmp_dir, log_filename)
            logger.info(f"Log file path: {log_filepath}")

            # Prepare detailed log data
            log_data = {
                "job_id": job_id,
                "target_market": target_market,
                "timestamp": datetime.now().isoformat(),
                "consumer_data": consumer_data
            }

            # Write log file
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Created detailed log file: {log_filepath}")
            # logger.info(f"Log file contains data for job {job_id} with {log_data['data_summary']['total_insights']} insights")

            return log_filepath

        except Exception as e:
            # logger.error(f"Error creating detailed log file for job {job_id}: {e}")
            return ""

    async def process_consumer_insights_for_report(self, consumer_insights_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process consumer insights data to create a comprehensive report format.
        Summarizes each raw data entry using LLM and creates structured output optimized for report generation.
        """
        try:
            logger.info("Starting consumer insights processing for report generation")

            # raw_data = consumer_insights_data.get("consumer_data", {})
            print(consumer_insights_data)
            # logger.info(f"Found {len(raw_data)} raw data entries to process")

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=500
            )

            # Define prompt templates
            summary_prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a consumer insights analyst summarizing Japanese curry market data."),
                ("human", """Summarize the following consumer insights for the Japanese curry market:

Title: {title}
Data Type: {data_type}
Source Category: {source_category}
Query: {query}

Content:
{content}

Provide a concise summary (2–3 sentences) focusing on actionable consumer insights, preferences, or concerns.""")
            ])

            pain_points_prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a consumer insights analyst. Extract specific, actionable pain points from consumer data."),
                ("human", """From the following consumer insight summaries, extract recurring consumer **pain points**:
- Pain points are frustrations, unmet needs, or negative experiences.
- Write them as a bulleted list of 5–7 items.

Summaries:
{summaries}""")
            ])

            executive_summary_prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a senior market research analyst. Write executive-level summaries that highlight key business insights."),
                ("human", """Based on these consumer insights about the Japanese curry market, write an **executive summary** (5–6 sentences).
Cover key consumer trends, preferences, market drivers, and pain points.

Consumer Insights Data:
{summaries}""")
            ])

            processed_entries = []
            pain_points = []
            executive_summary = []

            # Process individual entries
            for entry_id, entry_data in consumer_insights_data.items():
                logger.info(f"Processing entry: {entry_id}")

                content = entry_data.get('content', '')
                title = entry_data.get('title', '')
                data_type = entry_data.get('data_type', '')
                source_category = entry_data.get('source_category', '')
                query = entry_data.get('query', '')
                
                citations = entry_data.get('citations', [])
                url = entry_data.get('url', '')

                try:
                    chain = summary_prompt_template | llm
                    summary_response = await chain.ainvoke({
                        "title": title,
                        "data_type": data_type,
                        "source_category": source_category,
                        "query": query,
                        "content": content[:1500]
                    })
                    summary_text = summary_response.content
                except Exception as e:
                    logger.error(f"Error generating summary for entry {entry_id}: {e}")
                    summary_text = f"Consumer insights from {data_type}: {content[:200]}..."

                processed_entry = {
                    'entry_id': entry_id,
                    'title': title,
                    'data_type': data_type,
                    'source_category': source_category,
                    'query': query,
                    'summary': summary_text,
                    'original_content': content,
                    'citations': citations,
                    'url': url,
                    'processed_at': datetime.now().isoformat(),
                    'confidence_score': self._calculate_confidence_score(content, summary_text),
                    'insight_category': self._categorize_insight(summary_text),
                    'sentiment': self._analyze_sentiment(summary_text),
                    'key_phrases': self._extract_key_phrases(summary_text),
                }
                processed_entries.append(processed_entry)

            # Generate pain points using all summaries
            try:
                chain = pain_points_prompt_template | llm
                pain_points_response = await chain.ainvoke({
                    "summaries": "\n".join([e['summary'] for e in processed_entries])
                })
                pain_points_text = pain_points_response.content.strip()
                pain_points = [line.strip('- ').strip() for line in pain_points_text.split('\n') 
                             if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•'))]

                if not pain_points:
                    pain_points = ["Limited data available for pain point extraction."]
            except Exception as e:
                logger.error(f"Error generating pain points: {e}")
                pain_points = ["Limited data available for pain point extraction."]

            # Generate executive summary
            try:
                chain = executive_summary_prompt_template | llm
                exec_summary_response = await chain.ainvoke({
                    "summaries": "\n".join([f"- {e['summary']}" for e in processed_entries])
                })
                executive_summary = exec_summary_response.content
            except Exception as e:
                logger.error(f"Error generating executive summary: {e}")
                executive_summary = "Executive summary could not be generated."

            # Final report structure
            report_data = {
                'report_metadata': {
                    'total_entries_processed': len(processed_entries),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'market_focus': consumer_insights_data.get('target_market', 'japanese_curry'),
                    'report_type': 'consumer_insights_summary',
                    'data_quality_score': self._calculate_data_quality_score(processed_entries)
                },
                'consumer_insights_summary': {
                    'processed_entries': processed_entries,
                    'key_themes': self._extract_key_themes(processed_entries),
                    'data_sources': list(set([entry['source_category'] for entry in processed_entries])),
                    'insight_categories': self._categorize_insights(processed_entries),
                    'sentiment_analysis': self._analyze_overall_sentiment(processed_entries),
                    'confidence_distribution': self._analyze_confidence_distribution(processed_entries),
                },
                'pain_points': pain_points,
                'structured_insights': consumer_insights_data.get('structured_insights', []),
                'customer_mapping_integration': consumer_insights_data.get('customer_mapping_integration', {}),
                'executive_summary_data': executive_summary,
                'key_findings': self._extract_key_findings(processed_entries),
                'recommendations': self._generate_recommendations(processed_entries, pain_points),
                'consumer_insights': self._format_for_report_generator(processed_entries),
                'customer_personas': self._generate_customer_personas(processed_entries),
                'purchase_journey': self._generate_purchase_journey(processed_entries),
            }

            logger.info(f"Successfully processed {len(processed_entries)} entries")
            return report_data

        except Exception as e:
            logger.error(f"Error processing consumer insights for report: {e}")
            return {
                'error': str(e),
                'report_metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'status': 'failed'
                },
                'consumer_insights_summary': {},
                'pain_points': [],
                'structured_insights': [],
                'customer_mapping_integration': {}
            }

    def _extract_key_themes(self, processed_entries: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key themes from processed entries for quick reference.
        """
        themes = []

        # Common themes in Japanese curry consumer insights
        theme_keywords = {
            'convenience': ['convenience', 'ready-to-eat', 'quick', 'easy', 'instant'],
            'authenticity': ['authentic', 'traditional', 'genuine', 'original'],
            'health': ['health', 'healthy', 'organic', 'natural', 'low-sodium', 'vegan'],
            'flavor': ['flavor', 'taste', 'spicy', 'sweet', 'savory'],
            'social_media': ['social media', 'instagram', 'youtube', 'influencer'],
            'family': ['family', 'comfort', 'nutritious', 'children'],
            'premium': ['premium', 'gourmet', 'high-quality', 'luxury']
        }

        # Count theme occurrences
        theme_counts = {theme: 0 for theme in theme_keywords.keys()}

        for entry in processed_entries:
            content_lower = (entry['summary'] + ' ' + entry['original_content']).lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    theme_counts[theme] += 1

        # Return themes with significant presence
        for theme, count in theme_counts.items():
            if count > 0:
                themes.append(f"{theme.title()} (mentioned in {count} entries)")

        return themes[:10]  # Limit to top 10 themes

    def _calculate_confidence_score(self, content: str, summary: str) -> float:
        """Calculate confidence score based on content quality and summary coherence."""
        try:
            # Simple confidence calculation based on content length and summary quality
            content_length = len(content.strip())
            summary_length = len(summary.strip())

            # Base confidence on content completeness
            if content_length < 100:
                base_confidence = 0.3
            elif content_length < 500:
                base_confidence = 0.6
            else:
                base_confidence = 0.8

            # Adjust based on summary quality
            if summary_length > 50 and "insight" in summary.lower():
                base_confidence += 0.1

            return min(1.0, base_confidence)
        except Exception:
            return 0.5  # Default confidence

    def _categorize_insight(self, summary: str) -> str:
        """Categorize insight based on content analysis."""
        summary_lower = summary.lower()

        if any(keyword in summary_lower for keyword in ['taste', 'flavor', 'spicy', 'sweet']):
            return 'taste_preference'
        elif any(keyword in summary_lower for keyword in ['convenience', 'quick', 'easy', 'instant']):
            return 'convenience'
        elif any(keyword in summary_lower for keyword in ['price', 'cost', 'expensive', 'cheap']):
            return 'price_sensitivity'
        elif any(keyword in summary_lower for keyword in ['health', 'healthy', 'organic', 'natural']):
            return 'health_concern'
        elif any(keyword in summary_lower for keyword in ['authentic', 'traditional', 'genuine']):
            return 'authenticity'
        else:
            return 'general_insight'

    def _analyze_sentiment(self, summary: str) -> str:
        """Analyze sentiment of the insight."""
        summary_lower = summary.lower()

        positive_words = ['love', 'great', 'excellent', 'amazing', 'perfect', 'best', 'wonderful']
        negative_words = ['hate', 'terrible', 'awful', 'worst', 'bad', 'disappointing', 'poor']

        positive_count = sum(1 for word in positive_words if word in summary_lower)
        negative_count = sum(1 for word in negative_words if word in summary_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _extract_key_phrases(self, summary: str) -> List[str]:
        """Extract key phrases from summary for report generation."""
        # Simple key phrase extraction
        words = summary.lower().split()
        key_phrases = []

        # Look for important phrases
        important_words = ['curry', 'japanese', 'taste', 'flavor', 'convenience', 'price', 'health', 'authentic']
        for word in important_words:
            if word in summary.lower():
                key_phrases.append(word)

        return key_phrases[:5]  # Limit to top 5

    def _calculate_data_quality_score(self, processed_entries: List[Dict[str, Any]]) -> float:
        """Calculate overall data quality score for the processed entries."""
        if not processed_entries:
            return 0.0

        total_confidence = sum(entry.get('confidence_score', 0.5) for entry in processed_entries)
        avg_confidence = total_confidence / len(processed_entries)

        # Factor in data completeness
        completeness_factor = min(1.0, len(processed_entries) / 10)  # Normalize to 10 entries

        return (avg_confidence + completeness_factor) / 2

    def _categorize_insights(self, processed_entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize insights by type for report generation."""
        categories = {}
        for entry in processed_entries:
            category = entry.get('insight_category', 'general_insight')
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _analyze_overall_sentiment(self, processed_entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze overall sentiment distribution."""
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for entry in processed_entries:
            sentiment = entry.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        return sentiment_counts

    def _analyze_confidence_distribution(self, processed_entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze confidence score distribution."""
        confidence_ranges = {'high': 0, 'medium': 0, 'low': 0}
        for entry in processed_entries:
            confidence = entry.get('confidence_score', 0.5)
            if confidence >= 0.8:
                confidence_ranges['high'] += 1
            elif confidence >= 0.5:
                confidence_ranges['medium'] += 1
            else:
                confidence_ranges['low'] += 1
        return confidence_ranges

    def _generate_executive_summary_data(self, processed_entries: List[Dict[str, Any]], pain_points: List[str]) -> Dict[str, Any]:
        """Generate executive summary data for report generation."""
        return {
            'total_insights': len(processed_entries),
            'total_pain_points': len(pain_points),
            'top_themes': self._extract_key_themes(processed_entries)[:5],
            'data_quality': 'high' if len(processed_entries) >= 5 else 'medium' if len(processed_entries) >= 2 else 'low',
            'insight_categories': self._categorize_insights(processed_entries),
            'sentiment_summary': self._analyze_overall_sentiment(processed_entries)
        }

    def _extract_key_findings(self, processed_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key findings for report generation."""
        key_findings = []

        # Get top insights by confidence score
        sorted_entries = sorted(processed_entries, key=lambda x: x.get('confidence_score', 0), reverse=True)

        for entry in sorted_entries[:5]:  # Top 5 findings
            key_findings.append({
                'title': entry.get('title', 'Consumer Insight'),
                'summary': entry.get('summary', ''),
                'category': entry.get('insight_category', 'general'),
                'confidence': entry.get('confidence_score', 0.5),
                'sentiment': entry.get('sentiment', 'neutral'),
                'source': entry.get('source_category', 'Unknown')
            })

        return key_findings

    def _generate_recommendations(self, processed_entries: List[Dict[str, Any]], pain_points: List[str]) -> List[str]:
        """Generate strategic recommendations based on insights and pain points."""
        recommendations = []

        # Analyze pain points for recommendations
        if pain_points:
            recommendations.append(f"Address {len(pain_points)} identified consumer pain points to improve market positioning")

        # Analyze insight categories for recommendations
        categories = self._categorize_insights(processed_entries)
        if categories.get('convenience', 0) > 0:
            recommendations.append("Focus on convenience features as consumers prioritize ease of use")
        if categories.get('price_sensitivity', 0) > 0:
            recommendations.append("Consider pricing strategies to address consumer price sensitivity")
        if categories.get('health_concern', 0) > 0:
            recommendations.append("Emphasize health benefits and natural ingredients in marketing")

        # General recommendations
        if len(processed_entries) >= 5:
            recommendations.append("Leverage comprehensive consumer insights for targeted marketing strategies")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _format_for_report_generator(self, processed_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format consumer insights data for the report generator's expected format.
        This creates the 'consumer_insights' structure that the report generator expects.
        """
        try:
            # Convert processed entries to the format expected by report generator
            structured_insights = []

            for entry in processed_entries:
                structured_insight = {
                    'extracted_insight': entry.get('summary', ''),
                    'confidence_score': entry.get('confidence_score', 0.5),
                    'source': entry.get('source_category', 'Unknown'),
                    'category': entry.get('insight_category', 'general'),
                    'sentiment': entry.get('sentiment', 'neutral'),
                    'title': entry.get('title', 'Consumer Insight'),
                    'key_phrases': entry.get('key_phrases', [])
                }
                structured_insights.append(structured_insight)

            return {
                'structured_insights': structured_insights,
                'total_insights': len(structured_insights),
                'data_sources': list(set([entry.get('source_category', 'Unknown') for entry in processed_entries])),
                'insight_categories': self._categorize_insights(processed_entries),
                'sentiment_analysis': self._analyze_overall_sentiment(processed_entries)
            }

        except Exception as e:
            logger.error(f"Error formatting for report generator: {e}")
            return {'structured_insights': [], 'total_insights': 0}

    def _generate_customer_personas(self, processed_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate customer personas based on consumer insights data.
        This creates the 'customer_personas' structure that the report generator expects.
        """
        try:
            personas = []

            # Analyze insights to create personas
            categories = self._categorize_insights(processed_entries)
            sentiment_analysis = self._analyze_overall_sentiment(processed_entries)

            # Convenience-focused persona
            if categories.get('convenience', 0) > 0:
                personas.append({
                    'name': 'Convenience Seeker',
                    'description': 'Consumers who prioritize quick and easy meal solutions, often choosing ready-to-eat options over traditional preparation methods.',
                    'key_characteristics': ['Time-conscious', 'Prefers instant solutions', 'Values ease of use'],
                    'insights_count': categories.get('convenience', 0)
                })

            # Authenticity-focused persona
            if categories.get('authenticity', 0) > 0:
                personas.append({
                    'name': 'Authenticity Enthusiast',
                    'description': 'Consumers who value traditional and authentic Japanese curry flavors, willing to invest time in proper preparation.',
                    'key_characteristics': ['Quality-focused', 'Traditional preferences', 'Willing to pay premium'],
                    'insights_count': categories.get('authenticity', 0)
                })

            # Health-conscious persona
            if categories.get('health_concern', 0) > 0:
                personas.append({
                    'name': 'Health-Conscious Consumer',
                    'description': 'Consumers who prioritize health benefits and natural ingredients in their food choices.',
                    'key_characteristics': ['Health-focused', 'Ingredient-conscious', 'Natural preferences'],
                    'insights_count': categories.get('health_concern', 0)
                })

            # Price-sensitive persona
            if categories.get('price_sensitivity', 0) > 0:
                personas.append({
                    'name': 'Price-Conscious Buyer',
                    'description': 'Consumers who are sensitive to pricing and look for value in their purchases.',
                    'key_characteristics': ['Price-sensitive', 'Value-focused', 'Budget-conscious'],
                    'insights_count': categories.get('price_sensitivity', 0)
                })

            return personas[:4]  # Limit to top 4 personas

        except Exception as e:
            logger.error(f"Error generating customer personas: {e}")
            return []

    def _generate_purchase_journey(self, processed_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate purchase journey insights based on consumer data.
        This creates the 'purchase_journey' structure that the report generator expects.
        """
        try:
            journey_stages = {}

            # Analyze insights for journey patterns
            convenience_insights = [entry for entry in processed_entries if entry.get('insight_category') == 'convenience']
            authenticity_insights = [entry for entry in processed_entries if entry.get('insight_category') == 'authenticity']
            price_insights = [entry for entry in processed_entries if entry.get('insight_category') == 'price_sensitivity']

            # Awareness stage
            if convenience_insights or authenticity_insights:
                journey_stages['awareness'] = "Consumers discover Japanese curry through social media, food blogs, and recommendations from friends and family."

            # Consideration stage
            if price_insights or authenticity_insights:
                journey_stages['consideration'] = "Consumers evaluate options based on authenticity, price point, and convenience factors. They compare brands and read reviews."

            # Purchase stage
            if convenience_insights:
                journey_stages['purchase'] = "Purchase decisions are influenced by convenience factors, with consumers preferring ready-to-eat options or easy-to-prepare products."

            # Usage stage
            if authenticity_insights:
                journey_stages['usage'] = "Consumers value authentic taste and quality during consumption, often sharing experiences on social media."

            # Post-purchase stage
            sentiment_analysis = self._analyze_overall_sentiment(processed_entries)
            if sentiment_analysis.get('positive', 0) > sentiment_analysis.get('negative', 0):
                journey_stages['post_purchase'] = "Positive experiences lead to repeat purchases and recommendations to others."
            else:
                journey_stages['post_purchase'] = "Mixed experiences lead to selective repurchasing and detailed review sharing."

            return journey_stages

        except Exception as e:
            logger.error(f"Error generating purchase journey: {e}")
            return {}

    def generate_consumer_report_section(self, consumer_insights_data: Dict[str, Any]) -> str:
        """
        Generate a formatted consumer insights section for report generation.
        This method demonstrates how to use the enhanced consumer data in reports.
        """
        try:
            if not consumer_insights_data:
                return "Consumer insights data not available."

            report_sections = []

            # Executive Summary Section
            executive_data = consumer_insights_data.get('executive_summary_data', {})
            if executive_data:
                report_sections.append("## Consumer Analysis Executive Summary")
                report_sections.append(f"**Total Insights Analyzed:** {executive_data.get('total_insights', 0)}")
                report_sections.append(f"**Pain Points Identified:** {executive_data.get('total_pain_points', 0)}")
                report_sections.append(f"**Data Quality:** {executive_data.get('data_quality', 'Unknown')}")
                report_sections.append("")

            # Key Findings Section
            key_findings = consumer_insights_data.get('key_findings', [])
            if key_findings:
                report_sections.append("## Key Consumer Findings")
                for i, finding in enumerate(key_findings, 1):
                    report_sections.append(f"### {i}. {finding.get('title', 'Consumer Insight')}")
                    report_sections.append(f"**Category:** {finding.get('category', 'General').replace('_', ' ').title()}")
                    report_sections.append(f"**Sentiment:** {finding.get('sentiment', 'Neutral').title()}")
                    report_sections.append(f"**Confidence:** {finding.get('confidence', 0):.2f}")
                    report_sections.append(f"**Summary:** {finding.get('summary', 'No summary available')}")
                    report_sections.append(f"**Source:** {finding.get('source', 'Unknown')}")
                    report_sections.append("")

            # Insights Summary Section
            insights_summary = consumer_insights_data.get('consumer_insights_summary', {})
            if insights_summary:
                report_sections.append("## Consumer Insights Analysis")

                # Key Themes
                key_themes = insights_summary.get('key_themes', [])
                if key_themes:
                    report_sections.append("### Key Themes Identified")
                    for theme in key_themes:
                        report_sections.append(f"- {theme}")
                    report_sections.append("")

                # Data Sources
                data_sources = insights_summary.get('data_sources', [])
                if data_sources:
                    report_sections.append("### Data Sources")
                    report_sections.append(f"Analysis based on: {', '.join(data_sources)}")
                    report_sections.append("")

                # Sentiment Analysis
                sentiment_analysis = insights_summary.get('sentiment_analysis', {})
                if sentiment_analysis:
                    report_sections.append("### Sentiment Analysis")
                    for sentiment, count in sentiment_analysis.items():
                        report_sections.append(f"- **{sentiment.title()}:** {count} insights")
                    report_sections.append("")

                # Confidence Distribution
                confidence_dist = insights_summary.get('confidence_distribution', {})
                if confidence_dist:
                    report_sections.append("### Confidence Distribution")
                    for level, count in confidence_dist.items():
                        report_sections.append(f"- **{level.title()} Confidence:** {count} insights")
                    report_sections.append("")

            # Strategic Recommendations
            recommendations = consumer_insights_data.get('recommendations', [])
            if recommendations:
                report_sections.append("## Strategic Recommendations")
                for i, rec in enumerate(recommendations, 1):
                    report_sections.append(f"{i}. {rec}")
                report_sections.append("")

            # Pain Points Section
            pain_points = consumer_insights_data.get('pain_points', [])
            if pain_points:
                report_sections.append("## Identified Consumer Pain Points")
                for i, pain_point in enumerate(pain_points, 1):
                    report_sections.append(f"{i}. {pain_point}")
                report_sections.append("")

            return "\n".join(report_sections)

        except Exception as e:
            logger.error(f"Error generating consumer report section: {e}")
            return f"Error generating consumer insights section: {str(e)}"

    def get_report_metrics(self, consumer_insights_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics from consumer insights data for report generation.
        """
        try:
            metrics = {}

            # Basic metrics
            executive_data = consumer_insights_data.get('executive_summary_data', {})
            metrics.update({
                'total_insights': executive_data.get('total_insights', 0),
                'total_pain_points': executive_data.get('total_pain_points', 0),
                'data_quality': executive_data.get('data_quality', 'unknown')
            })

            # Advanced metrics
            insights_summary = consumer_insights_data.get('consumer_insights_summary', {})
            if insights_summary:
                metrics.update({
                    'data_sources_count': len(insights_summary.get('data_sources', [])),
                    'key_themes_count': len(insights_summary.get('key_themes', [])),
                    'sentiment_distribution': insights_summary.get('sentiment_analysis', {}),
                    'confidence_distribution': insights_summary.get('confidence_distribution', {}),
                    'insight_categories': insights_summary.get('insight_categories', {})
                })

            # Report metadata
            report_metadata = consumer_insights_data.get('report_metadata', {})
            metrics.update({
                'analysis_timestamp': report_metadata.get('analysis_timestamp', ''),
                'data_quality_score': report_metadata.get('data_quality_score', 0.0),
                'market_focus': report_metadata.get('market_focus', 'unknown')
            })

            return metrics

        except Exception as e:
            logger.error(f"Error extracting report metrics: {e}")
            return {'error': str(e)}

    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Main entry point for the Consumer Analysis Agent."""
        return await self.analyze_consumer_insights(state)
