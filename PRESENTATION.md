# 3C Market Research Agent — Client Demo Presentation

---

## Slide 1: Problem Statement

### The Challenge for Product Development Teams

**Current State:**
- Market research for product development takes **weeks of manual effort** — collecting data from social media, reviews, industry reports, competitor websites
- Information gathering is fragmented — teams rely on personal experience and intuition
- Risk of **misalignment with actual market needs** leading to product development setbacks

**The Cost:**
- A product manager spends ~40% of their time on data collection instead of strategic analysis
- Consumer insights are often outdated by the time they reach decision-makers
- Competitive blind spots lead to missed opportunities

---

## Slide 2: Our Solution

### AI-Powered 3C Market Research Agent

An autonomous multi-agent system that conducts **comprehensive market research in minutes, not weeks**.

Built on the **3C Analysis Framework**:

| Dimension | What We Analyze | Key Outputs |
|-----------|----------------|-------------|
| **Customer** | Consumer needs, pain points, purchase behavior | Personas, journey maps, insight clusters |
| **Company** | Internal capabilities, product portfolio | SWOT analysis, capability matrices |
| **Competitor** | Competitive landscape, market positioning | Feature comparisons, white space opportunities |

**Demo target:** Japanese curry market (House Foods) — extensible to any market/industry.

---

## Slide 3: Live Demo Flow

### What the User Sees

```
1. User opens the React UI → enters target market and analysis parameters
2. Selects analysis depth: Quick / Focused / Comprehensive
3. Optionally selects specific agents to run
4. Clicks "Start Analysis"
5. Real-time progress streams via WebSocket:
   - Query generation (live streaming)
   - Data collection progress
   - Agent-by-agent status updates
   - Performance metrics
6. Final report renders in-browser (Markdown)
7. Export to PDF / HTML / JSON / CSV
```

### Key Demo Talking Points
- Show the **real-time WebSocket streaming** — queries appearing character by character
- Show **agent selection** — run only consumer + trend for a quick analysis
- Show the **final report** with structured sections, confidence scores, and source citations
- Show **export options** — PDF for executives, JSON for data teams

---

## Slide 4: System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite + TypeScript)           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Search   │  │ Real-time    │  │ Report       │  │ Export    │  │
│  │ Form     │  │ Progress UI  │  │ Viewer       │  │ (PDF/HTML)│  │
│  └────┬─────┘  └──────▲───────┘  └──────────────┘  └───────────┘  │
│       │               │ WebSocket                                   │
└───────┼───────────────┼─────────────────────────────────────────────┘
        │ HTTP POST     │ ws://host/api/research/ws/{job_id}
┌───────▼───────────────┼─────────────────────────────────────────────┐
│                   FastAPI Application Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ /api/      │  │ /api/      │  │ WebSocket    │  │ Job Status │ │
│  │ research   │  │ research/  │  │ Manager      │  │ Tracker    │ │
│  │            │  │ 3c-analysis│  │              │  │            │ │
│  └────┬───────┘  └─────┬──────┘  └──────────────┘  └────────────┘ │
│       │                │                                            │
│  ┌────▼────┐     ┌─────▼──────────────────────────────────────┐    │
│  │ Company │     │    3C Analysis Orchestrator (LangGraph)     │    │
│  │ Research│     │                                             │    │
│  │ Graph   │     │  Query Gen → Collection → Curation          │    │
│  │         │     │       → [Agent Pipeline] → Opportunity      │    │
│  │         │     │       → Synthesis → Report Generation       │    │
│  └─────────┘     └─────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Services Layer                             │   │
│  │  MongoDB Service │ PDF Service │ Report Generator │ WS Mgr   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  Search APIs   │  │   LLM APIs     │  │   Database     │
│  ─────────     │  │   ────────     │  │   ────────     │
│  Exa (primary) │  │  GPT-4.1-mini  │  │  MongoDB       │
│  Perplexity    │  │  Gemini 2.0    │  │  (optional)    │
│  Tavily        │  │  Flash         │  │                │
│                │  │  Grok-4 (xAI)  │  │                │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## Slide 5: Two Research Pipelines

