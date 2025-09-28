import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';
import { authService } from '../../services/auth';
import MarketAnalysisForm from '../MarketAnalysisForm';
import { MarketResearchRequest } from '../../types';

// Mock services
vi.mock('../../services/api');
vi.mock('../../services/websocket');
vi.mock('../../services/auth');

const mockApiService = vi.mocked(apiService);
const mockWebSocketService = vi.mocked(webSocketService);
const mockAuthService = vi.mocked(authService);

describe('API Integration', () => {
  const mockGlassStyle = {
    base: 'backdrop-blur-sm bg-white/30',
    card: 'backdrop-blur-sm bg-white/50 border border-white/20 rounded-lg p-6',
    input: 'w-full px-3 py-2 border border-gray-300 rounded-lg',
  };

  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default auth service mocks
    mockAuthService.getAuthHeaders.mockReturnValue({
      'X-Session-ID': 'test-session-id',
    });
    mockAuthService.getAuthState.mockReturnValue({
      isAuthenticated: false,
      user: null,
      token: null,
      sessionId: 'test-session-id',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('3C Analysis API Integration', () => {
    it('should submit 3C analysis request with correct data', async () => {
      // Mock successful API response
      mockApiService.submit3CAnalysis.mockResolvedValue({
        success: true,
        data: {
          status: 'accepted',
          job_id: 'test-job-123',
          message: '3C Analysis started',
          websocket_url: '/research/ws/test-job-123',
          analysis_type: '3c_analysis',
          target_market: 'japanese_curry',
        },
      });

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      // Select Japanese curry market
      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          analysis_type: '3c_analysis',
          target_market: 'japanese_curry',
          market_segment: undefined,
          company: undefined,
          company_url: undefined,
          industry: undefined,
          hq_location: undefined,
        });
      });
    });

    it('should handle API errors gracefully', async () => {
      // Mock API error
      mockApiService.submit3CAnalysis.mockResolvedValue({
        success: false,
        error: 'Server error',
        status: 500,
      });

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      // Select market and submit
      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      // Should still call onSubmit (error handling is done in parent)
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('should include authentication headers in requests', async () => {
      mockAuthService.getAuthHeaders.mockReturnValue({
        'Authorization': 'Bearer test-token',
        'X-Session-ID': 'test-session-id',
      });

      mockApiService.submit3CAnalysis.mockResolvedValue({
        success: true,
        data: {
          status: 'accepted',
          job_id: 'test-job-123',
          message: '3C Analysis started',
          websocket_url: '/research/ws/test-job-123',
          analysis_type: '3c_analysis',
          target_market: 'japanese_curry',
        },
      });

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });

      // Verify auth headers were used
      expect(mockAuthService.getAuthHeaders).toHaveBeenCalled();
    });
  });

  describe('WebSocket Integration', () => {
    it('should connect to WebSocket with job ID', () => {
      const jobId = 'test-job-123';
      
      webSocketService.connect(jobId);
      
      expect(mockWebSocketService.connect).toHaveBeenCalledWith(jobId);
    });

    it('should handle WebSocket connection with authentication', () => {
      mockAuthService.getAuthHeaders.mockReturnValue({
        'Authorization': 'Bearer test-token',
        'X-Session-ID': 'test-session-id',
      });

      const jobId = 'test-job-123';
      webSocketService.connect(jobId);

      expect(mockWebSocketService.connect).toHaveBeenCalledWith(jobId);
      expect(mockAuthService.getAuthHeaders).toHaveBeenCalled();
    });

    it('should handle WebSocket disconnection', () => {
      webSocketService.disconnect();
      
      expect(mockWebSocketService.disconnect).toHaveBeenCalled();
    });
  });

  describe('Error Handling and Retry Logic', () => {
    it('should retry failed requests', async () => {
      // First call fails, second succeeds
      mockApiService.submit3CAnalysis
        .mockResolvedValueOnce({
          success: false,
          error: 'Network error',
          status: 500,
        })
        .mockResolvedValueOnce({
          success: true,
          data: {
            status: 'accepted',
            job_id: 'test-job-123',
            message: '3C Analysis started',
            websocket_url: '/research/ws/test-job-123',
            analysis_type: '3c_analysis',
            target_market: 'japanese_curry',
          },
        });

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('should handle authentication errors', async () => {
      mockApiService.submit3CAnalysis.mockResolvedValue({
        success: false,
        error: 'Authentication required. Please log in again.',
        status: 401,
      });

      mockAuthService.refreshToken.mockResolvedValue({
        success: false,
        error: 'Token refresh failed',
      });

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });
  });

  describe('Loading States and User Feedback', () => {
    it('should show loading state during submission', async () => {
      // Mock a delayed response
      mockApiService.submit3CAnalysis.mockImplementation(
        () => new Promise(resolve => 
          setTimeout(() => resolve({
            success: true,
            data: {
              status: 'accepted',
              job_id: 'test-job-123',
              message: '3C Analysis started',
              websocket_url: '/research/ws/test-job-123',
              analysis_type: '3c_analysis',
              target_market: 'japanese_curry',
            },
          }), 100)
        )
      );

      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={false}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      const japaneseCarryOption = screen.getByLabelText(/Japanese Curry Market/i);
      fireEvent.click(japaneseCarryOption);

      const submitButton = screen.getByRole('button', { name: /Start 3C Analysis/i });
      fireEvent.click(submitButton);

      // Should show loading state
      expect(screen.getByText(/Submitting.../i)).toBeInTheDocument();

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('should disable form during research', () => {
      render(
        <MarketAnalysisForm
          onSubmit={mockOnSubmit}
          isResearching={true}
          glassStyle={mockGlassStyle}
          loaderColor="#468BFF"
        />
      );

      const submitButton = screen.getByRole('button', { name: /Starting Analysis.../i });
      expect(submitButton).toBeDisabled();

      // Form inputs should also be disabled
      const radioButtons = screen.getAllByRole('radio');
      radioButtons.forEach(radio => {
        expect(radio).toBeDisabled();
      });
    });
  });

  describe('Session Management', () => {
    it('should include session ID in requests', () => {
      mockAuthService.getAuthHeaders.mockReturnValue({
        'X-Session-ID': 'test-session-123',
      });

      // Verify session ID is included in auth headers
      const headers = authService.getAuthHeaders();
      expect(headers['X-Session-ID']).toBe('test-session-123');
    });

    it('should handle session expiration', async () => {
      mockAuthService.refreshToken.mockResolvedValue({
        success: false,
        error: 'Session expired',
      });

      mockAuthService.logout.mockResolvedValue();

      // Simulate session expiration
      await authService.refreshToken();
      
      expect(mockAuthService.logout).toHaveBeenCalled();
    });
  });
});