import logging
import os
import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from langchain_core.messages import AIMessage
from googleapiclient.discovery import build
import aiohttp
from bs4 import BeautifulSoup
from ..classes import InputState, ResearchState

logger = logging.getLogger(__name__)

# Default user agent for web scraping
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
)


class GroundingNode:
    """Gathers initial grounding data about the main company and its competitors using Google CSE."""

    def __init__(self) -> None:
        # Get Google API credentials
        self.google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_KEY")
        self.google_cx = (
            os.getenv("GOOGLE_CX") or os.getenv("CSX_ENGINE") or os.getenv("CSE_ID")
        )

        if not self.google_api_key or not self.google_cx:
            raise ValueError(
                "Missing GOOGLE_API_KEY and GOOGLE_CX environment variables"
            )

        # Initialize Google Custom Search service
        self.search_service = build(
            "customsearch", "v1", developerKey=self.google_api_key
        )

    def normalize_ws(self, s: str) -> str:
        """Normalize whitespace in text"""
        return re.sub(r"\s+", " ", s or "").strip()

    def generate_structured_queries(self, company: str, company_url: str = None) -> Tuple[List[str], Dict[str, str]]:
        """Generate structured queries for comprehensive company analysis"""
        queries = []
        query_to_area = {}  # Map query to analysis area
        
        # Base company name for queries
        company_quoted = f'"{company}"'
        
        # Remove site-specific constraint to allow broader web searches
        # This enables finding information from news, reports, analyst coverage, etc.
        
        # Define analysis areas
        analysis_areas = [
            {
                "topic": "product_offerings",
                "display_name": "Product Offerings",
                "keywords": ["products", "services", "offerings", "solutions", "portfolio", "catalog"]
            },
            {
                "topic": "product_direction", 
                "display_name": "Product Direction",
                "keywords": ["product roadmap", "future products", "innovation", "R&D", "development", "strategy"]
            },
            {
                "topic": "strategic_direction",
                "display_name": "Strategic Direction", 
                "keywords": ["strategy", "strategic plan", "business strategy", "vision", "mission", "goals"]
            },
            {
                "topic": "strengths",
                "display_name": "Strengths",
                "keywords": ["strengths", "advantages", "competitive advantages", "core competencies", "capabilities"]
            },
            {
                "topic": "weaknesses", 
                "display_name": "Weaknesses",
                "keywords": ["weaknesses", "challenges", "limitations", "risks", "vulnerabilities"]
            },
            {
                "topic": "market_position",
                "display_name": "Market Position",
                "keywords": ["market position", "market share", "competitive position", "industry leadership", "market analysis"]
            }
        ]
        
        # Generate queries for each analysis area
        for area in analysis_areas:
            topic = area["topic"]
            display_name = area["display_name"]
            keywords = area["keywords"]
            
            # Create a comprehensive query for this area
            query_parts = [company_quoted]
            query_parts.extend(keywords)
            
            query = f"{' '.join(query_parts)}"
            queries.append(query)
            query_to_area[query] = topic
            
            # Add a more specific query for each area
            specific_query = f"{company_quoted} {topic.replace('_', ' ')} {' '.join(keywords[:2])}"
            queries.append(specific_query)
            query_to_area[specific_query] = topic
        
        return queries, query_to_area

    def google_cse_search(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using Google Custom Search Engine"""
        items: List[Dict[str, Any]] = []
        start = 1

        while len(items) < max_results:
            num = min(10, max_results - len(items))
            try:
                res = (
                    self.search_service.cse()
                    .list(q=query, cx=self.google_cx, num=num, start=start)
                    .execute()
                )

                page_items = res.get("items", [])
                if not page_items:
                    break

                items.extend(page_items)
                start += len(page_items)

                if len(page_items) < num:
                    break

            except Exception as e:
                logger.error(f"Google CSE search error: {e}")
                break

        return items

    async def fetch_html(
        self, session: aiohttp.ClientSession, url: str
    ) -> Tuple[str, Optional[str]]:
        """Fetch HTML content from a URL"""
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
                html = await resp.text(errors="ignore")
                return url, html
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return url, None

    def parse_page(self, url: str, html: Optional[str]) -> Dict[str, Any]:
        """Parse HTML content and extract relevant information"""
        if not html:
            return {
                "url": url,
                "title": None,
                "content": None,
                "domain": urlparse(url).netloc,
            }

        soup = BeautifulSoup(html, "lxml")
        title = self.normalize_ws(soup.title.get_text()) if soup.title else None

        # Remove script and style elements
        for bad in soup(["script", "style", "noscript"]):
            bad.decompose()

        # Extract main content
        content = self.normalize_ws(soup.get_text(" ", strip=True))

        # Limit content size to avoid memory issues
        if len(content) > 100000:
            content = content[:100000] + "... [truncated]"

        return {
            "url": url,
            "title": title,
            "content": content,
            "domain": urlparse(url).netloc,
        }

    async def search_and_scrape_company(
        self,
        company: str,
        company_url: str,
        company_type: str,
        websocket_manager=None,
        job_id=None,
    ) -> dict:
        """Search for and scrape company information using structured Google CSE queries"""
        site_scrape = {}
        msg = f"🔍 Analyzing {company_type} website: {company}"
        logger.info(f"Starting structured Google CSE analysis for {company}")

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message=f"Searching for {company} information",
                result={
                    "step": "Site Scrape",
                    "company": company,
                    "type": company_type,
                },
            )

        try:
            # Generate structured queries with area mapping
            queries, query_to_area = self.generate_structured_queries(company, company_url)
            logger.info(f"Generated {len(queries)} structured queries for {company}")

            # Search for relevant pages using all queries
            all_search_results = []
            query_results = {}  # Track results by query
            
            for i, query in enumerate(queries):
                logger.info(f"Query {i+1}/{len(queries)}: {query}")
                search_results = self.google_cse_search(query, max_results=3)
                all_search_results.extend(search_results)
                query_results[query] = search_results
                
                # Small delay between queries to avoid rate limiting
                await asyncio.sleep(0.5)

            if not all_search_results:
                logger.warning(f"No search results found for {company}")
                msg += "\n⚠️ No search results found"
                return site_scrape, msg

            # Remove duplicate URLs
            seen_urls = set()
            unique_results = []
            for result in all_search_results:
                url = result.get("link")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            # Extract URLs to scrape (limit to top 8 to avoid overwhelming)
            urls_to_scrape = [result.get("link") for result in unique_results[:8] if result.get("link")]

            if not urls_to_scrape:
                logger.warning(f"No valid URLs found for {company}")
                msg += "\n⚠️ No valid URLs found"
                return site_scrape, msg

            logger.info(f"Found {len(urls_to_scrape)} unique URLs to scrape for {company}")

            # Scrape the URLs
            connector = aiohttp.TCPConnector(limit_per_host=3)
            headers = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept-Language": "en-US,en;q=0.8",
            }

            scraped_content = []
            async with aiohttp.ClientSession(
                headers=headers, connector=connector
            ) as session:
                for url in urls_to_scrape:
                    try:
                        url, html = await self.fetch_html(session, url)
                        parsed = self.parse_page(url, html)

                        if parsed["content"]:
                            scraped_content.append(
                                {
                                    "url": url,
                                    "title": parsed["title"],
                                    "content": parsed["content"],
                                }
                            )

                        # Small delay between requests
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
                        continue

            if scraped_content:
                # Organize content by analysis areas
                organized_content = self.organize_content_by_areas(
                    scraped_content, query_to_area, queries
                )

                site_scrape = {
                    "title": company,
                    "raw_content": "\n".join([item["content"] for item in scraped_content]),
                    "organized_content": organized_content,
                }

                logger.info(
                    f"Successfully scraped {len(scraped_content)} pages for {company}"
                )
                msg += f"\n✅ Successfully scraped {len(scraped_content)} pages"
            else:
                logger.warning(f"No content extracted for {company}")
                msg += "\n⚠️ No content extracted from pages"

        except Exception as e:
            error_str = str(e)
            logger.error(
                f"Google CSE search error for {company}: {error_str}", exc_info=True
            )
            error_msg = f"⚠️ Error searching for {company}: {error_str}"
            msg += f"\n{error_msg}"

            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="website_error",
                    message=error_msg,
                    result={
                        "step": "Site Scrape",
                        "company": company,
                        "type": company_type,
                        "error": error_str,
                        "continue_research": True,
                    },
                )

        return site_scrape, msg

    def organize_content_by_areas(self, scraped_content: List[Dict], query_to_area: Dict[str, str], queries: List[str]) -> Dict[str, Any]:
        """Organize scraped content by analysis areas"""
        organized = {
            "product_offerings": {"content": [], "sources": []},
            "product_direction": {"content": [], "sources": []},
            "strategic_direction": {"content": [], "sources": []},
            "strengths": {"content": [], "sources": []},
            "weaknesses": {"content": [], "sources": []},
            "market_position": {"content": [], "sources": []},
        }
        
        # For now, we'll distribute content across all areas since we can't easily map
        # which content came from which specific query after scraping
        # In a more sophisticated implementation, you could track this during scraping
        
        for item in scraped_content:
            content_piece = {
                "url": item["url"],
                "title": item["title"],
                "content": item["content"][:5000] + "..." if len(item["content"]) > 5000 else item["content"]  # Truncate long content
            }
            
            # Add to all areas for now - in practice you might want to use NLP to categorize
            for area in organized:
                organized[area]["content"].append(content_piece)
                organized[area]["sources"].append(item["url"])
        
        return organized

    async def crawl_company_website(
        self,
        company: str,
        url: str,
        company_type: str,
        websocket_manager=None,
        job_id=None,
    ) -> dict:
        """Crawl a single company's website and extract relevant data using Google CSE"""
        return await self.search_and_scrape_company(
            company, url, company_type, websocket_manager, job_id
        )

    async def process_company(
        self, company_data: dict, websocket_manager=None, job_id=None, is_main=True
    ) -> dict:
        """Process a single company's data (main company or competitor)"""
        company = company_data.get("company", "Unknown Company")
        url = company_data.get("company_url")
        hq_location = company_data.get("hq_location", "Unknown")
        industry = company_data.get("industry", "Unknown")

        company_type = "main company" if is_main else "competitor"
        msg = f"🎯 Processing {company_type}: {company}...\n"

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message=f"🎯 Processing {company_type}: {company}",
                result={
                    "step": "Company Processing",
                    "company": company,
                    "type": company_type,
                },
            )

        site_scrape = {}

        # Always attempt to search and scrape (even without URL)
        site_scrape, crawl_msg = await self.search_and_scrape_company(
            company, url, company_type, websocket_manager, job_id
        )
        msg += f"\n{crawl_msg}"

        return {
            "company": company,
            "company_url": url,
            "hq_location": hq_location,
            "industry": industry,
            "site_scrape": site_scrape,
            "message": msg,
            "is_main": is_main,
            "is_competitor": not is_main,
        }

    async def process_all_companies(self, state: InputState) -> tuple:
        """Process all companies (main + competitors) sequentially"""
        websocket_manager = state.get("websocket_manager")
        job_id = state.get("job_id")
        main_company = state.get("company", "Unknown Company")
        competitors = state.get("competitors", [])

        logger.info(
            f"Processing main company: {main_company} with {len(competitors)} competitors"
        )

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message=f"🎯 Initiating research for {main_company} and {len(competitors)} competitors",
                result={
                    "step": "Initializing",
                    "main_company": main_company,
                    "competitors_count": len(competitors),
                },
            )

        # Prepare all companies for processing
        all_companies = []

        # Add main company
        main_company_data = {
            "company": main_company,
            "company_url": state.get("company_url"),
            "hq_location": state.get("hq_location"),
            "industry": state.get("industry"),
        }
        all_companies.append((main_company_data, True))  # (data, is_main)

        # Add competitors
        for competitor in competitors:
            all_companies.append((competitor, False))  # (data, is_main)

        # Process all companies sequentially
        processed_companies = {}
        all_messages = []

        for i, (company_data, is_main) in enumerate(all_companies):
            # Add delay between companies to avoid rate limiting
            if i > 0:
                delay = 3  # Delay between companies
                await asyncio.sleep(delay)

            company_result = await self.process_company(
                company_data, websocket_manager, job_id, is_main=is_main
            )

            company_name = company_result["company"]
            processed_companies[company_name] = company_result
            all_messages.append(company_result["message"])

        return processed_companies, all_messages

    async def build_research_state(
        self, state: InputState, processed_companies: dict, all_messages: list
    ) -> ResearchState:
        """Build the final research state from processed companies"""
        main_company = state.get("company", "Unknown Company")
        competitors = state.get("competitors", [])
        websocket_manager = state.get("websocket_manager")
        job_id = state.get("job_id")

        # Create combined message
        combined_msg = f"🎯 Multi-Company Research Initiated\n\n"
        combined_msg += f"📊 Main Company: {main_company}\n"
        if competitors:
            competitor_names = [c["company"] for c in competitors]
            combined_msg += f"🏢 Competitors: {', '.join(competitor_names)}\n"
        combined_msg += "\n" + "\n".join(all_messages)

        # Separate main company and competitors data
        main_result = processed_companies[main_company]
        competitors_data = {
            name: data
            for name, data in processed_companies.items()
            if name != main_company
        }

        # Prepare companies_data for SWOT analysis
        companies_data = {
            main_company: {
                "company": main_result["company"],
                "company_url": main_result["company_url"],
                "hq_location": main_result["hq_location"],
                "industry": main_result["industry"],
                "site_scrape": main_result["site_scrape"],
                "is_main": True,
                "is_competitor": False,
            }
        }

        # Add competitors to companies_data
        for competitor_name, competitor_result in competitors_data.items():
            companies_data[competitor_name] = {
                "company": competitor_result["company"],
                "company_url": competitor_result["company_url"],
                "hq_location": competitor_result["hq_location"],
                "industry": competitor_result["industry"],
                "site_scrape": competitor_result["site_scrape"],
                "is_main": False,
                "is_competitor": True,
            }

        # Initialize ResearchState with all company information
        research_state = {
            # Copy input fields
            "company": main_company,
            "company_url": state.get("company_url"),
            "hq_location": state.get("hq_location"),
            "industry": state.get("industry"),
            "competitors": competitors,
            "websocket_manager": websocket_manager,
            "job_id": job_id,
            # Initialize research fields
            "messages": [AIMessage(content=combined_msg)],
            "site_scrape": main_result["site_scrape"],  # Main company's site scrape
            "competitors_site_scrape": competitors_data,  # All competitors data
            "companies_data": companies_data,  # All companies data for SWOT analysis
            # Initialize empty research fields
            "financial_data": {},
            "news_data": {},
            "industry_data": {},
            "company_data": {},
            "curated_financial_data": {},
            "curated_news_data": {},
            "curated_industry_data": {},
            "curated_company_data": {},
            "financial_briefing": "",
            "news_briefing": "",
            "industry_briefing": "",
            "company_briefing": "",
            "references": [],
            "briefings": {},
            "swot_analyses": {},
            "report": "",
        }

        logger.info(
            f"Successfully initialized research state for {main_company} and {len(competitors)} competitors"
        )

        # Save logs
        with open("research_state_grounding_logs.json", "w") as f:
            json.dump(
                {
                    "step": "Grounding",
                    "job_id": job_id,
                    "main_company": main_result,
                    "competitors": competitors_data,
                    "research_state": research_state,
                },
                f,
                indent=2,
                default=str,
            )

        return research_state

    async def initial_search(self, state: InputState) -> ResearchState:
        """Main entry point: Process all companies and initialize ResearchState"""
        # Process all companies (main + competitors) sequentially
        processed_companies, all_messages = await self.process_all_companies(state)

        # Build the final research state
        research_state = await self.build_research_state(
            state, processed_companies, all_messages
        )

        return research_state

    async def run(self, state: InputState) -> ResearchState:
        return await self.initial_search(state)