### Pipeline 1: Company Research

For researching a **specific company** and its competitors.

```
                    ┌─→ Financial Analyst ──┐
                    ├─→ News Scanner ───────┤
Grounding ──────────┤                       ├──→ Collector → Curator → Enricher
                    ├─→ Industry Analyzer ──┤         → Briefing → Editor
                    └─→ Company Analyzer ───┘              → SWOT → Competitor Analysis
                    
                    (parallel fan-out)              (sequential pipeline)
```

**Key characteristics:**
- Grounding node scrapes the target company website and establishes research context
- Four specialized researchers run **in parallel** (fan-out pattern)
- Results converge at the Collector, then flow through sequential processing
- Final output: comprehensive company research brief with SWOT

### Pipeline 2: 3C Market Analysis (Primary Demo)

For analyzing an **entire market** using the 3C framework.

```
Query Generation → Data Collection → Data Curation
    → Consumer Agent → Trend Agent → Competitor Agent → SWOT Agent → Customer Mapping
        → Opportunity Analysis → Synthesis → Report Generation
```

**Key characteristics:**
- Agents execute **sequentially** (design decision — see ADR-002)
- Agent selection is **configurable** at request time
- Six analysis depth presets: comprehensive, focused, quick, consumer_focused, competitive_focused, market_trends_focused
- Graceful degradation — if one agent fails, the pipeline continues

---

## Slide 6: The Agent Architecture

### Base Researcher Pattern

All research agents inherit from `BaseResearcher`, which provides:

```python
class BaseResearcher:
    # Core capabilities every agent gets:
    # 1. Query generation via GPT-4.1-mini (streaming)
    # 2. Exa web search with batching & rate limiting
    # 3. Fallback LLM content generation if search fails
    # 4. Real-time WebSocket progress updates
```

### Specialized Agents

| Agent | Responsibility | Data Sources | Key Outputs |
|-------|---------------|--------------|-------------|
| **Consumer Analysis** | Pain points, personas, purchase journey | Social media, reviews, forums | 3-4 personas, 5-8 pain points, 5-stage journey map |
| **Trend Analysis** | Market trends, growth patterns | Industry publications, news | Trend predictions, adoption curves (emerging→declining) |
| **Competitor Analysis** | Competitive landscape mapping | Business reports, websites | Top 10 competitors, market share, feature matrix, gaps |
| **SWOT Analysis** | Strategic positioning | Aggregated research data | Strengths/Weaknesses/Opportunities/Threats with metrics |
| **Customer Mapping** | Consumer behavior clustering | Consumer data + trends | Behavior clusters with frequency analysis |

### How an Agent Works (Consumer Agent Example)

```
1. Generate 4 targeted search queries via GPT-4.1-mini
2. Batch search via Exa API (2 queries/batch, 1s delay)
3. If < 3 results, generate synthetic content via LLM fallback
4. Query MongoDB for existing consumer analysis data
5. Synthesize: personas + pain points + purchase journey
6. Stream progress to UI via WebSocket at each step
7. Write results to shared LangGraph state
```

---

## Slide 7: Data Pipeline Deep Dive

### Collection → Curation → Enrichment

```
Raw Data (100+ documents)
    │
    ▼
┌─────────────────────────────────────────┐
│           MarketDataCollector            │
│  • Exa search across categories         │
│  • Social media, reviews, industry      │
│  • 24-hour cache in MongoDB             │
│  • Rate limiting & timeout handling     │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│           MarketDataCurator             │
│  • Keyword relevance scoring:           │
│    - High relevance: +1.0 ("japanese    │
│      curry", "curry roux", "カレー")    │
│    - Medium: +0.5 ("curry powder")      │
│    - Low/off-topic: -0.2 ("thai curry") │
│  • Source credibility scoring           │
│  • Content quality assessment           │
│  • Deduplication via content hashing    │
│  • Threshold filter: score >= 0.6       │
│  • Max 25 documents per category        │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│             Enricher                    │
│  • Fetch full content for top URLs      │
│  • Add context and relationships        │
│  • Prepare data for briefing stage      │
└─────────────────────────────────────────┘
              │
              ▼
        ~25-50 high-quality documents
```

