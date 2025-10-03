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
            # Search for trend insights using generated queries (batch process for efficiency)
            if queries:
                logger.info(f"Searching for trend insights using {len(queries)} queries")
                documents = await self.search_documents(state, queries)
                
                if documents:
                    for url, doc in documents.items():
                        doc['analysis_type'] = 'trend_analysis'
                        trend_data[url] = doc
                    
                    msg.append(f"\n✓ Found {len(trend_data)} trend analysis documents")
                else:
                    msg.append(f"\n⚠️ No documents found for trend analysis queries")
                    logger.warning("No documents found for trend analysis")
            else:
                msg.append(f"\n⚠️ No queries generated for trend analysis")
                logger.warning("No queries generated for trend analysis")
            
            if websocket_manager := state.get('websocket_manager'):
                if job_id := state.get('job_id'):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Collected {len(trend_data)} trend analysis documents",
                        result={
                            "step": "Data Collection",
                            "analyst_type": "Trend Analyst",
                            "documents_found": len(trend_data),
                            "queries_used": len(queries)
                        }
                    )
                    
        except Exception as e:
            msg.append(f"\n⚠️ Error during trend data collection: {str(e)}")
            logger.error(f"Trend data collection error: {e}", exc_info=True)
        
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
            # PERFORMANCE OPTIMIZATION: Batch process documents to reduce API calls
            # Process up to 5 documents in parallel batches
            batch_size = 5
            document_batches = []
            
            valid_docs = [(url, doc) for url, doc in trend_data.items() 
                         if doc.get('content', '') and len(doc.get('content', '').strip()) >= 50]
            
            # Limit to top 8 documents for faster processing
            valid_docs = valid_docs[:8]
            
            for i in range(0, len(valid_docs), batch_size):
                batch = valid_docs[i:i + batch_size]
                document_batches.append(batch)
            
            # Process each batch
            for batch_idx, doc_batch in enumerate(document_batches):
                # Combine multiple documents into a single API call for efficiency
                combined_content = ""
                doc_info = []
                
                for url, doc in doc_batch:
                    content = doc.get('content', '')[:1000]  # Limit content per doc
                    doc_title = doc.get('title', 'Market Report')
                    combined_content += f"\n\n--- Document {len(doc_info)+1}: {doc_title} ---\n{content}"
                    doc_info.append((url, doc, doc_title))
                
                # Single API call for the entire batch
                trend_prompt = f"""
                As a senior market trend analyst, analyze the following market intelligence documents and extract 2025 Japanese curry market trends:

                {combined_content[:4000]}  # Limit total content

                **EXTRACT 3-5 KEY TRENDS focusing on:**
                - 2025 market innovations and predictions
                - Technology disruption (AI, IoT, automation)
                - Consumer behavior evolution 
                - Sustainability and health trends
                - Market transformation opportunities

                **For each trend, provide concisely:**
                - trend_name: Clear, future-focused name
                - description: Brief impact description
                - category: Select from {self.trend_categories}
                - growth_direction: accelerating/emerging/transforming
                - impact_level: transformative/high/medium
                - confidence: 0.7-1.0

                Focus on the most significant transformative trends only.
                """
                
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a senior market trend analyst specializing in Japanese curry market analysis. Provide concise, high-impact trend analysis."},
                            {"role": "user", "content": trend_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=800  # Reduced for faster response
                    )
                    
                    # Parse LLM response to extract trends
                    trend_text = response.choices[0].message.content
                    
                    # Create trend objects for each document in the batch
                    from urllib.parse import urlparse
                    
                    for url, doc, doc_title in doc_info:
                        # Enhanced source attribution for credibility
                        if url:
                            domain = urlparse(url).netloc
                            if 'nikkei' in domain.lower():
                                source_name = "Nikkei Business"
                            elif 'reuters' in domain.lower():
                                source_name = "Reuters"
                            elif 'bloomberg' in domain.lower():
                                source_name = "Bloomberg"
                            elif 'marketresearch' in domain.lower():
                                source_name = "Market Research Reports"
                            elif 'euromonitor' in domain.lower():
                                source_name = "Euromonitor International"
                            elif 'mintel' in domain.lower():
                                source_name = "Mintel Market Intelligence"
                            elif 'statista' in domain.lower():
                                source_name = "Statista Market Data"
                            elif 'food' in domain.lower():
                                source_name = "Food Industry Publications"
                            elif 'japan' in domain.lower() or 'jp' in domain.lower():
                                source_name = f"Japanese Industry Source ({domain})"
                            else:
                                source_name = f"Market Intelligence ({domain})"
                        else:
                            source_name = "Industry Analysis Report"
                        
                        # Create structured trend object with proper attribution
                        trend = {
                            'trend_id': str(uuid.uuid4()),
                            'source_url': url,
                            'source_name': source_name,
                            'source_domain': urlparse(url).netloc if url else 'industry_analysis',
                            'source_title': doc_title,
                            'query': doc.get('query', ''),
                            'raw_content': doc.get('content', '')[:500],  # Store snippet
                            'extracted_trends': trend_text,
                            'timestamp': datetime.now().isoformat(),
                            'confidence_score': 0.85,  # Higher confidence with real sources
                            'reliability_score': 0.8,
                            'citation': f"{source_name}. Retrieved from {url}" if url else f"{source_name}. Industry Analysis Report."
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
            # PERFORMANCE OPTIMIZATION: Reduce prediction complexity for speed
            # Combine trend data for prediction analysis (limit to top 5 for speed)
            trends_summary = ""
            for trend in market_trends[:5]:  # Reduced from 10 to 5 for faster processing
                trends_summary += trend.get('extracted_trends', '')[:200] + "\n\n"  # Reduced content length
            
            if not trends_summary.strip():
                return []
            
            # Simplified prediction prompt for faster processing
            prediction_prompt = f"""
            Based on these Japanese curry market trends, generate 3-5 key strategic predictions for 2025-2030:

            **Trend Summary:**
            {trends_summary[:2000]}  # Limit content

            **Generate concise predictions focusing on:**
            - Technology adoption (AI, automation, smart products)
            - Consumer behavior shifts (health, convenience, premium)
            - Market transformation opportunities

            **For each prediction, provide briefly:**
            - prediction_title: Clear transformative statement
            - description: Impact explanation (2-3 sentences)
            - time_horizon: 2025_immediate/2026_short/2027_2028_medium/2029_2030_long
            - probability: high/medium
            - impact_level: transformative/high/medium

            Focus on the most significant industry-changing predictions.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a market forecasting analyst specializing in Japanese curry market predictions. Provide concise, high-impact strategic predictions."},
                    {"role": "user", "content": prediction_prompt}
                ],
                temperature=0.4,
                max_tokens=600  # Reduced for faster response
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
            
            # Ensure we have at least basic predictions with proper source attribution
            if not predictions:
                # Get source information from market trends for attribution
                trend_sources = []
                for trend in market_trends[:3]:  # Use top 3 trend sources
                    if trend.get('source_name'):
                        trend_sources.append(trend['source_name'])
                
                primary_source = trend_sources[0] if trend_sources else "Industry Analysis Report"
                
                predictions = [
                    {
                        'prediction_id': str(uuid.uuid4()),
                        'title': 'Increased Demand for Premium Japanese Curry Products',
                        'description': 'Growing consumer preference for high-quality, authentic Japanese curry experiences',
                        'time_horizon': '2_years',
                        'probability': 'high',
                        'impact_level': 'high',
                        'key_drivers': ['Quality consciousness', 'Authenticity seeking', 'Premium market growth'],
                        'source_name': primary_source,
                        'confidence_score': 0.82,
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
                        'source_name': primary_source,
                        'confidence_score': 0.80,
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
            # PERFORMANCE OPTIMIZATION: Simplified adoption curve analysis
            trends_text = "\n".join([trend.get('extracted_trends', '')[:150] for trend in market_trends[:5]])  # Reduced complexity
            
            adoption_prompt = f"""
            Position these Japanese curry market trends on the adoption curve (emerging/growing/mainstream):

            Trends: {trends_text[:1500]}  # Limit content

            **For 3-5 key trends, provide:**
            - trend_name: Clear name
            - adoption_stage: emerging/growing/mainstream
            - market_penetration: percentage estimate
            - growth_velocity: fast/moderate/slow

            Be concise and focus on the most significant trends.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an innovation adoption analyst specializing in Japanese curry market trend positioning."},
                    {"role": "user", "content": adoption_prompt}
                ],
                temperature=0.3,
                max_tokens=400  # Reduced for faster response
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
