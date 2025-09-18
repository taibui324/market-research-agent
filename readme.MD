# マーケティングチーム製品開発エージェント (Marketing Team – Product Development Agent)

> Status: **Draft / MVP scope defined**

## Table of Contents
- [1. Overview](#1-overview)
  - [1.1 Understanding 3C Analysis](#11-understanding-3c-analysis)
    - [Customer Analysis](#customer-analysis)
    - [Company Analysis](#company-analysis)
    - [Competitor Analysis](#competitor-analysis)
    - [Market Size Understanding](#market-size-understanding)
    - [Opportunity Identification](#opportunity-identification)
- [2. User Stories](#2-user-stories)
- [3. Team](#3-team)
- [4. Risks](#4-risks)
- [5. Core Features](#5-core-features)
- [6. Extended Features (Nice-to-Have)](#6-extended-features-nice-to-have)
- [7. Collaboration from Givery](#7-collaboration-from-givery)
- [AI Agent – Market Research for Curry (House Foods)](#ai-agent--market-research-for-curry-house-foods)
  - [1. Target Category](#1-target-category)
  - [2. Scope](#2-scope)
  - [3. Consumer Needs Sources](#3-consumer-needs-sources)
  - [4. Trend Information Sources](#4-trend-information-sources)
  - [5. Expected Output](#5-expected-output)
  - [6. Workflow in DECA (Suggested)](#6-workflow-in-deca-suggested)
  - [7. Next Steps / Action Items](#7-next-steps--action-items)

---

## 1. Overview

**Target Users**
- Product development managers and marketers  
- Departments: Product Planning, Marketing

**Customer Challenges**
- Market research for product development requires significant time and effort for information collection and analysis  
- Difficulty in comprehensively gathering information leads to concept creation based on personal experience and intuition  
- Creates risks of misalignment with market needs and development setbacks

**Solution**
- Introduce AI agents that automatically support **3C Analysis** (Customer, Company, Competitor)  
- Enable rapid collection, analysis, and visualization of comprehensive market information  
- Empower marketers to create logical, data-driven concepts without relying on subjectivity

**Success Metrics**
- Reduction in research time for product development (TBD)  
- Increased quality and quantity of consumer insights (TBD)  
- Improved market trend identification accuracy (TBD)

### 1.1 Understanding 3C Analysis

**3C Analysis Framework**  
The 3C Analysis is a strategic framework that examines three critical areas to identify market opportunities.

#### Customer Analysis
- **Consumer Needs & Insights**
  - Data Sources: Word-of-mouth, Social Media (X, Instagram), Blogs, Forums, Reviews
  - Key Questions: What are customers' pain points? What needs are unmet? What are their buying patterns?
  - Expected Outputs: Customer persona profiles, need hierarchies, purchase journey maps
- **Market Trends**
  - Data Sources: Nikkei Trends, Industry Publications, Overseas Technology Reports, Market Research Data
  - Key Questions: What movements are emerging in the market? How are consumer preferences evolving?
  - Expected Outputs: Trend analysis reports, future market predictions, adoption curve positioning

#### Company Analysis
- **Internal Capabilities Assessment**
  - Areas: Product portfolio, Technology assets, Manufacturing capabilities, Brand strength
  - Key Questions: What are our core competencies? Where do we excel compared to competitors?
  - Expected Outputs: Capability matrices, SWOT analysis, resource allocation recommendations

#### Competitor Analysis
- **Competitive Landscape Mapping**
  - Data Sources: Competitor websites, Product reviews, Annual reports, Press releases
  - Key Questions: What are competitors' product directions? What technologies are they leveraging?
  - Expected Outputs: Competitive positioning maps, feature comparison matrices, white space opportunity identification

#### Market Size Understanding
- **TAM, SAM, SOM Framework**
  - **TAM** (Total Addressable Market): Major categories and total market potential  
  - **SAM** (Serviceable Available Market): Surrounding categories that align with company capabilities  
  - **SOM** (Serviceable Obtainable Market): Specific product categories that can be realistically targeted
- **Market Sizing Approach**
  - AI-generated multiple pattern suggestions for TAM/SAM definitions  
  - Category exploration based on similar consumer needs and usage patterns  
  - Quantitative market size estimation with confidence intervals

#### Opportunity Identification
- **Strategic White Space Analysis**
  - Target underserved market segments where consumer needs align with company capabilities  
  - Identify areas where competitors are weak but consumer demand is strong  
  - Discover emerging needs not yet addressed by any market player

---

## 2. User Stories

- As a product manager, I want to easily **access consumer insights** so I can develop products that better meet customer needs.  
- As a marketing strategist, I want to **track emerging market trends** so I can propose innovative product concepts.  
- As a marketing researcher, I want **automated analysis of consumer data** so I can focus on strategic interpretation rather than data collection.

---

## 3. Team

- **Givery**: @永田祐介 @三阪康栄 @布川裕子  
- **Resola**: @Nhat Pham @Truong Ma Phi @Tai Bui @Akbar Khoshimov

---

## 4. Risks

**Technical Risks**
- AI agents may not capture nuanced consumer insights accurately  
- Data sources for market trends may be incomplete or biased

---

## 5. Core Features

**Consumer Insight Discovery**
- Analyze social media (Twitter/X, Instagram), blogs, forums, and reviews to identify customer pain points and needs.  
- Extract actionable insights such as _“Top 3 pain points customers feel in this category.”_

**Trend Tracking**
- Monitor industry publications, news sources, and foreign technology reports.  
- Generate reports highlighting _“Key consumer product trends gaining attention this month.”_

**Competitor Analysis**
- Collect data about competitor products from their websites, customer support logs, and reviews.  
- Identify weaknesses and market gaps with insights like _“Competitor X has UX weaknesses → potential differentiation point.”_

**Company Capability Assessment**
- Evaluate company's own product portfolio and capabilities.  
- Match market needs with company strengths to identify opportunities.

**Opportunity Identification**
- Match consumer needs with company capabilities using the **3C** framework.  
- Highlight **white space** opportunities where neither competitors nor the company are addressing specific needs.

![image.png](Product%20Market%20Research%20Agent%20260c269badb6801d96f4f07bf322929d/image.png)

---

## 6. Extended Features (Nice-to-Have)

- **Slack Integration**: Ask questions like _“What are the top trends in the XX industry this month?”_ and receive summarized responses.  
- **CRM/Survey Tool Integration**: Directly import customer feedback for analysis.

---

## 7. Collaboration from Givery

- Help identify specific data sources for the agent to access (websites, publications, forums).  
- Provide example URLs for industry publications, consumer feedback sites, and competitor information.  
- Narrow the scope to one specific category/industry for better initial results.

---

# AI Agent – Market Research for Curry (House Foods)

## 1. Target Category

- Focus: **Packaged curry products** (curry roux & ready-to-eat/retort curry)  
- Example company: **House Foods**  
  - Catalog: [House Foods Curry Products](https://housefoods.jp/products/catalog/cat_1,curry.html)

---

## 2. Scope

- **Primary Focus:** Consumer needs and trends related to curry.  
- **Company Analysis:** Not required this time.  
- **Competitor Analysis:** Limited to:
  1. **S&B Foods** → [S&B Curry Products](https://www.sbfoods.co.jp/products/category/?category=00300)  
  2. **Ezaki Glico** → [Glico Curry Products](https://www.glico.com/jp/product/food_curry/)  
  3. **PB Private Label Products** → [PB](https://www.seiyu.co.jp/pb/mo/instant/)  
  - PB/Private Label products optional; omit for now.

---

## 3. Consumer Needs Sources

Collect consumer reviews, comments, and feedback from:

| Type                         | Sites                                                                                             |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| Food review / user opinions | Grok ([grok.com](https://grok.com/)), Tabelog ([tabelog.com](https://tabelog.com/)), Mognavi ([mognavi.jp](https://mognavi.jp/)) |

**AI Task**
- Crawl or scrape user posts on curry products.  
- Group posts by **common pain points, preferences, flavor trends**.  
- Generate **consumer insight clusters** (e.g., taste, spiciness, packaging convenience).

---

## 4. Trend Information Sources

Collect broader trend data from:

| Type                | Sites                                                                                                                |
|---------------------|----------------------------------------------------------------------------------------------------------------------|
| Food trend platforms| Retty ([retty.me](https://retty.me/)), Sarah ([sarah30.com](https://sarah30.com/))                                   |
| Industry publications | Food Industry Newspaper ([shokuhin.net](https://shokuhin.net/)), Nikkei Marketing Journal ([nikkei.com/special/nikkeimj](https://www.nikkei.com/special/nikkeimj)) |
| General news        | Yahoo News ([news.yahoo.co.jp](https://news.yahoo.co.jp/))                                                          |

**AI Task**
- Extract **emerging curry trends**, e.g., new flavors, popular product formats, seasonal preferences.  
- Summarize in **trend bullet points** with links for reference.

---

## 5. Expected Output

**Consumer Needs Mapping**
- Clustered insights (e.g., “Spiciness preference,” “Convenience of ready-to-eat,” “Packaging concerns”).  
- Highlight most frequent comments or mentions.

**Trend Summary**
- Monthly or recent trend highlights.  
- Insights from both industry sources and social feedback.

**Visualization (optional)**
- Word clouds, bar charts, or grouped tables for DECA presentation.

**Example format**

| Cluster      | Insight                              | Source Count | Notes                     |
|--------------|---------------------------------------|--------------|---------------------------|
| Spiciness    | Mild curry preferred by families      | 35 posts     | Mostly on Grok & Tabelog  |
| Convenience  | Prefers microwavable retort packs     | 20 posts     | Highlighted in Mognavi    |
| Flavor Variety | Trend: international curry flavors  | -            | Retty & Sarah articles    |

---

## 6. Workflow in DECA (Suggested)

1. Pull consumer posts from Grok → Group by topic → Generate clusters.  
2. Pull trend information from Retty/Sarah/industry publications → Summarize insights.  
3. Map insights → Output in table or visual for product team review.

**Minimum viable demo**
- Start with **Grok posts → grouped insights → output table**.  
- Later iterations can expand to trends and competitor mentions.

---

## 7. Next Steps / Action Items

1. **Set up scraping/data pull:** Focus
2. **Define AI grouping logic:** Clustering by sentiment, topic, or need.
3. **Prepare output template:** Table + JSON/CSV export (schema below).
4. **Add trend analysis:** Integrate Retty/Sarah/industry sources post-MVP.
5. **Consider DECA integration:** Wire outputs into DECA views for PM review.

**Output Schema (draft)**
```json
{
  "cluster": "Spiciness",
  "insight": "Mild curry preferred by families",
  "sourceCount": 35,
  "sources": ["grok", "tabelog"],
  "examples": [
    { "url": "https://...", "snippet": "..." }
  ],
  "confidence": 0.78,
  "updatedAt": "2025-09-16T00:00:00Z"
}


<p align="center">
  <img src="https://raw.githubusercontent.com/mermaid-js/mermaid/develop/docs/public/favicon.svg" height="64" />
</p>

<h1 align="center">3C Research Agent</h1>

<p align="center">
  Generate high-context company research briefs via FastAPI + LangGraph with a React (Vite) UI.
</p>

---

# Architecture


```mermaid
%%{init: {'theme':'neutral','flowchart':{'htmlLabels':true,'curve':'linear','nodeSpacing':50,'rankSpacing':40}} }%%
flowchart LR
    %% ===== UI =====
    subgraph UI["React Frontend (Vite)"]
      A["Search Form + Progress UI"]
      WS["WebSocket (ws /research/ws/{job_id})"]
      HTTP["HTTP API (:8000)"]
    end

    %% ===== Backend =====
    subgraph Backend["FastAPI + LangGraph"]
      direction TB
      ORCH["Market Research Orchestrator<br/>(LangGraph controller)"]
      QG["Query Generator"]
      COL["Collector"]
      CUR["Curator<br/>(relevance scoring >= threshold)"]

      subgraph ResearchAgents["Research Agents (Nodes)"]
        CAgt["Customer Analysis Agent"]
        COAgt["Competitor Analysis Agent"]
        TAgt["Trend Analysis Agent"]
        CMAgt["Company Analysis Agent"]
        RptAgt["Reporting Agent"]
      end

      subgraph BriefingStage["Briefing"]
        BR["briefing.py<br/>Synthesize category briefs"]
      end

      subgraph EditorStage["Editor"]
        ED["editor.py<br/>Format + deduplicate<br/>Markdown report"]
      end

      WSMgr["WebSocket Manager<br/>status + chunk streaming"]
      DB[("MongoDB<br/>optional persistence")]
    end

    %% ===== External / Data Sources =====
    subgraph ExternalAPIs["External Services and Data Sources"]
      TAV["Tavily Search API"]
      MCP["MCP Web Search Server"]
      GROK["grok / retty<br/>food review sources"]
      IND["Industry reports"]
      SOC["Social Media APIs"]
      GMAPS["Google Maps API"]
      LLM1["Gemini 2.0 Flash"]
      LLM2["OpenAI GPT-4.1-mini"]
      LLM3["OpenAI gpt-4o-mini-search-preview"]
      LLM4["OpenAI o4-mini-deep-research"]
    end

    %% ===== UI -> Backend =====
    A -- "submit company/topic" --> HTTP
    HTTP --> ORCH
    ORCH --> QG --> COL

    %% ===== Orchestrator dispatches agents =====
    ORCH --> CAgt
    ORCH --> COAgt
    ORCH --> TAgt
    ORCH --> CMAgt
    ORCH --> RptAgt

    %% ===== Agents collect via Collector/Curator and MCP/Tavily =====
    CAgt --> COL
    COAgt --> COL
    TAgt --> COL
    CMAgt --> COL

    COL --> CUR
    CUR -->|fetch/score| TAV
    %% Optional: agents also pull via MCP server
    CAgt -. "search" .-> MCP
    COAgt -. "search" .-> MCP
    TAgt  -. "search" .-> MCP
    CMAgt -. "search" .-> MCP

    %% MCP fan-out to sources
    MCP --> GROK
    MCP --> IND
    MCP --> SOC

    %% ===== Briefing / Editing =====
    CUR -- "relevant docs" --> BR
    BR --> LLM1
    BR --> ED
    ED --> LLM2
    ED --> LLM3
    ED --> LLM4

    %% ===== Reporting Agent ties into editor/output =====
    RptAgt --> ED

    %% ===== Streaming + storage =====
    CUR -->|stats| WSMgr
    BR -->|phase status| WSMgr
    ED -->|report chunks| WSMgr
    WSMgr <--> WS
    ED --> DB

    %% ===== Misc integrations =====
    A -. "map embeds" .-> GMAPS


