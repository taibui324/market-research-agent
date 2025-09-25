import asyncio
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

from backend.graph import Graph
from backend.nodes.orchestrator import ThreeCAnalysisOrchestrator
from backend.services.mongodb import MongoDBService
from backend.services.pdf_service import PDFService
from backend.services.websocket_manager import WebSocketManager

# Load environment variables from .env file at startup
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

app = FastAPI(title="Tavily Company Research API")

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
    "result": None,
    "error": None,
    "debug_info": [],
    "company": None,
    "report": None,
    "last_update": datetime.now().isoformat()
})

mongodb = None
if mongo_uri := os.getenv("MONGODB_URI"):
    try:
        mongodb = MongoDBService(mongo_uri)
        logger.info("MongoDB integration enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize MongoDB: {e}. Continuing without persistence.")

class ResearchRequest(BaseModel):
    company: str
    company_url: Optional[str] = None
    industry: Optional[str] = None
    hq_location: Optional[str] = None

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

@app.options("/research")
async def preflight():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
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
    try:
        if mongodb:
            mongodb.create_job(job_id, data.dict())
        await asyncio.sleep(1)  # Allow WebSocket connection

        await manager.send_status_update(job_id, status="processing", message="Starting research")

        graph = Graph(
            company=data.company,
            url=data.company_url,
            industry=data.industry,
            hq_location=data.hq_location,
            websocket_manager=manager,
            job_id=job_id
        )

        state = {}
        async for s in graph.run(thread={}):
            state.update(s)
        
        # Look for the compiled report in either location.
        report_content = state.get('report') or (state.get('editor') or {}).get('report')
        if report_content:
            logger.info(f"Found report in final state (length: {len(report_content)})")
            job_status[job_id].update({
                "status": "completed",
                "report": report_content,
                "company": data.company,
                "last_update": datetime.now().isoformat()
            })
            if mongodb:
                mongodb.update_job(job_id=job_id, status="completed")
                mongodb.store_report(job_id=job_id, report_data={"report": report_content})
            await manager.send_status_update(
                job_id=job_id,
                status="completed",
                message="Research completed successfully",
                result={
                    "report": report_content,
                    "company": data.company
                }
            )
        else:
            logger.error(f"Research completed without finding report. State keys: {list(state.keys())}")
            logger.error(f"Editor state: {state.get('editor', {})}")
            
            # Check if there was a specific error in the state
            error_message = "No report found"
            if error := state.get('error'):
                error_message = f"Error: {error}"
            
            await manager.send_status_update(
                job_id=job_id,
                status="failed",
                message="Research completed but no report was generated",
                error=error_message
            )

    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        await manager.send_status_update(
            job_id=job_id,
            status="failed",
            message=f"Research failed: {str(e)}",
            error=str(e)
        )
        if mongodb:
            mongodb.update_job(job_id=job_id, status="failed", error=str(e))

async def process_3c_analysis(job_id: str, data: MarketResearchRequest):
    """Process 3C market research analysis workflow"""
    try:
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

@app.get("/research/pdf/{filename}")
async def get_pdf(filename: str):
    pdf_path = os.path.join("pdfs", filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type='application/pdf', filename=filename)

@app.websocket("/research/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
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

@app.get("/research/{job_id}")
async def get_research(job_id: str):
    if not mongodb:
        raise HTTPException(status_code=501, detail="Database persistence not configured")
    job = mongodb.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job

@app.get("/research/{job_id}/report")
async def get_research_report(job_id: str):
    if not mongodb:
        if job_id in job_status:
            result = job_status[job_id]
            if report := result.get("report"):
                return {"report": report}
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = mongodb.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found")
    return report

@app.post("/generate-pdf")
async def generate_pdf(data: PDFGenerationRequest):
    """Generate a PDF from markdown content and stream it to the client."""
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)