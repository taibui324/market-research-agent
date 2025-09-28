import React from 'react';

interface LoadingStateProps {
  message?: string;
  submessage?: string;
  progress?: number;
  showProgress?: boolean;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
  submessage,
  progress,
  showProgress = false,
  size = 'medium',
  color = '#468BFF',
  className = '',
}) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
  };

  const textSizeClasses = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg',
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-4 ${className}`}>
      {/* Spinner */}
      <div className="relative">
        <div
          className={`${sizeClasses[size]} border-2 border-gray-200 rounded-full animate-spin`}
          style={{
            borderTopColor: color,
            borderRightColor: color,
          }}
        />
        
        {/* Pulse effect */}
        <div
          className={`absolute inset-0 ${sizeClasses[size]} rounded-full animate-ping opacity-20`}
          style={{ backgroundColor: color }}
        />
      </div>

      {/* Progress bar */}
      {showProgress && typeof progress === 'number' && (
        <div className="w-full max-w-xs">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-300 ease-out"
              style={{
                width: `${Math.min(100, Math.max(0, progress))}%`,
                backgroundColor: color,
              }}
            />
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="text-center space-y-1">
        <div className={`font-medium text-gray-800 ${textSizeClasses[size]}`}>
          {message}
        </div>
        {submessage && (
          <div className={`text-gray-600 ${size === 'large' ? 'text-base' : 'text-sm'}`}>
            {submessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default LoadingState;