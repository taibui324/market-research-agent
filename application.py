import asyncio
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

from backend.company_single_research import Graph
from backend.nodes.orchestrator import ThreeCAnalysisOrchestrator
from backend.services.mongodb import MongoDBService
from backend.services.mock_mongodb import MockMongoDBService
from backend.services.pdf_service import PDFService
from backend.services.websocket_manager import WebSocketManager

import json


def make_json_serializable(obj):
    """Recursively remove/convert non-serializable objects."""
    if isinstance(obj, dict):
        return {
            k: make_json_serializable(v)
            for k, v in obj.items()
            if k != "websocket_manager"
        }
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    try:
        json.dumps(obj)  # test serialization
        return obj
    except (TypeError, OverflowError):
        return str(obj)  # fallback to string


# Load environment variables from .env file at startup
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

app = FastAPI(
    title="Company Research API",
    description="API for conducting comprehensive company research and analysis",
    version="1.0.0"
)

# Create API router for all endpoints
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Mount static files at root (must be last to avoid conflicts with API routes)
app.mount("/", StaticFiles(directory=os.getenv("STATIC_DIR", "ui/dist"), html=True), name="static")

manager = WebSocketManager()
pdf_service = PDFService({"pdf_output_dir": "pdfs"})

job_status = defaultdict(lambda: {
    "status": "pending",
    "progress": 0,
    "message": "",
    "result": None,
    "error": None,
    "created_at": datetime.now().isoformat(),
    "completed_at": None
})


# Store shared reports in memory (in production, use a database)
shared_reports = {}

mongodb = None
if mongo_uri := os.getenv("MONGODB_URI"):
    try:
        mongodb = MongoDBService(mongo_uri)
        logger.info("MongoDB integration enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize MongoDB: {e}. Using mock service.")
        mongodb = MockMongoDBService()
else:
    # Use mock service for development
    mongodb = MockMongoDBService()
    logger.info("Using MockMongoDBService for development")


# Updated data models for main company with competitors
class CompetitorData(BaseModel):
    company: str
    company_url: Optional[str] = None
    hq_location: Optional[str] = None
    industry: Optional[str] = None
    product_category: Optional[str] = None


class ResearchRequest(BaseModel):
    company: str
    company_url: Optional[str] = None
    industry: Optional[str] = None
    hq_location: Optional[str] = None
    product_category: Optional[str] = None
    competitors: List[CompetitorData] = []

class MarketResearchRequest(BaseModel):
    """Enhanced request model for 3C market research analysis with agent selection"""
    analysis_type: str = "3c_analysis"  # Type of analysis to perform
    analysis_depth: str = "comprehensive"  # comprehensive, focused, quick, consumer_focused, competitive_focused, market_trends_focused
    target_market: str = "japanese_curry"  # Market focus for analysis
    market_segment: Optional[str] = None  # Specific market segment
    company: Optional[str] = None  # Optional company context
    company_url: Optional[str] = None  # Optional company URL
    industry: Optional[str] = None  # Optional industry context
    hq_location: Optional[str] = None  # Optional location context
    selected_agents: Optional[List[str]] = None  # Specific agents to run: consumer_analysis, trend_analysis, competitor_analysis, swot_analysis, customer_mapping
    enable_parallel_execution: bool = True  # Enable parallel agent execution
    execution_mode: str = "hybrid"  # parallel, sequential, hybrid
    enable_performance_tracking: bool = True  # Enable detailed performance metrics
    priority_level: str = "normal"  # high, normal, low - affects resource allocation

class PDFGenerationRequest(BaseModel):
    report_content: str
    company_name: Optional[str] = None


class SharedReportRequest(BaseModel):
    job_id: str
    expiration_days: Optional[int] = 30

@api_router.options("/research")
async def preflight():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@api_router.options("/research/3c-analysis")
async def preflight_3c():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@api_router.post("/research")
async def research(data: ResearchRequest):
    try:
        logger.info(f"Received research request for {data.company}")
        job_id = str(uuid.uuid4())
        asyncio.create_task(process_research(job_id, data))

        response = JSONResponse(content={
            "status": "accepted",
            "job_id": job_id,
            "message": "Research started. Connect to WebSocket for updates.",
            "websocket_url": f"/api/research/ws/{job_id}",
            "analysis_type": "company_research"
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    except Exception as e:
        logger.error(f"Error initiating research: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/research/3c-analysis")
async def market_research(data: MarketResearchRequest):
    """Enhanced endpoint for 3C market research analysis with agent selection and performance tracking"""
    try:
        logger.info(f"Received enhanced 3C analysis request for {data.target_market} market")
        logger.info(f"Analysis depth: {data.analysis_depth}, Selected agents: {data.selected_agents}")
        logger.info(f"Execution mode: {data.execution_mode}, Performance tracking: {data.enable_performance_tracking}")
        
        job_id = str(uuid.uuid4())
        
        # Validate selected agents
        available_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"]
        if data.selected_agents:
            invalid_agents = [agent for agent in data.selected_agents if agent not in available_agents]
            if invalid_agents:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid agents specified: {invalid_agents}. Available agents: {available_agents}"
                )
        
        # Validate analysis depth
        valid_depths = ["comprehensive", "focused", "quick", "consumer_focused", "competitive_focused", "market_trends_focused"]
        if data.analysis_depth not in valid_depths:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis depth: {data.analysis_depth}. Valid options: {valid_depths}"
            )
        
        # Validate execution mode
        valid_modes = ["parallel", "sequential", "hybrid"]
        if data.execution_mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution mode: {data.execution_mode}. Valid options: {valid_modes}"
            )
        
        # Start the enhanced analysis process
        asyncio.create_task(process_enhanced_3c_analysis(job_id, data))

        # Calculate estimated completion time based on selected agents and execution mode
        estimated_duration = _calculate_estimated_duration(data.selected_agents, data.analysis_depth, data.execution_mode)
        
        response = JSONResponse(content={
            "status": "accepted",
            "job_id": job_id,
            "message": "Enhanced 3C Analysis started. Connect to WebSocket for real-time updates.",
            "websocket_url": f"/api/research/ws/{job_id}",
            "analysis_configuration": {
                "analysis_type": "3c_analysis",
                "analysis_depth": data.analysis_depth,
                "target_market": data.target_market,
                "market_segment": data.market_segment,
                "selected_agents": data.selected_agents,
                "execution_mode": data.execution_mode,
                "parallel_execution_enabled": data.enable_parallel_execution,
                "performance_tracking_enabled": data.enable_performance_tracking,
                "priority_level": data.priority_level
            },
            "estimated_completion_time_minutes": estimated_duration,
            "available_agents": available_agents,
            "supported_analysis_depths": valid_depths,
            "supported_execution_modes": valid_modes
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating enhanced 3C analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_research(job_id: str, data: ResearchRequest):
    """Process research workflow for company analysis"""
    try:
        # Use global MongoDB instance (real or mock)
        global mongodb

        if mongodb:
            mongodb.create_job(job_id, {
                "main_company": data.company,
                "company_url": data.company_url,
                "industry": data.industry,
                "hq_location": data.hq_location,
                "competitors": [competitor.dict() for competitor in data.competitors]
            })

        await manager.send_status_update(
            job_id, 
            status="processing", 
            message=f"Starting research for {data.company} and {len(data.competitors)} competitors"
        )

        # Initialize Graph with main company and competitors
        graph = Graph(
            company=data.company,
            company_url=data.company_url,
            industry=data.industry,
            hq_location=data.hq_location,
            product_category=data.product_category,
            competitors=[competitor.dict() for competitor in data.competitors],
            websocket_manager=manager,
            job_id=job_id
        )

        # Run the workflow
        final_state = None
        async for state in graph.run(thread={}):
            # Capture the final state
            final_state = state

        # Wait a moment for any final processing
        await asyncio.sleep(2)

        # Save the final report to database if we have the state
        if mongodb and final_state:
            try:
                clean_state = make_json_serializable(final_state)

                # Debug: Log the available keys in the final state
                logger.info(f"Final state keys: {list(final_state.keys())}")

                # Store the report in the database
                # Extract the report content and competitor analysis data
                report_content = final_state.get("report", "")
                competitor_analyses = final_state.get("competitor_analyses", {})
                swot_analyses = final_state.get("swot_analyses", {})
                companies_data = final_state.get("companies_data", {})
                
                # Store the final report with all data
                mongodb.store_report(
                    job_id=job_id,
                    report_content=report_content,
                    report_competitor_analyses=competitor_analyses,
                    report_main_company=data.company,
                    report_competitors=[c.dict() for c in data.competitors],
                    report_industry=data.industry,
                    report_hq_location=data.hq_location,
                    report_product_category=data.product_category,
                    report_type="competitive_analysis"
                )
                logger.info(f"Successfully saved report to database for job {job_id}")

            except Exception as e:
                logger.error(f"Failed to save report to database: {e}")
                raise Exception(f"Failed to save report to database: {e}")

        # Query the database for the report using job_id
        report_data = None
        if mongodb:
            try:
                report_data = mongodb.get_report(job_id)
                logger.info(f"Retrieved report from database for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to retrieve report from database: {e}")

        if not report_data:
            raise Exception("No report found in database")

        # Extract data from the database
        report_content = report_data.get("report_content", "")
        swot_analyses = report_data.get("swot_analyses", {})
        competitor_analyses = report_data.get("competitor_analyses", {})
        companies_data = report_data.get("companies_data", {})

        if not report_content:
            raise Exception("No report content found in database")

        # Update job status
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["progress"] = 100
        job_status[job_id]["message"] = "Research completed successfully"
        job_status[job_id]["result"] = {
            "report_content": report_content,
            "swot_analyses": swot_analyses,
            "competitor_analyses": competitor_analyses,
            "companies_analyzed": list(companies_data.keys()),
            "main_company": data.company,
            "competitors": [c.company for c in data.competitors]
        }
        job_status[job_id]["completed_at"] = datetime.now().isoformat()

        # Send final WebSocket update
        await manager.send_status_update(
            job_id,
            status="completed",
            message="Research completed successfully",
            result=job_status[job_id]["result"]
        )

    except Exception as e:
        logger.error(f"Error in background analysis: {str(e)}", exc_info=True)
        job_status[job_id]["status"] = "error"
        job_status[job_id]["error"] = str(e)
        job_status[job_id]["message"] = f"Research failed: {str(e)}"

        if mongodb:
            try:
                mongodb.update_job(job_id, {
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to update MongoDB with error: {e}")

        # Send error WebSocket update
        await manager.send_status_update(
            job_id,
            status="error",
            message=f"Research failed: {str(e)}",
            error=str(e)
        )
        if mongodb:
            mongodb.update_job(job_id=job_id, status="failed", error=str(e))

def _calculate_estimated_duration(selected_agents: Optional[List[str]], analysis_depth: str, execution_mode: str) -> int:
    """Calculate estimated completion time in minutes based on configuration"""
    # Base durations per agent (in minutes)
    agent_durations = {
        "consumer_analysis": 2.0,
        "trend_analysis": 1.7,
        "competitor_analysis": 1.8,
        "swot_analysis": 1.3,
        "customer_mapping": 1.5
    }
    
    # Get agents based on analysis depth if not explicitly selected
    if not selected_agents:
        if analysis_depth == "comprehensive":
            selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"]
        elif analysis_depth == "focused":
            selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]
        elif analysis_depth == "quick":
            selected_agents = ["consumer_analysis", "trend_analysis"]
        elif analysis_depth == "consumer_focused":
            selected_agents = ["consumer_analysis", "customer_mapping", "trend_analysis"]
        elif analysis_depth == "competitive_focused":
            selected_agents = ["competitor_analysis", "swot_analysis", "trend_analysis"]
        elif analysis_depth == "market_trends_focused":
            selected_agents = ["trend_analysis", "consumer_analysis"]
        else:
            selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]
    
    # Calculate total duration
    if execution_mode == "parallel":
        # Parallel execution - use maximum duration
        duration = max([agent_durations.get(agent, 2.0) for agent in selected_agents])
    else:
        # Sequential or hybrid - sum all durations
        duration = sum([agent_durations.get(agent, 2.0) for agent in selected_agents])
    
    # Add overhead for data collection, synthesis, and report generation
    overhead = 1.5
    
    return int(duration + overhead)

async def process_enhanced_3c_analysis(job_id: str, data: MarketResearchRequest):
    """Enhanced 3C analysis processing with agent selection and performance tracking"""
    try:
        # Use global MongoDB instance (real or mock)
        global mongodb

        # Initialize job status
        job_status[job_id].update({
            "status": "processing",
            "progress": 0,
            "message": "Starting Enhanced 3C Analysis workflow",
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        })

        if mongodb:
            mongodb.create_job(job_id, data.model_dump())
        await asyncio.sleep(1)  # Allow WebSocket connection

        # Send initial status with configuration details
        await manager.send_status_update(
            job_id, 
            status="processing", 
            message="Starting Enhanced 3C Analysis workflow",
            result={
                "analysis_configuration": {
                    "analysis_depth": data.analysis_depth,
                    "execution_mode": data.execution_mode,
                    "selected_agents": data.selected_agents,
                    "performance_tracking": data.enable_performance_tracking,
                    "priority_level": data.priority_level
                },
                "workflow_stage": "initialization"
            }
        )

        # Import MarketResearchState here to avoid circular imports
        from backend.classes.state import MarketResearchState
        from backend.nodes.orchestrator import ThreeCAnalysisOrchestrator

        # Determine selected agents based on analysis depth
        selected_agents = data.selected_agents
        if not selected_agents:
            if data.analysis_depth == "comprehensive":
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"]
            elif data.analysis_depth == "focused":
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]
            elif data.analysis_depth == "quick":
                selected_agents = ["consumer_analysis", "trend_analysis"]
            elif data.analysis_depth == "consumer_focused":
                selected_agents = ["consumer_analysis", "customer_mapping", "trend_analysis"]
            elif data.analysis_depth == "competitive_focused":
                selected_agents = ["competitor_analysis", "swot_analysis", "trend_analysis"]
            elif data.analysis_depth == "market_trends_focused":
                selected_agents = ["trend_analysis", "consumer_analysis"]
            else:
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]

        # Initialize enhanced orchestrator with new capabilities
        orchestrator = ThreeCAnalysisOrchestrator(
            websocket_manager=manager,
            job_id=job_id,
            analysis_type=data.analysis_depth,
            selected_agents=selected_agents
        )

        # Create initial state for enhanced 3C analysis
        initial_state = MarketResearchState(
            analysis_type=data.analysis_type,
            target_market=data.target_market,
            market_segment=data.market_segment or "general",
            company=data.company or "Market Analysis",
            company_url=data.company_url,
            industry=data.industry,
            hq_location=data.hq_location,
            websocket_manager=manager,
            job_id=job_id,
            messages=[],
            # Initialize required fields with empty values
            site_scrape={},
            financial_data={},
            news_data={},
            industry_data={},
            company_data={},
            curated_financial_data={},
            curated_news_data={},
            curated_industry_data={},
            curated_company_data={},
            financial_briefing="",
            news_briefing="",
            industry_briefing="",
            company_briefing="",
            references=[],
            briefings={},
            report="",
            companies_data={},
            swot_analyses={},
            competitor_analyses={},
            competitor_analysis_content="",
            competitor_analysis_structured={},
            competitor_analysis_metrics={},
            customer_mapping_results={
                "start_date": datetime.now(),
                "end_date": datetime.now(),
                "trend_summaries": [],
                "consumer_insights": []
            },
            # Initialize 3C analysis fields
            consumer_insights={},
            customer_personas=[],
            pain_points=[],
            purchase_journey={},
            market_trends={},
            trend_predictions=[],
            adoption_curves={},
            competitor_landscape={},
            competitive_positioning={},
            feature_comparisons=[],
            market_gaps=[],
            opportunities=[],
            white_spaces=[],
            recommendations=[],
            market_focus_keywords=[]
        )

        # Track performance metrics
        performance_metrics = {
            "workflow_start_time": datetime.now().isoformat(),
            "selected_agents": selected_agents,
            "execution_mode": data.execution_mode,
            "agent_performance": {},
            "total_duration": 0,
            "success_rate": 0
        }

        # Execute enhanced 3C analysis workflow
        final_state = {}
        completed_agents = []
        failed_agents = []

        async for state in orchestrator.run(initial_state):
            final_state.update(state)

            # Track agent completion and performance
            if data.enable_performance_tracking:
                # Update performance metrics based on state changes
                for agent_name in selected_agents:
                    if agent_name not in performance_metrics["agent_performance"]:
                        performance_metrics["agent_performance"][agent_name] = {
                            "status": "pending",
                            "start_time": None,
                            "end_time": None,
                            "duration": 0,
                            "success": False
                        }

                # Send performance metrics update
                await manager.send_performance_metrics_update(job_id, performance_metrics)

        ## get the report_conrent from db
        ## how we store it
        # mongodb_service.reports.insert_one(
        #     {
        #         "job_id": state.get("job_id"),
        #         "analysis_type": "consumer_analysis_report",
        #         "created_at": datetime.now(),
        #         "updated_at": datetime.now(),
        #         "report": formatted_consumer_content,
        #     }
        # )
        ## need to refactor
        report_content = mongodb.get_report(job_id,analysis_type="consumer_analysis_report")['report']

        # Calculate final performance metrics
        workflow_end_time = datetime.now()
        workflow_start_time = datetime.fromisoformat(performance_metrics["workflow_start_time"])
        total_duration = (workflow_end_time - workflow_start_time).total_seconds()

        performance_metrics.update({
            "workflow_end_time": workflow_end_time.isoformat(),
            "total_duration": total_duration,
            "success_rate": len(completed_agents) / len(selected_agents) if selected_agents else 1.0,
            "completed_agents": completed_agents,
            "failed_agents": failed_agents
        })

        if report_content:
            logger.info(f"Enhanced 3C Analysis completed successfully (report length: {len(report_content)})")
            job_status[job_id].update({
                "status": "completed",
                "report": report_content,
                "analysis_type": "3c_analysis_backup",
                "target_market": data.target_market,
                "last_update": datetime.now().isoformat(),
                "performance_metrics": performance_metrics
            })
            if mongodb:
                mongodb.update_job(job_id=job_id, status="completed")
                mongodb.store_report(job_id=job_id, report_data={
                    "report": report_content,
                    "analysis_type": "3c_analysis",
                    "target_market": data.target_market,
                    "performance_metrics": performance_metrics
                })

            # Send final completion update with comprehensive results
            await manager.send_status_update(
                job_id=job_id,
                status="completed",
                message="Enhanced 3C Analysis completed successfully",
                result={
                    "report": report_content,
                    "analysis_configuration": {
                        "analysis_type": "3c_analysis",
                        "analysis_depth": data.analysis_depth,
                        "target_market": data.target_market,
                        "selected_agents": selected_agents,
                        "execution_mode": data.execution_mode
                    },
                    "performance_metrics": performance_metrics,
                    "analysis_summary": final_state.get('analysis_synthesis', {}),
                    "agent_results": {
                        "consumer_analysis": "completed" if "consumer_analysis" in completed_agents else ("failed" if "consumer_analysis" in failed_agents else "skipped"),
                        "trend_analysis": "completed" if "trend_analysis" in completed_agents else ("failed" if "trend_analysis" in failed_agents else "skipped"),
                        "competitor_analysis": "completed" if "competitor_analysis" in completed_agents else ("failed" if "competitor_analysis" in failed_agents else "skipped"),
                        "swot_analysis": "completed" if "swot_analysis" in completed_agents else ("failed" if "swot_analysis" in failed_agents else "skipped"),
                        "customer_mapping": "completed" if "customer_mapping" in completed_agents else ("failed" if "customer_mapping" in failed_agents else "skipped")
                    }
                }
            )
        else:
            logger.error(f"Enhanced 3C Analysis completed without generating report. State keys: {list(final_state.keys())}")

            error_message = "Enhanced 3C Analysis completed but no report was generated"
            if error := final_state.get('error'):
                error_message = f"Error: {error}"

            # Update job status for failed report generation
            job_status[job_id].update({
                "status": "failed",
                "error": error_message,
                "message": error_message,
                "last_update": datetime.now().isoformat(),
                "performance_metrics": performance_metrics
            })

            await manager.send_status_update(
                job_id=job_id,
                status="failed",
                message=error_message,
                error=error_message,
                result={
                    "performance_metrics": performance_metrics,
                    "failed_agents": failed_agents,
                    "final_state_keys": list(final_state.keys())
                }
            )

    except Exception as e:
        logger.error(f"Enhanced 3C Analysis failed: {str(e)}", exc_info=True)

        # Update job status for exception
        job_status[job_id].update({
            "status": "failed",
            "error": str(e),
            "message": f"Enhanced 3C Analysis failed: {str(e)}",
            "last_update": datetime.now().isoformat()
        })

        await manager.send_status_update(
            job_id=job_id,
            status="failed",
            message=f"Enhanced 3C Analysis failed: {str(e)}",
            error=str(e),
            result={
                "error_type": type(e).__name__,
                "analysis_configuration": {
                    "analysis_depth": data.analysis_depth,
                    "selected_agents": data.selected_agents,
                    "execution_mode": data.execution_mode
                }
            }
        )
        if mongodb:
            mongodb.update_job(job_id=job_id, status="failed", error=str(e))

