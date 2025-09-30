import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph

from ..classes.state import MarketResearchState
from ..services.websocket_manager import WebSocketManager
from ..services.report_generator import MarketResearchReportGenerator
from ..utils.monitoring import (
    monitor_performance, 
    workflow_monitoring_context, 
    log_error_with_context,
    performance_monitor
)
from .researchers.consumer import ConsumerAnalysisAgent
from .researchers.trend import TrendAnalysisAgent
from .researchers.competitor import CompetitorAnalysisAgent
from .researchers.customer_mapping import CustomerMappingResearcher
from .market_collector import MarketDataCollector
from .market_curator import MarketDataCurator
from .swot_analysis_agent import SwotAnalysisAgent

logger = logging.getLogger(__name__)


class AgentFailureHandler:
    """Handles graceful degradation when individual agents fail"""
    
    def __init__(self, websocket_manager: Optional[WebSocketManager] = None, job_id: Optional[str] = None):
        self.websocket_manager = websocket_manager
        self.job_id = job_id
    
    async def handle_agent_failure(self, agent_name: str, error: Exception, state: MarketResearchState) -> MarketResearchState:
        """Handle agent failure with graceful degradation"""
        logger.error(f"Agent {agent_name} failed: {str(error)}")
        
        # Update state with failure information
        if agent_name == "consumer_analysis":
            state['consumer_insights'] = {
                "status": "failed", 
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
            state['pain_points'] = []
            state['customer_personas'] = []
            state['purchase_journey'] = {}
        elif agent_name == "trend_analysis":
            state['market_trends'] = {
                "status": "failed", 
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
            state['trend_predictions'] = []
            state['adoption_curves'] = {}
        elif agent_name == "competitor_analysis":
            state['competitor_landscape'] = {
                "status": "failed", 
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
            state['competitive_positioning'] = {}
            state['feature_comparisons'] = []
            state['market_gaps'] = []
        elif agent_name == "swot_analysis":
            state['swot_analysis'] = {
                "status": "failed", 
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
        elif agent_name == "customer_mapping":
            state['customer_mapping_results'] = {
                "status": "failed", 
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
        
        # Notify via WebSocket
        if self.websocket_manager and self.job_id:
            await self.websocket_manager.send_status_update(
                job_id=self.job_id,
                status="warning",
                message=f"{agent_name} failed, continuing with available data",
                error=str(error)
            )
        
        return state


class ThreeCAnalysisOrchestrator:
    """
    Enhanced 3C Analysis Orchestrator that coordinates Consumer, Company, and Competitor analysis agents.
    Supports intelligent agent selection, parallel execution, and comprehensive error handling.
    """
    
    def __init__(self, websocket_manager: Optional[WebSocketManager] = None, job_id: Optional[str] = None, 
                 analysis_type: str = "comprehensive", selected_agents: Optional[List[str]] = None):
        self.websocket_manager = websocket_manager
        self.job_id = job_id
        self.analysis_type = analysis_type
        self.selected_agents = selected_agents or self._get_default_agents(analysis_type)
        self.failure_handler = AgentFailureHandler(websocket_manager, job_id)
        
        # Initialize all available agents
        self.consumer_agent = ConsumerAnalysisAgent()
        self.trend_agent = TrendAnalysisAgent()
        self.competitor_agent = CompetitorAnalysisAgent()
        self.swot_agent = SwotAnalysisAgent()
        self.customer_mapping_agent = CustomerMappingResearcher()
        
        # Initialize enhanced data pipeline components
        self.data_collector = MarketDataCollector()
        self.data_curator = MarketDataCurator()
        
        # Initialize report generator
        self.report_generator = MarketResearchReportGenerator()
        
        # Build the enhanced workflow based on selected agents
        self._build_enhanced_workflow()
    
    def _get_default_agents(self, analysis_type: str) -> List[str]:
        """Get default agent selection based on analysis type."""
        if analysis_type == "comprehensive":
            return ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"]
        elif analysis_type == "focused":
            return ["consumer_analysis", "trend_analysis", "competitor_analysis"]
        elif analysis_type == "quick":
            return ["consumer_analysis", "trend_analysis"]
        else:
            return ["consumer_analysis", "trend_analysis", "competitor_analysis"]
    
    def _build_enhanced_workflow(self):
        """Configure the enhanced 3C analysis state graph workflow with intelligent agent selection."""
        self.workflow = StateGraph(MarketResearchState)
        
        # Core workflow nodes (always included)
        self.workflow.add_node("query_generation", self._generate_market_queries)
        self.workflow.add_node("data_collection", self._collect_market_data)
        self.workflow.add_node("data_curation", self._curate_market_data)
        
        # Agent-specific nodes (conditional based on selection)
        if "consumer_analysis" in self.selected_agents:
            self.workflow.add_node("consumer_analysis", self._run_consumer_analysis)
        
        if "trend_analysis" in self.selected_agents:
            self.workflow.add_node("trend_analysis", self._run_trend_analysis)
        
        if "competitor_analysis" in self.selected_agents:
            self.workflow.add_node("competitor_analysis", self._run_competitor_analysis)
        
        if "swot_analysis" in self.selected_agents:
            self.workflow.add_node("swot_analysis", self._run_swot_analysis)
        
        if "customer_mapping" in self.selected_agents:
            self.workflow.add_node("customer_mapping", self._run_customer_mapping)
        
        # Always include synthesis and reporting
        self.workflow.add_node("opportunity_analysis", self._run_opportunity_analysis)
        self.workflow.add_node("synthesis", self._synthesize_results)
        self.workflow.add_node("report_generation", self._generate_final_report)
        
        # Configure workflow edges with intelligent dependency management
        self.workflow.set_entry_point("query_generation")
        self.workflow.set_finish_point("report_generation")
        
        # Core pipeline edges
        self.workflow.add_edge("query_generation", "data_collection")
        self.workflow.add_edge("data_collection", "data_curation")
        
        # Analysis agents edges with dependency management
        last_analysis_step = "data_curation"
        
        # Customer mapping can run in parallel with consumer analysis
        if "customer_mapping" in self.selected_agents and "consumer_analysis" in self.selected_agents:
            self.workflow.add_edge("data_curation", "customer_mapping")
            self.workflow.add_edge("customer_mapping", "consumer_analysis")
            last_analysis_step = "consumer_analysis"
        elif "consumer_analysis" in self.selected_agents:
            self.workflow.add_edge(last_analysis_step, "consumer_analysis")
            last_analysis_step = "consumer_analysis"
        elif "customer_mapping" in self.selected_agents:
            self.workflow.add_edge(last_analysis_step, "customer_mapping")
            last_analysis_step = "customer_mapping"
        
        # Trend analysis depends on consumer insights for better analysis
        if "trend_analysis" in self.selected_agents:
            self.workflow.add_edge(last_analysis_step, "trend_analysis")
            last_analysis_step = "trend_analysis"
        
        # Competitor analysis can run after trend analysis
        if "competitor_analysis" in self.selected_agents:
            self.workflow.add_edge(last_analysis_step, "competitor_analysis")
            last_analysis_step = "competitor_analysis"
        
        # SWOT analysis should run after competitor analysis for best results
        if "swot_analysis" in self.selected_agents:
            self.workflow.add_edge(last_analysis_step, "swot_analysis")
            last_analysis_step = "swot_analysis"
        
        # Connect to opportunity analysis and final steps
        self.workflow.add_edge(last_analysis_step, "opportunity_analysis")
        self.workflow.add_edge("opportunity_analysis", "synthesis")
        self.workflow.add_edge("synthesis", "report_generation")
    
    async def run(self, state: MarketResearchState) -> AsyncIterator[Dict[str, Any]]:
        """Execute the 3C analysis workflow with comprehensive monitoring and error handling"""
        job_id = self.job_id or "unknown_job"
        target_market = state.get('target_market', 'japanese_curry')
        
        # Use monitoring context for comprehensive tracking
        async with workflow_monitoring_context(job_id, "3c_analysis", target_market) as monitor_logger:
            try:
                # Initialize state with 3C analysis metadata
                state['analysis_type'] = '3c_analysis'
                state['target_market'] = target_market
                state['market_focus_keywords'] = self._get_market_keywords(target_market)
                state['workflow_start_time'] = datetime.now().isoformat()
                
                # Add initial system message
                if 'messages' not in state:
                    state['messages'] = []
                
                state['messages'].append(
                    SystemMessage(content=f"Starting 3C Analysis for {target_market} market")
                )
                
                monitor_logger.info(f"Initializing 3C Analysis workflow for {target_market} market")
                
                # Record workflow start metric
                performance_monitor.record_metric(
                    "workflow_started",
                    1,
                    {"job_id": job_id, "target_market": target_market}
                )
                
                # Send initial status update
                if self.websocket_manager and self.job_id:
                    await self.websocket_manager.send_status_update(
                        job_id=self.job_id,
                        status="processing",
                        message="Initializing 3C Analysis workflow",
                        result={
                            "analysis_type": "3c_analysis",
                            "target_market": target_market,
                            "workflow_stage": "initialization",
                            "start_time": state['workflow_start_time']
                        }
                    )
                
                # Compile and execute the workflow
                compiled_graph = self.workflow.compile()
                
                step_count = 0
                workflow_start_time = datetime.now()
                
                async for workflow_state in compiled_graph.astream(state):
                    step_count += 1
                    
                    # Log workflow progress with monitoring
                    current_step = self._get_current_step(workflow_state)
                    progress = self._calculate_progress(workflow_state)
                    elapsed_time = (datetime.now() - workflow_start_time).total_seconds()
                    
                    monitor_logger.info(
                        f"Workflow step {step_count}: {current_step} ({progress:.1f}% complete, {elapsed_time:.1f}s elapsed)"
                    )
                    
                    # Record step completion metric
                    performance_monitor.record_metric(
                        "workflow_step_completed",
                        1,
                        {
                            "job_id": job_id,
                            "step_name": current_step,
                            "step_number": step_count,
                            "progress_percentage": progress
                        }
                    )
                    
                    # Send periodic progress updates
                    if self.websocket_manager and self.job_id and step_count % 2 == 0:  # Every 2nd step
                        await self.websocket_manager.send_status_update(
                            job_id=self.job_id,
                            status="processing",
                            message=f"Workflow progress: {current_step}",
                            result={
                                "current_step": current_step,
                                "progress_percentage": progress,
                                "step_count": step_count,
                                "elapsed_time": elapsed_time
                            }
                        )
                    
                    yield workflow_state
                
                # Record successful completion
                total_duration = (datetime.now() - workflow_start_time).total_seconds()
                
                performance_monitor.record_metric(
                    "workflow_completed_successfully",
                    1,
                    {
                        "job_id": job_id,
                        "target_market": target_market,
                        "duration_seconds": total_duration,
                        "total_steps": step_count
                    }
                )
                
                monitor_logger.info(f"Workflow completed successfully: {step_count} steps, {total_duration:.2f}s")
                
                # Final completion status
                if self.websocket_manager and self.job_id:
                    await self.websocket_manager.send_status_update(
                        job_id=self.job_id,
                        status="completed",
                        message="3C Analysis workflow completed successfully",
                        result={
                            "workflow_completed": True,
                            "total_duration_seconds": total_duration,
                            "total_steps": step_count,
                            "completion_time": datetime.now().isoformat()
                        }
                    )
                    
            except Exception as e:
                # Log error with comprehensive context
                log_error_with_context(
                    e,
                    component="3c_orchestrator",
                    job_id=job_id,
                    target_market=target_market,
                    workflow_stage="execution"
                )
                
                # Record failure metric
                performance_monitor.record_metric(
                    "workflow_failed",
                    1,
                    {
                        "job_id": job_id,
                        "target_market": target_market,
                        "error_type": type(e).__name__
                    }
                )
                
                # Send error status
                if self.websocket_manager and self.job_id:
                    await self.websocket_manager.send_status_update(
                        job_id=self.job_id,
                        status="error",
                        message=f"3C Analysis workflow failed: {str(e)}",
                        error=str(e),
                        result={
                            "workflow_failed": True,
                            "error_type": type(e).__name__,
                            "failure_time": datetime.now().isoformat()
                        }
                    )
                
                # Re-raise the exception to be handled by the calling code
                raise
    
    async def _handle_workflow_error(self, error: Exception, stage: str, state: MarketResearchState) -> MarketResearchState:
        """Handle workflow-level errors with comprehensive logging and recovery"""
        error_id = str(uuid.uuid4())[:8]
        
        # Log error with comprehensive context
        log_error_with_context(
            error,
            component="3c_orchestrator_workflow",
            job_id=self.job_id,
            workflow_stage=stage,
            error_id=error_id,
            target_market=state.get('target_market', 'unknown'),
            current_step=self._get_current_step(state)
        )
        
        # Record error metric
        performance_monitor.record_metric(
            "workflow_error",
            1,
            {
                "job_id": self.job_id or "unknown",
                "stage": stage,
                "error_type": type(error).__name__,
                "error_id": error_id
            }
        )
        
        # Update state with error information
        state['workflow_errors'] = state.get('workflow_errors', [])
        state['workflow_errors'].append({
            'error_id': error_id,
            'stage': stage,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'recovery_attempted': True
        })
        
        # Send error notification via WebSocket
        if self.websocket_manager and self.job_id:
            await self.websocket_manager.send_status_update(
                job_id=self.job_id,
                status="error",
                message=f"Workflow error in {stage}: {str(error)}",
                error=str(error),
                result={
                    "error_id": error_id,
                    "stage": stage,
                    "recovery_status": "attempting_recovery"
                }
            )
        
        return state
    
    async def _generate_market_queries(self, state: MarketResearchState) -> MarketResearchState:
        """Generate market-specific queries for Japanese curry research"""
        target_market = state.get('target_market', 'japanese_curry')
        company = state.get('company', 'Unknown Company')
        
        logger.info(f"Generating market queries for {target_market} analysis")
        
        # Generate base queries for Japanese curry market research
        base_queries = [
            f"{target_market} consumer preferences and behavior",
            f"{target_market} market trends and growth patterns",
            f"{target_market} competitive landscape and key players",
            f"{target_market} product innovation and development trends",
            f"{target_market} consumer pain points and unmet needs",
            f"{target_market} market size and segmentation analysis",
            f"{target_market} distribution channels and retail presence",
            f"{target_market} pricing strategies and value perception"
        ]
        
        # Store queries in state for use by individual agents
        state['market_queries'] = base_queries
        state['query_generation_timestamp'] = datetime.now().isoformat()
        
        # Add message about query generation
        messages = state.get('messages', [])
        query_msg = f"🎯 Generated {len(base_queries)} market research queries for {target_market} analysis"
        messages.append(AIMessage(content=query_msg))
        state['messages'] = messages
        
        # Send WebSocket update
        if self.websocket_manager and self.job_id:
            await self.websocket_manager.send_status_update(
                job_id=self.job_id,
                status="processing",
                message="Market research queries generated",
                result={
                    "step": "Query Generation",
                    "queries_generated": len(base_queries),
                    "target_market": target_market
                }
            )
        
        return state
    
    @monitor_performance("data_collection", {"component": "3c_orchestrator"})
    async def _collect_market_data(self, state: MarketResearchState) -> MarketResearchState:
        """Collect market research data using enhanced data collection pipeline"""
        try:
            logger.info("Starting market data collection")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Collecting market research data",
                    result={"step": "Data Collection", "status": "starting"}
                )
            
            # Get queries from previous step
            queries = state.get('market_queries', [])
            target_market = state.get('target_market', 'japanese_curry')
            
            # Collect data using enhanced market data collector
            collected_data = await self.data_collector.collect_market_research_data(state)
            
            # Store collected data in state
            state['raw_market_data'] = collected_data
            state['data_collection_timestamp'] = datetime.now().isoformat()
            
            # Add message about data collection
            messages = state.get('messages', [])
            data_msg = f"📊 Collected market research data from {len(collected_data.get('sources', []))} sources"
            messages.append(AIMessage(content=data_msg))
            state['messages'] = messages
            
            logger.info(f"Market data collection completed: {len(collected_data.get('sources', []))} sources")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "data_collection")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Market data collection completed",
                    result={
                        "step": "Data Collection", 
                        "status": "completed",
                        "sources_collected": len(collected_data.get('sources', []))
                    }
                )
            
        except Exception as e:
            logger.error(f"Market data collection failed: {e}")
            state['raw_market_data'] = {'status': 'failed', 'error': str(e)}
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="warning",
                    message="Market data collection failed, continuing with available data",
                    error=str(e)
                )
        
        return state
    
    @monitor_performance("data_curation", {"component": "3c_orchestrator"})
    async def _curate_market_data(self, state: MarketResearchState) -> MarketResearchState:
        """Curate and filter market research data for quality and relevance"""
        try:
            logger.info("Starting market data curation")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Curating market research data",
                    result={"step": "Data Curation", "status": "starting"}
                )
            
            # Get raw data from previous step
            raw_data = state.get('raw_market_data', {})
            target_market = state.get('target_market', 'japanese_curry')
            
            if raw_data.get('status') == 'failed':
                logger.warning("Skipping data curation due to collection failure")
                state['curated_market_data'] = {'status': 'skipped', 'reason': 'collection_failed'}
            else:
                # Curate data using enhanced market data curator
                curated_data = await self.data_curator.curate_market_data(state)
                
                # Store curated data in state
                state['curated_market_data'] = curated_data
            
            state['data_curation_timestamp'] = datetime.now().isoformat()
            
            # Add message about data curation
            messages = state.get('messages', [])
            if state['curated_market_data'].get('status') != 'skipped':
                curation_msg = f"🔍 Curated market data with {state['curated_market_data'].get('quality_score', 0):.2f} quality score"
            else:
                curation_msg = "⚠️ Data curation skipped due to collection issues"
            messages.append(AIMessage(content=curation_msg))
            state['messages'] = messages
            
            logger.info("Market data curation completed")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "data_curation")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Market data curation completed",
                    result={
                        "step": "Data Curation", 
                        "status": "completed",
                        "quality_score": state['curated_market_data'].get('quality_score', 0)
                    }
                )
            
        except Exception as e:
            logger.error(f"Market data curation failed: {e}")
            state['curated_market_data'] = {'status': 'failed', 'error': str(e)}
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="warning",
                    message="Market data curation failed, continuing with raw data",
                    error=str(e)
                )
        
        return state
    
    @monitor_performance("consumer_analysis", {"component": "3c_orchestrator"})
    async def _run_consumer_analysis(self, state: MarketResearchState) -> MarketResearchState:
        """Execute consumer analysis with error handling"""
        try:
            logger.info("Starting consumer analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting consumer analysis",
                    result={"step": "Consumer Analysis", "status": "starting"}
                )
            
            # Pass curated data to consumer analysis agent
            curated_data = state.get('curated_market_data', {})
            if curated_data.get('status') not in ['failed', 'skipped']:
                state['enhanced_consumer_data'] = curated_data.get('consumer_data', {})
            
            # Run consumer analysis agent
            result = await self.consumer_agent.run(state)
            
            # Update state with consumer analysis results - only specific keys
            if isinstance(result, dict):
                # Only update consumer-specific keys to avoid conflicts
                consumer_keys = ['consumer_insights', 'pain_points', 'customer_personas', 'purchase_journey']
                for key in consumer_keys:
                    if key in result:
                        state[key] = result[key]
            
            logger.info("Consumer analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "consumer_analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Consumer analysis completed",
                    result={"step": "Consumer Analysis", "status": "completed"}
                )
            
        except Exception as e:
            logger.error(f"Consumer analysis failed: {e}")
            state = await self.failure_handler.handle_agent_failure("consumer_analysis", e, state)
        
        return state
    
    @monitor_performance("trend_analysis", {"component": "3c_orchestrator"})
    async def _run_trend_analysis(self, state: MarketResearchState) -> MarketResearchState:
        """Execute trend analysis with error handling"""
        try:
            logger.info("Starting trend analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting trend analysis",
                    result={"step": "Trend Analysis", "status": "starting"}
                )
            
            # Pass curated data to trend analysis agent
            curated_data = state.get('curated_market_data', {})
            if curated_data.get('status') not in ['failed', 'skipped']:
                state['enhanced_trend_data'] = curated_data.get('trend_data', {})
            
            # Run trend analysis agent
            result = await self.trend_agent.run(state)
            
            # Update state with trend analysis results - only specific keys
            if isinstance(result, dict):
                # Only update trend-specific keys to avoid conflicts
                trend_keys = ['market_trends', 'trend_predictions', 'adoption_curves']
                for key in trend_keys:
                    if key in result:
                        state[key] = result[key]
            
            logger.info("Trend analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "trend_analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Trend analysis completed",
                    result={"step": "Trend Analysis", "status": "completed"}
                )
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            state = await self.failure_handler.handle_agent_failure("trend_analysis", e, state)
        
        return state
    
    async def _run_competitor_analysis(self, state: MarketResearchState) -> MarketResearchState:
        """Execute competitor analysis with error handling"""
        try:
            logger.info("Starting competitor analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting competitor analysis",
                    result={"step": "Competitor Analysis", "status": "starting"}
                )
            
            # Pass curated data to competitor analysis agent
            curated_data = state.get('curated_market_data', {})
            if curated_data.get('status') not in ['failed', 'skipped']:
                state['enhanced_competitor_data'] = curated_data.get('competitor_data', {})
            
            # Run competitor analysis agent
            result = await self.competitor_agent.run(state)
            
            # Update state with competitor analysis results
            if isinstance(result, dict):
                # Update competitor-specific keys
                competitor_keys = ['competitor_landscape', 'competitive_positioning', 'feature_comparisons', 'market_gaps']
                for key in competitor_keys:
                    if key in result:
                        state[key] = result[key]
            
            logger.info("Competitor analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "competitor_analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Competitor analysis completed",
                    result={"step": "Competitor Analysis", "status": "completed"}
                )
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            state = await self.failure_handler.handle_agent_failure("competitor_analysis", e, state)
        
        return state
    
    async def _run_swot_analysis(self, state: MarketResearchState) -> MarketResearchState:
        """Execute SWOT analysis with error handling"""
        try:
            logger.info("Starting SWOT analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting SWOT analysis",
                    result={"step": "SWOT Analysis", "status": "starting"}
                )
            
            # Run SWOT analysis agent
            result = await self.swot_agent.run(state)
            
            # Update state with SWOT analysis results
            if isinstance(result, dict):
                state['swot_analysis'] = result
            
            logger.info("SWOT analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "swot_analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="SWOT analysis completed",
                    result={"step": "SWOT Analysis", "status": "completed"}
                )
            
        except Exception as e:
            logger.error(f"SWOT analysis failed: {e}")
            state = await self.failure_handler.handle_agent_failure("swot_analysis", e, state)
        
        return state
    
    async def _run_customer_mapping(self, state: MarketResearchState) -> MarketResearchState:
        """Execute customer mapping analysis with error handling"""
        try:
            logger.info("Starting customer mapping analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting customer mapping analysis",
                    result={"step": "Customer Mapping", "status": "starting"}
                )
            
            # Run customer mapping agent
            target_market = state.get('target_market', 'japanese_curry')
            industry = state.get('industry', 'Food & Beverage')
            
            result = await self.customer_mapping_agent.research_customer_mapping(
                state, industry=industry
            )
            
            # Update state with customer mapping results
            if isinstance(result, dict):
                state['customer_mapping_results'] = result
            
            logger.info("Customer mapping analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "customer_mapping")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Customer mapping analysis completed",
                    result={"step": "Customer Mapping", "status": "completed"}
                )
            
        except Exception as e:
            logger.error(f"Customer mapping analysis failed: {e}")
            state = await self.failure_handler.handle_agent_failure("customer_mapping", e, state)
        
        return state
    
    @monitor_performance("opportunity_analysis", {"component": "3c_orchestrator"})
    async def _run_opportunity_analysis(self, state: MarketResearchState) -> MarketResearchState:
        """Execute opportunity analysis by synthesizing insights from other agents"""
        try:
            logger.info("Starting opportunity analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Starting opportunity analysis",
                    result={"step": "Opportunity Analysis", "status": "starting"}
                )
            
            # Collect insights from completed analyses
            consumer_insights = state.get('consumer_insights', {})
            market_trends = state.get('market_trends', {})
            pain_points = state.get('pain_points', [])
            
            # Generate opportunities based on available data
            opportunities = await self._identify_market_opportunities(
                consumer_insights, market_trends, pain_points, state
            )
            
            # Generate white space analysis
            white_spaces = await self._identify_white_spaces(
                consumer_insights, market_trends, state
            )
            
            # Generate actionable recommendations
            recommendations = await self._generate_recommendations(
                opportunities, white_spaces, state
            )
            
            # Update state with opportunity analysis results
            state['opportunities'] = opportunities
            state['white_spaces'] = white_spaces
            state['recommendations'] = recommendations
            state['opportunity_analysis_timestamp'] = datetime.now().isoformat()
            
            # Add message about opportunity analysis
            messages = state.get('messages', [])
            opp_msg = f"💡 Identified {len(opportunities)} market opportunities and {len(white_spaces)} white spaces"
            messages.append(AIMessage(content=opp_msg))
            state['messages'] = messages
            
            logger.info("Opportunity analysis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "opportunity_analysis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Opportunity analysis completed",
                    result={
                        "step": "Opportunity Analysis", 
                        "status": "completed",
                        "opportunities_found": len(opportunities),
                        "white_spaces_identified": len(white_spaces)
                    }
                )
            
        except Exception as e:
            logger.error(f"Opportunity analysis failed: {e}")
            # Set default empty results
            state['opportunities'] = []
            state['white_spaces'] = []
            state['recommendations'] = []
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="warning",
                    message="Opportunity analysis failed, continuing with available data",
                    error=str(e)
                )
        
        return state
    
    async def _synthesize_results(self, state: MarketResearchState) -> MarketResearchState:
        """Synthesize all analysis results into final 3C analysis output"""
        try:
            logger.info("Starting results synthesis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Synthesizing 3C analysis results",
                    result={"step": "Synthesis", "status": "starting"}
                )
            
            # Create synthesis summary
            synthesis = {
                'analysis_id': str(uuid.uuid4()),
                'target_market': state.get('target_market', 'japanese_curry'),
                'analysis_type': '3c_analysis',
                'completion_timestamp': datetime.now().isoformat(),
                'summary': {
                    'consumer_insights_count': len(state.get('consumer_insights', {}).get('structured_insights', [])),
                    'pain_points_identified': len(state.get('pain_points', [])),
                    'customer_personas_created': len(state.get('customer_personas', [])),
                    'market_trends_identified': len(state.get('market_trends', {}).get('structured_trends', [])),
                    'trend_predictions_generated': len(state.get('trend_predictions', [])),
                    'opportunities_identified': len(state.get('opportunities', [])),
                    'white_spaces_found': len(state.get('white_spaces', [])),
                    'recommendations_provided': len(state.get('recommendations', []))
                },
                'data_quality': self._assess_data_quality(state),
                'next_steps': self._generate_next_steps(state)
            }
            
            state['analysis_synthesis'] = synthesis
            
            # Add final summary message
            messages = state.get('messages', [])
            summary_msg = f"✅ 3C Analysis completed for {state.get('target_market', 'japanese_curry')} market"
            messages.append(AIMessage(content=summary_msg))
            state['messages'] = messages
            
            logger.info("Results synthesis completed successfully")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "synthesis")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Results synthesis completed",
                    result={
                        "step": "Synthesis",
                        "status": "completed",
                        "analysis_summary": synthesis['summary']
                    }
                )
            
        except Exception as e:
            logger.error(f"Results synthesis failed: {e}")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="error",
                    message="Results synthesis failed",
                    error=str(e)
                )
        
        return state
    
    async def _identify_market_opportunities(self, consumer_insights: Dict[str, Any], 
                                           market_trends: Dict[str, Any], 
                                           pain_points: List[str], 
                                           state: MarketResearchState) -> List[Dict[str, Any]]:
        """Identify market opportunities by analyzing consumer needs and market trends"""
        opportunities = []
        
        try:
            # Combine available data for opportunity analysis
            analysis_data = []
            
            if consumer_insights and consumer_insights.get('structured_insights'):
                insights_text = "\n".join([
                    insight.get('extracted_insight', '')[:200] 
                    for insight in consumer_insights['structured_insights'][:5]
                ])
                analysis_data.append(f"Consumer Insights:\n{insights_text}")
            
            if market_trends and market_trends.get('structured_trends'):
                trends_text = "\n".join([
                    trend.get('extracted_trends', '')[:200] 
                    for trend in market_trends['structured_trends'][:5]
                ])
                analysis_data.append(f"Market Trends:\n{trends_text}")
            
            if pain_points:
                pain_points_text = "\n".join([f"- {pp}" for pp in pain_points[:8]])
                analysis_data.append(f"Consumer Pain Points:\n{pain_points_text}")
            
            if not analysis_data:
                return []
            
            combined_data = "\n\n".join(analysis_data)
            
            # Only generate opportunities based on real data analysis
            # No default sample opportunities - if no real opportunities identified, return empty list
            
        except Exception as e:
            logger.error(f"Error identifying market opportunities: {e}")
        
        return opportunities
    
    async def _identify_white_spaces(self, consumer_insights: Dict[str, Any], 
                                   market_trends: Dict[str, Any], 
                                   state: MarketResearchState) -> List[Dict[str, Any]]:
        """Identify white space opportunities in the market"""
        white_spaces = []
        
        try:
            # Only generate white spaces based on real data analysis
            # No default sample white spaces - if no real white spaces identified, return empty list
            pass
            
        except Exception as e:
            logger.error(f"Error identifying white spaces: {e}")
        
        return white_spaces
    
    async def _generate_recommendations(self, opportunities: List[Dict[str, Any]], 
                                      white_spaces: List[Dict[str, Any]], 
                                      state: MarketResearchState) -> List[str]:
        """Generate actionable recommendations based on identified opportunities"""
        recommendations = []
        
        try:
            # Only generate recommendations based on real data analysis
            # No default sample recommendations - if no real recommendations generated, return empty list
            pass
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _assess_data_quality(self, state: MarketResearchState) -> Dict[str, Any]:
        """Assess the quality and completeness of collected data"""
        quality_assessment = {
            'overall_score': 0.0,
            'consumer_data_quality': 'unknown',
            'trend_data_quality': 'unknown',
            'competitor_data_quality': 'unknown',
            'data_completeness': 0.0,
            'reliability_factors': []
        }
        
        try:
            # Assess consumer data quality
            consumer_insights = state.get('consumer_insights', {})
            if consumer_insights and consumer_insights.get('status') != 'failed':
                quality_assessment['consumer_data_quality'] = 'good'
                quality_assessment['overall_score'] += 0.33
            
            # Assess trend data quality
            market_trends = state.get('market_trends', {})
            if market_trends and market_trends.get('status') != 'failed':
                quality_assessment['trend_data_quality'] = 'good'
                quality_assessment['overall_score'] += 0.33
            
            # Assess competitor data quality (placeholder for when task 4 is complete)
            competitor_landscape = state.get('competitor_landscape', {})
            if competitor_landscape and competitor_landscape.get('status') != 'failed':
                quality_assessment['competitor_data_quality'] = 'good'
                quality_assessment['overall_score'] += 0.34
            
            # Calculate data completeness
            expected_fields = ['consumer_insights', 'market_trends', 'pain_points', 'opportunities']
            completed_fields = sum(1 for field in expected_fields if state.get(field))
            quality_assessment['data_completeness'] = completed_fields / len(expected_fields)
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
        
        return quality_assessment
    
    def _generate_next_steps(self, state: MarketResearchState) -> List[str]:
        """Generate recommended next steps based on analysis results"""
        next_steps = [
            "Review identified market opportunities and prioritize based on business objectives",
            "Conduct deeper analysis on high-priority opportunities",
            "Develop product concepts targeting identified white space opportunities",
            "Validate findings with additional market research or consumer testing",
            "Create detailed business cases for selected opportunities"
        ]
        
        return next_steps
    
    @monitor_performance("report_generation", {"component": "3c_orchestrator"})
    async def _generate_final_report(self, state: MarketResearchState) -> MarketResearchState:
        """Generate the final 3C analysis report using the MarketResearchReportGenerator"""
        try:
            logger.info("Starting final report generation")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="processing",
                    message="Generating comprehensive 3C analysis report",
                    result={"step": "Report Generation", "status": "starting"}
                )
            
            # Generate the comprehensive 3C analysis report
            report_content = await self.report_generator.generate_3c_report(state)
            
            # Store the report in state
            state['report'] = report_content
            state['report_generation_timestamp'] = datetime.now().isoformat()
            
            # Add message about report generation
            messages = state.get('messages', [])
            report_msg = f"📄 Generated comprehensive 3C analysis report ({len(report_content)} characters)"
            messages.append(AIMessage(content=report_msg))
            state['messages'] = messages
            
            logger.info(f"Final report generated successfully ({len(report_content)} characters)")
            
            # Track workflow metrics
            await self._track_workflow_metrics(state, "report_generation")
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="completed",
                    message="3C Analysis report generated successfully",
                    result={
                        "step": "Report Generation",
                        "status": "completed",
                        "report_length": len(report_content),
                        "analysis_complete": True
                    }
                )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            
            # Generate a basic error report
            error_report = f"""# 3C Analysis Report - Error

**Target Market:** {state.get('target_market', 'Unknown')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Error

## Error Details

Report generation failed: {str(e)}

## Available Analysis Summary

- **Consumer Insights:** {'Available' if state.get('consumer_insights') else 'Not Available'}
- **Market Trends:** {'Available' if state.get('market_trends') else 'Not Available'}
- **Opportunities:** {len(state.get('opportunities', []))} identified
- **Recommendations:** {len(state.get('recommendations', []))} generated

Please check system logs for detailed error information.
"""
            
            state['report'] = error_report
            state['report_generation_error'] = str(e)
            
            if self.websocket_manager and self.job_id:
                await self.websocket_manager.send_status_update(
                    job_id=self.job_id,
                    status="warning",
                    message="Report generation encountered errors but analysis data is available",
                    error=str(e)
                )
        
        return state
    
    async def _track_workflow_metrics(self, state: MarketResearchState, stage: str):
        """Track comprehensive workflow metrics for production monitoring"""
        try:
            job_id = self.job_id or "unknown"
            target_market = state.get('target_market', 'unknown')
            
            # Track stage completion
            performance_monitor.record_metric(
                f"workflow_stage_{stage}_completed",
                1,
                {
                    "job_id": job_id,
                    "target_market": target_market,
                    "stage": stage
                }
            )
            
            # Track data quality metrics
            if stage == "data_curation":
                curated_data = state.get('curated_market_data', {})
                quality_score = curated_data.get('quality_score', 0)
                performance_monitor.record_metric(
                    "data_quality_score",
                    quality_score,
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track analysis completeness
            if stage == "consumer_analysis":
                consumer_insights = state.get('consumer_insights', {})
                insights_count = len(consumer_insights.get('structured_insights', []))
                performance_monitor.record_metric(
                    "consumer_insights_count",
                    insights_count,
                    {"job_id": job_id, "target_market": target_market}
                )
            
            if stage == "trend_analysis":
                market_trends = state.get('market_trends', {})
                trends_count = len(market_trends.get('structured_trends', []))
                performance_monitor.record_metric(
                    "market_trends_count",
                    trends_count,
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track competitor analysis
            if stage == "competitor_analysis":
                competitor_landscape = state.get('competitor_landscape', {})
                competitors_count = len(competitor_landscape.get('competitors', []))
                performance_monitor.record_metric(
                    "competitors_identified",
                    competitors_count,
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track SWOT analysis
            if stage == "swot_analysis":
                swot_analysis = state.get('swot_analysis', {})
                market_swot = swot_analysis.get('market_swot_analysis', {})
                swot_metrics = market_swot.get('swot_metrics', {})
                performance_monitor.record_metric(
                    "swot_quality_score",
                    swot_metrics.get('swot_quality_score', 0),
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track customer mapping
            if stage == "customer_mapping":
                customer_mapping = state.get('customer_mapping_results', {})
                insights_count = len(customer_mapping.get('consumer_insights', []))
                performance_monitor.record_metric(
                    "customer_insights_count",
                    insights_count,
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track opportunity identification
            if stage == "opportunity_analysis":
                opportunities = state.get('opportunities', [])
                white_spaces = state.get('white_spaces', [])
                performance_monitor.record_metric(
                    "opportunities_identified",
                    len(opportunities),
                    {"job_id": job_id, "target_market": target_market}
                )
                performance_monitor.record_metric(
                    "white_spaces_identified",
                    len(white_spaces),
                    {"job_id": job_id, "target_market": target_market}
                )
            
            # Track report generation
            if stage == "report_generation":
                report = state.get('report', '')
                performance_monitor.record_metric(
                    "report_length_characters",
                    len(report),
                    {"job_id": job_id, "target_market": target_market}
                )
                
                # Track report quality indicators
                report_quality_score = self._assess_report_quality(report)
                performance_monitor.record_metric(
                    "report_quality_score",
                    report_quality_score,
                    {"job_id": job_id, "target_market": target_market}
                )
            
        except Exception as e:
            logger.warning(f"Failed to track workflow metrics for stage {stage}: {e}")
    
    def _assess_report_quality(self, report: str) -> float:
        """Assess report quality based on content analysis"""
        if not report:
            return 0.0
        
        quality_indicators = [
            ('# 3C Analysis Report' in report, 0.2),  # Has proper header
            ('Executive Summary' in report, 0.15),     # Has executive summary
            ('Consumer Analysis' in report, 0.15),     # Has consumer section
            ('Market Trends' in report, 0.15),         # Has trends section
            ('Market Opportunities' in report, 0.15),  # Has opportunities section
            (len(report) > 2000, 0.1),                 # Substantial content
            ('Source:' in report, 0.1)                 # Has source attribution
        ]
        
        score = sum(weight for condition, weight in quality_indicators if condition)
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_market_keywords(self, target_market: str) -> List[str]:
        """Get market-specific keywords for enhanced search"""
        if target_market == 'japanese_curry':
            return [
                "japanese curry", "curry rice", "カレー", "curry roux", "curry sauce",
                "japanese food", "curry house", "curry restaurant", "instant curry",
                "curry powder", "curry spice", "curry flavor", "curry taste"
            ]
        else:
            return [target_market, f"{target_market} market", f"{target_market} industry"]
    
    async def _handle_ws_update(self, state: Dict[str, Any]):
        """Handle WebSocket updates based on state changes"""
        if not self.websocket_manager or not self.job_id:
            return
        
        update = {
            "type": "workflow_update",
            "data": {
                "current_step": self._get_current_step(state),
                "progress": self._calculate_progress(state),
                "state_keys": list(state.keys())
            }
        }
        
        await self.websocket_manager.broadcast_to_job(self.job_id, update)
    
    def _get_current_step(self, state: Dict[str, Any]) -> str:
        """Determine current workflow step based on state and selected agents"""
        if 'report' in state:
            return "report_generation"
        elif 'analysis_synthesis' in state:
            return "synthesis"
        elif 'opportunities' in state:
            return "opportunity_analysis"
        elif 'swot_analysis' in state:
            return "swot_analysis"
        elif 'competitor_landscape' in state:
            return "competitor_analysis"
        elif 'customer_mapping_results' in state:
            return "customer_mapping"
        elif 'market_trends' in state:
            return "trend_analysis"
        elif 'consumer_insights' in state:
            return "consumer_analysis"
        elif 'curated_market_data' in state:
            return "data_curation"
        elif 'raw_market_data' in state:
            return "data_collection"
        elif 'market_queries' in state:
            return "query_generation"
        else:
            return "initialization"
    
    def _calculate_progress(self, state: Dict[str, Any]) -> float:
        """Calculate workflow progress percentage based on selected agents"""
        completed_steps = 0
        
        # Core workflow steps (always present)
        base_steps = [
            ('market_queries', 'query_generation'),
            ('raw_market_data', 'data_collection'),
            ('curated_market_data', 'data_curation'),
            ('opportunities', 'opportunity_analysis'),
            ('analysis_synthesis', 'synthesis'),
            ('report', 'report_generation')
        ]
        
        # Agent-specific steps (conditional)
        agent_steps = []
        if "consumer_analysis" in self.selected_agents:
            agent_steps.append(('consumer_insights', 'consumer_analysis'))
        if "trend_analysis" in self.selected_agents:
            agent_steps.append(('market_trends', 'trend_analysis'))
        if "competitor_analysis" in self.selected_agents:
            agent_steps.append(('competitor_landscape', 'competitor_analysis'))
        if "swot_analysis" in self.selected_agents:
            agent_steps.append(('swot_analysis', 'swot_analysis'))
        if "customer_mapping" in self.selected_agents:
            agent_steps.append(('customer_mapping_results', 'customer_mapping'))
        
        all_steps = base_steps + agent_steps
        total_steps = len(all_steps)
        
        # Count completed steps
        for state_key, step_name in all_steps:
            if state_key in state:
                completed_steps += 1
        
        return (completed_steps / total_steps) * 100 if total_steps > 0 else 0
    
    def compile(self):
        """Compile the 3C analysis workflow graph"""
        return self.workflow.compile()