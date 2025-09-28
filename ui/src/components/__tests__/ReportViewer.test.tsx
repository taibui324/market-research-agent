import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ReportViewer from '../ReportViewer';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the external dependencies
vi.mock('jspdf', () => {
  return {
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
  };
});

vi.mock('html2canvas', () => {
  return {
    default: vi.fn().mockResolvedValue({
      width: 800,
      height: 600,
      toDataURL: () => 'data:image/png;base64,mock-image-data',
    }),
  };
});

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    createShareableReport: vi.fn().mockResolvedValue({
      success: true,
      data: {
        shareId: 'mock-share-id',
        shareUrl: 'https://example.com/shared-report/mock-share-id',
      },
    }),
  },
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-blob-url');
global.URL.revokeObjectURL = vi.fn();

describe('ReportViewer', () => {
  const mockReport = `# Test Report

## Introduction
This is a test report with **bold text** and *italic text*.

### Subsection
- Item 1
- Item 2
- Item 3

## Conclusion
This concludes the test report.`;

  const defaultProps = {
    report: mockReport,
    reportTitle: 'Test Market Research Report',
    analysisType: '3C Analysis',
    targetMarket: 'Japanese Curry Market',
    generatedAt: '2024-01-15T10:30:00Z',
    jobId: 'test-job-123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the report content correctly', () => {
    render(<ReportViewer {...defaultProps} />);
    
    expect(screen.getByText('Test Market Research Report')).toBeInTheDocument();
    expect(screen.getByText('3C Analysis')).toBeInTheDocument();
    expect(screen.getByText('Japanese Curry Market')).toBeInTheDocument();
    expect(screen.getByText('Test Report')).toBeInTheDocument();
  });

  it('displays export controls', () => {
    render(<ReportViewer {...defaultProps} />);
    
    expect(screen.getByText('Export Markdown')).toBeInTheDocument();
    expect(screen.getByText('Export HTML')).toBeInTheDocument();
    expect(screen.getByText('Export PDF')).toBeInTheDocument();
    expect(screen.getByText('Print')).toBeInTheDocument();
    expect(screen.getByText('Share')).toBeInTheDocument();
  });

  it('handles markdown export', () => {
    render(<ReportViewer {...defaultProps} />);
    
    const exportButton = screen.getByText('Export Markdown');
    fireEvent.click(exportButton);
    
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('handles HTML export', () => {
    render(<ReportViewer {...defaultProps} />);
    
    const exportButton = screen.getByText('Export HTML');
    fireEvent.click(exportButton);
    
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('handles PDF export', async () => {
    render(<ReportViewer {...defaultProps} />);
    
    const exportButton = screen.getByText('Export PDF');
    fireEvent.click(exportButton);
    
    expect(screen.getByText('Generating PDF...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Export PDF')).toBeInTheDocument();
    });
  });

  it('handles share functionality', async () => {
    render(<ReportViewer {...defaultProps} />);
    
    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);
    
    await waitFor(() => {
      expect(screen.getByText('Share Report')).toBeInTheDocument();
    });
  });

  it('does not show share button when jobId is not provided', () => {
    const propsWithoutJobId = { ...defaultProps, jobId: undefined };
    render(<ReportViewer {...propsWithoutJobId} />);
    
    expect(screen.queryByText('Share')).not.toBeInTheDocument();
  });

  it('renders markdown content with proper formatting', () => {
    render(<ReportViewer {...defaultProps} />);
    
    // Check for markdown elements
    expect(screen.getByText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Subsection')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Conclusion')).toBeInTheDocument();
  });

  it('generates proper filename with timestamp', () => {
    render(<ReportViewer {...defaultProps} />);
    
    const exportButton = screen.getByText('Export Markdown');
    fireEvent.click(exportButton);
    
    // Check that a download link was created (mocked)
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(
      expect.any(Blob)
    );
  });

  it('handles print functionality', () => {
    const mockPrint = vi.fn();
    global.print = mockPrint;
    
    render(<ReportViewer {...defaultProps} />);
    
    const printButton = screen.getByText('Print');
    fireEvent.click(printButton);
    
    expect(mockPrint).toHaveBeenCalled();
  });

  it('closes share modal when close button is clicked', async () => {
    render(<ReportViewer {...defaultProps} />);
    
    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);
    
    await waitFor(() => {
      expect(screen.getByText('Share Report')).toBeInTheDocument();
    });
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    await waitFor(() => {
      expect(screen.queryByText('Share Report')).not.toBeInTheDocument();
    });
  });
});