import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Union

from openai import AsyncOpenAI

from ..classes import ResearchState
from backend.services.mongodb import MongoDBService
import datetime

logger = logging.getLogger(__name__)


class CompetitorAnalysis:
    """Generates competitor product direction and technology leverage analysis."""

    def __init__(self) -> None:
        self.max_doc_length = 8000
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=self.openai_key)
        self.model = "gpt-4o-mini"

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

    def _parse_competitor_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse competitor analysis text into structured data"""
        if not analysis_text:
            return {
                "product_directions": [],
                "technology_leverage": [],
                "positioning_insights": [],
                "competitive_matrix": {},
                "summary": {
                    "total_insights": 0,
                    "product_directions_count": 0,
                    "technology_leverage_count": 0,
                    "positioning_insights_count": 0
                }
            }

        # Split content by headers
        sections = re.split(r'### (Product Directions|Technology Leverage|Positioning Insights|Competitive Matrix)', analysis_text)

        structured_analysis = {
            "product_directions": [],
            "technology_leverage": [],
            "positioning_insights": [],
            "competitive_matrix": {},
            "summary": {
                "total_insights": 0,
                "product_directions_count": 0,
                "technology_leverage_count": 0,
                "positioning_insights_count": 0
            }
        }

        # Process each section
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_name = sections[i].lower().replace(" ", "_")
                section_content = sections[i + 1].strip()

                if section_name == "competitive_matrix":
                    # Parse competitive matrix as structured data
                    structured_analysis["competitive_matrix"] = self._parse_competitive_matrix(section_content)
                else:
                    # Extract bullet points for other sections
                    bullet_points = []
                    for line in section_content.split('\n'):
                        line = line.strip()
                        if line.startswith('- ') or line.startswith('• '):
                            point_text = line[2:].strip()
                            bullet_points.append({
                                "text": point_text,
                                "citation": self._extract_citation(point_text)
                            })

                    structured_analysis[section_name] = bullet_points
                    structured_analysis["summary"][f"{section_name}_count"] = len(bullet_points)

        # Calculate total insights
        structured_analysis["summary"]["total_insights"] = sum([
            structured_analysis["summary"]["product_directions_count"],
            structured_analysis["summary"]["technology_leverage_count"],
            structured_analysis["summary"]["positioning_insights_count"]
        ])

        return structured_analysis

    def _parse_competitive_matrix(self, matrix_content: str) -> Dict[str, Any]:
        """Parse competitive matrix section into structured data"""
        matrix = {
            "companies": [],
            "comparison_criteria": [],
            "scores": {},
            "insights": []
        }

        # Extract company names and criteria from the matrix
        lines = matrix_content.split('\n')
        for line in lines:
            line = line.strip()
            if '|' in line and not line.startswith('|'):
                # This is likely a data row
                parts = [part.strip() for part in line.split('|') if part.strip()]
                if len(parts) >= 2:
                    company = parts[0]
                    if company not in matrix["companies"]:
                        matrix["companies"].append(company)

                    # Extract scores for this company
                    for i, part in enumerate(parts[1:], 1):
                        if part and not part.startswith('-'):
                            matrix["scores"][f"{company}_{i}"] = part

        return matrix

    def _extract_citation(self, text: str) -> str:
        """Extract citation from text like '[Company Briefing]'"""
        citation_match = re.search(r'\[([^\]]+)\]', text)
        return citation_match.group(1) if citation_match else "Unknown"

    def _calculate_analysis_metrics(self, structured_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics for competitor analysis"""
        metrics = {
            "analysis_depth": "medium",
            "technology_focus": 0,
            "product_focus": 0,
            "competitive_insights_quality": "medium"
        }

        product_count = structured_analysis["summary"]["product_directions_count"]
        tech_count = structured_analysis["summary"]["technology_leverage_count"]
        positioning_count = structured_analysis["summary"]["positioning_insights_count"]
        total_insights = structured_analysis["summary"]["total_insights"]

        # Calculate focus ratios
        if total_insights > 0:
            metrics["technology_focus"] = tech_count / total_insights
            metrics["product_focus"] = product_count / total_insights

        # Determine analysis depth
        if total_insights >= 15 and positioning_count >= 5:
            metrics["analysis_depth"] = "high"
        elif total_insights >= 8 and positioning_count >= 3:
            metrics["analysis_depth"] = "medium"
        else:
            metrics["analysis_depth"] = "low"

        # Determine competitive insights quality
        if total_insights >= 12 and metrics["technology_focus"] > 0.3 and metrics["product_focus"] > 0.3:
            metrics["competitive_insights_quality"] = "high"
        elif total_insights >= 6:
            metrics["competitive_insights_quality"] = "medium"
        else:
            metrics["competitive_insights_quality"] = "low"

        return metrics

    async def generate_competitor_analysis(
        self,
        company: str,
        industry: str,
        hq_location: str,
        state: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate competitor analysis using briefing data from state"""

        if websocket_manager := context.get("websocket_manager"):
            if job_id := context.get("job_id"):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="competitor_analysis_start",
                    message=f"Generating competitor analysis for {company}",
                    result={
                        "step": "Competitor Analysis",
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

        # Get competitor data for analysis
        competitor_insights = []
        competitor_companies = []

        for company_name, company_data in companies_data.items():
            if company_name != company and company_data.get("is_competitor", False):
                competitor_content = (
                    company_data.get("site_scrape", {})
                    .get("organized_content", "")
                )
                if competitor_content:
                    competitor_insights.append(f"=== {company_name} Competitor Data ===\n{competitor_content}\n")
                    competitor_companies.append(company_name)

        # Build prompt using only competitor insights (no main company data)
        competitor_section = "\n".join(competitor_insights) if competitor_insights else ""
        competitor_list = ", ".join(competitor_companies) if competitor_companies else "No competitors identified"

        # If no competitors, create a simplified analysis
        if not competitor_companies:
            return await self._generate_no_competitors_analysis(company, industry, hq_location, state, context)

        # If no competitors, return early with a simple message
        if not competitor_companies:
            logger.info(f"No competitors found for {company}, skipping competitor analysis")
            return {
                "company": company, 
                "competitor_analysis": "### No Competitors Identified\n\nNo competitor data was available for analysis. This may be due to:\n- No competitors specified in the input\n- Competitor data not found during research\n- All competitors filtered out during processing"
            }

        prompt = f"""
You are a competitive intelligence analyst specializing in product strategy and technology assessment.

Task:
Create a comprehensive competitor analysis focusing on the competitors of **{company}**, a {industry} company headquartered in {hq_location}.

Information about the main company:
{company_briefing}

Financial information about the main company:
{financial_briefing}

Recent news and developments about the main company:
{news_briefing}

Industry context:
{industry_briefing}

### Competitors to Analyze
Competitors to analyze: {competitor_list}

Rules:
1. Use these exact headers:
### Product Directions
### Technology Leverage
### Positioning Insights
### Competitive Matrix

2. Each bullet must be a single, complete insight.
3. Each bullet MUST include a citation in square brackets indicating the source.
   Example:
   - Investing heavily in AI/ML capabilities [Competitor Data]
   - Launched new mobile app platform [Competitor Data]
   - Strong market position in enterprise segment [Competitor Data]
   - Advanced cloud infrastructure [Competitor Data]

4. Focus on:
   - **Product Directions**: What products/services competitors are developing, launching, or planning
   - **Technology Leverage**: What technologies competitors are using (AI, cloud, mobile, etc.)
   - **Positioning Insights**: How competitors position themselves in the market
   - **Competitive Matrix**: Create a comparison table of key factors between competitors

5. Use ONLY the competitor data to identify strategic insights.
6. Do not include any information about the main company ({company}). besides one in the bullet point of ### Competitive Matrix. 
7. Do not mention "no data available" or "no information found".
8. Use only bullet points, no paragraphs.
9. Provide only the competitor analysis, no extra commentary.

Sources:

=== Competitor Data ===
{competitor_section}
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
                return {"competitor_analysis": ""}

            if websocket_manager := context.get("websocket_manager"):
                if job_id := context.get("job_id"):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="competitor_analysis_complete",
                        message=f"Completed competitor analysis for {company}",
                        result={"step": "Competitor Analysis", "company": company},
                    )

            return {"competitor_analysis": content}
        except Exception as e:
            logger.error(f"Error generating competitor analysis for {company}: {e}")
            return {"competitor_analysis": ""}

    async def _generate_no_competitors_analysis(
        self,
        company: str,
        industry: str,
        hq_location: str,
        state: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a simplified competitor analysis when no competitors are provided"""

        if websocket_manager := context.get("websocket_manager"):
            if job_id := context.get("job_id"):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="competitor_analysis_start",
                    message=f"Generating market positioning analysis for {company} (no competitors provided)",
                    result={
                        "step": "Competitor Analysis",
                        "company": company,
                    },
                )

        # Extract briefing data from state
        company_briefing = state.get("company_briefing", "")
        financial_briefing = state.get("financial_briefing", "")
        news_briefing = state.get("news_briefing", "")
        industry_briefing = state.get("industry_briefing", "")

        briefing_section = f"""
=== Company Overview ===
{company_briefing}

=== Financial Information ===
{financial_briefing}

=== Recent News & Developments ===
{news_briefing}

=== Industry Context ===
{industry_briefing}
"""

        prompt = f"""
You are a market intelligence analyst specializing in competitive positioning.

Task:
Create a market positioning analysis for **{company}**, a {industry} company headquartered in {hq_location}.

Note: No specific competitors were provided, so focus on general market positioning and industry landscape.

Rules:
1. Use these exact headers:
### Product Directions
### Technology Leverage
### Positioning Insights
### Competitive Matrix

2. Each bullet must be a single, complete insight.
3. Each bullet MUST include a citation in square brackets indicating the source.
4. Focus on:
   - **Product Directions**: What products/services the company is developing or planning
   - **Technology Leverage**: What technologies the company is using or investing in
   - **Positioning Insights**: How the company positions itself in the market
   - **Competitive Matrix**: Create a general market positioning analysis

5. Use the briefing data to identify strategic insights.
6. Do not mention "no competitors provided" - focus on the company's own positioning.
7. Use only bullet points, no paragraphs.
8. Provide only the analysis, no extra commentary.

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
                return {"competitor_analysis": ""}

            if websocket_manager := context.get("websocket_manager"):
                if job_id := context.get("job_id"):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="competitor_analysis_complete",
                        message=f"Completed market positioning analysis for {company}",
                        result={"step": "Competitor Analysis", "company": company},
                    )

            return {"competitor_analysis": content}
        except Exception as e:
            logger.error(f"Error generating market positioning analysis for {company}: {e}")
            return {"competitor_analysis": ""}

    async def run(self, state: ResearchState) -> ResearchState:
        """Run competitor analysis for competitors using briefing data"""

        # Get competitors from state, not the main company
        competitors = state.get("competitors", [])
        state["competitor_analysis_previous_step"] = state.get("editor")
        prev_step = state.get("competitor_analysis_previous_step")
        main_company = state.get("company")

        # Analyze all competitors at once
        competitor_analyses = {}

        # Get industry and location from state
        industry = state.get("industry", "Unknown")
        hq_location = state.get("hq_location", "Unknown")

        result = await self.generate_competitor_analysis(
            main_company,  # the main company vs its competitors
            industry,
            hq_location,
            state,
            {
                "websocket_manager": state.get("websocket_manager"),
                "job_id": state.get("job_id"),
            },
        )

        # Parse the competitor analysis content into structured data
        structured_analysis = self._parse_competitor_analysis(result["competitor_analysis"])

        # Calculate metrics
        metrics = self._calculate_analysis_metrics(structured_analysis)

        competitors_names = " ".join(
            [competitor["company"] for competitor in competitors]
        )

        # Store analysis for the main company vs all competitors
        competitor_analyses[main_company] = {
            "company": main_company,
            "competitor": competitors_names,
            "raw_content": result["competitor_analysis"],
            "structured_data": structured_analysis,
            "metrics": metrics,
            "generated_at": state.get("timestamp", ""),
            "analysis_quality": {
                "total_insights": structured_analysis["summary"]["total_insights"],
                "analysis_depth": metrics["analysis_depth"],
                "quality_rating": metrics["competitive_insights_quality"],
                "focus_ratios": {
                    "technology_focus": metrics["technology_focus"],
                    "product_focus": metrics["product_focus"],
                },
            },
        }

        # Store all competitor analyses
        state["competitor_analyses"] = competitor_analyses
        state["competitor_analysis_structured"] = competitor_analyses
        state["competitor_analysis_metrics"] = competitor_analyses

        # JSON dump the entire state for debugging
        with open("competitor_analysis_logs.json", "w") as f:
            json.dump(
                {
                    "state": state,
                    "competitors": competitors,
                    "industry": state.get("industry"),
                    "hq_location": state.get("hq_location"),
                    "state_keys": list(state.keys()),
                },
                f,
                indent=2,
                default=str,
            )

        ## save to the db with the name competitor_analysis
        mongodb = MongoDBService()
        if mongodb:
            mongodb.store_report(
                job_id=state["job_id"],
                report_competitor_analyses=state["competitor_analyses"],
                report_main_company=state["company"],
                report_competitors=state["competitors"],
                report_industry=state["industry"],
                report_hq_location=state["hq_location"],
                report_product_category=state.get("product_category"),
                report_type="competitor_analysis",
                report_created_at= datetime.datetime.utcnow(),
                report_content=state["report"],
            )

        return state
