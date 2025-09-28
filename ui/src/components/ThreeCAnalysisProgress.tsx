import React, { useState, useEffect } from 'react';
import { ThreeCAnalysisState, ThreeCProgressPhase } from '../types';

interface ThreeCAnalysisProgressProps {
  analysisState: ThreeCAnalysisState;
  currentPhase: ThreeCProgressPhase | null;
  glassStyle: {
    base: string;
    card: string;
    input: string;
  };
  loaderColor: string;
  isResetting: boolean;
  startTime?: Date;
  errors?: Array<{
    phase: string;
    message: string;
    timestamp: Date;
  }>;
  websocketConnected?: boolean;
  onRetryConnection?: () => void;
}

const ThreeCAnalysisProgress: React.FC<ThreeCAnalysisProgressProps> = ({
  analysisState,
  currentPhase,
  glassStyle,
  loaderColor,
  isResetting,
  startTime,
  errors = [],
  websocketConnected = true,
  onRetryConnection
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second for real-time elapsed time calculation
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);
  const phases: Array<{
    key: ThreeCProgressPhase;
    label: string;
    description: string;
    icon: string;
  }> = [
    {
      key: 'query_generation',
      label: 'Query Generation',
      description: 'Generating market research queries',
      icon: '🎯'
    },
    {
      key: 'data_collection',
      label: 'Data Collection',
      description: 'Collecting market research data',
      icon: '📊'
    },
    {
      key: 'data_curation',
      label: 'Data Curation',
      description: 'Filtering and curating data quality',
      icon: '🔍'
    },
    {
      key: 'consumer_analysis',
      label: 'Consumer Analysis',
      description: 'Analyzing consumer insights and behavior',
      icon: '👥'
    },
    {
      key: 'trend_analysis',
      label: 'Trend Analysis',
      description: 'Identifying market trends and predictions',
      icon: '📈'
    },
    {
      key: 'competitor_analysis',
      label: 'Competitor Analysis',
      description: 'Analyzing competitive landscape',
      icon: '🏢'
    },
    {
      key: 'opportunity_analysis',
      label: 'Opportunity Analysis',
      description: 'Identifying market opportunities',
      icon: '💡'
    },
    {
      key: 'synthesis',
      label: 'Synthesis',
      description: 'Synthesizing analysis results',
      icon: '🔄'
    },
    {
      key: 'report_generation',
      label: 'Report Generation',
      description: 'Generating comprehensive report',
      icon: '📄'
    },
    {
      key: 'complete',
      label: 'Complete',
      description: '3C Analysis completed successfully',
      icon: '✅'
    }
  ];

  const getPhaseStatus = (phase: ThreeCProgressPhase) => {
    if (!currentPhase) return 'pending';
    
    const currentIndex = phases.findIndex(p => p.key === currentPhase);
    const phaseIndex = phases.findIndex(p => p.key === phase);
    
    if (phaseIndex < currentIndex) return 'completed';
    if (phaseIndex === currentIndex) return 'active';
    return 'pending';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'active':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-400 bg-gray-100';
    }
  };

  const getProgressPercentage = () => {
    if (!currentPhase) return 0;
    const currentIndex = phases.findIndex(p => p.key === currentPhase);
    return ((currentIndex + 1) / phases.length) * 100;
  };

  const getEstimatedTimeRemaining = () => {
    if (!startTime || !currentPhase || currentPhase === 'complete') return null;
    
    const elapsedMinutes = (currentTime.getTime() - startTime.getTime()) / (1000 * 60);
    const currentIndex = phases.findIndex(p => p.key === currentPhase);
    const progress = Math.max(0.1, (currentIndex + 1) / phases.length); // Avoid division by zero
    
    if (progress === 0) return null;
    
    const estimatedTotalMinutes = elapsedMinutes / progress;
    const remainingMinutes = Math.max(0, estimatedTotalMinutes - elapsedMinutes);
    
    if (remainingMinutes < 1) return 'Less than 1 minute';
    if (remainingMinutes < 60) return `${Math.round(remainingMinutes)} minutes`;
    
    const hours = Math.floor(remainingMinutes / 60);
    const minutes = Math.round(remainingMinutes % 60);
    return `${hours}h ${minutes}m`;
  };

  const getElapsedTime = () => {
    if (!startTime) return null;
    
    const elapsedSeconds = Math.floor((currentTime.getTime() - startTime.getTime()) / 1000);
    
    if (elapsedSeconds < 60) return `${elapsedSeconds}s`;
    
    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = elapsedSeconds % 60;
    
    if (minutes < 60) return `${minutes}m ${seconds}s`;
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m ${seconds}s`;
  };

  const getPhaseProgress = (phase: ThreeCProgressPhase) => {
    const phaseIndex = phases.findIndex(p => p.key === phase);
    const currentIndex = currentPhase ? phases.findIndex(p => p.key === currentPhase) : -1;
    
    if (phaseIndex < currentIndex) return 100;
    if (phaseIndex === currentIndex) {
      // Show partial progress for current phase based on elapsed time
      const elapsedMinutes = startTime ? (currentTime.getTime() - startTime.getTime()) / (1000 * 60) : 0;
      const expectedPhaseTime = 3; // Assume 3 minutes per phase on average
      const phaseProgress = Math.min(90, (elapsedMinutes % expectedPhaseTime) / expectedPhaseTime * 100);
      return Math.max(10, phaseProgress); // Show at least 10% progress
    }
    return 0;
  };

  return (
    <div className={`${glassStyle.card} font-['DM_Sans'] ${isResetting ? 'opacity-0 transform -translate-y-4' : 'opacity-100 transform translate-y-0'} transition-all duration-500`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800">3C Analysis Progress</h3>
        <div className="flex items-center space-x-3">
          {/* WebSocket Connection Status */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${websocketConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className={`text-xs font-medium ${websocketConnected ? 'text-green-600' : 'text-red-600'}`}>
              {websocketConnected ? 'Live Updates' : 'Connection Lost'}
            </span>
            {!websocketConnected && onRetryConnection && (
              <button
                onClick={onRetryConnection}
                className="text-xs text-blue-600 hover:text-blue-800 underline font-medium"
                title="Retry WebSocket connection"
              >
                Reconnect
              </button>
            )}
          </div>
          
          {analysisState.targetMarket && (
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {analysisState.targetMarket.replace('_', ' ').toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Overall Progress</span>
          <span>{Math.round(getProgressPercentage())}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 relative overflow-hidden shadow-inner">
          <div
            className="h-4 rounded-full transition-all duration-500 ease-out relative"
            style={{
              width: `${getProgressPercentage()}%`,
              backgroundColor: loaderColor,
              boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.1)'
            }}
          >
            {/* Animated progress indicator */}
            {currentPhase && currentPhase !== 'complete' && (
              <div 
                className="absolute inset-0 bg-white/30 animate-pulse rounded-full"
                style={{ animationDuration: '2s' }}
              />
            )}
            
            {/* Progress segments for each phase */}
            <div className="absolute inset-0 flex">
              {phases.slice(0, -1).map((_, index) => (
                <div
                  key={index}
                  className="flex-1 border-r border-white/20 last:border-r-0"
                  style={{ width: `${100 / (phases.length - 1)}%` }}
                />
              ))}
            </div>
          </div>
        </div>
        
        {/* Time Information */}
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>
            {getElapsedTime() ? `Elapsed: ${getElapsedTime()}` : 'Starting...'}
          </span>
          <span>
            {getEstimatedTimeRemaining() ? `Est. remaining: ${getEstimatedTimeRemaining()}` : ''}
          </span>
        </div>
        
        {/* Current Phase Progress */}
        {currentPhase && currentPhase !== 'complete' && (
          <div className="mt-3 p-2 bg-blue-50 rounded-lg">
            <div className="flex justify-between text-xs text-blue-700 mb-1">
              <span>Current Phase: {phases.find(p => p.key === currentPhase)?.label}</span>
              <span>{Math.round(getPhaseProgress(currentPhase))}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="h-2 bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${getPhaseProgress(currentPhase)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {errors.length > 0 && (
        <div className="mb-6 p-4 bg-red-50 rounded-lg border border-red-200">
          <h4 className="font-medium text-red-800 mb-3 flex items-center justify-between">
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              Analysis Issues ({errors.length})
            </div>
            <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded-full">
              Continuing with available data
            </span>
          </h4>
          <div className="space-y-3 max-h-32 overflow-y-auto">
            {errors.slice(-5).map((error, index) => (
              <div key={index} className="text-sm border-l-2 border-red-300 pl-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="font-medium text-red-800">{error.phase}:</span>
                    <span className="text-red-700 ml-1">{error.message}</span>
                  </div>
                  <span className="text-xs text-red-500 ml-2 whitespace-nowrap">
                    {error.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
          {errors.length > 5 && (
            <div className="text-xs text-red-600 mt-2 text-center">
              ... and {errors.length - 5} more issues
            </div>
          )}
        </div>
      )}

      {/* Current Status */}
      {currentPhase && (
        <div className={`mb-6 p-4 rounded-lg border ${
          errors.length > 0 ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center space-x-3">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center text-white font-medium"
              style={{ backgroundColor: errors.length > 0 ? '#f59e0b' : loaderColor }}
            >
              {phases.find(p => p.key === currentPhase)?.icon}
            </div>
            <div className="flex-1">
              <div className="font-medium text-gray-900">
                {phases.find(p => p.key === currentPhase)?.label}
              </div>
              <div className="text-sm text-gray-600">
                {phases.find(p => p.key === currentPhase)?.description}
              </div>
              {errors.length > 0 && (
                <div className="text-xs text-yellow-700 mt-1">
                  Continuing with available data despite some issues
                </div>
              )}
            </div>
            {currentPhase !== 'complete' && (
              <div className="ml-auto">
                <div 
                  className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
                  style={{ 
                    borderColor: errors.length > 0 ? '#f59e0b' : loaderColor,
                    borderTopColor: 'transparent'
                  }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Phase List */}
      <div className="space-y-3">
        {phases.map((phase, index) => {
          const status = getPhaseStatus(phase.key);
          const isActive = status === 'active';
          const isCompleted = status === 'completed';
          const hasError = errors.some(error => error.phase === phase.key);
          const phaseProgress = getPhaseProgress(phase.key);
          
          return (
            <div
              key={phase.key}
              className={`
                flex items-center space-x-3 p-4 rounded-lg transition-all duration-300 border
                ${isActive ? 'bg-blue-50 border-blue-200 shadow-md' : ''}
                ${isCompleted ? 'bg-green-50 border-green-200 shadow-sm' : ''}
                ${hasError ? 'bg-red-50 border-red-200 shadow-sm' : ''}
                ${!isActive && !isCompleted && !hasError ? 'bg-gray-50 border-gray-200 hover:bg-gray-100' : ''}
              `}
            >
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center text-lg font-medium relative
                ${hasError ? 'bg-red-100 text-red-600' : getStatusColor(status)}
                ${isActive && !hasError ? 'animate-pulse' : ''}
              `}>
                {hasError ? '⚠️' : isCompleted ? '✅' : isActive ? '⏳' : phase.icon}
                
                {/* Real-time pulse for active phase */}
                {isActive && !hasError && (
                  <div className="absolute inset-0 rounded-full bg-blue-400 animate-ping opacity-20"></div>
                )}
                
                {/* Progress ring for active phase */}
                {isActive && !hasError && (
                  <svg className="absolute inset-0 w-10 h-10 transform -rotate-90">
                    <circle
                      cx="20"
                      cy="20"
                      r="18"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      className="text-blue-200"
                    />
                    <circle
                      cx="20"
                      cy="20"
                      r="18"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 18}`}
                      strokeDashoffset={`${2 * Math.PI * 18 * (1 - phaseProgress / 100)}`}
                      className="text-blue-500 transition-all duration-500"
                    />
                  </svg>
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className={`
                  font-medium flex items-center justify-between
                  ${hasError ? 'text-red-800' : isCompleted ? 'text-green-800' : isActive ? 'text-blue-800' : 'text-gray-500'}
                `}>
                  <div className="flex items-center">
                    {phase.label}
                    {isActive && !hasError && (
                      <div className="ml-2 flex space-x-1">
                        <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    )}
                  </div>
                  
                  {/* Phase progress percentage */}
                  {isActive && !hasError && (
                    <span className="text-xs font-normal text-blue-600">
                      {Math.round(phaseProgress)}%
                    </span>
                  )}
                </div>
                
                <div className={`
                  text-sm mt-1
                  ${hasError ? 'text-red-600' : isCompleted ? 'text-green-600' : isActive ? 'text-blue-600' : 'text-gray-400'}
                `}>
                  {hasError ? 'Completed with issues' : phase.description}
                </div>
                
                {/* Phase progress bar for active phase */}
                {isActive && !hasError && (
                  <div className="mt-2">
                    <div className="w-full bg-blue-200 rounded-full h-1.5">
                      <div
                        className="h-1.5 bg-blue-500 rounded-full transition-all duration-500"
                        style={{ width: `${phaseProgress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {/* Show specific error for this phase */}
                {hasError && (
                  <div className="text-xs text-red-500 mt-2 p-2 bg-red-100 rounded border-l-2 border-red-400">
                    {errors.find(error => error.phase === phase.key)?.message}
                  </div>
                )}
              </div>

              {/* Status indicator */}
              <div className="flex flex-col items-center space-y-1">
                <div className={`
                  text-xs font-medium px-2 py-1 rounded-full min-w-[24px] text-center
                  ${hasError ? 'bg-red-200 text-red-800' : isCompleted ? 'bg-green-200 text-green-800' : isActive ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-500'}
                `}>
                  {index + 1}
                </div>
                
                {/* Status icon */}
                <div className="text-xs">
                  {isCompleted && '✓'}
                  {hasError && '⚠'}
                  {isActive && !hasError && '⏳'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Analysis Summary */}
      {analysisState.analysisComplete && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <h4 className="font-medium text-green-800 mb-2">Analysis Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="text-center">
              <div className="font-semibold text-green-700">{analysisState.consumerInsights.length}</div>
              <div className="text-green-600">Consumer Insights</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-green-700">{analysisState.marketTrends.length}</div>
              <div className="text-green-600">Market Trends</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-green-700">{analysisState.opportunities.length}</div>
              <div className="text-green-600">Opportunities</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-green-700">{analysisState.recommendations.length}</div>
              <div className="text-green-600">Recommendations</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreeCAnalysisProgress;