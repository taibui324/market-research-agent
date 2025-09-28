import os
import re
import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

from langchain_core.messages import AIMessage
from langchain_perplexity import ChatPerplexity

from ...classes import ResearchState
from .base import BaseResearcher

logger = logging.getLogger(__name__)

class CompanyAnalyzer(BaseResearcher):
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "company_analyzer"
        
        # Initialize Perplexity client
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.perplexity_api_key:
            raise ValueError("Missing PERPLEXITY_API_KEY environment variable")
        
        self.perplexity_llm = ChatPerplexity(
            model="sonar",
            api_key=self.perplexity_api_key,
            temperature=0.1,
            max_tokens=2000,
        )

    async def perplexity_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search using Perplexity via LangChain integration"""
        docs = {}
        
        try:
            # Build user message with more specific instructions
            user_prompt = f"""Search and provide comprehensive information about: {query}

Please include:
- Relevant URLs and sources
- Brief descriptions of key findings
- Recent and authoritative information
- Focus on business, products, and market information

Format your response with clear URLs and descriptions."""

            # Call Perplexity LLM
            resp = await self.perplexity_llm.ainvoke(user_prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)

            logger.info(f"Perplexity response length: {len(content)}")

            # Extract URLs with better regex
            url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
            urls = re.findall(url_pattern, content)

            # Remove duplicates while preserving order
            seen_urls = set()
            unique_urls = []
            for url in urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(url)

            logger.info(f"Found {len(unique_urls)} URLs in Perplexity response")

            # Create search result items
            for i, url in enumerate(unique_urls[:max_results]):
                # Try to extract title from content around the URL
                title_match = re.search(
                    rf'([^.\n]{{10,100}})\.?\s*{re.escape(url)}',
                    content,
                    re.IGNORECASE,
                )
                title = title_match.group(1).strip() if title_match else f"Result {i+1}"

                # Extract snippet from content around the URL
                snippet_start = max(0, content.find(url) - 100)
                snippet_end = min(len(content), content.find(url) + 200)
                snippet = content[snippet_start:snippet_end].strip()

                docs[url] = {
                    "title": title,
                    "content": snippet,
                    "query": query,
                    "url": url,
                    "source": "perplexity_search",
                    "score": 1.0  # Perplexity doesn't provide scores, so we use 1.0
                }

        except Exception as e:
            logger.error(f"Perplexity search error: {e}")

        return docs

    async def search_documents_perplexity(self, state: ResearchState, queries: List[str]) -> Dict[str, Any]:
        """
        Execute all Perplexity searches in parallel
        """
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')

        if not queries:
            logger.error("No valid queries to search")
            return {}

        # Send status update for generated queries
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="queries_generated",
                message=f"Generated {len(queries)} queries for {self.analyst_type}",
                result={
                    "step": "Searching",
                    "analyst": self.analyst_type,
                    "queries": queries,
                    "total_queries": len(queries)
                }
            )

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="search_started",
                message=f"Using Perplexity to search for {len(queries)} queries",
                result={
                    "step": "Searching",
                    "total_queries": len(queries)
                }
            )

        # Execute all Perplexity searches in parallel
        import asyncio
        search_tasks = [
            self.perplexity_search(query, max_results=5)
            for query in queries
        ]

        try:
            results = await asyncio.gather(*search_tasks)
        except Exception as e:
            logger.error(f"Error during parallel Perplexity search execution: {e}")
            return {}

        # Process results
        merged_docs = {}
        for query, result in zip(queries, results):
            for url, doc in result.items():
                doc['query'] = query  # Associate each document with its query
                merged_docs[url] = doc

        # Send completion status
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="search_complete",
                message=f"Perplexity search completed with {len(merged_docs)} documents found",
                result={
                    "step": "Searching",
                    "total_documents": len(merged_docs),
                    "queries_processed": len(queries)
                }
            )

        return merged_docs

    async def analyze(self, state: ResearchState) -> Dict[str, Any]:
        company = state.get('company', 'Unknown Company')
        msg = [f"🏢 Company Analyzer analyzing {company}"]

        # Generate search queries using LLM
        queries = await self.generate_queries(
            state,
            """
        # Research Prompt: Company Fundamentals

            Generate structured research queries to gather key fundamentals about **{company}** operating in the **{industry}** industry.  

            ## Focus Areas

            ### 1. Core Products & Services  
            - What the company sells  
            - Flagship offerings  
            - Unique value propositions  

            ### 2. Company History & Milestones  
            - Founding story  
            - Major expansions  
            - Acquisitions  
            - Key achievements  

            ### 3. Leadership Team  
            - Executive profiles  
            - Board members  
            - Notable leadership changes  

            ### 4. Business Model & Strategy  
            - Revenue model  
            - Customer segments  
            - Market approach  
            - Growth strategies  

        """,
        )

        # Add message to show subqueries with emojis
        subqueries_msg = "🔍 Subqueries for company analysis:\n" + "\n".join([f"• {query}" for query in queries])
        messages = state.get('messages', [])
        messages.append(AIMessage(content=subqueries_msg))
        state['messages'] = messages

        # Send queries through WebSocket
        if websocket_manager := state.get('websocket_manager'):
            if job_id := state.get('job_id'):
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Company analysis queries generated",
                    result={
                        "step": "Company Analyst",
                        "analyst_type": "Company Analyst",
                        "queries": queries
                    }
                )

        company_data = {}

        # If we have site_scrape data, include it first
        if site_scrape := state.get('site_scrape'):
            msg.append("\n📊 Including site scrape data in company analysis...")
            company_url = state.get('company_url', 'company-website')
            company_data[company_url] = {
                'title': state.get('company', 'Unknown Company'),
                'raw_content': site_scrape,
                'query': f'Company overview and information about {company}'  # Add a default query for site scrape
            }

        # Perform additional research with Perplexity search
        try:
            # Use Perplexity search instead of Tavily
            documents = await self.search_documents_perplexity(state, queries)
            if documents:  # Only process if we got results
                for url, doc in documents.items():
                    company_data[url] = doc

            msg.append(f"\n✓ Found {len(company_data)} documents")
            if websocket_manager := state.get('websocket_manager'):
                if job_id := state.get('job_id'):
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Used Perplexity Search to find {len(company_data)} documents",
                        result={
                            "step": "Searching",
                            "analyst_type": "Company Analyst",
                            "queries": queries
                        }
                    )
        except Exception as e:
            msg.append(f"\n⚠️ Error during research: {str(e)}")

        # Update state with our findings
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        state['messages'] = messages
        state['company_data'] = company_data

        return {
            'message': msg,
            'company_data': company_data
        }

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        return await self.analyze(state) 
