export type ResearchStatusType = {
  step: string;
  message: string;
};

export type ResearchOutput = {
  summary: string;
  details: {
    report: string;
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
  target_market: string;
  market_segment?: string;
  company?: string;
  company_url?: string;
  industry?: string;
  hq_location?: string;
};

export type ThreeCAnalysisState = {
  status: string;
  message: string;
  currentStep: string;
  progress: number;
  analysisType: AnalysisType;
  targetMarket: string;
  consumerInsights: Array<{
    insight: string;
    confidence: number;
    source: string;
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
  }>;
  trendPredictions: Array<{
    title: string;
    description: string;
    timeHorizon: string;
  }>;
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