import logging
from typing import Any, AsyncIterator, Dict, List

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph

from .classes.state import InputState, CompetitorData
from .nodes import GroundingNode
from .nodes.briefing import Briefing
from .nodes.collector import Collector
from .nodes.curator import Curator
from .nodes.editor import Editor
from .nodes.enricher import Enricher
from .nodes.competitor_analysis import CompetitorAnalysis  # New competitor analysis node
from .nodes.swot_analysis import SwotAnalysis  # New competitor analysis node
from .nodes.researchers import (
    CompanyAnalyzer,
    FinancialAnalyst,
    IndustryAnalyzer,
    NewsScanner,
)

logger = logging.getLogger(__name__)

class Graph:
    def __init__(self, company=None, company_url=None, industry=None, hq_location=None, 
                 product_category=None, competitors=None, websocket_manager=None, job_id=None):
        """
        Initialize the research workflow for a main company with competitors.
        
        Args:
            company: Main company name
            company_url: Main company URL
            industry: Industry
            hq_location: Main company HQ location
            product_category: Main company product category
            competitors: List of competitor data
            websocket_manager: WebSocket manager for real-time updates
            job_id: Job ID for tracking
        """
        self.websocket_manager = websocket_manager
        self.job_id = job_id

        # Initialize InputState with main company and competitors
        self.input_state = InputState(
            company=company,
            company_url=company_url,
            hq_location=hq_location,
            industry=industry,
            product_category=product_category,
            competitors=competitors or [],
            websocket_manager=websocket_manager,
            job_id=job_id,
            messages=[
                SystemMessage(content=f"Expert researcher starting investigation for {company} and {len(competitors or [])} competitors")
            ]
        )

        # Initialize nodes with WebSocket manager and job ID
        self._init_nodes()
        self._build_workflow()

    def _init_nodes(self):
        """Initialize all workflow nodes"""
        self.ground = GroundingNode(search_provider="perplexity")
        self.financial_analyst = FinancialAnalyst()
        self.news_scanner = NewsScanner()
        self.industry_analyst = IndustryAnalyzer()
        self.company_analyst = CompanyAnalyzer()
        self.collector = Collector()
        self.curator = Curator()
        self.enricher = Enricher()
        self.briefing = Briefing()
        self.swot = SwotAnalysis()  # SWOT analysis node
        self.competitor_analysis = CompetitorAnalysis()  # Competitor analysis node
        self.editor = Editor()

    def _build_workflow(self):
        """Configure the state graph workflow"""
        self.workflow = StateGraph(InputState)

        # Add nodes with their respective processing functions
        self.workflow.add_node("grounding", self.ground.run)
        self.workflow.add_node("financial_analyst", self.financial_analyst.run)
        self.workflow.add_node("news_scanner", self.news_scanner.run)
        self.workflow.add_node("industry_analyst", self.industry_analyst.run)
        self.workflow.add_node("company_analyst", self.company_analyst.run)
        self.workflow.add_node("collector", self.collector.run)
        self.workflow.add_node("curator", self.curator.run)
        self.workflow.add_node("enricher", self.enricher.run)
        self.workflow.add_node("briefing", self.briefing.run)
        self.workflow.add_node("editor", self.editor.run)
        self.workflow.add_node("swot", self.swot.run)  # SWOT analysis node
        self.workflow.add_node("competitor_analysis", self.competitor_analysis.run)  # Competitor analysis node

        # Configure workflow edges
        self.workflow.set_entry_point("grounding")
        # Set finish point for final report
        self.workflow.set_finish_point("competitor_analysis")  # Competitor analysis as final report

        research_nodes = [
            "financial_analyst", 
            "news_scanner",
            "industry_analyst", 
            "company_analyst"
        ]

        # Connect grounding to all research nodes
        for node in research_nodes:
            self.workflow.add_edge("grounding", node)
            self.workflow.add_edge(node, "collector")

        # # Connect remaining nodes
        self.workflow.add_edge("collector", "curator")
        self.workflow.add_edge("curator", "enricher")
        self.workflow.add_edge("enricher", "briefing")
        self.workflow.add_edge("briefing", "editor")    # Connect briefing to editor

        # Run both analyses in parallel after editor
        self.workflow.add_edge("editor", "swot")  # Connect editor to SWOT
        self.workflow.add_edge(
            "swot", "competitor_analysis"
        )  # Connect editor to competitor analysis

    async def run(self, thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the research workflow"""
        compiled_graph = self.workflow.compile()

        async for state in compiled_graph.astream(
            self.input_state,
            thread
        ):
            if self.websocket_manager and self.job_id:
                await self._handle_ws_update(state)
            yield state

    async def _handle_ws_update(self, state: Dict[str, Any]):
        """Handle WebSocket updates based on state changes"""
        update = {
            "type": "state_update",
            "data": {
                "current_node": state.get("current_node", "unknown"),
                "progress": state.get("progress", 0),
                "keys": list(state.keys())
            }
        }
        await self.websocket_manager.broadcast_to_job(
            self.job_id,
            update
        )

    def compile(self):
        graph = self.workflow.compile()
        return graph
