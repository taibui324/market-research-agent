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
from pydantic import BaseModel
from typing import Optional

from backend.company_single_research import Graph
from backend.nodes.orchestrator import ThreeCAnalysisOrchestrator
from backend.services.mongodb import MongoDBService
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
    title="Tavily Company Research API",
    description="API for conducting comprehensive company research and analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

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
        logger.warning(f"Failed to initialize MongoDB: {e}. Continuing without persistence.")


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
    """Request model for 3C market research analysis"""
    analysis_type: str = "3c_analysis"  # Type of analysis to perform
    target_market: str = "japanese_curry"  # Market focus for analysis
    market_segment: Optional[str] = None  # Specific market segment
    company: Optional[str] = None  # Optional company context
    company_url: Optional[str] = None  # Optional company URL
    industry: Optional[str] = None  # Optional industry context
    hq_location: Optional[str] = None  # Optional location context

class PDFGenerationRequest(BaseModel):
    report_content: str
    company_name: Optional[str] = None


class SharedReportRequest(BaseModel):
    job_id: str
    expiration_days: Optional[int] = 30

@app.options("/research")
async def preflight():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.options("/research/3c-analysis")
async def preflight_3c():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.post("/research")
async def research(data: ResearchRequest):
    try:
        logger.info(f"Received research request for {data.company}")
        job_id = str(uuid.uuid4())
        asyncio.create_task(process_research(job_id, data))

        response = JSONResponse(content={
            "status": "accepted",
            "job_id": job_id,
            "message": "Research started. Connect to WebSocket for updates.",
            "websocket_url": f"/research/ws/{job_id}",
            "analysis_type": "company_research"
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    except Exception as e:
        logger.error(f"Error initiating research: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/3c-analysis")
async def market_research(data: MarketResearchRequest):
    """Endpoint for 3C market research analysis"""
    try:
        logger.info(f"Received 3C analysis request for {data.target_market} market")
        job_id = str(uuid.uuid4())
        asyncio.create_task(process_3c_analysis(job_id, data))

        response = JSONResponse(content={
            "status": "accepted",
            "job_id": job_id,
            "message": "3C Analysis started. Connect to WebSocket for updates.",
            "websocket_url": f"/research/ws/{job_id}",
            "analysis_type": "3c_analysis",
            "target_market": data.target_market
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    except Exception as e:
        logger.error(f"Error initiating 3C analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_research(job_id: str, data: ResearchRequest):
    """Process research workflow for company analysis"""
    try:
        # Initialize MongoDB if available
        mongodb = None
        try:
            mongodb = MongoDBService()
        except Exception as e:
            logger.warning(f"MongoDB not available: {e}")

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

async def process_3c_analysis(job_id: str, data: MarketResearchRequest):
    """Process 3C market research analysis workflow"""
    try:
        # Initialize MongoDB if available
        mongodb = None
        try:
            mongodb = MongoDBService()
        except Exception as e:
            logger.warning(f"MongoDB not available: {e}")

        if mongodb:
            mongodb.create_job(job_id, data.dict())
        await asyncio.sleep(1)  # Allow WebSocket connection

        await manager.send_status_update(
            job_id, 
            status="processing", 
            message="Starting 3C Analysis workflow"
        )

        # Import MarketResearchState here to avoid circular imports
        from backend.classes.state import MarketResearchState
        
        # Initialize 3C analysis orchestrator
        orchestrator = ThreeCAnalysisOrchestrator(
            websocket_manager=manager,
            job_id=job_id
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
                    "target_market": data.target_market,
                    "analysis_summary": final_state.get('analysis_synthesis', {})
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

@app.get("/")
async def ping():
    return {"message": "Alive"}

@app.post("/company_analysis", tags=["company_analysis"])
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

@app.get("/job_status/{job_id}", tags=["job_status"])
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

@app.get("/job_result/{job_id}", tags=["job_result"])
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

@app.get("/company_analysis/pdf/{filename}", tags=["company_analysis"], summary="Get PDF Report", description="Download a generated PDF report by filename")
async def get_pdf(filename: str):
    """
    Download a PDF report by filename.
    
    Returns the PDF file if it exists in the system.
    """
    pdf_path = os.path.join("pdfs", filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type='application/pdf', filename=filename)

@app.websocket("/company_analysis/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time research progress updates.
    
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

@app.get("/company_analysis/{job_id}", tags=["company_analysis"], summary="Get Research Job Status", description="Retrieve the status and details of a research job")
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

@app.get("/company_analysis/{job_id}/report", tags=["company_analysis"], summary="Get Research Report", description="Retrieve the final research report for a completed job")
async def get_research_report(job_id: str):
    """
    Get the final research report for a completed job.
    
    Returns the comprehensive research report if the job has been completed.
    """
    # Initialize MongoDB if available
    mongodb = None
    try:
        mongodb = MongoDBService()
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}")
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

@app.post("/generate-pdf", tags=["company_analysis"], summary="Generate PDF Report", description="Generate a PDF from markdown content and stream it to the client")
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

@app.post("/shared-reports")
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

@app.get("/shared-reports/{share_id}")
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

@app.delete("/shared-reports/{share_id}")
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
