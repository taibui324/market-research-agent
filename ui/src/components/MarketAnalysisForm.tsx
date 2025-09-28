import React, { useState } from 'react';
import { MarketResearchRequest } from '../types';

interface MarketAnalysisFormProps {
  onSubmit: (data: MarketResearchRequest) => void;
  isResearching: boolean;
  glassStyle: {
    base: string;
    card: string;
    input: string;
  };
  loaderColor: string;
}

const MarketAnalysisForm: React.FC<MarketAnalysisFormProps> = ({
  onSubmit,
  isResearching,
  glassStyle,
  loaderColor
}) => {
  const [formData, setFormData] = useState({
    target_market: 'japanese_curry',
    market_segment: '',
    company: '',
    company_url: '',
    industry: '',
    hq_location: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const marketOptions = [
    { value: 'japanese_curry', label: 'Japanese Curry Market', description: 'Curry rice, curry roux, instant curry products' },
    { value: 'ramen_noodles', label: 'Ramen Noodles Market', description: 'Instant ramen, fresh ramen, ramen restaurants' },
    { value: 'japanese_snacks', label: 'Japanese Snacks Market', description: 'Pocky, Kit Kat, rice crackers, mochi' },
    { value: 'japanese_beverages', label: 'Japanese Beverages Market', description: 'Green tea, sake, soft drinks, energy drinks' },
    { value: 'japanese_desserts', label: 'Japanese Desserts Market', description: 'Wagashi, ice cream, cakes, traditional sweets' },
    { value: 'japanese_cosmetics', label: 'Japanese Cosmetics Market', description: 'Skincare, makeup, beauty products' },
    { value: 'japanese_electronics', label: 'Japanese Electronics Market', description: 'Consumer electronics, gaming, appliances' },
    { value: 'custom', label: 'Custom Market (specify below)', description: 'Define your own market for analysis' }
  ];

  const industryOptions = [
    'Food & Beverage',
    'Consumer Goods',
    'Technology',
    'Healthcare',
    'Retail',
    'Manufacturing',
    'Automotive',
    'Entertainment',
    'Financial Services',
    'Telecommunications'
  ];

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.target_market.trim()) {
      newErrors.target_market = 'Please select a target market for analysis';
    }

    if (formData.target_market === 'custom' && !formData.market_segment.trim()) {
      newErrors.market_segment = 'Please specify the custom market name (e.g., "organic tea market")';
    }

    if (formData.target_market === 'custom' && formData.market_segment.trim().length < 3) {
      newErrors.market_segment = 'Market name must be at least 3 characters long';
    }

    if (formData.company_url && !isValidUrl(formData.company_url)) {
      newErrors.company_url = 'Please enter a valid URL (e.g., https://example.com)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (url: string) => {
    try {
      new URL(url.startsWith('http') ? url : `https://${url}`);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const finalTargetMarket = formData.target_market === 'custom' 
      ? formData.market_segment 
      : formData.target_market;

    const requestData: MarketResearchRequest = {
      analysis_type: '3c_analysis',
      target_market: finalTargetMarket,
      market_segment: formData.market_segment || undefined,
      company: formData.company || undefined,
      company_url: formData.company_url || undefined,
      industry: formData.industry || undefined,
      hq_location: formData.hq_location || undefined
    };

    onSubmit(requestData);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }

    // Real-time validation for specific fields
    if (field === 'company_url' && value && !isValidUrl(value)) {
      setErrors(prev => ({ ...prev, company_url: 'Please enter a valid URL' }));
    }

    if (field === 'market_segment' && formData.target_market === 'custom' && value.length > 0 && value.length < 3) {
      setErrors(prev => ({ ...prev, market_segment: 'Market name must be at least 3 characters long' }));
    }
  };

  return (
    <div className={`${glassStyle.card} font-['DM_Sans']`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-6">3C Market Analysis Configuration</h3>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Target Market Selection */}
        <div>
          <label htmlFor="target_market" className="block text-sm font-medium text-gray-700 mb-2">
            Target Market *
          </label>
          <div className="space-y-3">
            {marketOptions.map(option => (
              <label
                key={option.value}
                className={`
                  flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-all duration-200
                  ${formData.target_market === option.value 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }
                  ${isResearching ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <input
                  type="radio"
                  name="target_market"
                  value={option.value}
                  checked={formData.target_market === option.value}
                  onChange={(e) => handleInputChange('target_market', e.target.value)}
                  disabled={isResearching}
                  className="mt-1 w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{option.label}</div>
                  <div className="text-sm text-gray-600 mt-1">{option.description}</div>
                </div>
              </label>
            ))}
          </div>
          {errors.target_market && (
            <p className="mt-1 text-sm text-red-600">{errors.target_market}</p>
          )}
        </div>

        {/* Custom Market Input */}
        {formData.target_market === 'custom' && (
          <div>
            <label htmlFor="market_segment" className="block text-sm font-medium text-gray-700 mb-2">
              Custom Market Name *
            </label>
            <input
              type="text"
              id="market_segment"
              value={formData.market_segment}
              onChange={(e) => handleInputChange('market_segment', e.target.value)}
              placeholder="e.g., organic tea market, premium sake market"
              disabled={isResearching}
              className={`${glassStyle.input} ${errors.market_segment ? 'border-red-300' : ''}`}
            />
            {errors.market_segment && (
              <p className="mt-1 text-sm text-red-600">{errors.market_segment}</p>
            )}
          </div>
        )}

        {/* Market Segment */}
        {formData.target_market !== 'custom' && (
          <div>
            <label htmlFor="market_segment" className="block text-sm font-medium text-gray-700 mb-2">
              Market Segment (Optional)
            </label>
            <input
              type="text"
              id="market_segment"
              value={formData.market_segment}
              onChange={(e) => handleInputChange('market_segment', e.target.value)}
              placeholder="e.g., premium segment, budget segment, health-conscious segment"
              disabled={isResearching}
              className={glassStyle.input}
            />
            <p className="mt-1 text-xs text-gray-500">
              Specify a particular segment within the market for focused analysis
            </p>
          </div>
        )}

        {/* Optional Company Context */}
        <div className="border-t pt-6">
          <h4 className="text-md font-medium text-gray-800 mb-4">Company Context (Optional)</h4>
          <p className="text-sm text-gray-600 mb-4">
            Provide company information to get more targeted insights and competitive positioning
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                Company Name
              </label>
              <input
                type="text"
                id="company"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                placeholder="e.g., House Foods, Glico"
                disabled={isResearching}
                className={glassStyle.input}
              />
            </div>

            <div>
              <label htmlFor="company_url" className="block text-sm font-medium text-gray-700 mb-2">
                Company Website
              </label>
              <input
                type="url"
                id="company_url"
                value={formData.company_url}
                onChange={(e) => handleInputChange('company_url', e.target.value)}
                placeholder="https://example.com"
                disabled={isResearching}
                className={glassStyle.input}
              />
            </div>

            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <select
                id="industry"
                value={formData.industry}
                onChange={(e) => handleInputChange('industry', e.target.value)}
                disabled={isResearching}
                className={glassStyle.input}
              >
                <option value="">Select an industry (optional)</option>
                {industryOptions.map(industry => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="hq_location" className="block text-sm font-medium text-gray-700 mb-2">
                Headquarters Location
              </label>
              <input
                type="text"
                id="hq_location"
                value={formData.hq_location}
                onChange={(e) => handleInputChange('hq_location', e.target.value)}
                placeholder="e.g., Tokyo, Japan"
                disabled={isResearching}
                className={glassStyle.input}
              />
            </div>
          </div>
        </div>

        {/* Analysis Preview */}
        {formData.target_market && formData.target_market !== 'custom' && (
          <div className="border-t pt-6">
            <h4 className="text-md font-medium text-gray-800 mb-3">Analysis Preview</h4>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-800 mb-2">
                <strong>Target Market:</strong> {marketOptions.find(opt => opt.value === formData.target_market)?.label}
              </p>
              <p className="text-sm text-blue-700">
                This analysis will examine customer behavior, market trends, competitive landscape, and identify opportunities in the {formData.target_market.replace('_', ' ')} market.
              </p>
              {formData.market_segment && (
                <p className="text-sm text-blue-700 mt-2">
                  <strong>Focus:</strong> {formData.market_segment} segment
                </p>
              )}
              {formData.company && (
                <p className="text-sm text-blue-700 mt-2">
                  <strong>Company Context:</strong> Analysis will include competitive positioning for {formData.company}
                </p>
              )}
            </div>
          </div>
        )}



        {/* Submit Button */}
        <div className="flex justify-between items-center pt-6">
          <div className="text-sm text-gray-500">
            <p>Analysis typically takes 3-5 minutes</p>
            <p>You'll receive real-time progress updates</p>

          </div>
          <button
            type="submit"
            disabled={isResearching || !formData.target_market}
            className={`
              px-8 py-3 rounded-lg font-medium text-white transition-all duration-300
              ${isResearching || !formData.target_market
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transform hover:scale-105 shadow-lg'
              }
            `}
          >
            {isResearching ? (
              <div className="flex items-center space-x-2">
                <div 
                  className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
                  style={{ borderTopColor: loaderColor }}
                ></div>
                <span>Starting Analysis...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <span>Start 3C Analysis</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default MarketAnalysisForm;