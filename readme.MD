<p align="center">
  <img src="https://raw.githubusercontent.com/mermaid-js/mermaid/develop/docs/public/favicon.svg" height="64" />
</p>

<h1 align="center">AI Company Research Agent</h1>

<p align="center">
  Generate high-context company research briefs via FastAPI + LangGraph with a React (Vite) UI.
</p>

---

## Architecture

> GitHub renders Mermaid blocks out of the box.  
> Tip: switch theme by changing `'theme':'neutral'` → `'dark'` in the init line.

```mermaid
%%{init: {'theme':'neutral','flowchart':{'htmlLabels':true,'curve':'linear','nodeSpacing':50,'rankSpacing':40}} }%%
flowchart LR
  subgraph UI["React Frontend (Vite)"]
    A["Search Form + Progress UI"]
    WS["WebSocket (ws /research/ws/{job_id})"]
    HTTP["HTTP API (:8000)"]
  end

  subgraph Backend["FastAPI Backend + LangGraph"]
    direction TB
    QG["Query Generator"]
    COL["Collector"]
    CUR["Curator<br/>(Tavily scores >= threshold)"]

    subgraph ResearchAgents["Research Nodes"]
      CA["CompanyAnalyzer"]
      IA["IndustryAnalyzer"]
      FA["FinancialAnalyst"]
      NS["NewsScanner"]
    end

    subgraph BriefingStage["Briefing (Gemini 2.0 Flash)"]
      BR["briefing.py<br/>High-context synthesis"]
    end

    subgraph EditorStage["Editor (GPT-4.1-mini + variants)"]
      ED["editor.py<br/>Format + Deduplicate<br/>Markdown report"]
    end

    WSMgr["WebSocket Manager<br/>status + chunk streaming"]
    DB[("MongoDB<br/>optional persistence")]
  end

  subgraph ExternalAPIs["External Services"]
    TAV["Tavily Search API"]
    GMAPS["Google Maps API"]
    LLM1["Gemini 2.0 Flash"]
    LLM2["OpenAI GPT-4.1-mini"]
    LLM3["OpenAI gpt-4o-mini-search-preview"]
    LLM4["OpenAI o4-mini-deep-research"]
  end

  A -- "submit company" --> HTTP
  HTTP --> QG --> COL
  COL --> CA
  COL --> IA
  COL --> FA
  COL --> NS
  CA --> CUR
  IA --> CUR
  FA --> CUR
  NS --> CUR
  CUR -- "filtered docs" --> BR
  BR --> LLM1
  BR --> ED
  ED --> LLM2
  ED --> LLM3
  ED --> LLM4
  CUR -->|stats| WSMgr
  BR -->|category status| WSMgr
  ED -->|report chunks| WSMgr
  WSMgr <--> WS
  ED --> DB
  CUR --> TAV
  A -. "map embeds" .-> GMAPS