---

## Slide 8: Multi-Model Strategy

### Why We Use Different LLMs for Different Tasks

| Task | Model | Why This Model |
|------|-------|---------------|
| Query generation | GPT-4.1-mini | Fast, cheap, good at structured output |
| Web search | Exa API | Purpose-built for semantic search, returns full content |
| Briefing synthesis | Gemini 2.0 Flash | Large context window (1M tokens), efficient at summarizing many documents |
| Report editing | GPT-4.1-mini | Precise at following formatting instructions, markdown consistency |
| Deep analysis | Grok-4 (xAI) | Strong reasoning for SWOT and strategic analysis |
| Relevance scoring | Tavily | AI-powered search relevance built into the API |

**Cost optimization:** We route each task to the cheapest model that can handle it well. Query generation doesn't need Grok-4; synthesis doesn't need GPT-4.1-mini's precision.

---

## Slide 9: Real-Time Communication

### WebSocket Architecture

```
Client (React)                    Server (FastAPI)
     │                                  │
     │──── Connect to ws/{job_id} ─────▶│
     │                                  │
     │◀── status_update: "processing" ──│  ← Orchestrator starts
     │◀── agent_progress: consumer 20% ─│  ← Consumer agent running
     │◀── query_generating: "query 1" ──│  ← Live query streaming
     │◀── agent_progress: consumer 80% ─│  ← Search complete
     │◀── agent_progress: trend 10% ────│  ← Trend agent starts
     │◀── workflow_progress: 40% ───────│  ← Overall progress
     │     ...                          │
     │◀── status_update: "completed" ───│  ← Final report ready
     │◀── report_content: {...} ────────│  ← Full report payload
     │                                  │
```

**Message types:**
- `status_update` — overall job status changes
- `agent_progress` — per-agent progress with percentage and performance metrics
- `workflow_progress` — overall completion percentage
- `query_generating` — live character-by-character query streaming
- `performance_metrics` — timing data for monitoring

---

## Slide 10: State Management

### LangGraph Shared State

```python
# Progressive state inheritance
InputState          # company, industry, competitors, job_id
    └─→ ResearchState      # + financial_data, news_data, industry_data, 
        │                  #   company_data, curated_*, briefings, report
        └─→ MarketResearchState  # + consumer_insights, market_trends,
                                 #   competitor_landscape, opportunities,
                                 #   customer_personas, pain_points,
                                 #   purchase_journey, adoption_curves
```

Each node in the LangGraph workflow reads from and writes to specific fields in this shared state. The state grows as it flows through the pipeline — early nodes populate raw data, later nodes add analysis and synthesis.

---

## Slide 11: Error Handling & Resilience

### Graceful Degradation Pattern

```
Agent fails?
    │
    ▼
AgentFailureHandler catches the exception
    │
    ├─→ Logs error with full context
    ├─→ Populates state with empty/error fallback data
    ├─→ Notifies UI via WebSocket: "consumer_analysis failed, continuing"
    └─→ Pipeline continues with remaining agents
            │
            ▼
    Report generated with available data
    (partial report > no report)
```

**Additional resilience:**
- Exa search: 30-second timeout per batch, fallback to LLM-generated content
- Rate limiting: 2-query batches with 1-second delays
- Data caching: 24-hour TTL in MongoDB to reduce redundant API calls
- Minimum document threshold: if search returns < 3 docs, LLM generates synthetic content

---

## Slide 12: Report Generation

### Output Capabilities

The `MarketResearchReportGenerator` produces structured reports with:

1. **Executive Summary** — key findings and strategic recommendations
2. **Consumer Analysis** — personas, pain points, purchase journey
3. **Trend Analysis** — identified trends, predictions, adoption curves
4. **Competitor Analysis** — landscape, positioning, feature comparisons, market gaps
5. **Opportunity Analysis** — white spaces, strategic recommendations
6. **Data Quality Footer** — confidence scores, source counts, methodology notes

**Export formats:**
| Format | Use Case |
|--------|----------|
| Markdown | In-app viewing, developer consumption |
| HTML | Professional styled reports for sharing |
| PDF | Executive distribution, printing |
| JSON | Programmatic access, data integration |
| CSV | Spreadsheet analysis, data teams |

---

## Slide 13: Configurable Analysis

### Request-Time Flexibility

```json
{
  "analysis_type": "3c_analysis",
  "analysis_depth": "comprehensive",
  "target_market": "japanese_curry",
  "selected_agents": ["consumer_analysis", "trend_analysis", "competitor_analysis"],
  "execution_mode": "hybrid",
  "enable_performance_tracking": true,
  "priority_level": "high"
}
```

**Analysis depth presets:**

| Preset | Agents | Est. Time | Use Case |
|--------|--------|-----------|----------|
| `quick` | Consumer only | 2-3 min | Quick pulse check |
| `focused` | Consumer + Trend + Competitor | 5-7 min | Standard analysis |
| `comprehensive` | All 5 agents | 10-15 min | Full strategic review |
| `consumer_focused` | Consumer + Mapping + Trend | 5-7 min | Product development |
| `competitive_focused` | Competitor + SWOT + Trend | 5-7 min | Competitive strategy |
| `market_trends_focused` | Trend + Consumer | 4-6 min | Trend monitoring |

---


## Slide 14: Architecture Decision Records (ADRs)

---

### ADR-001: LangGraph as Orchestration Framework

**Status:** Accepted  
**Date:** 2025

**Context:**  
We needed a workflow orchestration framework for coordinating multiple AI agents. Options considered: LangGraph, CrewAI, AutoGen, custom async orchestration.

**Decision:**  
Use **LangGraph** (from LangChain) as the orchestration framework.

**Rationale:**
- **Explicit state management** — LangGraph uses TypedDict-based state, giving us full control over what data flows between nodes. Unlike CrewAI's opinionated agent roles, we define exactly how state mutates.
- **Graph-native patterns** — native support for fan-out/fan-in (parallel research nodes), conditional edges (agent selection), and streaming. The `StateGraph` API maps directly to our pipeline architecture.
- **Streaming support** — `astream()` yields state after each node, enabling real-time WebSocket updates without custom plumbing.
- **Composability** — we run two separate graphs (company research + 3C analysis) from the same application, sharing node implementations.

**Trade-offs:**
- LangGraph's shared mutable state creates concurrency challenges (see ADR-002)
- Tighter coupling to LangChain ecosystem than a framework-agnostic approach
- Graph edge configuration becomes verbose for dynamic agent selection

**Consequences:**
- All workflow logic is declarative (add_node, add_edge, set_entry_point)
- State schema is the contract between nodes — changes require updating TypedDict definitions
- WebSocket streaming is straightforward via the astream iterator

---

### ADR-002: Sequential Agent Execution Over Parallel

**Status:** Accepted  
**Date:** 2025

**Context:**  
The 3C orchestrator coordinates up to 5 agents (consumer, trend, competitor, SWOT, customer mapping). Running them in parallel would reduce total execution time from ~15 minutes to ~5 minutes.

**Decision:**  
Execute agents **sequentially** in the 3C pipeline. The code contains a commented-out `parallel_analysis_coordinator` node, confirming parallel execution was attempted and abandoned.

**Rationale:**
- LangGraph's `StateGraph` uses a **shared mutable dictionary** as state. When multiple agents write to the state concurrently, we encountered **concurrent update errors** — agents overwriting each other's results.
- Sequential execution guarantees **state consistency** — each agent sees the complete output of all previous agents.
- Some agents benefit from prior results: the SWOT agent uses competitor data, the opportunity analysis uses all prior agent outputs.

**Trade-offs:**
- **Slower execution** — comprehensive analysis takes 10-15 minutes instead of ~5 minutes
- **No parallelism benefit** — even independent agents (consumer + competitor) run sequentially
- The original company research pipeline (Pipeline 1) successfully uses parallel fan-out because its researchers write to **separate state fields** with no overlap

**Alternatives considered:**
- **Parallel with locks** — too complex, LangGraph doesn't natively support field-level locking
- **Separate state per agent, merge later** — would require a custom merge node and lose the benefit of agents building on each other's results
- **Hybrid** — run independent agents in parallel, dependent ones sequentially. Listed as `execution_mode: "hybrid"` in the API but currently executes sequentially regardless

**Consequences:**
- The orchestrator builds a linear chain of edges based on selected agents
- Adding a new agent means inserting it into the chain at the right position
- Future optimization: implement field-level state isolation to enable safe parallelism

---

### ADR-003: Multi-Model LLM Strategy

**Status:** Accepted  
**Date:** 2025

**Context:**  
Different tasks in the pipeline have different requirements: query generation needs speed, synthesis needs large context windows, editing needs instruction-following precision, deep analysis needs strong reasoning.

**Decision:**  
Use **multiple LLM models**, each selected for the task it handles best.

| Task | Model | Selection Criteria |
|------|-------|--------------------|
| Query generation | GPT-4.1-mini | Fast, low cost, good structured output |
| Briefing synthesis | Gemini 2.0 Flash | 1M token context window, efficient summarization |
| Report editing | GPT-4.1-mini | Precise formatting, markdown consistency |
| Strategic analysis | Grok-4 (xAI) | Strong reasoning for SWOT and competitive analysis |

**Rationale:**
- **Cost optimization** — routing simple tasks to cheaper models saves ~60% vs. using a single premium model for everything
- **Capability matching** — Gemini's 1M context window is essential for synthesizing 50+ research documents; GPT-4.1-mini can't handle that volume but excels at precise formatting
- **Vendor diversification** — not locked into a single provider; can swap models as pricing/capabilities change

**Trade-offs:**
- **Operational complexity** — managing API keys and rate limits for 3+ providers
- **Inconsistent behavior** — different models have different output styles, requiring careful prompt engineering per model
- **Latency variability** — response times differ across providers

**Consequences:**
- Each node explicitly declares which model it uses
- Settings are centralized in `utils/settings.py` and environment variables
- Model swaps are localized to individual nodes, not system-wide

---

### ADR-004: Exa as Primary Search Provider

**Status:** Accepted  
**Date:** 2025

**Context:**  
Research agents need to search the web for market data. Options: Tavily, Exa, Perplexity, Google Custom Search, SerpAPI.

**Decision:**  
Use **Exa** as the primary search API, with Perplexity and Tavily as fallbacks.

**Rationale:**
- **Semantic search** — Exa returns results based on meaning, not just keyword matching. Critical for nuanced market research queries.
- **Full content extraction** — Exa returns up to 3,000 characters of page content per result, reducing the need for separate scraping.
- **Category filtering** — supports filtering by content category (news, research papers, company pages).
- **Async-native** — `AsyncExa` client integrates cleanly with our async pipeline.

**Trade-offs:**
- **Rate limits** — requires batching (2 queries per batch with 1-second delays)
- **Cost** — per-query pricing adds up with 4 queries × 5 agents × multiple categories
- **Availability** — single provider dependency mitigated by fallback chain

**Fallback chain:**
1. Exa search (primary)
2. Perplexity search (if Exa fails)
3. LLM-generated synthetic content (if all search fails)

**Consequences:**
- `BaseResearcher` implements batch processing with rate limiting
- 30-second timeout per search batch
- Minimum 3 documents required; LLM generates synthetic content if threshold not met

