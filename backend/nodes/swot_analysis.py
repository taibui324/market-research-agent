import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Union

from openai import AsyncOpenAI

from ..classes import ResearchState

logger = logging.getLogger(__name__)


class SwotAnalysis:
    """Generates a single SWOT analysis for a main company using both its own and competitors' data."""

    def __init__(self) -> None:
        self.max_doc_length = 8000
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=self.openai_key)
        self.model = "gpt-4.1-mini"

    def _normalize_docs(
        self, docs: Union[Dict[str, Any], List[Dict[str, Any]]], prefix: str = "doc"
    ) -> List[str]:
        """Convert docs into truncated text blocks"""
        items = (
            list(docs.items())
            if isinstance(docs, dict)
            else [(doc.get("url", f"{prefix}_{i}"), doc) for i, doc in enumerate(docs)]
        )
        sorted_items = sorted(
            items,
            key=lambda x: float(x[1].get("evaluation", {}).get("overall_score", "0")),
            reverse=True,
        )

        doc_texts, total_length = [], 0
        for doc_id, doc in sorted_items:
            title = doc.get("title", doc_id)
            content = doc.get("raw_content") or doc.get("content", "")
            if len(content) > self.max_doc_length:
                content = content[: self.max_doc_length] + "... [content truncated]"
            doc_entry = f"Source: {title}\n\nContent: {content}"
            if total_length + len(doc_entry) < 120000:
                doc_texts.append(doc_entry)
                total_length += len(doc_entry)
            else:
                break
        return doc_texts

    def _parse_swot_content(self, swot_text: str) -> Dict[str, Any]:
        """Parse SWOT text into structured data"""
        if not swot_text:
            return {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
                "summary": {
                    "total_points": 0,
                    "strengths_count": 0,
                    "weaknesses_count": 0,
                    "opportunities_count": 0,
                    "threats_count": 0
                }
            }

        # Split content by headers
        sections = re.split(r'### (Strengths|Weaknesses|Opportunities|Threats)', swot_text)

        structured_swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "summary": {
                "total_points": 0,
                "strengths_count": 0,
                "weaknesses_count": 0,
                "opportunities_count": 0,
                "threats_count": 0
            }
        }

        # Process each section
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_name = sections[i].lower()
                section_content = sections[i + 1].strip()

                # Extract bullet points
                bullet_points = []
                for line in section_content.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('• '):
                        # Extract the point and citation
                        point_text = line[2:].strip()
                        bullet_points.append({
                            "text": point_text,
                            "citation": self._extract_citation(point_text)
                        })

                structured_swot[section_name] = bullet_points
                structured_swot["summary"][f"{section_name}_count"] = len(bullet_points)

        # Calculate total points
        structured_swot["summary"]["total_points"] = sum([
            structured_swot["summary"]["strengths_count"],
            structured_swot["summary"]["weaknesses_count"],
            structured_swot["summary"]["opportunities_count"],
            structured_swot["summary"]["threats_count"]
        ])

        return structured_swot

    def _extract_citation(self, text: str) -> str:
        """Extract citation from text like '[Company Briefing]'"""
        citation_match = re.search(r'\[([^\]]+)\]', text)
        return citation_match.group(1) if citation_match else "Unknown"

    def _calculate_swot_metrics(self, structured_swot: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics for SWOT analysis"""
        metrics = {
            "balance_score": 0,
            "internal_focus": 0,
            "external_focus": 0,
            "positive_negative_ratio": 0,
            "insights_quality": "medium"
        }

        strengths_count = structured_swot["summary"]["strengths_count"]
        weaknesses_count = structured_swot["summary"]["weaknesses_count"]
        opportunities_count = structured_swot["summary"]["opportunities_count"]
        threats_count = structured_swot["summary"]["threats_count"]

        # Calculate balance score (how balanced the analysis is)
        internal_total = strengths_count + weaknesses_count
        external_total = opportunities_count + threats_count

        if internal_total > 0 and external_total > 0:
            metrics["balance_score"] = min(internal_total, external_total) / max(internal_total, external_total)

        # Calculate focus ratios
        if internal_total > 0:
            metrics["internal_focus"] = strengths_count / internal_total

        if external_total > 0:
            metrics["external_focus"] = opportunities_count / external_total

        # Calculate positive/negative ratio
        positive_total = strengths_count + opportunities_count
        negative_total = weaknesses_count + threats_count

        if negative_total > 0:
            metrics["positive_negative_ratio"] = positive_total / negative_total

        # Determine insights quality based on total points and balance
        total_points = structured_swot["summary"]["total_points"]
        if total_points >= 12 and metrics["balance_score"] >= 0.7:
            metrics["insights_quality"] = "high"
        elif total_points >= 8 and metrics["balance_score"] >= 0.5:
            metrics["insights_quality"] = "medium"
        else:
            metrics["insights_quality"] = "low"

        return metrics

    async def generate_swot(
        self,
        company: str,
        industry: str,
        hq_location: str,
        state: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate one SWOT using briefing data from state"""

        if websocket_manager := context.get("websocket_manager"):
            if job_id := context.get("job_id"):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="swot_start",
                    message=f"Generating SWOT analysis for {company} using briefing data",
                    result={
                        "step": "SWOT",
                        "company": company,
                    },
                )

        # Extract briefing data from state
        company_briefing = state.get("company_briefing", "")
        financial_briefing = state.get("financial_briefing", "")
        news_briefing = state.get("news_briefing", "")
        industry_briefing = state.get("industry_briefing", "")

        # Get all companies data (main company + competitors)
        companies_data = state.get("companies_data", {})
        
        # Get main company data
        main_company_data = companies_data.get(company, {})
        main_organized_content = (
            main_company_data.get("site_scrape", {})
            .get("organized_content")
        )
        
        # Get competitor data for context
        competitor_insights = []
        for company_name, company_data in companies_data.items():
            if company_name != company and company_data.get("is_competitor", False):
                competitor_content = (
                    company_data.get("site_scrape", {})
                    .get("organized_content", "")
                )
                if competitor_content:
                    competitor_insights.append(f"=== {company_name} Competitor Data ===\n{competitor_content}\n")

        # Build prompt using briefing data and competitor insights
        competitor_section = "\n".join(competitor_insights) if competitor_insights else ""
        logger.info(f"Competitor section: {competitor_section[:100]}")
        
        briefing_section = f"""
=== Company Overview ===
{company_briefing}

=== Financial Information ===
{financial_briefing}

=== Recent News & Developments ===
{news_briefing}

=== Industry Context ===
{industry_briefing}

=== Competitor Data ===
{competitor_section}
"""

        prompt = f"""
You are a business research analyst. 

Task:
Create a single SWOT Analysis for **{company}**, a {industry} company headquartered in {hq_location}.

Rules:
1. Use these exact headers:
### Strengths
### Weaknesses
### Opportunities
### Threats

2. Each bullet must be a single, complete fact.
3. Each bullet MUST include a citation in square brackets indicating the source.
   Example:
   - Strong brand presence [Company Briefing]
   - Recent product launch [News Briefing]
   - Market leadership position [Industry Briefing]
   - Competitive advantage over [Competitor Name] [Competitor Data]

4. Use the briefing data and competitor insights to identify key insights for each SWOT category.
5. Consider competitive positioning when analyzing strengths, weaknesses, opportunities, and threats.
6. Do not mention "no data available" or "no information found".
7. Use only bullet points, no paragraphs.
8. Provide only the SWOT analysis, no extra commentary.

Sources:

{briefing_section}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            if not content:
                logger.error(f"Empty response from LLM for {company}")
                return {"company": company, "swot": ""}

            if websocket_manager := context.get("websocket_manager"):
                if job_id := context.get("job_id"):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="swot_complete",
                        message=f"Completed SWOT analysis for {company}",
                        result={"step": "SWOT", "company": company},
                    )

            return {"company": company, "swot": content}
        except Exception as e:
            logger.error(f"Error generating SWOT for {company}: {e}")
            return {"company": company, "swot": ""}

    async def run(self, state: ResearchState) -> ResearchState:
        """Run combined SWOT for main company using briefing data"""

        company = state.get("company")
        state["previous_step"] = state.get("editor")
        prev_step = state.get("previous_step")

        # JSON dump the entire state for debugging
        with open("previous_step.json", "w") as f:
            json.dump(
                {
                    "state": state,
                    "company": company,
                    "industry": state.get("industry"),
                    "hq_location": state.get("hq_location"),
                    "state_keys": list(state.keys()),
                },
                f,
                indent=2,
                default=str,
            )

        result = await self.generate_swot(
            company,
            state.get("industry", "Unknown"),
            state.get("hq_location", "Unknown"),
            state,  # Pass the entire state instead of individual parameters
            {
                "websocket_manager": state.get("websocket_manager"),
                "job_id": state.get("job_id"),
            },
        )

        # Parse the SWOT content into structured data
        structured_swot = self._parse_swot_content(result["swot"])

        # Calculate metrics
        metrics = self._calculate_swot_metrics(structured_swot)

        # Create comprehensive SWOT analysis result
        swot_analysis_result = {
            "company": company,
            "raw_content": result["swot"],
            "structured_data": structured_swot,
            "metrics": metrics,
            "generated_at": state.get("timestamp", ""),
            "analysis_quality": {
                "total_insights": structured_swot["summary"]["total_points"],
                "balance_score": metrics["balance_score"],
                "quality_rating": metrics["insights_quality"],
                "internal_external_balance": {
                    "internal_focus": metrics["internal_focus"],
                    "external_focus": metrics["external_focus"]
                },
                "positive_negative_ratio": metrics["positive_negative_ratio"]
            }
        }

        # Store the comprehensive SWOT analysis
        state["swot_analysis"] = swot_analysis_result
        state["report_content"] = result["swot"]  # Keep raw content for backward compatibility

        # Store structured data for easy access
        state["swot_structured"] = structured_swot
        state["swot_metrics"] = metrics

        # Also store in swot_analyses for compatibility
        if "swot_analyses" not in state:
            state["swot_analyses"] = {}

        # state["swot_analyses"] = result["swot"]

        return state