async def process_3c_analysis(job_id: str, data: MarketResearchRequest):
    """Process 3C market research analysis workflow"""
    try:
        # Use global MongoDB instance (real or mock)
        global mongodb

        if mongodb:
            mongodb.create_job(job_id, data.model_dump())
        await asyncio.sleep(1)  # Allow WebSocket connection

        await manager.send_status_update(
            job_id, 
            status="processing", 
            message="Starting 3C Analysis workflow"
        )

        # Import MarketResearchState here to avoid circular imports
        from backend.classes.state import MarketResearchState
        
        # Initialize enhanced 3C analysis orchestrator with agent selection
        selected_agents = data.selected_agents
        if not selected_agents:
            # Use default agents based on analysis depth
            if data.analysis_depth == "comprehensive":
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"]
            elif data.analysis_depth == "focused":
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]
            elif data.analysis_depth == "quick":
                selected_agents = ["consumer_analysis", "trend_analysis"]
            else:
                selected_agents = ["consumer_analysis", "trend_analysis", "competitor_analysis"]
        
        orchestrator = ThreeCAnalysisOrchestrator(
            websocket_manager=manager,
            job_id=job_id,
            analysis_type=data.analysis_depth,
            selected_agents=selected_agents
        )

        # Create initial state for 3C analysis
        initial_state = MarketResearchState(
            analysis_type=data.analysis_type,
            target_market=data.target_market,
            market_segment=data.market_segment or "general",
            company=data.company or "Market Analysis",
            company_url=data.company_url,
            industry=data.industry,
            hq_location=data.hq_location,
            websocket_manager=manager,
            job_id=job_id,
            messages=[],
            # Initialize required fields with empty values
            site_scrape={},
            financial_data={},
            news_data={},
            industry_data={},
            company_data={},
            curated_financial_data={},
            curated_news_data={},
            curated_industry_data={},
            curated_company_data={},
            financial_briefing="",
            news_briefing="",
            industry_briefing="",
            company_briefing="",
            references=[],
            briefings={},
            report="",
            # Initialize 3C analysis fields
            consumer_insights={},
            customer_personas=[],
            pain_points=[],
            purchase_journey={},
            market_trends={},
            trend_predictions=[],
            adoption_curves={},
            competitor_landscape={},
            competitive_positioning={},
            feature_comparisons=[],
            market_gaps=[],
            opportunities=[],
            white_spaces=[],
            recommendations=[],
            market_focus_keywords=[]
        )

        # Execute 3C analysis workflow (report generation is now integrated)
        final_state = {}
        async for state in orchestrator.run(initial_state):
            final_state.update(state)
        
        # Report is now generated as part of the workflow
        report_content = final_state.get('report')
        
        if report_content:
            logger.info(f"3C Analysis completed successfully (report length: {len(report_content)})")
            job_status[job_id].update({
                "status": "completed",
                "report": report_content,
                "analysis_type": "3c_analysis",
                "target_market": data.target_market,
                "last_update": datetime.now().isoformat()
            })
            if mongodb:
                mongodb.update_job(job_id=job_id, status="completed")
                mongodb.store_report(job_id=job_id, report_data={
                    "report": report_content,
                    "analysis_type": "3c_analysis",
                    "target_market": data.target_market
                })
            await manager.send_status_update(
                job_id=job_id,
                status="completed",
                message="3C Analysis completed successfully",
                result={
                    "report": report_content,
                    "analysis_type": "3c_analysis",
                    "analysis_depth": data.analysis_depth,
                    "target_market": data.target_market,
                    "selected_agents": selected_agents,
                    "analysis_summary": final_state.get('analysis_synthesis', {}),
                    "agent_performance": {
                        "consumer_analysis": "completed" if "consumer_analysis" in selected_agents else "skipped",
                        "trend_analysis": "completed" if "trend_analysis" in selected_agents else "skipped",
                        "competitor_analysis": "completed" if "competitor_analysis" in selected_agents else "skipped",
                        "swot_analysis": "completed" if "swot_analysis" in selected_agents else "skipped",
                        "customer_mapping": "completed" if "customer_mapping" in selected_agents else "skipped"
                    }
                }
            )
        else:
            logger.error(f"3C Analysis completed without generating report. State keys: {list(final_state.keys())}")
            
            error_message = "3C Analysis completed but no report was generated"
            if error := final_state.get('error'):
                error_message = f"Error: {error}"
            
            await manager.send_status_update(
                job_id=job_id,
                status="failed",
                message=error_message,
                error=error_message
            )

    except Exception as e:
        logger.error(f"3C Analysis failed: {str(e)}", exc_info=True)
        await manager.send_status_update(
            job_id=job_id,
            status="failed",
            message=f"3C Analysis failed: {str(e)}",
            error=str(e)
        )
        if mongodb:
            mongodb.update_job(job_id=job_id, status="failed", error=str(e))

async def generate_3c_report(state: dict) -> str:
    """Generate a formatted 3C analysis report using the MarketResearchReportGenerator"""
    try:
        from backend.services.report_generator import MarketResearchReportGenerator
        
        # Initialize the report generator
        report_generator = MarketResearchReportGenerator()
        
        # Generate the comprehensive report
        report = await report_generator.generate_3c_report(state)
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating 3C report: {e}")
        return f"# 3C Analysis Report\n\nError generating report: {str(e)}"

@api_router.get("/")
async def ping():
    return {"message": "Alive"}

@api_router.get("/research/capabilities")
async def get_analysis_capabilities():
    """Get available analysis capabilities, agents, and configuration options"""
    return {
        "available_agents": [
            {
                "name": "consumer_analysis",
                "description": "Analyzes consumer insights, pain points, and customer personas",
                "estimated_duration_minutes": 2.0,
                "data_sources": ["social_media", "reviews", "forums", "surveys"]
            },
            {
                "name": "trend_analysis", 
                "description": "Identifies market trends and future predictions",
                "estimated_duration_minutes": 1.7,
                "data_sources": ["industry_publications", "market_reports", "news"]
            },
            {
                "name": "competitor_analysis",
                "description": "Maps competitive landscape and positioning",
                "estimated_duration_minutes": 1.8,
                "data_sources": ["competitor_websites", "product_reviews", "press_releases"]
            },
            {
                "name": "swot_analysis",
                "description": "Performs SWOT analysis based on market research",
                "estimated_duration_minutes": 1.3,
                "data_sources": ["synthesized_market_data"]
            },
            {
                "name": "customer_mapping",
                "description": "Maps customer journey and behavior patterns",
                "estimated_duration_minutes": 1.5,
                "data_sources": ["consumer_behavior_data", "purchase_patterns"]
            }
        ],
        "analysis_depths": [
            {
                "name": "comprehensive",
                "description": "Full 3C analysis with all available agents",
                "default_agents": ["consumer_analysis", "trend_analysis", "competitor_analysis", "swot_analysis", "customer_mapping"],
                "estimated_duration_minutes": 8
            },
            {
                "name": "focused",
                "description": "Core 3C analysis with essential agents",
                "default_agents": ["consumer_analysis", "trend_analysis", "competitor_analysis"],
                "estimated_duration_minutes": 6
            },
            {
                "name": "quick",
                "description": "Rapid analysis focusing on consumer and trends",
                "default_agents": ["consumer_analysis", "trend_analysis"],
                "estimated_duration_minutes": 4
            },
            {
                "name": "consumer_focused",
                "description": "Deep dive into consumer behavior and needs",
                "default_agents": ["consumer_analysis", "customer_mapping", "trend_analysis"],
                "estimated_duration_minutes": 5
            },
            {
                "name": "competitive_focused",
                "description": "Comprehensive competitive intelligence",
                "default_agents": ["competitor_analysis", "swot_analysis", "trend_analysis"],
                "estimated_duration_minutes": 5
            },
            {
                "name": "market_trends_focused",
                "description": "Market trend analysis and predictions",
                "default_agents": ["trend_analysis", "consumer_analysis"],
                "estimated_duration_minutes": 4
            }
        ],
        "execution_modes": [
            {
                "name": "parallel",
                "description": "Maximum parallel execution for fastest completion",
                "benefits": ["Fastest execution", "Resource intensive"],
                "recommended_for": ["High priority analysis", "Time-sensitive requests"]
            },
            {
                "name": "sequential", 
                "description": "Sequential execution with full dependency management",
                "benefits": ["Lower resource usage", "Better error handling"],
                "recommended_for": ["Resource-constrained environments", "Complex dependencies"]
            },
            {
                "name": "hybrid",
                "description": "Intelligent mix of parallel and sequential execution",
                "benefits": ["Balanced performance", "Optimal resource usage"],
                "recommended_for": ["Most use cases", "Default recommendation"]
            }
        ],
        "supported_markets": [
            "japanese_curry",
            "food",
            "restaurant", 
            "packaged_food",
            "technology",
            "software",
            "saas",
            "fintech",
            "healthcare",
            "pharmaceutical",
            "medical"
        ],
        "priority_levels": ["high", "normal", "low"]
    }

