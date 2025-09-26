import React from 'react';
import { CompetitorAnalysis, CompetitorAnalyses, GlassStyle, AnimationStyle } from '../types';

interface CompetitorAnalysisProps {
  competitorAnalyses: CompetitorAnalyses;
  isResetting: boolean;
  glassStyle: GlassStyle;
  fadeInAnimation: AnimationStyle;
}

const CompetitorAnalysisComponent: React.FC<CompetitorAnalysisProps> = ({
  competitorAnalyses,
  isResetting,
  glassStyle,
  fadeInAnimation
}) => {
  console.log("CompetitorAnalysis component received data:", competitorAnalyses);
  console.log("CompetitorAnalysis data keys:", Object.keys(competitorAnalyses || {}));
  console.log("CompetitorAnalysis data length:", Object.keys(competitorAnalyses || {}).length);
  
  if (!competitorAnalyses || Object.keys(competitorAnalyses).length === 0) {
    console.log("No competitor analysis data available");
    return null;
  }

  // Add debugging for each analysis
  Object.entries(competitorAnalyses).forEach(([companyName, analysis]) => {
    console.log(`Analysis for ${companyName}:`, analysis);
    console.log(`Analysis structured_data:`, analysis.structured_data);
    console.log(`Analysis metrics:`, analysis.metrics);
  });

  const renderInsights = (insights: Array<{ text: string; citation: string }>, title: string) => {
    if (!insights || insights.length === 0) {
      console.log(`No insights found for ${title}`);
      return null;
    }

    return (
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">{title}</h4>
        <ul className="space-y-2">
          {insights.map((insight, index) => (
            <li key={index} className="text-gray-800">
              <span className="text-gray-600">•</span> {insight.text}
              {insight.citation && (
                <span className="text-sm text-gray-500 ml-2">[{insight.citation}]</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  // Add a function to parse markdown table from raw content
  const parseMarkdownTable = (rawContent: string) => {
    const matrixSection = rawContent.match(/### Competitive Matrix\n\n([\s\S]*?)(?=\n\n|$)/);
    if (!matrixSection) return null;
    
    const tableContent = matrixSection[1];
    const lines = tableContent.split('\n').filter(line => line.trim());
    
    if (lines.length < 2) return null;
    
    // Parse header row
    const headerRow = lines[0].split('|').map(cell => cell.trim()).filter(cell => cell);
    const companies = headerRow.slice(1); // Skip first column (Feature/Competitor)
    
    // Parse data rows
    const criteria = [];
    const scores = {};
    
    for (let i = 1; i < lines.length; i++) {
      const row = lines[i].split('|').map(cell => cell.trim()).filter(cell => cell);
      if (row.length > 1) {
        const criterion = row[0];
        criteria.push(criterion);
        
        companies.forEach((company, index) => {
          if (!scores[company]) scores[company] = {};
          scores[company][criterion] = row[index + 1] || '-';
        });
      }
    }
    
    return {
      companies,
      comparison_criteria: criteria,
      scores,
      insights: []
    };
  };

  const renderCompetitiveMatrix = (matrix: any, rawContent?: string) => {
    let matrixData = matrix;
    
    // If structured data is empty, try to parse from raw content
    if ((!matrix || !matrix.companies || matrix.companies.length === 0) && rawContent) {
      matrixData = parseMarkdownTable(rawContent);
    }
    
    if (!matrixData || !matrixData.companies || matrixData.companies.length === 0) {
      console.log("No competitive matrix data available");
      return null;
    }

    return (
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Competitive Matrix</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-900 border-b">Feature/Factor</th>
                {matrixData.companies.map((company: string, index: number) => (
                  <th key={index} className="px-4 py-2 text-left text-sm font-medium text-gray-900 border-b">
                    {company}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrixData.comparison_criteria?.map((criterion: string, index: number) => (
                <tr key={index} className="border-b">
                  <td className="px-4 py-2 text-sm text-gray-900 font-medium">{criterion}</td>
                  {matrixData.companies.map((company: string, companyIndex: number) => (
                    <td key={companyIndex} className="px-4 py-2 text-sm text-gray-800">
                      {matrixData.scores?.[company]?.[criterion] || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {matrixData.insights && matrixData.insights.length > 0 && (
          <div className="mt-3">
            <h5 className="text-sm font-medium text-gray-900 mb-2">Key Insights:</h5>
            <ul className="space-y-1">
              {matrixData.insights.map((insight: string, index: number) => (
                <li key={index} className="text-sm text-gray-700">
                  • {insight}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderAnalysisMetrics = (metrics: any) => {
    if (!metrics) {
      console.log("No metrics data available");
      return null;
    }

    return (
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <h5 className="text-sm font-medium text-gray-900 mb-2">Analysis Quality</h5>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Analysis Depth:</span>
            <span className="ml-2 font-medium text-gray-900">{metrics.analysis_depth}</span>
          </div>
          <div>
            <span className="text-gray-600">Quality Rating:</span>
            <span className="ml-2 font-medium text-gray-900">{metrics.competitive_insights_quality}</span>
          </div>
          <div>
            <span className="text-gray-600">Technology Focus:</span>
            <span className="ml-2 font-medium text-gray-900">
              {Math.round(metrics.technology_focus * 100)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Product Focus:</span>
            <span className="ml-2 font-medium text-gray-900">
              {Math.round(metrics.product_focus * 100)}%
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div 
      className={`${glassStyle.card} ${fadeInAnimation.fadeIn} ${isResetting ? 'opacity-0 transform -translate-y-4' : 'opacity-100 transform translate-y-0'} font-['DM_Sans']`}
    >
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Competitor Analysis</h2>
        <p className="text-gray-600">Detailed analysis of key competitors and their strategic positioning</p>
      </div>

      {Object.entries(competitorAnalyses).map(([companyName, analysis]) => {
        console.log(`Rendering analysis for ${companyName}:`, analysis);
        return (
          <div key={companyName} className="mb-8 p-6 border border-gray-200 rounded-lg">
            <div className="mb-4">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {analysis.company} vs {analysis.competitor}
              </h3>
              <p className="text-gray-600 text-sm">
                Analysis generated on {analysis.generated_at && analysis.generated_at.trim() !== "" 
                  ? new Date(analysis.generated_at).toLocaleDateString() 
                  : "Recently"}
              </p>
            </div>

            {renderAnalysisMetrics(analysis.metrics)}

            <div className="space-y-6">
              {renderInsights(analysis.structured_data.product_directions, "Product Directions")}
              {renderInsights(analysis.structured_data.technology_leverage, "Technology Leverage")}
              {renderInsights(analysis.structured_data.positioning_insights, "Positioning Insights")}
              {renderCompetitiveMatrix(analysis.structured_data.competitive_matrix, analysis.raw_content)}
            </div>

            {analysis.structured_data.summary && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h5 className="text-sm font-medium text-blue-900 mb-2">Analysis Summary</h5>
                <div className="text-sm text-blue-800">
                  <p>Total insights: {analysis.structured_data.summary.total_insights}</p>
                  <p>Product directions: {analysis.structured_data.summary.product_directions_count}</p>
                  <p>Technology leverage: {analysis.structured_data.summary.technology_leverage_count}</p>
                  <p>Positioning insights: {analysis.structured_data.summary.positioning_insights_count}</p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default CompetitorAnalysisComponent;
