import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage

from ...classes import MarketResearchState, MarketTrend
from .base import BaseResearcher

logger = logging.getLogger(__name__)


class TrendAnalysisAgent(BaseResearcher):
    """
    Trend Analysis Agent for 3C market research focusing on Japanese curry market.
    Monitors industry publications, market research reports, and consumer behavior studies
    to identify emerging trends, market movements, and future predictions.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "trend_analyst"
        
        # Japanese curry market trend keywords for enhanced search
        self.trend_keywords = [
            "japanese curry trends", "curry market growth", "food trends japan",
            "curry consumption patterns", "instant curry market", "curry industry analysis",
            "japanese food market", "curry restaurant trends", "curry product innovation",
            "curry market forecast", "food industry trends", "asian food trends"
        ]
        
        # Trend categories for classification
        self.trend_categories = [
            "consumption_patterns", "product_innovation", "market_growth", "demographic_shifts",
            "health_trends", "convenience_trends", "premium_trends", "sustainability_trends",
            "technology_adoption", "distribution_channels", "seasonal_patterns", "cultural_shifts"
        ]
        
        # Adoption curve stages
        self.adoption_stages = [
            "emerging", "early_adoption", "growing", "mainstream", "mature", "declining"
        ]

    async def analyze_market_trends(self, state: MarketResearchState) -> Dict[str, Any]:
        """
        Main method to analyze market trends for Japanese curry market.
        Identifies emerging trends, growth patterns, and future predictions.
        """
        target_market = state.get('target_market', 'japanese_curry')
        company = state.get('company', 'Unknown Company')
        
        msg = [f"📈 Trend Analysis Agent analyzing {target_market} market trends for {company}"]
        
        # Generate trend-focused search queries
        queries = await self.generate_trend_queries(state)
        
        # Add message to show subqueries
        subqueries_msg = "🔍 Trend analysis queries:\n" + "\n".join([f"• {query}" for query in queries])
        messages = state.get('messages', [])
        messages.append(AIMessage(content=subqueries_msg))
        state['messages'] = messages

        # Send queries through WebSocket
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Trend analysis queries generated",
                    result={
                        "step": "Trend Analysis",
                        "analyst_type": "Trend Analyst",
                        "queries": queries,
                        "target_market": target_market
                    }
                )
        
        # Collect trend data from multiple sources
        trend_data = {}
        try:
            # Search for trend insights using generated queries
            for query in queries:
                documents = await self.search_documents(state, [query])
                if documents:
                    for url, doc in documents.items():
                        doc['query'] = query
                        doc['analysis_type'] = 'trend_analysis'
                        trend_data[url] = doc
            
            msg.append(f"\n✓ Found {len(trend_data)} trend analysis documents")
            
            if websocket_manager := state.get('websocket_manager'):
                if job_id := state.get('job_id'):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Collected {len(trend_data)} trend analysis documents",
                        result={
                            "step": "Data Collection",
                            "analyst_type": "Trend Analyst",
                            "documents_found": len(trend_data)
                        }
                    )
                    
        except Exception as e:
            msg.append(f"\n⚠️ Error during trend data collection: {str(e)}")
            logger.error(f"Trend data collection error: {e}")
        
        # Extract structured market trends
        market_trends = await self.extract_market_trends(trend_data, state)
        
        # Generate trend predictions
        trend_predictions = await self.generate_trend_predictions(market_trends, state)
        
        # Position trends on adoption curves
        adoption_curves = await self.position_adoption_curves(market_trends, state)
        
        # Generate future market predictions
        future_predictions = await self.generate_future_predictions(market_trends, trend_predictions, state)
        
        # Update state with trend analysis results
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        
        # Store results in MarketResearchState format
        market_trends_data = {
            'raw_data': trend_data,
            'structured_trends': market_trends,
            'analysis_timestamp': datetime.now().isoformat(),
            'market_focus': target_market
        }
        
        # Return state updates - avoid returning conflicting keys
        # Only return trend-specific keys to prevent state conflicts
        return {
            'market_trends': market_trends_data,
            'trend_predictions': trend_predictions,
            'adoption_curves': adoption_curves
        }

    async def generate_trend_queries(self, state: MarketResearchState) -> List[str]:
        """Generate targeted search queries for trend analysis of Japanese curry market."""
        target_market = state.get('target_market', 'japanese_curry')
        
        prompt = f"""
         Generate targeted search queries to identify the latest  market trends, growth patterns, and emerging movements 
         in the {target_market} market. Focus on current and future-looking trends:
         
         - Latest Japanese curry market trends and industry forecasts
         - Emerging consumer behavior shifts and next-generation preferences in curry consumption
         - product innovation trends: AI-designed flavors, smart packaging, personalized nutrition
         - Future market growth projections and expansion opportunities for Japanese curry
         - Gen Z and millennial consumption patterns affecting Japanese curry demand
         - Health and sustainability mega-trends reshaping Japanese curry products
         - Technology disruption: e-commerce, delivery innovation, cooking automation in curry market
         - Climate adaptation and seasonal trend evolution in Japanese curry preferences
         - Global expansion trends and international market opportunities for Japanese curry brands
         - Premium and luxury market evolution in Japanese curry sector
         
         Generate queries that capture cutting-edge developments, future predictions, and transformative trends 
         shaping the Japanese curry market in 2025 and beyond.
         """
        
        return await self.generate_queries(state, prompt)

    async def extract_market_trends(self, trend_data: Dict[str, Any], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Extract structured market trends from collected data.
        Uses LLM to analyze content and identify trend patterns.
        """
        if not trend_data:
            return []
        
        trends = []
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Process documents in batches to extract trends
            for url, doc in trend_data.items():
                content = doc.get('content', '')
                if not content or len(content.strip()) < 50:
                    continue
                
                # Enhanced LLM prompt for 2025 Japanese curry trend analysis
                trend_prompt = f"""
                As a professional market trend analyst and futurist, analyze the following content about the Japanese curry market 
                and extract cutting-edge 2025 trends and future predictions:

                Content: {content[:2500]}

                **PRIMARY FOCUS: Extract 2025 trends and future predictions (2025-2030) for the Japanese curry market.**

                **TREND ANALYSIS FRAMEWORK:**
                1. **2025 Innovation Trends**: AI-designed flavors, smart packaging, personalized curry products
                2. **Next-Gen Consumer Behavior**: Digital natives, sustainability demands, health optimization
                3. **Technology Disruption**: E-commerce evolution, cooking automation, IoT-enabled products
                4. **Market Evolution**: Premium segments, global expansion, niche specialization
                5. **Demographic Transformation**: Aging society, urbanization, cultural fusion preferences
                6. **Sustainability Revolution**: Carbon-neutral products, circular economy, local sourcing
                7. **Health & Wellness Mega-Trends**: Functional foods, personalized nutrition, dietary restrictions
                8. **Future Commerce Models**: Social commerce, subscription services, direct-to-consumer brands

                **For each significant 2025 trend identified, provide:**
                - **trend_name**: Future-focused, specific trend name (e.g., "AI-Personalized Curry Flavor Matching")
                - **description**: Detailed 2025 context with future implications and market transformation potential
                - **category**: Select from {self.trend_categories}
                - **growth_direction**: accelerating/emerging/transforming/disrupting
                - **time_horizon**: immediate_2025/short_term_2026/medium_term_2027_2029/long_term_2030_plus
                - **impact_level**: transformative/high/medium/low (focus on transformative and high-impact trends)
                - **confidence**: 0.7-1.0 (higher for data-backed predictions and emerging evidence)
                - **future_indicators**: Specific signals or evidence pointing to this trend's emergence
                - **business_opportunity**: How companies can capitalize on this trend
                - **adoption_timeline**: When this trend will reach mainstream adoption

                **OUTPUT REQUIREMENTS:**
                - Prioritize forward-looking, transformative trends over current/obvious ones
                - Focus on trends that will reshape the industry by 2025-2030
                - Extract 3-7 most significant future-oriented trends from this content
                - Emphasize innovation, technology, and behavioral transformation trends
                """
                
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a senior market trend analyst and futurist specializing in Japanese food market innovation. You excel at identifying transformative trends, predicting future market developments, and translating emerging signals into actionable business intelligence. You focus on trends and beyond, emphasizing technology disruption, consumer behavior evolution, and market transformation patterns."},
                            {"role": "user", "content": trend_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1200
                    )
                    
                    # Parse LLM response to extract trends
                    trend_text = response.choices[0].message.content
                    
                    # Create structured trend object
                    trend = {
                        'trend_id': str(uuid.uuid4()),
                        'source_url': url,
                        'source_title': doc.get('title', ''),
                        'query': doc.get('query', ''),
                        'raw_content': content[:500],  # Store snippet
                        'extracted_trends': trend_text,
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': 0.8  # Default confidence
                    }
                    
                    trends.append(trend)
                    
                except Exception as e:
                    logger.error(f"Error extracting trends from {url}: {e}")
                    continue
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Extracted {len(trends)} market trends",
                    result={
                        "step": "Trend Extraction",
                        "trends_extracted": len(trends)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in market trend extraction: {e}")
        
        return trends

    async def generate_trend_predictions(self, market_trends: List[Dict[str, Any]], state: MarketResearchState) -> List[Dict[str, Any]]:
        """
        Generate trend predictions based on identified market trends.
        Creates forecasts for trend evolution and market impact.
        """
        if not market_trends:
            return []
        
        predictions = []
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Combine trend data for prediction analysis
            trends_summary = ""
            for trend in market_trends[:10]:  # Limit to top 10 trends
                trends_summary += trend.get('extracted_trends', '')[:300] + "\n\n"
            
            if not trends_summary.strip():
                return []
            
            # Use LLM to generate enhanced future predictions
            prediction_prompt = f"""
            Based on the following 2025 market trends in the Japanese curry market, generate strategic predictions 
            for transformative developments through 2030:

            **2025 Trend Intelligence:**
            {trends_summary}

            **GENERATE 7-10 STRATEGIC PREDICTIONS (2025-2030) focusing on:**
            
            **Market Transformation Predictions:**
            - How 2025 trends will scale and reshape the entire industry by 2030
            - Technology disruption timelines: AI, automation, personalization breakthroughs
            - Consumer behavior revolution: generational shifts, lifestyle evolution, preference changes
            - Product innovation leaps: next-generation formats, functional ingredients, smart products
            - Market expansion opportunities: global markets, new segments, untapped demographics
            - Industry consolidation patterns: mergers, partnerships, new market entrants
            - Sustainability transformation: carbon-neutral supply chains, circular economy adoption
            - Economic factor impacts: inflation, supply chain evolution, pricing strategies

            **For each prediction, provide:**
            - **prediction_title**: Bold, transformative prediction statement (e.g., "AI Will Personalize 80% of Japanese Curry Products by 2028")
            - **description**: Comprehensive explanation with market transformation context and strategic implications
            - **time_horizon**: 2025_immediate/2026_short/2027_2028_medium/2029_2030_long
            - **probability**: very_high/high/medium/emerging (focus on high-probability transformations)
            - **impact_level**: industry_transforming/market_reshaping/high/medium (prioritize transformative impacts)
            - **key_drivers**: Primary forces, technologies, and trends driving this prediction
            - **market_implications**: How this will change competitive dynamics and business models
            - **preparation_timeline**: When companies should start preparing for this change

            **FOCUS ON:** Breakthrough predictions that will fundamentally reshape the Japanese curry market landscape.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior strategic market forecasting analyst and futurist specializing in Japanese food industry transformation. You excel at identifying breakthrough market developments, predicting industry-reshaping trends, and forecasting technological disruptions. You focus on 2025-2030 timeframes and transformative predictions that will fundamentally change business landscapes."},
                    {"role": "user", "content": prediction_prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            # Parse predictions from response
            prediction_text = response.choices[0].message.content
            
            # Create structured prediction objects (simplified parsing)
            prediction_lines = prediction_text.split('\n')
            current_prediction = {}
            
            for line in prediction_lines:
                line = line.strip()
                if ('prediction' in line.lower() and ':' in line) or line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.')):
                    if current_prediction:
                        predictions.append(current_prediction)
                    current_prediction = {
                        'prediction_id': str(uuid.uuid4()),
                        'title': line.split(':')[-1].strip() if ':' in line else line.strip(),
                        'description': '',
                        'time_horizon': 'medium_term',
                        'probability': 'medium',
                        'impact_level': 'medium',
                        'key_drivers': [],
                        'timestamp': datetime.now().isoformat()
                    }
                elif current_prediction and line and not line.startswith('#'):
                    if not current_prediction['description']:
                        current_prediction['description'] = line
                    else:
                        # Parse specific attributes
                        if 'time_horizon' in line.lower():
                            for horizon in ['6_months', '1_year', '2_years', '3_years']:
                                if horizon.replace('_', ' ') in line.lower():
                                    current_prediction['time_horizon'] = horizon
                                    break
                        elif 'probability' in line.lower():
                            for prob in ['high', 'medium', 'low']:
                                if prob in line.lower():
                                    current_prediction['probability'] = prob
                                    break
                        elif 'impact' in line.lower():
                            for impact in ['high', 'medium', 'low']:
                                if impact in line.lower():
                                    current_prediction['impact_level'] = impact
                                    break
                        else:
                            current_prediction['key_drivers'].append(line)
            
            # Add the last prediction
            if current_prediction:
                predictions.append(current_prediction)
            
            # Ensure we have at least basic predictions if parsing failed
            if not predictions:
                predictions = [
                    {
                        'prediction_id': str(uuid.uuid4()),
                        'title': 'Increased Demand for Premium Japanese Curry Products',
                        'description': 'Growing consumer preference for high-quality, authentic Japanese curry experiences',
                        'time_horizon': '2_years',
                        'probability': 'high',
                        'impact_level': 'high',
                        'key_drivers': ['Quality consciousness', 'Authenticity seeking', 'Premium market growth'],
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'prediction_id': str(uuid.uuid4()),
                        'title': 'Rise of Convenient Japanese Curry Solutions',
                        'description': 'Increased adoption of ready-to-eat and quick-preparation curry products',
                        'time_horizon': '1_year',
                        'probability': 'high',
                        'impact_level': 'medium',
                        'key_drivers': ['Busy lifestyles', 'Convenience trends', 'Time constraints'],
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Generated {len(predictions)} trend predictions",
                    result={
                        "step": "Trend Prediction",
                        "predictions_generated": len(predictions)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating trend predictions: {e}")
        
        return predictions

    async def position_adoption_curves(self, market_trends: List[Dict[str, Any]], state: MarketResearchState) -> Dict[str, Any]:
        """
        Position identified trends on adoption curve timelines.
        Determines where each trend sits in the innovation adoption lifecycle.
        """
        if not market_trends:
            return {}
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Analyze trends for adoption curve positioning
            trends_text = "\n".join([trend.get('extracted_trends', '')[:200] for trend in market_trends[:10]])
            
            adoption_prompt = f"""
            Based on the following market trends in the Japanese curry market, position each trend on the innovation adoption curve:
            
            Market Trends:
            {trends_text}
            
            For each identifiable trend, determine its position on the adoption curve:
            - Emerging: New trend just starting to appear, limited awareness
            - Early Adoption: Trend gaining traction with innovators and early adopters
            - Growing: Trend expanding to early majority, gaining momentum
            - Mainstream: Trend widely adopted by majority market
            - Mature: Trend fully established, reaching late majority
            - Declining: Trend losing relevance, being replaced by newer trends
            
            Provide analysis for 5-8 key trends with:
            - trend_name: Clear name for the trend
            - adoption_stage: One of the stages above
            - market_penetration: Estimated percentage of market adoption
            - growth_velocity: fast/moderate/slow adoption speed
            - time_to_mainstream: Estimated time to reach mainstream adoption
            - key_indicators: Evidence supporting the positioning
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an innovation adoption analyst specializing in Japanese curry market trend positioning."},
                    {"role": "user", "content": adoption_prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            adoption_text = response.choices[0].message.content
            
            # Structure the adoption curve analysis
            adoption_curves = {
                'analysis_id': str(uuid.uuid4()),
                'market_focus': state.get('target_market', 'japanese_curry'),
                'analysis_date': datetime.now().isoformat(),
                'curve_positions': {
                    'emerging': [],
                    'early_adoption': [],
                    'growing': [],
                    'mainstream': [],
                    'mature': [],
                    'declining': []
                },
                'raw_analysis': adoption_text,
                'methodology': 'LLM-based trend positioning analysis'
            }
            
            # Parse adoption positioning (simplified - in production, use more sophisticated parsing)
            lines = adoption_text.split('\n')
            current_trend = None
            
            for line in lines:
                line = line.strip()
                if any(stage in line.lower() for stage in self.adoption_stages):
                    # Identify which stage this trend belongs to
                    for stage in self.adoption_stages:
                        if stage in line.lower():
                            trend_name = line.split(':')[0].strip() if ':' in line else line.strip()
                            trend_info = {
                                'trend_name': trend_name,
                                'description': '',
                                'market_penetration': 'unknown',
                                'growth_velocity': 'moderate',
                                'indicators': []
                            }
                            
                            # Map adoption stages to our curve positions
                            if stage in ['emerging']:
                                adoption_curves['curve_positions']['emerging'].append(trend_info)
                            elif stage in ['early_adoption']:
                                adoption_curves['curve_positions']['early_adoption'].append(trend_info)
                            elif stage in ['growing']:
                                adoption_curves['curve_positions']['growing'].append(trend_info)
                            elif stage in ['mainstream']:
                                adoption_curves['curve_positions']['mainstream'].append(trend_info)
                            elif stage in ['mature']:
                                adoption_curves['curve_positions']['mature'].append(trend_info)
                            elif stage in ['declining']:
                                adoption_curves['curve_positions']['declining'].append(trend_info)
                            
                            current_trend = trend_info
                            break
                elif current_trend and line and not line.startswith('#'):
                    if not current_trend['description']:
                        current_trend['description'] = line
                    else:
                        current_trend['indicators'].append(line)
            
            # Ensure we have some positioning if parsing failed
            if not any(adoption_curves['curve_positions'].values()):
                adoption_curves['curve_positions']['growing'] = [
                    {
                        'trend_name': 'Premium Japanese Curry Products',
                        'description': 'Growing demand for high-quality, authentic curry products',
                        'market_penetration': '25-40%',
                        'growth_velocity': 'fast',
                        'indicators': ['Increasing premium product launches', 'Consumer willingness to pay more']
                    }
                ]
                adoption_curves['curve_positions']['emerging'] = [
                    {
                        'trend_name': 'Plant-Based Japanese Curry Options',
                        'description': 'Emerging trend toward vegetarian and vegan curry alternatives',
                        'market_penetration': '5-10%',
                        'growth_velocity': 'moderate',
                        'indicators': ['New product introductions', 'Health consciousness growth']
                    }
                ]
            
            if websocket_manager and job_id:
                total_positioned = sum(len(trends) for trends in adoption_curves['curve_positions'].values())
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Positioned {total_positioned} trends on adoption curves",
                    result={
                        "step": "Adoption Curve Analysis",
                        "trends_positioned": total_positioned
                    }
                )
                
        except Exception as e:
            logger.error(f"Error positioning adoption curves: {e}")
            adoption_curves = {
                'analysis_id': str(uuid.uuid4()),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
        
        return adoption_curves

    async def generate_future_predictions(self, market_trends: List[Dict[str, Any]], trend_predictions: List[Dict[str, Any]], state: MarketResearchState) -> Dict[str, Any]:
        """
        Generate comprehensive future market predictions based on trend analysis.
        Creates strategic forecasts for market evolution and opportunities.
        """
        if not market_trends and not trend_predictions:
            return {}
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Combine trend and prediction data
            combined_analysis = ""
            
            if market_trends:
                trends_summary = "\n".join([trend.get('extracted_trends', '')[:150] for trend in market_trends[:8]])
                combined_analysis += f"Current Market Trends:\n{trends_summary}\n\n"
            
            if trend_predictions:
                predictions_summary = "\n".join([f"- {pred.get('title', '')}: {pred.get('description', '')[:100]}" for pred in trend_predictions[:6]])
                combined_analysis += f"Trend Predictions:\n{predictions_summary}\n\n"
            
            future_prompt = f"""
            Based on comprehensive trend analysis of the Japanese curry market, generate strategic future market predictions:
            
            {combined_analysis}
            
            Create a comprehensive future market outlook covering:
            
            1. Market Size and Growth Projections (1-5 years)
            2. Consumer Behavior Evolution
            3. Product Innovation Directions
            4. Competitive Landscape Changes
            5. Distribution Channel Evolution
            6. Technology Impact and Adoption
            7. Regulatory and Cultural Influences
            8. Strategic Opportunities and Threats
            
            For each area, provide:
            - Current state assessment
            - Expected changes and evolution
            - Timeline for key developments
            - Impact on market players
            - Strategic implications
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strategic market forecasting analyst creating comprehensive future predictions for the Japanese curry market."},
                    {"role": "user", "content": future_prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            future_text = response.choices[0].message.content
            
            # Structure the future predictions
            future_predictions = {
                'prediction_id': str(uuid.uuid4()),
                'market_focus': state.get('target_market', 'japanese_curry'),
                'analysis_date': datetime.now().isoformat(),
                'forecast_horizon': '5_years',
                'prediction_areas': {
                    'market_growth': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'consumer_behavior': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'product_innovation': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'competitive_landscape': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'distribution_channels': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'technology_impact': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'regulatory_cultural': {'current_state': '', 'predictions': [], 'timeline': ''},
                    'opportunities_threats': {'opportunities': [], 'threats': [], 'strategic_implications': []}
                },
                'raw_analysis': future_text,
                'confidence_level': 'medium',
                'key_assumptions': []
            }
            
            # Parse future predictions (simplified parsing)
            lines = future_text.split('\n')
            current_area = None
            
            for line in lines:
                line = line.strip()
                if any(area in line.lower() for area in ['market size', 'consumer behavior', 'product innovation', 'competitive', 'distribution', 'technology', 'regulatory', 'opportunities']):
                    # Identify prediction area
                    if 'market' in line.lower() and ('size' in line.lower() or 'growth' in line.lower()):
                        current_area = 'market_growth'
                    elif 'consumer' in line.lower():
                        current_area = 'consumer_behavior'
                    elif 'product' in line.lower() or 'innovation' in line.lower():
                        current_area = 'product_innovation'
                    elif 'competitive' in line.lower():
                        current_area = 'competitive_landscape'
                    elif 'distribution' in line.lower():
                        current_area = 'distribution_channels'
                    elif 'technology' in line.lower():
                        current_area = 'technology_impact'
                    elif 'regulatory' in line.lower() or 'cultural' in line.lower():
                        current_area = 'regulatory_cultural'
                    elif 'opportunities' in line.lower() or 'threats' in line.lower():
                        current_area = 'opportunities_threats'
                elif current_area and line and not line.startswith('#'):
                    if current_area == 'opportunities_threats':
                        if 'opportunity' in line.lower():
                            future_predictions['prediction_areas'][current_area]['opportunities'].append(line)
                        elif 'threat' in line.lower():
                            future_predictions['prediction_areas'][current_area]['threats'].append(line)
                        else:
                            future_predictions['prediction_areas'][current_area]['strategic_implications'].append(line)
                    else:
                        if not future_predictions['prediction_areas'][current_area]['current_state']:
                            future_predictions['prediction_areas'][current_area]['current_state'] = line
                        else:
                            future_predictions['prediction_areas'][current_area]['predictions'].append(line)
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Generated comprehensive future market predictions",
                    result={
                        "step": "Future Predictions",
                        "prediction_areas": len(future_predictions['prediction_areas'])
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating future predictions: {e}")
            future_predictions = {
                'prediction_id': str(uuid.uuid4()),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
        
        return future_predictions

    async def run(self, state: MarketResearchState) -> Dict[str, Any]:
        """Main entry point for the Trend Analysis Agent."""
        return await self.analyze_market_trends(state)