@api_router.get("/research/agents/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Get detailed status and capabilities of a specific agent"""
    agent_info = {
        "consumer_analysis": {
            "name": "Consumer Analysis Agent",
            "status": "available",
            "capabilities": [
                "Social media sentiment analysis",
                "Review and forum analysis", 
                "Pain point identification",
                "Customer persona generation",
                "Purchase journey mapping"
            ],
            "data_sources": ["Twitter/X", "Instagram", "Reddit", "Review sites", "Forums"],
            "output_format": ["consumer_insights", "pain_points", "customer_personas", "purchase_journey"]
        },
        "trend_analysis": {
            "name": "Trend Analysis Agent",
            "status": "available", 
            "capabilities": [
                "Market trend identification",
                "Industry publication monitoring",
                "Trend prediction and forecasting",
                "Adoption curve analysis"
            ],
            "data_sources": ["Industry publications", "Market research reports", "News sources"],
            "output_format": ["market_trends", "trend_predictions", "adoption_curves"]
        },
        "competitor_analysis": {
            "name": "Competitor Analysis Agent",
            "status": "available",
            "capabilities": [
                "Competitive landscape mapping",
                "Feature comparison analysis",
                "Market positioning analysis", 
                "White space identification"
            ],
            "data_sources": ["Competitor websites", "Product reviews", "Press releases", "Annual reports"],
            "output_format": ["competitor_landscape", "competitive_positioning", "feature_comparisons", "market_gaps"]
        },
        "swot_analysis": {
            "name": "SWOT Analysis Agent",
            "status": "available",
            "capabilities": [
                "Strengths analysis",
                "Weaknesses identification",
                "Opportunities assessment",
                "Threats evaluation"
            ],
            "data_sources": ["Synthesized market research data"],
            "output_format": ["swot_analysis", "strategic_recommendations"]
        },
        "customer_mapping": {
            "name": "Customer Mapping Agent", 
            "status": "available",
            "capabilities": [
                "Customer behavior clustering",
                "Journey mapping",
                "Trend frequency analysis",
                "Consumer insight categorization"
            ],
            "data_sources": ["Consumer behavior data", "Purchase patterns", "Interaction data"],
            "output_format": ["customer_mapping_results", "behavior_clusters", "journey_maps"]
        }
    }
    
    if agent_name not in agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return agent_info[agent_name]

@api_router.get("/research/performance/metrics")
async def get_performance_metrics():
    """Get system-wide performance metrics and statistics"""
    # This would typically come from a monitoring system
    # For now, return mock data structure
    return {
        "system_metrics": {
            "average_analysis_duration_minutes": 5.2,
            "success_rate_percentage": 94.5,
            "total_analyses_completed": 1247,
            "active_analyses": 3
        },
        "agent_metrics": {
            "consumer_analysis": {
                "average_duration_minutes": 2.1,
                "success_rate_percentage": 96.2,
                "total_executions": 1247
            },
            "trend_analysis": {
                "average_duration_minutes": 1.8,
                "success_rate_percentage": 94.8,
                "total_executions": 1198
            },
            "competitor_analysis": {
                "average_duration_minutes": 1.9,
                "success_rate_percentage": 92.1,
                "total_executions": 987
            },
            "swot_analysis": {
                "average_duration_minutes": 1.4,
                "success_rate_percentage": 97.3,
                "total_executions": 856
            },
            "customer_mapping": {
                "average_duration_minutes": 1.6,
                "success_rate_percentage": 95.7,
                "total_executions": 743
            }
        },
        "execution_mode_metrics": {
            "parallel": {
                "average_duration_minutes": 3.2,
                "resource_usage": "high",
                "success_rate_percentage": 93.1
            },
            "sequential": {
                "average_duration_minutes": 7.8,
                "resource_usage": "low", 
                "success_rate_percentage": 96.4
            },
            "hybrid": {
                "average_duration_minutes": 5.2,
                "resource_usage": "medium",
                "success_rate_percentage": 94.5
            }
        }
    }

@api_router.post("/company_analysis", tags=["company_analysis"])
async def company_analysis(data: ResearchRequest):
    """
    Start comprehensive research and analysis for a main company and its competitors.
    Returns job_id immediately and processes in background.
    """
    logger.info(f"Starting research for main company: {data.company} with {len(data.competitors)} competitors")
    
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id]["status"] = "pending"
    job_status[job_id]["progress"] = 0
    job_status[job_id]["message"] = f"Starting research for {data.company} and {len(data.competitors)} competitors"
    job_status[job_id]["result"] = {
        "main_company": data.company,
        "competitors": [c.company for c in data.competitors],
        "total_companies": len(data.competitors) + 1
    }

    # Start background task
    asyncio.create_task(process_research(job_id, data))

    # Return job_id immediately
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Research started in background",
        "result": {
            "main_company": data.company,
            "competitors": [c.company for c in data.competitors],
            "total_companies": len(data.competitors) + 1
        }
    }

async def run_analysis_background(job_id: str, data: ResearchRequest):
    """Background task to run the analysis"""
    await process_research(job_id, data)

@api_router.get("/job_status/{job_id}", tags=["job_status"])
async def get_job_status(job_id: str):
    """Get the status of a specific job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job_status[job_id]["status"],
        "progress": job_status[job_id]["progress"],
        "message": job_status[job_id]["message"],
        "result": job_status[job_id]["result"],
        "error": job_status[job_id]["error"],
        "created_at": job_status[job_id]["created_at"],
        "completed_at": job_status[job_id]["completed_at"]
    }

@api_router.get("/research/job/{job_id}/status")
async def get_enhanced_job_status(job_id: str):
    """Get enhanced job status with performance metrics and agent details"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_status[job_id]
    
    # Extract performance metrics if available
    performance_metrics = job_data.get("performance_metrics", {})
    
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "progress": job_data.get("progress", 0),
        "message": job_data["message"],
        "result": job_data["result"],
        "error": job_data["error"],
        "created_at": job_data["created_at"],
        "completed_at": job_data["completed_at"],
        "analysis_type": job_data.get("analysis_type", "unknown"),
        "target_market": job_data.get("target_market", ""),
        "performance_metrics": performance_metrics,
        "agent_status": {
            "consumer_analysis": _get_agent_status_from_metrics(performance_metrics, "consumer_analysis"),
            "trend_analysis": _get_agent_status_from_metrics(performance_metrics, "trend_analysis"),
            "competitor_analysis": _get_agent_status_from_metrics(performance_metrics, "competitor_analysis"),
            "swot_analysis": _get_agent_status_from_metrics(performance_metrics, "swot_analysis"),
            "customer_mapping": _get_agent_status_from_metrics(performance_metrics, "customer_mapping")
        }
    }

