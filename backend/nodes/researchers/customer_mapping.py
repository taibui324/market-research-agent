"""
Customer Mapping Researcher - Analyzes consumer needs and trends using AIG client
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ...services.xai_aig_chat import XAIChatAIG
from ...classes.state import CustomerMappingResults

logger = logging.getLogger(__name__)


class CustomerMappingResearcher:
    """Researcher specialized in customer mapping and consumer needs analysis"""
    
    def __init__(self):
        llm = XAIChatAIG()
        # Create structured LLM for CustomerMappingResults using our custom XAI AIG chat
        self.structured_llm = llm.with_structured_output(CustomerMappingResults, search_parameters={"search_mode": "on"})
        logger.info("AIG structured chat client initialized for customer mapping")
        self.analyst_type = "customer_mapping_analyst"
    
    async def research_customer_mapping(self, state: Dict, industry: str = None, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Research customer mapping and consumer needs using AIG client
        Focuses on general consumer behavior and market trends without company-specific information
        
        Args:
            state: Research state containing websocket_manager, job_id, and industry
            industry: Industry to analyze (optional, will use state if not provided)
            start_date: Start date for analysis period (optional, defaults to 6 months ago)
            end_date: End date for analysis period (optional, defaults to today)
        
        Returns:
            CustomerMappingResults with structured consumer insights and trend summaries
        """
        # Get industry from state if not provided
        industry = industry or state.get("industry")
        if not industry:
            logger.error("Industry not provided for customer mapping research")
            raise ValueError("Industry not provided")
        
        # Define analysis period - use provided dates or default to last 6 months
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=180)  # 6 months from end_date
            
        logger.info(f"Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            logger.info(f"Starting customer mapping research for {industry} industry")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="customer_mapping_started",
                    message=f"Starting customer mapping analysis for {industry} industry",
                    result={
                        "step": "Customer Mapping",
                        "industry": industry
                    }
                )
            
            # Create the research prompt for structured output
            message_content = f"""
Analyze consumer needs mapping and market trends for the {industry} industry.

Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

Provide a comprehensive analysis including:

1. **Consumer Insights**: Identify key consumer behavior clusters with specific needs/trends, frequency counts (number of posts/mentions), and key insights.

2. **Trend Summaries**: Break down the 6-month period into monthly or bi-monthly trend summaries showing how consumer behavior evolved.

3. **Industry Focus**: Analyze the {industry} industry specifically without focusing on any particular company.

Requirements:
- For consumer insights: Provide cluster categories (Quality, Convenience, Price, Sustainability, Digital, etc.)
- For frequency: Provide actual numbers of posts/mentions found
- For trend summaries: Include specific date ranges and behavioral changes
- Focus on demographic and psychographic trends
- Include emerging consumer needs and pain points
- Provide market-level insights from industry sources and social feedback

Generate structured data that covers the entire analysis period from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.
"""
            
            logger.info(f"Making AIG API request for customer mapping research")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="customer_mapping_analyzing",
                    message="Analyzing consumer needs and market trends using AIG",
                    result={
                        "step": "Customer Mapping",
                        "status": "Analyzing with AIG"
                    }
                )
            
            # Make the API call using structured LLM
            structured_result = await self.structured_llm.ainvoke(message_content)
            
            logger.info("Successfully received structured response from AIG API")
            
            # Convert structured result to dict and add metadata
            result = dict(structured_result)
            result.update({
                "analyst_type": self.analyst_type,
                "status": "success"
            })
            
            logger.info(f"Customer mapping analysis completed for {industry} industry")
            logger.info(f"Generated {len(result.get('consumer_insights', []))} consumer insights")
            logger.info(f"Generated {len(result.get('trend_summaries', []))} trend summaries")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="customer_mapping_completed",
                    message=f"Customer mapping analysis completed for {industry} industry",
                    result={
                        "step": "Customer Mapping",
                        "status": "Completed",
                        "consumer_insights_count": len(result.get('consumer_insights', [])),
                        "trend_summaries_count": len(result.get('trend_summaries', []))
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in customer mapping research for {industry} industry: {e}")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="customer_mapping_error",
                    message=f"Customer mapping analysis failed: {str(e)}",
                    error=f"Customer mapping failed: {str(e)}"
                )
            
            return {
                "start_date": start_date,
                "end_date": end_date,
                "trend_summaries": [],
                "consumer_insights": [],
                "analyst_type": self.analyst_type,
                "status": "error",
                "error": str(e)
            }
    