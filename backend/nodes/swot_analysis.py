import asyncio
import json
import logging
import os
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

        # Build prompt using only briefing data
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

4. Use the briefing data to identify key insights for each SWOT category.
5. Do not mention "no data available" or "no information found".
6. Use only bullet points, no paragraphs.
7. Provide only the SWOT analysis, no extra commentary.

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

        # Store the SWOT analysis in the correct format
        state["report_content"] = result["swot"]

        # Also store in swot_analyses for compatibility
        if "swot_analyses" not in state:
            state["swot_analyses"] = {}

        state["swot_analyses"] = result["swot"]

        return state