def _get_agent_status_from_metrics(performance_metrics: dict, agent_name: str) -> dict:
    """Extract agent status from performance metrics"""
    agent_perf = performance_metrics.get("agent_performance", {}).get(agent_name, {})
    
    return {
        "status": agent_perf.get("status", "not_selected"),
        "duration": agent_perf.get("duration", 0),
        "success": agent_perf.get("success", False),
        "start_time": agent_perf.get("start_time"),
        "end_time": agent_perf.get("end_time")
    }

@api_router.get("/job_result/{job_id}", tags=["job_result"])
async def get_job_result(job_id: str):
    """Get the result of a completed job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_status[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return {
        "job_id": job_id,
        "status": job_status[job_id]["status"],
        "result": job_status[job_id]["result"]
    }

@api_router.get("/company_analysis/pdf/{filename}", tags=["company_analysis"], summary="Get PDF Report", description="Download a generated PDF report by filename")
async def get_pdf(filename: str):
    """
    Download a PDF report by filename.
    
    Returns the PDF file if it exists in the system.
    """
    pdf_path = os.path.join("pdfs", filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type='application/pdf', filename=filename)

@app.websocket("/api/research/ws/{job_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    Enhanced WebSocket endpoint for real-time research progress updates with agent-specific tracking.
    
    Supports multiple update types:
    - status_update: General workflow status
    - agent_progress: Individual agent progress and performance
    - workflow_progress: Overall workflow progress with agent states
    - performance_metrics: Real-time performance metrics
    """
    try:
        await websocket.accept()
        await manager.connect(websocket, job_id)

        # Send initial connection confirmation with enhanced capabilities
        if job_id in job_status:
            status = job_status[job_id]
            await manager.send_status_update(
                job_id,
                status=status["status"],
                message="Connected to enhanced status stream with agent tracking",
                error=status["error"],
                result=status["result"]
            )
        else:
            await manager.send_status_update(
                job_id,
                status="connected",
                message="Connected to enhanced WebSocket stream. Waiting for analysis to start.",
                result={
                    "websocket_capabilities": [
                        "status_update",
                        "agent_progress", 
                        "workflow_progress",
                        "performance_metrics"
                    ]
                }
            )

        # Keep connection alive and handle client messages
        while True:
            try:
                # Listen for client messages (could be used for real-time control)
                message = await websocket.receive_text()
                
                # Handle client requests (optional feature for future enhancement)
                try:
                    client_request = json.loads(message)
                    if client_request.get("type") == "get_status":
                        # Send current status on request
                        if job_id in job_status:
                            await manager.send_status_update(
                                job_id,
                                status=job_status[job_id]["status"],
                                message="Status requested by client",
                                result=job_status[job_id].get("result")
                            )
                except json.JSONDecodeError:
                    # Ignore invalid JSON messages
                    pass
                    
            except WebSocketDisconnect:
                manager.disconnect(websocket, job_id)
                break

    except Exception as e:
        logger.error(f"Enhanced WebSocket error for job {job_id}: {str(e)}", exc_info=True)
        manager.disconnect(websocket, job_id)

