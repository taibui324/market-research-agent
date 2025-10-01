import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ResultsDashboard from '../ResultsDashboard';
import { ThreeCAnalysisState, GlassStyle } from '../../types';

const mockGlassStyle: GlassStyle = {
  base: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl",
  card: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl rounded-2xl p-6",
  input: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl pl-10 w-full rounded-lg py-3 px-4 text-gray-900 focus:border-[#468BFF]/50 focus:outline-none focus:ring-1 focus:ring-[#468BFF]/50 placeholder-gray-400 bg-white/80 shadow-none"
};

const mockAnalysisState: ThreeCAnalysisState = {
  status: "completed",
  message: "Analysis complete",
  currentStep: "Complete",
  progress: 100,
  analysisType: '3c_analysis',
  targetMarket: "japanese_curry",
  selectedAgents: ['consumer_analysis', 'trend_analysis', 'competitor_analysis', 'opportunity_analysis'],
  agentPerformance: {
    consumer_analysis: {
      status: 'completed',
      progress: 100,
      duration: 5000,
      dataPointsCollected: 25,
      qualityScore: 0.85,
      errorCount: 0,
      retryCount: 0
    },
    trend_analysis: {
      status: 'completed',
      progress: 100,
      duration: 4500,
      dataPointsCollected: 18,
      qualityScore: 0.9,
      errorCount: 0,
      retryCount: 0
    }
  },
  agentErrors: [],
  consumerInsights: [
    {
      insight: "Consumers prefer spicy curry",
      confidence: 0.85,
      source: "Social Media Analysis",
      agentId: "consumer_analysis"
    }
  ],
  painPoints: ["Too expensive", "Limited availability"],
  customerPersonas: [
    {
      name: "Curry Enthusiast",
      description: "Young professional who loves spicy food",
      characteristics: ["Age 25-35", "Urban", "High income"]
    }
  ],
  marketTrends: [
    {
      trend: "Growing demand for authentic Japanese curry",
      confidence: 0.9,
      source: "Market Research",
      agentId: "trend_analysis"
    }
  ],
  trendPredictions: [
    {
      title: "Premium curry market growth",
      description: "Expected 20% growth in premium segment",
      timeHorizon: "2-3 years"
    }
  ],
  opportunities: [
    {
      title: "Premium curry opportunity",
      description: "Gap in premium curry market",
      priority: "High",
      recommendations: ["Launch premium line", "Focus on quality ingredients"]
    }
  ],
  whiteSpaces: [
    {
      title: "Healthy curry options",
      description: "Limited healthy curry alternatives",
      marketGap: "Health-conscious consumers"
    }
  ],
  recommendations: ["Focus on premium segment", "Expand distribution"],
  analysisComplete: true
};

describe('ResultsDashboard', () => {
  it('renders without crashing', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    expect(screen.getByText('3C Analysis Results')).toBeInTheDocument();
  });

  it('displays all tabs', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    expect(screen.getByText('Consumer Analysis')).toBeInTheDocument();
    expect(screen.getByText('Market Trends')).toBeInTheDocument();
    expect(screen.getByText('Competitive Landscape')).toBeInTheDocument();
    expect(screen.getByText('Market Opportunities')).toBeInTheDocument();
  });

  it('shows consumer insights by default', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    expect(screen.getByText('Consumer Insights')).toBeInTheDocument();
    expect(screen.getByText('Consumers prefer spicy curry')).toBeInTheDocument();
  });

  it('switches tabs when clicked', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    // Click on Market Trends tab
    fireEvent.click(screen.getByText('Market Trends'));
    
    expect(screen.getByText('Growing demand for authentic Japanese curry')).toBeInTheDocument();
  });

  it('displays target market', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    expect(screen.getByText('JAPANESE CURRY')).toBeInTheDocument();
  });

  it('shows competitor analysis placeholder', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    // Click on Competitive Landscape tab
    fireEvent.click(screen.getByText('Competitive Landscape'));
    
    expect(screen.getByText('Competitive landscape analysis will appear here once the analysis is complete.')).toBeInTheDocument();
  });

  it('displays opportunities when tab is selected', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    // Click on Market Opportunities tab
    fireEvent.click(screen.getByText('Market Opportunities'));
    
    expect(screen.getByText('Premium curry opportunity')).toBeInTheDocument();
    expect(screen.getByText('High Priority')).toBeInTheDocument();
  });

  it('does not render when analysis is not started', () => {
    const idleState: ThreeCAnalysisState = {
      ...mockAnalysisState,
      status: 'idle',
      analysisComplete: false
    };

    const { container } = render(
      <ResultsDashboard
        analysisState={idleState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );
    
    expect(container.firstChild).toBeNull();
  });
});