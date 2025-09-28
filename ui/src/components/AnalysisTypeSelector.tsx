import React from 'react';
import { AnalysisType } from '../types';

interface AnalysisTypeSelectorProps {
  analysisType: AnalysisType;
  onAnalysisTypeChange: (type: AnalysisType) => void;
  glassStyle: {
    base: string;
    card: string;
    input: string;
  };
  isResearching: boolean;
}

const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  analysisType,
  onAnalysisTypeChange,
  glassStyle,
  isResearching
}) => {
  return (
    <div className={`${glassStyle.card} font-['DM_Sans']`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Analysis Type</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="radio"
            name="analysisType"
            value="company_research"
            checked={analysisType === 'company_research'}
            onChange={(e) => onAnalysisTypeChange(e.target.value as AnalysisType)}
            disabled={isResearching}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="font-medium text-gray-900">Company Research</div>
            <div className="text-sm text-gray-600">
              Comprehensive analysis of a specific company including financials, news, and industry context
            </div>
          </div>
        </label>
        
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="radio"
            name="analysisType"
            value="3c_analysis"
            checked={analysisType === '3c_analysis'}
            onChange={(e) => onAnalysisTypeChange(e.target.value as AnalysisType)}
            disabled={isResearching}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="font-medium text-gray-900">3C Market Analysis</div>
            <div className="text-sm text-gray-600">
              Strategic market analysis focusing on Customers, Company, and Competitors
            </div>
          </div>
        </label>
      </div>
    </div>
  );
};

export default AnalysisTypeSelector;