@app.websocket("/api/company_analysis/ws/{job_id}")
async def legacy_websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    Legacy WebSocket endpoint for backward compatibility.
    
    Connect to this endpoint to receive live updates about the research process.
    """
    try:
        await websocket.accept()
        await manager.connect(websocket, job_id)

        if job_id in job_status:
            status = job_status[job_id]
            await manager.send_status_update(
                job_id,
                status=status["status"],
                message="Connected to status stream",
                error=status["error"],
                result=status["result"]
            )

        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                manager.disconnect(websocket, job_id)
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}", exc_info=True)
        manager.disconnect(websocket, job_id)

@api_router.get("/company_analysis/{job_id}", tags=["company_analysis"], summary="Get Research Job Status", description="Retrieve the status and details of a research job")
async def get_research(job_id: str):
    """
    Get the status and details of a research job.
    
    Returns information about the research job including its current status,
    progress, and any results or errors.
    """
    # This endpoint is now redundant as job_status is a defaultdict
    # and the job_id will be in job_status.
    # Keeping it for now as per instructions, but it will always return the current state.
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job_status[job_id]

@api_router.get("/company_analysis/{job_id}/report", tags=["company_analysis"], summary="Get Research Report", description="Retrieve the final research report for a completed job")
async def get_research_report(job_id: str):
    """
    Get the final research report for a completed job.
    
    Returns the comprehensive research report if the job has been completed.
    """
    # Use global MongoDB instance (real or mock)
    global mongodb
    if not mongodb:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Query the database for the report
    try:
        report_data = mongodb.get_report(job_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Research report not found")
        
        # Extract data from the database
        report_content = report_data.get("report_content", "")
        swot_analyses = report_data.get("swot_analyses", {})
        competitor_analyses = report_data.get("competitor_analyses", {})
        companies_data = report_data.get("companies_data", {})
        main_company = report_data.get("main_company")
        competitors = report_data.get("competitors", [])
        
        if not report_content:
            raise HTTPException(status_code=404, detail="No report content found")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "report_content": report_content,
            "swot_analyses": swot_analyses,
            "competitor_analyses": competitor_analyses,
            "companies_analyzed": list(companies_data.keys()),
            "main_company": main_company,
            "competitors": competitors,
            "created_at": report_data.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report from database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")

@api_router.post("/generate-pdf", tags=["company_analysis"], summary="Generate PDF Report", description="Generate a PDF from markdown content and stream it to the client")
async def generate_pdf(data: PDFGenerationRequest):
    """
    Generate a PDF from markdown content and stream it to the client.
    
    Takes markdown content and converts it to a downloadable PDF file.
    """
    try:
        success, result = pdf_service.generate_pdf_stream(data.report_content, data.company_name)
        if success:
            pdf_buffer, filename = result
            return StreamingResponse(
                pdf_buffer,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/shared-reports")
async def create_shared_report(data: SharedReportRequest):
    """Create a shareable link for a report"""
    try:
        # Check if the job exists and has a report
        if data.job_id not in job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_status[data.job_id]
        if job["status"] != "completed" or not job.get("report"):
            raise HTTPException(status_code=400, detail="Report not available for sharing")
        
        # Generate a unique share ID
        share_id = str(uuid.uuid4())
        
        # Calculate expiration date
        expiration_date = None
        if data.expiration_days and data.expiration_days > 0:
            from datetime import timedelta
            expiration_date = (datetime.now() + timedelta(days=data.expiration_days)).isoformat()
        
        # Store the shared report
        shared_reports[share_id] = {
            "id": share_id,
            "title": f"{job.get('company', 'Market Research')} Report",
            "content": job["report"],
            "analysis_type": job_status[data.job_id].get("analysis_type", "Market Research"),
            "target_market": job_status[data.job_id].get("target_market", ""),
            "generated_at": job["last_update"],
            "expires_at": expiration_date,
            "is_public": True,
            "job_id": data.job_id
        }
        
        # Store in MongoDB if available
        if mongodb:
            try:
                mongodb.db.shared_reports.insert_one(shared_reports[share_id])
            except Exception as e:
                logger.warning(f"Failed to store shared report in MongoDB: {e}")
        
        return {
            "shareId": share_id,
            "shareUrl": f"/shared-report/{share_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating shared report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/shared-reports/{share_id}")
async def get_shared_report(share_id: str):
    """Get a shared report by ID"""
    try:
        # First check in-memory storage
        if share_id in shared_reports:
            report = shared_reports[share_id]
        elif mongodb:
            # Check MongoDB
            report = mongodb.db.shared_reports.find_one({"id": share_id})
            if not report:
                raise HTTPException(status_code=404, detail="Shared report not found")
        else:
            raise HTTPException(status_code=404, detail="Shared report not found")
        
        # Check if report has expired
        if report.get("expires_at"):
            expiration = datetime.fromisoformat(report["expires_at"])
            if datetime.now() > expiration:
                raise HTTPException(status_code=410, detail="Shared report has expired")
        
        # Check if report is public
        if not report.get("is_public", False):
            raise HTTPException(status_code=403, detail="This report is not publicly accessible")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shared report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/shared-reports/{share_id}")
async def delete_shared_report(share_id: str):
    """Delete a shared report"""
    try:
        # Remove from in-memory storage
        if share_id in shared_reports:
            del shared_reports[share_id]
        
        # Remove from MongoDB if available
        if mongodb:
            result = mongodb.db.shared_reports.delete_one({"id": share_id})
            if result.deleted_count == 0 and share_id not in shared_reports:
                raise HTTPException(status_code=404, detail="Shared report not found")
        elif share_id not in shared_reports:
            raise HTTPException(status_code=404, detail="Shared report not found")
        
        return {"message": "Shared report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting shared report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
