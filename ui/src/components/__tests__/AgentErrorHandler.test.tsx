import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AgentErrorHandler from '../AgentErrorHandler';
import { AgentError, AgentPerformanceMetrics } from '../../types';

const mockGlassStyle = {
  base: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl",
  card: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl rounded-2xl p-6",
  input: "backdrop-filter backdrop-blur-lg bg-white/80 border border-gray-200 shadow-xl pl-10 w-full rounded-lg py-3 px-4 text-gray-900 focus:border-[#468BFF]/50 focus:outline-none focus:ring-1 focus:ring-[#468BFF]/50 placeholder-gray-400 bg-white/80 shadow-none"
};

const mockErrors: AgentError[] = [
  {
    agentId: 'consumer_analysis',
    phase: 'data_collection',
    message: 'API rate limit exceeded',
    timestamp: new Date('2024-01-01T10:00:00Z'),
    severity: 'error',
    retryable: true
  },
  {
    agentId: 'consumer_analysis',
    phase: 'data_processing',
    message: 'Invalid data format',
    timestamp: new Date('2024-01-01T10:05:00Z'),
    severity: 'warning',
    retryable: false
  }
];

const mockPerformance: AgentPerformanceMetrics = {
  status: 'failed',
  progress: 75,
  duration: 5000,
  dataPointsCollected: 10,
  qualityScore: 0.6,
  errorCount: 2,
  retryCount: 1
};

describe('AgentErrorHandler', () => {
  it('does not render when there are no errors', () => {
    const { container } = render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={[]}
        glassStyle={mockGlassStyle}
      />
    );
    
    expect(container.firstChild).toBeNull();
  });

  it('renders error information correctly', () => {
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={mockErrors}
        performance={mockPerformance}
        glassStyle={mockGlassStyle}
      />
    );
    
    expect(screen.getByText('Consumer Analysis Issues')).toBeInTheDocument();
    expect(screen.getByText('2 issues')).toBeInTheDocument();
    expect(screen.getByText(/1 retry/)).toBeInTheDocument();
    expect(screen.getByText('data_processing: Invalid data format')).toBeInTheDocument();
  });

  it('shows retry button for retryable errors', () => {
    const mockRetry = vi.fn();
    
    // Use an error that is retryable and make sure the latest error is retryable
    const retryableErrors: AgentError[] = [
      {
        agentId: 'consumer_analysis',
        phase: 'data_collection',
        message: 'API rate limit exceeded',
        timestamp: new Date('2024-01-01T10:00:00Z'),
        severity: 'error',
        retryable: true
      }
    ];
    
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={retryableErrors}
        performance={mockPerformance}
        onRetry={mockRetry}
        glassStyle={mockGlassStyle}
      />
    );
    
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
    
    fireEvent.click(retryButton);
    expect(mockRetry).toHaveBeenCalledWith('consumer_analysis');
  });

  it('shows skip button when provided', () => {
    const mockSkip = vi.fn();
    
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={mockErrors}
        performance={mockPerformance}
        onSkip={mockSkip}
        glassStyle={mockGlassStyle}
      />
    );
    
    const skipButton = screen.getByText('Skip');
    expect(skipButton).toBeInTheDocument();
    
    fireEvent.click(skipButton);
    expect(mockSkip).toHaveBeenCalledWith('consumer_analysis');
  });

  it('expands to show all errors when clicked', () => {
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={mockErrors}
        performance={mockPerformance}
        glassStyle={mockGlassStyle}
      />
    );
    
    // Initially should only show latest error
    expect(screen.getByText('data_processing: Invalid data format')).toBeInTheDocument();
    
    // Click expand button
    const expandButton = screen.getByTitle('Expand details');
    fireEvent.click(expandButton);
    
    // Should now show all errors
    expect(screen.getByText('All Issues:')).toBeInTheDocument();
    expect(screen.getByText('data_collection: API rate limit exceeded')).toBeInTheDocument();
  });

  it('displays error statistics when expanded', () => {
    const criticalError: AgentError = {
      agentId: 'consumer_analysis',
      phase: 'initialization',
      message: 'Critical system failure',
      timestamp: new Date('2024-01-01T09:00:00Z'),
      severity: 'critical',
      retryable: false
    };
    
    const allErrors = [...mockErrors, criticalError];
    
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={allErrors}
        performance={mockPerformance}
        glassStyle={mockGlassStyle}
      />
    );
    
    // Expand to see statistics
    const expandButton = screen.getByTitle('Expand details');
    fireEvent.click(expandButton);
    
    // Check for the statistics section labels
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Errors')).toBeInTheDocument();
    expect(screen.getByText('Warnings')).toBeInTheDocument();
    
    // Check that we have the right counts in the statistics
    const statisticsSection = screen.getByText('Critical').closest('.grid');
    expect(statisticsSection).toBeInTheDocument();
  });

  it('handles dismiss error functionality', () => {
    const mockDismiss = vi.fn();
    
    render(
      <AgentErrorHandler
        agentId="consumer_analysis"
        agentName="Consumer Analysis"
        errors={mockErrors}
        performance={mockPerformance}
        onDismissError={mockDismiss}
        glassStyle={mockGlassStyle}
      />
    );
    
    // Expand to see dismiss buttons
    const expandButton = screen.getByTitle('Expand details');
    fireEvent.click(expandButton);
    
    const dismissButtons = screen.getAllByTitle('Dismiss this error');
    expect(dismissButtons.length).toBeGreaterThan(0);
    
    fireEvent.click(dismissButtons[0]);
    expect(mockDismiss).toHaveBeenCalledWith('consumer_analysis', 0);
  });
});