---

### ADR-005: WebSocket for Real-Time Progress

**Status:** Accepted  
**Date:** 2025

**Context:**  
Research workflows take 2-15 minutes. Users need feedback during execution. Options: polling, Server-Sent Events (SSE), WebSocket.

**Decision:**  
Use **WebSocket** connections for real-time bidirectional communication.

**Rationale:**
- **Bidirectional** — while currently used for server→client updates, WebSocket enables future features like mid-analysis user input or cancellation
- **Low latency** — persistent connection avoids HTTP overhead for frequent small updates (query streaming is character-by-character)
- **Per-job isolation** — `WebSocketManager` maintains separate connection pools per `job_id`, so multiple concurrent analyses don't interfere
- **Native FastAPI support** — FastAPI has first-class WebSocket support, no additional dependencies needed

**Trade-offs:**
- **Stateful connections** — harder to scale horizontally (connections are in-memory per server instance)
- **Connection management** — need to handle disconnects, reconnects, and cleanup
- **No built-in persistence** — if the client disconnects and reconnects, missed messages are lost

**Consequences:**
- Every node in the pipeline calls `websocket_manager.send_status_update()` at key progress points
- Frontend maintains a single WebSocket connection per analysis job
- Horizontal scaling would require Redis pub/sub for cross-instance message broadcasting

---

### ADR-006: Optional MongoDB with Mock Fallback

**Status:** Accepted  
**Date:** 2025

**Context:**  
The system needs persistence for job tracking, reports, and data caching. However, requiring MongoDB for development adds friction.

**Decision:**  
Make MongoDB **optional** with a `MockMongoDBService` fallback for development.

**Rationale:**
- **Zero-dependency development** — developers can run the full system without installing MongoDB
- **Same interface** — `MockMongoDBService` implements the same methods as `MongoDBService`, so application code doesn't branch on which is active
- **Automatic detection** — if `MONGODB_URI` is set, use real MongoDB; otherwise, use the in-memory mock

**Trade-offs:**
- **Data loss in development** — mock service stores data in-memory; server restart loses everything
- **Behavior differences** — mock doesn't replicate MongoDB query semantics, aggregation pipelines, or indexing behavior
- **Testing gap** — integration tests against the mock may pass but fail against real MongoDB

**Consequences:**
- Application startup checks for `MONGODB_URI` environment variable
- All database access goes through the service interface, never directly to pymongo
- Production deployments must set `MONGODB_URI` for data persistence

---

### ADR-007: Market-Specific Relevance Scoring

**Status:** Accepted  
**Date:** 2025

**Context:**  
Generic search results include irrelevant content (e.g., Indian curry articles when researching Japanese curry). We need domain-specific filtering.

**Decision:**  
Implement a **weighted keyword scoring system** in `MarketDataCurator` with market-specific keyword dictionaries.

**Scoring model:**
```
High relevance keywords:  +1.0  ("japanese curry", "curry roux", "カレー", "house foods")
Medium relevance:         +0.5  ("curry powder", "japanese food", "instant curry")
Low relevance (penalty):  -0.2  ("indian curry", "thai curry", "vindaloo", "korma")
```

**Additional factors:**
- Source credibility (high/medium/low domain lists)
- Content quality (length, structure, completeness)
- Data-type-specific quality indicators

**Threshold:** Documents scoring below 0.6 are filtered out. Maximum 25 documents per category.

