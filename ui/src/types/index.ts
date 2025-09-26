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