import asyncio
import logging
import os
from typing import Any, Dict, List, Union

from openai import AsyncOpenAI

from ..classes import ResearchState

logger = logging.getLogger(__name__)


class SwotAnalysis:
    """Generates SWOT analyses for multiple companies and updates ResearchState."""

    def __init__(self) -> None:
        self.max_doc_length = 8000
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=self.openai_key)
        self.model = "gpt-4.1-mini"

    async def generate_swot(
        self,
        docs: Union[Dict[str, Any], List[Dict[str, Any]]],
        company: str,
        industry: str,
        hq_location: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info(
            f"Generating SWOT analysis for {company} using {len(docs)} documents"
        )

        if websocket_manager := context.get("websocket_manager"):
            if job_id := context.get("job_id"):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="swot_start",
                    message=f"Generating SWOT analysis for {company}",
                    result={
                        "step": "SWOT",
                        "company": company,
                        "total_docs": len(docs),
                    },
                )

        # Normalize docs
        items = (
            list(docs.items())
            if isinstance(docs, dict)
            else [(doc.get("url", f"doc_{i}"), doc) for i, doc in enumerate(docs)]
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

        separator = "\n" + "-" * 40 + "\n"
        prompt = f"""
Create a structured SWOT Analysis for {company}, a {industry} company headquartered in {hq_location}.

Rules:
1. Use these exact headers:
### Strengths
### Weaknesses
### Opportunities
### Threats

2. Each bullet must be a single, complete fact.
3. Each bullet MUST include a citation in square brackets with the document title or URL, e.g.:
   - Strong brand presence [Doc: Annual Report 2024]
   - Expanding into Asia-Pacific [URL: example.com]

4. Do not mention "no data available" or "no information found".
5. Use only bullet points, no paragraphs.
6. Provide only the SWOT analysis, no extra commentary.

Analyze the following documents:

{separator}{separator.join(doc_texts)}{separator}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business research analyst. Always provide citations for each bullet point.",
                    },
                    {"role": "user", "content": prompt},
                ],
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