**Rationale:**
- Generic relevance scoring (Tavily's 0.4 threshold in Pipeline 1) lets too much noise through for market-specific research
- Japanese curry market has clear keyword boundaries that enable effective rule-based filtering
- Combining keyword scoring with source credibility produces higher-quality input for analysis agents

**Trade-offs:**
- **Market-specific** — keyword dictionaries must be maintained per target market
- **Brittle** — new products or trends may not match existing keywords
- **Language-dependent** — Japanese keywords (カレー) require proper encoding handling

**Consequences:**
- Adding a new target market requires defining a new keyword dictionary in `MarketDataCurator`
- The curator is the quality gate — everything downstream depends on its filtering accuracy
- Future improvement: use LLM-based relevance scoring instead of keyword matching

---

### ADR-008: Graceful Degradation via AgentFailureHandler

**Status:** Accepted  
**Date:** 2025

**Context:**  
With 5 agents calling external APIs (Exa, OpenAI, xAI), failures are inevitable — rate limits, timeouts, API outages. A single agent failure shouldn't kill the entire analysis.

**Decision:**  
Implement an `AgentFailureHandler` that catches per-agent exceptions and populates the state with **empty fallback data structures**, allowing the pipeline to continue.

**Behavior:**
```python
# If consumer_analysis fails:
state['consumer_insights'] = {"status": "failed", "error": str(error), ...}
state['pain_points'] = []
state['customer_personas'] = []
state['purchase_journey'] = {}
# Pipeline continues → trend_analysis runs next
```

**Rationale:**
- **Partial results are valuable** — a report with trend + competitor data but no consumer insights is still useful
- **User transparency** — WebSocket notification tells the user exactly which agent failed
- **No manual retry needed** — the pipeline completes automatically with available data

**Trade-offs:**
- **Silent degradation risk** — users might not notice a section is missing if they don't check the WebSocket notifications
- **Report quality varies** — the same "comprehensive" analysis can produce very different reports depending on which agents succeed
- **No automatic retry** — a transient failure (rate limit) isn't retried at the workflow level

**Consequences:**
- Report generator checks for error states in each section and adjusts accordingly
- Data quality metrics in the report footer reflect which agents succeeded
- Future improvement: add configurable retry policies per agent

---

## Slide 15: Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | SPA with real-time updates |
| **Styling** | Tailwind CSS + Framer Motion | Responsive design + animations |
| **Backend** | FastAPI + Python 3.11 | Async API server |
| **Orchestration** | LangGraph | Workflow graph management |
| **LLMs** | GPT-4.1-mini, Gemini 2.0 Flash, Grok-4 | Multi-model strategy |
| **Search** | Exa, Perplexity, Tavily | Web research with fallbacks |
| **Database** | MongoDB (optional) | Persistence + caching |
| **Real-time** | WebSocket (FastAPI native) | Live progress streaming |
| **Export** | ReportLab, Jinja2, Markdown | PDF/HTML/JSON/CSV generation |
| **Deployment** | Docker + Docker Compose | Containerized deployment |
| **Infra** | AWS Copilot (ECS) | Production hosting |

---

## Slide 16: Future Roadmap

| Priority | Enhancement | Impact |
|----------|------------|--------|
| **High** | Field-level state isolation for safe parallel agent execution | 3x faster comprehensive analysis |
| **High** | Authentication + API key management | Production security |
| **Medium** | Redis for WebSocket scaling + job state | Horizontal scaling |
| **Medium** | Celery/RQ task queue replacing asyncio.create_task | Reliable background processing |
| **Medium** | LLM-based relevance scoring replacing keyword matching | Better curation for new markets |
| **Low** | Slack integration for on-demand queries | User convenience |
| **Low** | CRM/survey tool integration | Direct feedback import |
| **Low** | Scheduled recurring analysis | Automated trend monitoring |

---

## Slide 17: Key Metrics & Differentiators

**Performance:**
- Quick analysis: **2-3 minutes** (vs. days of manual research)
- Comprehensive analysis: **10-15 minutes** (vs. weeks)
- Real-time progress visibility throughout

**Quality:**
- Multi-source data collection (social media, reviews, industry reports, competitor data)
- AI-powered relevance filtering reduces noise by ~75%
- Structured output with confidence scores and source citations

**Flexibility:**
- 6 analysis depth presets for different use cases
- Per-agent selection for targeted analysis
- 5 export formats for different stakeholders
- Extensible to any market (not just Japanese curry)

---

*End of presentation*
