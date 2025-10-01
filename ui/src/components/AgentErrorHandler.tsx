import React, { useState } from 'react';
import { AlertCircle, RefreshCw, SkipForward, ChevronDown, ChevronUp, Clock, Zap } from 'lucide-react';
import { AgentError, AgentPerformanceMetrics } from '../types';

interface AgentErrorHandlerProps {
  agentId: string;
  agentName: string;
  errors: AgentError[];
  performance?: AgentPerformanceMetrics;
  onRetry?: (agentId: string) => void;
  onSkip?: (agentId: string) => void;
  onDismissError?: (agentId: string, errorIndex: number) => void;
  glassStyle: {
    base: string;
    card: string;
    input: string;
  };
}

const AgentErrorHandler: React.FC<AgentErrorHandlerProps> = ({
  agentId,
  agentName,
  errors,
  performance,
  onRetry,
  onSkip,
  onDismissError,
  glassStyle
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  if (errors.length === 0) return null;

  const criticalErrors = errors.filter(error => error.severity === 'critical');
  const regularErrors = errors.filter(error => error.severity === 'error');
  const warnings = errors.filter(error => error.severity === 'warning');

  const latestError = errors[errors.length - 1];
  const canRetry = latestError?.retryable && onRetry && performance?.status !== 'running';
  const canSkip = onSkip && performance?.status !== 'completed';

  const handleRetry = async () => {
    if (!onRetry || isRetrying) return;
    
    setIsRetrying(true);
    try {
      await onRetry(agentId);
    } finally {
      setIsRetrying(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-700 bg-red-100 border-red-300';
      case 'error':
        return 'text-orange-700 bg-orange-100 border-orange-300';
      case 'warning':
        return 'text-yellow-700 bg-yellow-100 border-yellow-300';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-300';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-orange-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className={`${glassStyle.card} border-l-4 ${
      criticalErrors.length > 0 ? 'border-l-red-500' :
      regularErrors.length > 0 ? 'border-l-orange-500' :
      'border-l-yellow-500'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            criticalErrors.length > 0 ? 'bg-red-100 text-red-600' :
            regularErrors.length > 0 ? 'bg-orange-100 text-orange-600' :
            'bg-yellow-100 text-yellow-600'
          }`}>
            {getSeverityIcon(latestError.severity)}
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{agentName} Issues</h4>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>{errors.length} issue{errors.length !== 1 ? 's' : ''}</span>
              {performance?.retryCount && performance.retryCount > 0 && (
                <span>• {performance.retryCount} retr{performance.retryCount === 1 ? 'y' : 'ies'}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Action Buttons */}
          {canRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className={`
                flex items-center space-x-1 px-3 py-1 rounded text-sm font-medium transition-colors
                ${isRetrying 
                  ? 'bg-gray-100 text-gray-500 cursor-not-allowed' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }
              `}
              title="Retry this agent"
            >
              {isRetrying ? (
                <>
                  <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                  <span>Retrying...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3 h-3" />
                  <span>Retry</span>
                </>
              )}
            </button>
          )}

          {canSkip && (
            <button
              onClick={() => onSkip?.(agentId)}
              className="flex items-center space-x-1 px-3 py-1 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              title="Skip this agent and continue"
            >
              <SkipForward className="w-3 h-3" />
              <span>Skip</span>
            </button>
          )}

          {/* Expand/Collapse Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-gray-100 transition-colors"
            title={isExpanded ? 'Collapse details' : 'Expand details'}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Latest Error Summary */}
      <div className={`p-3 rounded border ${getSeverityColor(latestError.severity)}`}>
        <div className="flex items-start space-x-2">
          {getSeverityIcon(latestError.severity)}
          <div className="flex-1">
            <div className="font-medium text-sm">
              {latestError.phase}: {latestError.message}
            </div>
            <div className="text-xs mt-1 flex items-center space-x-2">
              <Clock className="w-3 h-3" />
              <span>{latestError.timestamp.toLocaleTimeString()}</span>
              {latestError.retryable && (
                <>
                  <span>•</span>
                  <div className="flex items-center space-x-1">
                    <Zap className="w-3 h-3" />
                    <span>Retryable</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded Error Details */}
      {isExpanded && errors.length > 1 && (
        <div className="mt-3 space-y-2">
          <div className="text-sm font-medium text-gray-700">All Issues:</div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {errors.map((error, index) => (
              <div
                key={index}
                className={`p-2 rounded border text-sm ${getSeverityColor(error.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-2 flex-1">
                    {getSeverityIcon(error.severity)}
                    <div className="flex-1">
                      <div className="font-medium">
                        {error.phase}: {error.message}
                      </div>
                      <div className="text-xs mt-1 flex items-center space-x-2">
                        <Clock className="w-3 h-3" />
                        <span>{error.timestamp.toLocaleTimeString()}</span>
                        <span className="capitalize">• {error.severity}</span>
                        {error.retryable && (
                          <>
                            <span>• Retryable</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {onDismissError && (
                    <button
                      onClick={() => onDismissError(agentId, index)}
                      className="ml-2 text-xs text-gray-500 hover:text-gray-700"
                      title="Dismiss this error"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Statistics */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center text-sm">
            <div>
              <div className="font-medium text-red-600">{criticalErrors.length}</div>
              <div className="text-xs text-gray-600">Critical</div>
            </div>
            <div>
              <div className="font-medium text-orange-600">{regularErrors.length}</div>
              <div className="text-xs text-gray-600">Errors</div>
            </div>
            <div>
              <div className="font-medium text-yellow-600">{warnings.length}</div>
              <div className="text-xs text-gray-600">Warnings</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentErrorHandler;