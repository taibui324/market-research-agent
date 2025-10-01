import React, { useState } from 'react';
import { ThreeCAnalysisState, GlassStyle } from '../types';
import {
  Users,
  TrendingUp,
  Building2,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  Clock,
  Target,
  Star,
  ArrowRight,
  BarChart3,
  Eye,
  Zap,
  Shield,
  TrendingDown,
  Activity
} from 'lucide-react';
// import ReportViewer from './ReportViewer';

interface ResultsDashboardProps {
  analysisState: ThreeCAnalysisState;
  glassStyle: GlassStyle;
  isResetting: boolean;
  onRetryAgent?: (agentId: string) => void;
}

type TabType = 'consumer' | 'trends' | 'competitors' | 'opportunities' | 'swot' | 'customer_mapping' | 'performance'; // | 'report';

interface TabConfig {
  id: TabType;
  label: string;
  icon: any;
  count: number;
  color: string;
  agentId?: string;
}

const ResultsDashboard: React.FC<ResultsDashboardProps> = ({
  analysisState,
  glassStyle,
  isResetting,
  onRetryAgent
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('consumer');

  const getTabsBasedOnSelectedAgents = (): TabConfig[] => {
    const baseTabs: TabConfig[] = [
      {
        id: 'consumer' as TabType,
        label: 'Consumer Analysis',
        icon: Users,
        count: analysisState.consumerInsights.length + analysisState.painPoints.length + analysisState.customerPersonas.length,
        color: 'blue',
        agentId: 'consumer_analysis'
      },
      {
        id: 'trends' as TabType,
        label: 'Market Trends',
        icon: TrendingUp,
        count: analysisState.marketTrends.length + analysisState.trendPredictions.length,
        color: 'green',
        agentId: 'trend_analysis'
      },
      {
        id: 'competitors' as TabType,
        label: 'Competitive Landscape',
        icon: Building2,
        count: analysisState.competitorAnalysis?.competitors.length || 0,
        color: 'purple',
        agentId: 'competitor_analysis'
      },
      {
        id: 'swot' as TabType,
        label: 'SWOT Analysis',
        icon: BarChart3,
        count: analysisState.swotAnalysis ?
          (analysisState.swotAnalysis.strengths.length +
            analysisState.swotAnalysis.weaknesses.length +
            analysisState.swotAnalysis.opportunities.length +
            analysisState.swotAnalysis.threats.length) : 0,
        color: 'indigo',
        agentId: 'swot_analysis'
      },
      {
        id: 'customer_mapping' as TabType,
        label: 'Customer Mapping',
        icon: Target,
        count: analysisState.customerMapping ?
          (analysisState.customerMapping.journeyStages.length +
            analysisState.customerMapping.segments.length) : 0,
        color: 'teal',
        agentId: 'customer_mapping'
      },
      {
        id: 'opportunities' as TabType,
        label: 'Market Opportunities',
        icon: Lightbulb,
        count: analysisState.opportunities.length + analysisState.whiteSpaces.length + analysisState.recommendations.length,
        color: 'orange',
        agentId: 'opportunity_analysis'
      }
    ];

    // Filter tabs based on selected agents
    const selectedAgents = analysisState.selectedAgents || [];
    const filteredTabs = selectedAgents.length > 0
      ? baseTabs.filter(tab => !('agentId' in tab) || !tab.agentId || selectedAgents.includes(tab.agentId))
      : baseTabs; // Show all tabs if no agents are specified (backward compatibility)

    // Always include performance tab
    filteredTabs.push({
      id: 'performance' as TabType,
      label: 'Performance',
      icon: Zap,
      count: selectedAgents.length,
      color: 'gray'
    });

    return filteredTabs;
  };

  const tabs = getTabsBasedOnSelectedAgents();

  const getTabColorClasses = (color: string, isActive: boolean) => {
    const colors = {
      blue: isActive
        ? 'bg-blue-100 text-blue-800 border-blue-300'
        : 'text-blue-600 hover:bg-blue-50 border-transparent hover:border-blue-200',
      green: isActive
        ? 'bg-green-100 text-green-800 border-green-300'
        : 'text-green-600 hover:bg-green-50 border-transparent hover:border-green-200',
      purple: isActive
        ? 'bg-purple-100 text-purple-800 border-purple-300'
        : 'text-purple-600 hover:bg-purple-50 border-transparent hover:border-purple-200',
      orange: isActive
        ? 'bg-orange-100 text-orange-800 border-orange-300'
        : 'text-orange-600 hover:bg-orange-50 border-transparent hover:border-orange-200',
      indigo: isActive
        ? 'bg-indigo-100 text-indigo-800 border-indigo-300'
        : 'text-indigo-600 hover:bg-indigo-50 border-transparent hover:border-indigo-200',
      teal: isActive
        ? 'bg-teal-100 text-teal-800 border-teal-300'
        : 'text-teal-600 hover:bg-teal-50 border-transparent hover:border-teal-200',
      gray: isActive
        ? 'bg-gray-100 text-gray-800 border-gray-300'
        : 'text-gray-600 hover:bg-gray-50 border-transparent hover:border-gray-200'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  const renderConsumerAnalysis = () => (
    <div className="space-y-6">
      {/* Consumer Insights Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Eye className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Consumer Insights</h3>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.consumerInsights.length}
          </span>
        </div>

        {analysisState.consumerInsights.length > 0 ? (
          <div className="grid gap-4">
            {analysisState.consumerInsights.map((insight, index) => (
              <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-gray-800 font-medium">{insight.insight}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center space-x-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Confidence: {Math.round(insight.confidence * 100)}%</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Target className="w-4 h-4 text-blue-500" />
                        <span>Source: {insight.source}</span>
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Eye className="w-6 h-6 text-blue-600" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Eye className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Consumer insights will appear here once analysis is complete</p>
          </div>
        )}
      </div>

      {/* Pain Points Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">Pain Points</h3>
          <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.painPoints.length}
          </span>
        </div>

        {analysisState.painPoints.length > 0 ? (
          <div className="grid gap-3">
            {analysisState.painPoints.map((painPoint, index) => (
              <div key={index} className="p-3 bg-red-50 rounded-lg border border-red-200 flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <span className="text-gray-800">{painPoint}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <AlertCircle className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>Pain points will be identified during consumer analysis</p>
          </div>
        )}
      </div>

      {/* Customer Personas Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Users className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Customer Personas</h3>
          <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.customerPersonas.length}
          </span>
        </div>

        {analysisState.customerPersonas.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {analysisState.customerPersonas.map((persona, index) => (
              <div key={index} className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-start space-x-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Users className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-1">{persona.name}</h4>
                    <p className="text-gray-700 text-sm mb-3">{persona.description}</p>
                    {persona.characteristics.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Characteristics</p>
                        <div className="flex flex-wrap gap-1">
                          {persona.characteristics.map((char, charIndex) => (
                            <span key={charIndex} className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                              {char}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Users className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>Customer personas will be generated from consumer insights</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderTrendAnalysis = () => (
    <div className="space-y-6">
      {/* Market Trends Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Market Trends</h3>
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.marketTrends.length}
          </span>
        </div>

        {analysisState.marketTrends.length > 0 ? (
          <div className="grid gap-4">
            {analysisState.marketTrends.map((trend, index) => (
              <div key={index} className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-gray-800 font-medium">{trend.trend}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center space-x-1">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span>Confidence: {Math.round(trend.confidence * 100)}%</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Target className="w-4 h-4 text-green-500" />
                        <span>Source: {trend.source}</span>
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-green-600" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Market trends will appear here once analysis is complete</p>
          </div>
        )}
      </div>

      {/* Trend Predictions Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Clock className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Trend Predictions</h3>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.trendPredictions.length}
          </span>
        </div>

        {analysisState.trendPredictions.length > 0 ? (
          <div className="grid gap-4">
            {analysisState.trendPredictions.map((prediction, index) => (
              <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Clock className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-1">{prediction.title}</h4>
                    <p className="text-gray-700 text-sm mb-2">{prediction.description}</p>
                    <div className="flex items-center space-x-2">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                        {prediction.timeHorizon}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Clock className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>Trend predictions will be generated from market analysis</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderCompetitorAnalysis = () => (
    <div className="space-y-6">
      {analysisState.competitorAnalysis ? (
        <>
          {/* Competitors List */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Building2 className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold text-gray-900">Competitor Landscape</h3>
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.competitorAnalysis.competitors.length} competitors
              </span>
            </div>

            <div className="grid gap-4">
              {analysisState.competitorAnalysis.competitors.map((competitor, index) => (
                <div key={index} className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-900">{competitor.name}</h4>
                      {competitor.marketShare && (
                        <p className="text-sm text-gray-600">Market Share: {competitor.marketShare}%</p>
                      )}
                      <p className="text-sm text-gray-700 mt-1">{competitor.positioning}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Strengths:</span>
                      <div className="mt-1 space-y-1">
                        {competitor.strengths.map((strength, sIndex) => (
                          <div key={sIndex} className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">
                            {strength}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Weaknesses:</span>
                      <div className="mt-1 space-y-1">
                        {competitor.weaknesses.map((weakness, wIndex) => (
                          <div key={wIndex} className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">
                            {weakness}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Market Gaps */}
          {analysisState.competitorAnalysis.marketGaps.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">Market Gaps</h3>
                <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">
                  {analysisState.competitorAnalysis.marketGaps.length}
                </span>
              </div>

              <div className="grid gap-3">
                {analysisState.competitorAnalysis.marketGaps.map((gap, index) => (
                  <div key={index} className="p-3 bg-orange-50 rounded-lg border border-orange-200 flex items-start space-x-3">
                    <Target className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-800">{gap}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Competitive Matrix */}
          {analysisState.competitorAnalysis.competitiveMatrix && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Competitive Matrix</h3>
              </div>

              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="text-sm text-blue-800">
                  Competitive analysis matrix with {analysisState.competitorAnalysis.competitiveMatrix.criteria.length} criteria
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {analysisState.competitorAnalysis.competitiveMatrix.criteria.map((criterion, index) => (
                    <span key={index} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                      {criterion}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Competitor Analysis</h3>
          <p className="text-gray-500 mb-4">
            Competitive landscape analysis will appear here once the analysis is complete.
          </p>
        </div>
      )}
    </div>
  );

  const renderSwotAnalysis = () => (
    <div className="space-y-6">
      {analysisState.swotAnalysis ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-900">Strengths</h3>
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.swotAnalysis.strengths.length}
              </span>
            </div>
            <div className="space-y-2">
              {analysisState.swotAnalysis.strengths.map((strength, index) => (
                <div key={index} className="p-3 bg-green-50 rounded-lg border border-green-200 flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-800 text-sm">{strength}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Weaknesses */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-5 h-5 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">Weaknesses</h3>
              <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.swotAnalysis.weaknesses.length}
              </span>
            </div>
            <div className="space-y-2">
              {analysisState.swotAnalysis.weaknesses.map((weakness, index) => (
                <div key={index} className="p-3 bg-red-50 rounded-lg border border-red-200 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-800 text-sm">{weakness}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Opportunities */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Lightbulb className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Opportunities</h3>
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.swotAnalysis.opportunities.length}
              </span>
            </div>
            <div className="space-y-2">
              {analysisState.swotAnalysis.opportunities.map((opportunity, index) => (
                <div key={index} className="p-3 bg-blue-50 rounded-lg border border-blue-200 flex items-start space-x-2">
                  <Lightbulb className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-800 text-sm">{opportunity}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Threats */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <h3 className="text-lg font-semibold text-gray-900">Threats</h3>
              <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.swotAnalysis.threats.length}
              </span>
            </div>
            <div className="space-y-2">
              {analysisState.swotAnalysis.threats.map((threat, index) => (
                <div key={index} className="p-3 bg-orange-50 rounded-lg border border-orange-200 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-800 text-sm">{threat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">SWOT Analysis</h3>
          <p className="text-gray-500 mb-4">
            SWOT analysis results will appear here once the analysis is complete.
          </p>
        </div>
      )}
    </div>
  );

  const renderCustomerMapping = () => (
    <div className="space-y-6">
      {analysisState.customerMapping ? (
        <>
          {/* Customer Journey Stages */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-teal-600" />
              <h3 className="text-lg font-semibold text-gray-900">Customer Journey</h3>
              <span className="bg-teal-100 text-teal-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.customerMapping.journeyStages.length} stages
              </span>
            </div>
            <div className="grid gap-4">
              {analysisState.customerMapping.journeyStages.map((stage, index) => (
                <div key={index} className="p-4 bg-teal-50 rounded-lg border border-teal-200">
                  <h4 className="font-semibold text-gray-900 mb-3">{stage.stage}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Touchpoints:</span>
                      <div className="mt-1 space-y-1">
                        {stage.touchpoints.map((touchpoint, tIndex) => (
                          <div key={tIndex} className="bg-teal-100 text-teal-700 px-2 py-1 rounded text-xs">
                            {touchpoint}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Pain Points:</span>
                      <div className="mt-1 space-y-1">
                        {stage.painPoints.map((painPoint, pIndex) => (
                          <div key={pIndex} className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">
                            {painPoint}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Opportunities:</span>
                      <div className="mt-1 space-y-1">
                        {stage.opportunities.map((opportunity, oIndex) => (
                          <div key={oIndex} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                            {opportunity}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Customer Segments */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold text-gray-900">Customer Segments</h3>
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                {analysisState.customerMapping.segments.length} segments
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysisState.customerMapping.segments.map((segment, index) => (
                <div key={index} className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{segment.name}</h4>
                    <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                      {segment.size}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-gray-700">Characteristics:</span>
                    <div className="flex flex-wrap gap-1">
                      {segment.characteristics.map((char, cIndex) => (
                        <span key={cIndex} className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                          {char}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <Target className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Customer Mapping</h3>
          <p className="text-gray-500 mb-4">
            Customer journey and segment mapping will appear here once the analysis is complete.
          </p>
        </div>
      )}
    </div>
  );

  const renderPerformanceAnalysis = () => (
    <div className="space-y-6">
      {/* Overall Performance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-blue-800">Total Agents</span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {analysisState.selectedAgents?.length || 0}
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-medium text-green-800">Completed</span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            {Object.values(analysisState.agentPerformance || {}).filter(p => p.status === 'completed').length}
          </div>
        </div>

        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="font-medium text-red-800">Errors</span>
          </div>
          <div className="text-2xl font-bold text-red-900">
            {analysisState.agentErrors?.length || 0}
          </div>
        </div>
      </div>

      {/* Agent Performance Details */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Agent Performance Details</h3>
        <div className="space-y-3">
          {analysisState.selectedAgents?.map(agentId => {
            const performance = analysisState.agentPerformance?.[agentId];
            const agentErrors = analysisState.agentErrors?.filter(error => error.agentId === agentId) || [];

            return (
              <div key={agentId} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900 capitalize">
                    {agentId.replace('_', ' ')} Agent
                  </h4>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${performance?.status === 'completed' ? 'bg-green-100 text-green-700' :
                      performance?.status === 'failed' ? 'bg-red-100 text-red-700' :
                        performance?.status === 'running' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                      }`}>
                      {performance?.status || 'pending'}
                    </span>
                    {agentErrors.length > 0 && onRetryAgent && (
                      <button
                        onClick={() => onRetryAgent(agentId)}
                        className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200 transition-colors"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                </div>

                {performance && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Duration:</span>
                      <div className="text-gray-800">
                        {performance.duration ? `${(performance.duration / 1000).toFixed(1)}s` : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Data Points:</span>
                      <div className="text-gray-800">
                        {performance.dataPointsCollected || 0}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Quality Score:</span>
                      <div className="text-gray-800">
                        {performance.qualityScore ? `${Math.round(performance.qualityScore * 100)}%` : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Retries:</span>
                      <div className="text-gray-800">
                        {performance.retryCount || 0}
                      </div>
                    </div>
                  </div>
                )}

                {agentErrors.length > 0 && (
                  <div className="mt-3 p-3 bg-red-50 rounded border border-red-200">
                    <div className="text-sm font-medium text-red-800 mb-2">
                      Errors ({agentErrors.length}):
                    </div>
                    <div className="space-y-1">
                      {agentErrors.slice(-3).map((error, index) => (
                        <div key={index} className="text-xs text-red-700">
                          <span className="font-medium">{error.phase}:</span> {error.message}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderOpportunityAnalysis = () => (
    <div className="space-y-6">
      {/* Market Opportunities Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Lightbulb className="w-5 h-5 text-orange-600" />
          <h3 className="text-lg font-semibold text-gray-900">Market Opportunities</h3>
          <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.opportunities.length}
          </span>
        </div>

        {analysisState.opportunities.length > 0 ? (
          <div className="grid gap-4">
            {analysisState.opportunities.map((opportunity, index) => (
              <div key={index} className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Lightbulb className="w-5 h-5 text-orange-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{opportunity.title}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${opportunity.priority === 'High' ? 'bg-red-100 text-red-700' :
                        opportunity.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                        {opportunity.priority} Priority
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">{opportunity.description}</p>
                    {opportunity.recommendations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Recommendations</p>
                        <div className="space-y-1">
                          {opportunity.recommendations.map((rec, recIndex) => (
                            <div key={recIndex} className="flex items-start space-x-2">
                              <ArrowRight className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
                              <span className="text-sm text-gray-700">{rec}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Lightbulb className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Market opportunities will be identified from analysis results</p>
          </div>
        )}
      </div>

      {/* White Spaces Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Target className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">White Space Opportunities</h3>
          <span className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.whiteSpaces.length}
          </span>
        </div>

        {analysisState.whiteSpaces.length > 0 ? (
          <div className="grid gap-4">
            {analysisState.whiteSpaces.map((whiteSpace, index) => (
              <div key={index} className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Target className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-1">{whiteSpace.title}</h4>
                    <p className="text-gray-700 text-sm mb-2">{whiteSpace.description}</p>
                    <div className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs inline-block">
                      Gap: {whiteSpace.marketGap}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Target className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>White space opportunities will be identified from competitive analysis</p>
          </div>
        )}
      </div>

      {/* Recommendations Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Strategic Recommendations</h3>
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
            {analysisState.recommendations.length}
          </span>
        </div>

        {analysisState.recommendations.length > 0 ? (
          <div className="grid gap-3">
            {analysisState.recommendations.map((recommendation, index) => (
              <div key={index} className="p-3 bg-green-50 rounded-lg border border-green-200 flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-800">{recommendation}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <CheckCircle className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>Strategic recommendations will be generated from opportunity analysis</p>
          </div>
        )}
      </div>
    </div>
  );

  // const renderFullReport = () => {
  //   // Temporarily disabled - will be re-enabled after fixing import issues
  //   return <div>Report functionality temporarily disabled</div>;
  // };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'consumer':
        return renderConsumerAnalysis();
      case 'trends':
        return renderTrendAnalysis();
      case 'competitors':
        return renderCompetitorAnalysis();
      case 'swot':
        return renderSwotAnalysis();
      case 'customer_mapping':
        return renderCustomerMapping();
      case 'performance':
        return renderPerformanceAnalysis();
      case 'opportunities':
        return renderOpportunityAnalysis();
      // case 'report':
      //   return renderFullReport();
      default:
        return renderConsumerAnalysis();
    }
  };

  if (!analysisState.analysisComplete && analysisState.status === 'idle') {
    return null;
  }

  return (
    <div className={`${glassStyle.card} font-['DM_Sans'] ${isResetting ? 'opacity-0 transform -translate-y-4' : 'opacity-100 transform translate-y-0'} transition-all duration-500`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">3C Analysis Results</h2>
        {analysisState.targetMarket && (
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
            {analysisState.targetMarket.replace('_', ' ').toUpperCase()}
          </span>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center space-x-2 px-4 py-3 rounded-t-lg border-b-2 transition-all duration-200 font-medium
                ${getTabColorClasses(tab.color, isActive)}
              `}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span className={`
                  px-2 py-0.5 rounded-full text-xs font-medium
                  ${isActive ? 'bg-white/50' : 'bg-gray-100 text-gray-600'}
                `}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {renderTabContent()}
      </div>

      {/* Analysis Status Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span>Analysis Status: {analysisState.analysisComplete ? 'Complete' : 'In Progress'}</span>
            </span>
            {analysisState.progress > 0 && (
              <span>Progress: {Math.round(analysisState.progress)}%</span>
            )}
          </div>
          <div className="text-xs text-gray-500">
            Target Market: {analysisState.targetMarket || 'Not specified'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsDashboard;