import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ResultsDashboard from '../ResultsDashboard';
import { ThreeCAnalysisState, GlassStyle } from '../../types';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the external dependencies
vi.mock('jspdf', () => ({
  default: vi.fn().mockImplementation(() => ({
    internal: {
      pageSize: {
        getWidth: () => 210,
        getHeight: () => 297,
      },
    },
    addImage: vi.fn(),
    save: vi.fn(),
  })),
}));

vi.mock('html2canvas', () => ({
  default: vi.fn().mockResolvedValue({
    width: 800,
    height: 600,
    toDataURL: () => 'data:image/png;base64,mock-image-data',
  }),
}));

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-blob-url');
global.URL.revokeObjectURL = vi.fn();

describe('Report Integration', () => {
  const mockAnalysisState: ThreeCAnalysisState = {
    status: 'complete',
    message: 'Analysis complete',
    currentStep: 'complete',
    progress: 100,
    analysisType: '3c_analysis',
    targetMarket: 'Japanese Curry Market',
    consumerInsights: [
      {
        insight: 'Consumers prefer mild curry flavors',
        confidence: 0.85,
        source: 'Social media analysis',
      },
    ],
    painPoints: ['Limited healthy options', 'High sodium content'],
    customerPersonas: [
      {
        name: 'Health-conscious Millennial',
        description: 'Young professional seeking healthy convenience food',
        characteristics: ['Health-focused', 'Time-constrained', 'Quality-oriented'],
      },
    ],
    marketTrends: [
      {
        trend: 'Plant-based curry alternatives growing',
        confidence: 0.78,
        source: 'Industry reports',
      },
    ],
    trendPredictions: [
      {
        title: 'Premium curry segment expansion',
        description: 'Premium curry products expected to grow 15% annually',
        timeHorizon: '2-3 years',
      },
    ],
    opportunities: [
      {
        title: 'Healthy curry line',
        description: 'Develop low-sodium, organic curry products',
        priority: 'high',
        recommendations: ['Partner with organic suppliers', 'Focus on natural ingredients'],
      },
    ],
    whiteSpaces: [
      {
        title: 'Kids-friendly curry',
        description: 'Mild curry products specifically for children',
        marketGap: 'No major brands targeting children specifically',
      },
    ],
    recommendations: [
      'Develop healthier product variants',
      'Target health-conscious consumers',
      'Expand premium product line',
    ],
    analysisComplete: true,
  };

  const mockGlassStyle: GlassStyle = {
    base: 'backdrop-blur-sm bg-white/80',
    card: 'backdrop-blur-sm bg-white/90',
    input: 'backdrop-blur-sm bg-white/70',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the report tab and switches to it', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );

    // Check that the report tab is present
    expect(screen.getByText('Full Report')).toBeInTheDocument();

    // Click on the report tab
    fireEvent.click(screen.getByText('Full Report'));

    // Check that report content is displayed
    expect(screen.getByText('Export Markdown')).toBeInTheDocument();
    expect(screen.getByText('Export HTML')).toBeInTheDocument();
    expect(screen.getByText('Export PDF')).toBeInTheDocument();
  });

  it('generates comprehensive report content', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );

    // Switch to report tab
    fireEvent.click(screen.getByText('Full Report'));

    // Check that report sections are present (using getAllByText to handle duplicates)
    expect(screen.getAllByText('Consumer Analysis')).toHaveLength(2); // One in tab, one in report
    expect(screen.getAllByText('Market Trends')).toHaveLength(2); // One in tab, one in report
    expect(screen.getAllByText('Market Opportunities')).toHaveLength(2); // One in tab, one in report

    // Check specific content (using partial text matching)
    expect(screen.getByText(/Consumers prefer mild curry flavors/)).toBeInTheDocument();
    expect(screen.getByText(/Plant-based curry alternatives growing/)).toBeInTheDocument();
    expect(screen.getByText(/Healthy curry line/)).toBeInTheDocument();
  });

  it('handles export functionality from the report tab', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );

    // Switch to report tab
    fireEvent.click(screen.getByText('Full Report'));

    // Test markdown export
    const markdownButton = screen.getByText('Export Markdown');
    fireEvent.click(markdownButton);

    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('does not show share button in report tab (no jobId)', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );

    // Switch to report tab
    fireEvent.click(screen.getByText('Full Report'));

    // Share button should not be present since no jobId is provided
    expect(screen.queryByText('Share')).not.toBeInTheDocument();
  });

  it('shows correct report title and metadata', () => {
    render(
      <ResultsDashboard
        analysisState={mockAnalysisState}
        glassStyle={mockGlassStyle}
        isResetting={false}
      />
    );

    // Switch to report tab
    fireEvent.click(screen.getByText('Full Report'));

    // Check report metadata (using getAllByText to handle duplicates)
    expect(screen.getAllByText('3C Analysis Report')).toHaveLength(2); // One in header, one in report
    expect(screen.getAllByText('Japanese Curry Market')).toHaveLength(2); // One in badge, one in report
  });
});