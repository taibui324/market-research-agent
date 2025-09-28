import React from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { ResearchStatusProps } from '../types';

const ResearchStatus: React.FC<ResearchStatusProps> = ({
  status,
  error,
  isComplete,
  currentPhase,
  isResetting,
  glassStyle,
  loaderColor,
  statusRef
}) => {
  const glassCardStyle = `${glassStyle.base} rounded-2xl p-6`;
  const fadeInAnimation = "transition-all duration-300 ease-in-out";

  if (!status) return null;

  const getStatusColor = () => {
    if (error) return 'text-red-600';
    if (isComplete) return 'text-green-600';
    return 'text-blue-600';
  };

  return (
    <div
      ref={statusRef}
      className={`${glassCardStyle} ${fadeInAnimation} ${
        isResetting ? 'opacity-0 transform -translate-y-4' : 'opacity-100 transform translate-y-0'
      } bg-white/80 backdrop-blur-sm border-gray-200 font-['DM_Sans']`}
    >
      <div className="flex items-center justify-between">
        <h3 className={`text-lg font-semibold ${getStatusColor()}`}>
          {error ? 'Research Error' : isComplete ? 'Research Complete' : status?.step || 'Processing'}
        </h3>
        
        {!error && !isComplete && (
          <div className="flex items-center space-x-2">
            <Loader2 
              className="animate-spin w-5 h-5" 
              style={{ stroke: loaderColor }} 
            />
          </div>
        )}
      </div>

      {status?.message && (
        <div className="mt-4">
          <p className="text-gray-600 text-sm">
            {status.message}
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 flex items-center space-x-2 text-red-600">
          <XCircle className="h-5 w-5" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {isComplete && (
        <div className="mt-4 flex items-center space-x-2 text-green-600">
          <CheckCircle2 className="h-5 w-5" />
          <span className="text-sm">Research completed successfully</span>
        </div>
      )}

      {currentPhase && !isComplete && !error && (
        <div className="mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600 capitalize">
              Current phase: {currentPhase}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchStatus;