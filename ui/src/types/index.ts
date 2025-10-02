export type ResearchStatusType = {
  step: string;
  message: string;
};

// Competitor analysis types
export type CompetitorInsight = {
  text: string;
  citation: string;
};

export type CompetitorStructuredData = {
  product_directions: CompetitorInsight[];
  technology_leverage: CompetitorInsight[];
  positioning_insights: CompetitorInsight[];
  competitive_matrix: {
    companies: string[];
    comparison_criteria: string[];
    scores: { [key: string]: any };
    insights: string[];
  };
  summary: {
    total_insights: number;
    product_directions_count: number;
    technology_leverage_count: number;
    positioning_insights_count: number;
  };
};

export type CompetitorAnalysis = {
  company: string;
  competitor: string;
  raw_content: string;
  structured_data: CompetitorStructuredData;
  metrics: {
    analysis_depth: string;
    technology_focus: number;
    product_focus: number;
    competitive_insights_quality: string;
  };
  generated_at: string;
  analysis_quality: {
    total_insights: number;
    analysis_depth: string;
    quality_rating: string;
    focus_ratios: {
      technology_focus: number;
      product_focus: number;
    };
  };
};

export type CompetitorAnalyses = {
  [key: string]: CompetitorAnalysis;
};

export type ResearchOutput = {
  summary: string;
  details: {
    report_content: string;
    report?: string;  // Enhanced API returns report field
    competitor_analyses?: CompetitorAnalyses;
  };
};

export type DocCount = {
  initial: number;
  kept: number;
};

export type DocCounts = {
  [key: string]: DocCount;
};

export type EnrichmentCounts = {
  company: { total: number; enriched: number };
  industry: { total: number; enriched: number };
  financial: { total: number; enriched: number };
  news: { total: number; enriched: number };
};

export type ResearchState = {
  status: string;
  message: string;
  queries: Array<{
    text: string;
    number: number;
    category: string;
  }>;
  streamingQueries: {
    [key: string]: {
      text: string;
      number: number;
      category: string;
      isComplete: boolean;
    };
  };
  briefingStatus: {
    company: boolean;
    industry: boolean;
    financial: boolean;
    news: boolean;
  };
  enrichmentCounts?: EnrichmentCounts;
  docCounts?: DocCounts;
};

export type GlassStyle = {
  base: string;
  card: string;
  input: string;
};

export type AnimationStyle = {
  fadeIn: string;
  writing: string;
  colorTransition: string;
};

export type ResearchStatusProps = {
  status: ResearchStatusType | null;
  error: string | null;
  isComplete: boolean;
  currentPhase: 'search' | 'enrichment' | 'briefing' | 'complete' | null;
  isResetting: boolean;
  glassStyle: GlassStyle;
  loaderColor: string;
  statusRef: React.RefObject<HTMLDivElement>;
};

// 3C Analysis Types
export type AnalysisType = 'company_research' | '3c_analysis';

export type MarketResearchRequest = {
  analysis_type: AnalysisType;
  analysis_depth?: 'comprehensive' | 'focused' | 'quick';
  target_market: string;
  market_segment?: string;
  company?: string;
  company_url?: string;
  industry?: string;
  hq_location?: string;
  selected_agents?: string[];
  enable_parallel_execution?: boolean;
};

export type AgentType = 
  | 'consumer_analysis'
  | 'trend_analysis'
  | 'competitor_analysis'
  | 'swot_analysis'
  | 'customer_mapping';

export type AnalysisDepth = 'comprehensive' | 'focused' | 'quick';

export type AgentPerformanceMetrics = {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying';
  startTime?: Date;
  endTime?: Date;
  duration?: number; // in milliseconds
  progress: number; // 0-100
  dataPointsCollected?: number;
  qualityScore?: number; // 0-1
  errorCount?: number;
  retryCount?: number;
  lastError?: string;
};

export type AgentError = {
  agentId: string;
  phase: string;
  message: string;
  timestamp: Date;
  severity: 'warning' | 'error' | 'critical';
  retryable: boolean;
};

export type ThreeCAnalysisState = {
  status: string;
  message: string;
  currentStep: string;
  progress: number;
  analysisType: AnalysisType;
  targetMarket: string;
  selectedAgents: string[];
  agentPerformance: Record<string, AgentPerformanceMetrics>;
  agentErrors: AgentError[];
  consumerInsights: Array<{
    insight: string;
    confidence: number;
    source: string;
    agentId?: string;
  }>;
  painPoints: string[];
  customerPersonas: Array<{
    name: string;
    description: string;
    characteristics: string[];
  }>;
  marketTrends: Array<{
    trend: string;
    confidence: number;
    source: string;
    agentId?: string;
  }>;
  trendPredictions: Array<{
    title: string;
    description: string;
    timeHorizon: string;
  }>;
  competitorAnalysis?: {
    competitors: Array<{
      name: string;
      marketShare?: number;
      strengths: string[];
      weaknesses: string[];
      positioning: string;
    }>;
    competitiveMatrix?: {
      criteria: string[];
      scores: Record<string, any>;
    };
    marketGaps: string[];
  };
  swotAnalysis?: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  customerMapping?: {
    journeyStages: Array<{
      stage: string;
      touchpoints: string[];
      painPoints: string[];
      opportunities: string[];
    }>;
    segments: Array<{
      name: string;
      size: string;
      characteristics: string[];
    }>;
  };
  opportunities: Array<{
    title: string;
    description: string;
    priority: string;
    recommendations: string[];
  }>;
  whiteSpaces: Array<{
    title: string;
    description: string;
    marketGap: string;
  }>;
  recommendations: string[];
  analysisComplete: boolean;
};

export type ThreeCProgressPhase = 
  | 'query_generation'
  | 'data_collection' 
  | 'data_curation'
  | 'consumer_analysis'
  | 'trend_analysis'
  | 'competitor_analysis'
  | 'swot_analysis'
  | 'customer_mapping'
  | 'opportunity_analysis'
  | 'synthesis'
  | 'report_generation'
  | 'complete';

// Report sharing types
export type SharedReport = {
  id: string;
  title: string;
  content: string;
  analysisType: string;
  targetMarket: string;
  generatedAt: string;
  expiresAt?: string;
  isPublic: boolean;
};

export type ReportExportFormat = 'markdown' | 'html' | 'pdf';

export type ReportViewerProps = {
  report: string;
  reportTitle?: string;
  analysisType?: string;
  targetMarket?: string;
  generatedAt?: string;
  jobId?: string;
}; 