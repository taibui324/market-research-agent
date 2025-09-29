import { useState, useEffect, useRef } from "react";
import Header from './components/Header';
import ResearchBriefings from './components/ResearchBriefings';
import CurationExtraction from './components/CurationExtraction';
import ResearchQueries from './components/ResearchQueries';
import ResearchStatus from './components/ResearchStatus';
import ResearchReport from './components/ResearchReport';
import ResearchForm from './components/ResearchForm';
import AnalysisTypeSelector from './components/AnalysisTypeSelector';
import MarketAnalysisForm from './components/MarketAnalysisForm';
import ThreeCAnalysisProgress from './components/ThreeCAnalysisProgress';
import {
  ResearchOutput, 
  DocCount,
  DocCounts, 
  EnrichmentCounts, 
  ResearchState, 
  ResearchStatusType,
  AnalysisType,
  MarketResearchRequest,
  ThreeCAnalysisState,
  ThreeCProgressPhase
} from './types';
import { checkForFinalReport } from './utils/handlers';
import { colorAnimation, dmSansStyle, glassStyle, fadeInAnimation } from './styles/index';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

if (!API_URL || !WS_URL) {
  console.warn("Environment variables VITE_API_URL and VITE_WS_URL should be set. Using defaults.");
}

// Add styles to document head
const colorStyle = document.createElement('style');
colorStyle.textContent = colorAnimation;
document.head.appendChild(colorStyle);

const dmSansStyleElement = document.createElement('style');
dmSansStyleElement.textContent = dmSansStyle;
document.head.appendChild(dmSansStyleElement);

function App() {
  // Analysis type state
  const [analysisType, setAnalysisType] = useState<AnalysisType>('company_research');

  const [isResearching, setIsResearching] = useState(false);
  const [status, setStatus] = useState<ResearchStatusType | null>(null);
  const [output, setOutput] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [hasFinalReport, setHasFinalReport] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 3;
  const reconnectDelay = 2000; // 2 seconds
  const [researchState, setResearchState] = useState<ResearchState>({
    status: "idle",
    message: "",
    queries: [],
    streamingQueries: {},
    briefingStatus: {
      company: false,
      industry: false,
      financial: false,
      news: false
    }
  });
  const [originalCompanyName, setOriginalCompanyName] = useState<string>("");

  // 3C Analysis specific state
  const [threeCAnalysisState, setThreeCAnalysisState] = useState<ThreeCAnalysisState>({
    status: "idle",
    message: "",
    currentStep: "",
    progress: 0,
    analysisType: '3c_analysis',
    targetMarket: "",
    consumerInsights: [],
    painPoints: [],
    customerPersonas: [],
    marketTrends: [],
    trendPredictions: [],
    opportunities: [],
    whiteSpaces: [],
    recommendations: [],
    analysisComplete: false
  });
  const [threeCCurrentPhase, setThreeCCurrentPhase] = useState<ThreeCProgressPhase | null>(null);
  const [threeCStartTime, setThreeCStartTime] = useState<Date | null>(null);
  const [threeCErrors, setThreeCErrors] = useState<Array<{
    phase: string;
    message: string;
    timestamp: Date;
  }>>([]);
  
  // Enhanced 3C Analysis state for agent selection
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [analysisDepth, setAnalysisDepth] = useState<string>('comprehensive');
  const [agentPerformance, setAgentPerformance] = useState<Record<string, string>>({});
  
  // WebSocket connection status
  const [websocketConnected, setWebsocketConnected] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Add ref for status section
  const statusRef = useRef<HTMLDivElement>(null);

  // Add state to track initial scroll
  const [hasScrolledToStatus, setHasScrolledToStatus] = useState(false);

  // Modify the scroll helper function
  const scrollToStatus = () => {
    if (!hasScrolledToStatus && statusRef.current) {
      const yOffset = -20; // Reduced negative offset to scroll further down
      const y = statusRef.current.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
      setHasScrolledToStatus(true);
    }
  };

  // Add new state for query section collapse
  const [isQueriesExpanded, setIsQueriesExpanded] = useState(true);
  const [shouldShowQueries, setShouldShowQueries] = useState(false);
  
  // Add new state for tracking search phase
  const [isSearchPhase, setIsSearchPhase] = useState(false);

  // Add state for section collapse
  const [isBriefingExpanded, setIsBriefingExpanded] = useState(true);
  const [isEnrichmentExpanded, setIsEnrichmentExpanded] = useState(true);

  // Add state for phase tracking
  const [currentPhase, setCurrentPhase] = useState<'search' | 'enrichment' | 'briefing' | 'complete' | null>(null);

  // Add new state for PDF generation
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [, setPdfUrl] = useState<string | null>(null);

  const [isResetting, setIsResetting] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Add new state for color cycling
  const [loaderColor, setLoaderColor] = useState("#468BFF");
  
  // Add useEffect for color cycling
  useEffect(() => {
    if (!isResearching) return;
    
    const colors = [
      "#468BFF", // Blue
      "#8FBCFA", // Light Blue
      "#FE363B", // Red
      "#FF9A9D", // Light Red
      "#FDBB11", // Yellow
      "#F6D785", // Light Yellow
    ];
    
    let currentIndex = 0;
    
    const interval = setInterval(() => {
      currentIndex = (currentIndex + 1) % colors.length;
      setLoaderColor(colors[currentIndex]);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isResearching]);

  // Retry WebSocket connection function
  const retryWebSocketConnection = () => {
    if (currentJobId && !websocketConnected) {
      console.log("Retrying WebSocket connection...");
      setReconnectAttempts(0);
      connectWebSocket(currentJobId);
    }
  };

  const resetResearch = () => {
    setIsResetting(true);
    
    // Use setTimeout to create a smooth transition
    setTimeout(() => {
      setStatus(null);
      setOutput(null);
      setError(null);
      setIsComplete(false);
      setResearchState({
        status: "idle",
        message: "",
        queries: [],
        streamingQueries: {},
        briefingStatus: {
          company: false,
          industry: false,
          financial: false,
          news: false
        }
      });
      // Reset 3C analysis state
      setThreeCAnalysisState({
        status: "idle",
        message: "",
        currentStep: "",
        progress: 0,
        analysisType: '3c_analysis',
        targetMarket: "",
        consumerInsights: [],
        painPoints: [],
        customerPersonas: [],
        marketTrends: [],
        trendPredictions: [],
        opportunities: [],
        whiteSpaces: [],
        recommendations: [],
        analysisComplete: false
      });
      setThreeCCurrentPhase(null);
      setThreeCStartTime(null);
      setThreeCErrors([]);
      setPdfUrl(null);
      setCurrentPhase(null);
      setIsSearchPhase(false);
      setShouldShowQueries(false);
      setIsQueriesExpanded(true);
      setWebsocketConnected(false);
      setCurrentJobId(null);
      setIsBriefingExpanded(true);
      setIsEnrichmentExpanded(true);
      setIsResetting(false);
      setHasScrolledToStatus(false); // Reset scroll flag when resetting research
    }, 300); // Match this with CSS transition duration
  };

  const handle3CAnalysisUpdate = (statusData: any) => {
    // Map status to 3C phases
    const stepToPhaseMap: Record<string, ThreeCProgressPhase> = {
      'Query Generation': 'query_generation',
      'Data Collection': 'data_collection',
      'Data Curation': 'data_curation',
      'Consumer Analysis': 'consumer_analysis',
      'Trend Analysis': 'trend_analysis',
      'Competitor Analysis': 'competitor_analysis',
      'SWOT Analysis': 'swot_analysis',
      'Customer Mapping': 'customer_mapping',
      'Opportunity Analysis': 'opportunity_analysis',
      'Synthesis': 'synthesis',
      'Report Generation': 'report_generation'
    };

    // Update agent performance tracking
    if (statusData.result?.agent_performance) {
      setAgentPerformance(statusData.result.agent_performance);
    }

    // Update analysis configuration from server response
    if (statusData.result?.selected_agents) {
      setSelectedAgents(statusData.result.selected_agents);
    }
    if (statusData.result?.analysis_depth) {
      setAnalysisDepth(statusData.result.analysis_depth);
    }

    // Update current phase
    if (statusData.result?.step) {
      const phase = stepToPhaseMap[statusData.result.step];
      if (phase) {
        setThreeCCurrentPhase(phase);
      }
    }

    // Handle completion
    if (statusData.status === "completed") {
      setThreeCCurrentPhase('complete');
      setIsComplete(true);
      setIsResearching(false);
      setStatus({
        step: "Complete",
        message: "3C Analysis completed successfully"
      });
      setOutput({
        summary: "",
        details: {
          report_content: statusData.result.report || "",
          report: statusData.result.report,
        },
      });
      setHasFinalReport(true);
      
      // Update 3C analysis state
      setThreeCAnalysisState(prev => ({
        ...prev,
        status: "completed",
        analysisComplete: true,
        progress: 100
      }));
      
      // Clear polling interval if it exists
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    // Handle processing updates
    else if (statusData.status === "processing") {
      setIsComplete(false);
      setStatus({
        step: statusData.result?.step || "Processing",
        message: statusData.message || "Processing...",
      });

      // Update 3C analysis state
      setThreeCAnalysisState(prev => ({
        ...prev,
        status: "processing",
        message: statusData.message || "Processing...",
        currentStep: statusData.result?.step || "",
        progress: statusData.result?.progress_percentage || prev.progress,
        targetMarket: statusData.result?.target_market || prev.targetMarket
      }));
      
      scrollToStatus();
    }

    // Handle specific 3C analysis data updates
    if (statusData.result) {
      const result = statusData.result;
      
      // Update consumer insights
      if (result.consumer_insights_count !== undefined) {
        setThreeCAnalysisState(prev => ({
          ...prev,
          consumerInsights: Array(result.consumer_insights_count).fill(null).map((_, i) => ({
            insight: `Consumer insight ${i + 1}`,
            confidence: 0.8,
            source: 'Market Research'
          }))
        }));
      }

      // Update market trends
      if (result.market_trends_count !== undefined) {
        setThreeCAnalysisState(prev => ({
          ...prev,
          marketTrends: Array(result.market_trends_count).fill(null).map((_, i) => ({
            trend: `Market trend ${i + 1}`,
            confidence: 0.8,
            source: 'Industry Analysis'
          }))
        }));
      }

      // Update opportunities
      if (result.opportunities_found !== undefined) {
        setThreeCAnalysisState(prev => ({
          ...prev,
          opportunities: Array(result.opportunities_found).fill(null).map((_, i) => ({
            title: `Market Opportunity ${i + 1}`,
            description: 'Identified market opportunity',
            priority: 'Medium',
            recommendations: []
          }))
        }));
      }
    }

    // Handle errors
    if (statusData.status === "failed" || statusData.status === "error") {
      const errorMessage = statusData.error || statusData.message || "3C Analysis failed";
      setError(errorMessage);
      setIsResearching(false);
      setIsComplete(false);
      
      // Add to errors list
      setThreeCErrors(prev => [...prev, {
        phase: statusData.result?.step || 'Unknown',
        message: errorMessage,
        timestamp: new Date()
      }]);
    }
  };

  const connectWebSocket = (jobId: string) => {
    console.log("Initializing WebSocket connection for job:", jobId);
    setCurrentJobId(jobId);
    
    // Use the WS_URL directly if it's a full URL, otherwise construct it
    const wsUrl = WS_URL.startsWith('wss://') || WS_URL.startsWith('ws://')
      ? `${WS_URL}/company_analysis/ws/${jobId}`
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${WS_URL}/company_analysis/ws/${jobId}`;
    
    console.log("Connecting to WebSocket URL:", wsUrl);
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connection established for job:", jobId);
      setReconnectAttempts(0);
      setWebsocketConnected(true);
    };

    ws.onclose = (event) => {
      console.log("WebSocket disconnected", {
        jobId,
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
        timestamp: new Date().toISOString()
      });
      
      setWebsocketConnected(false);

      if (isResearching && !hasFinalReport) {
        // Start polling for final report
        if (!pollingIntervalRef.current) {
          pollingIntervalRef.current = setInterval(() => checkForFinalReport(
            jobId,
            setOutput,
            setStatus,
            setIsComplete,
            setIsResearching,
            setCurrentPhase,
            setHasFinalReport,
            pollingIntervalRef
          ), 5000);
        }

        // Attempt reconnection if we haven't exceeded max attempts
        if (reconnectAttempts < maxReconnectAttempts) {
          console.log(`Attempting to reconnect (${reconnectAttempts + 1}/${maxReconnectAttempts})...`);
          setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket(jobId);
          }, reconnectDelay);
        } else {
          console.log("Max reconnection attempts reached");
          setError("Connection lost. Checking for final report...");
          // Keep polling for final report
        }
      } else if (isResearching) {
        setError("Research connection lost. Please try again.");
        setIsResearching(false);
      }
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", {
        jobId,
        error: event,
        timestamp: new Date().toISOString(),
        readyState: ws.readyState,
        url: wsUrl
      });
      setWebsocketConnected(false);
      setError("WebSocket connection error");
      setIsResearching(false);
    };

    ws.onmessage = (event) => {
      const rawData = JSON.parse(event.data);

      if (rawData.type === "status_update") {
        const statusData = rawData.data;

        // Handle 3C Analysis specific updates
        if (statusData.result?.analysis_type === '3c_analysis' || analysisType === '3c_analysis') {
          handle3CAnalysisUpdate(statusData);
          return;
        }

        // Handle phase transitions
        if (statusData.result?.step) {
          const step = statusData.result.step;
          if (step === "Search" && currentPhase !== 'search') {
            setCurrentPhase('search');
            setIsSearchPhase(true);
            setShouldShowQueries(true);
            setIsQueriesExpanded(true);
          } else if (step === "Enriching" && currentPhase !== 'enrichment') {
            setCurrentPhase('enrichment');
            setIsSearchPhase(false);
            setIsQueriesExpanded(false);
            setIsEnrichmentExpanded(true);
          } else if (step === "Briefing" && currentPhase !== 'briefing') {
            setCurrentPhase('briefing');
            setIsEnrichmentExpanded(false);
            setIsBriefingExpanded(true);
          }
        }

        // Handle completion
        if (statusData.status === "completed") {
          console.log("Research completed, received data:", statusData.result);
          console.log("Competitor analyses:", statusData.result.competitor_analyses);
          setCurrentPhase('complete');
          setIsComplete(true);
          setIsResearching(false);
          setStatus({
            step: "Complete",
            message: "Research completed successfully"
          });
          setOutput({
            summary: "",
            details: {
              report_content: statusData.result.report_content,
              competitor_analyses: statusData.result.competitor_analyses || {},
            },
          });
          setHasFinalReport(true);
          
          // Clear polling interval if it exists
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }

        // Set search phase when first query starts generating
        if (statusData.status === "query_generating" && !isSearchPhase) {
          setIsSearchPhase(true);
          setShouldShowQueries(true);
          setIsQueriesExpanded(true);
        }
        
        // End search phase and start enrichment when moving to next step
        if (statusData.result?.step && statusData.result.step !== "Search") {
          if (isSearchPhase) {
            setIsSearchPhase(false);
            // Add delay before collapsing queries
            setTimeout(() => {
              setIsQueriesExpanded(false);
            }, 1000);
          }
          
          // Handle enrichment phase
          if (statusData.result.step === "Enriching") {
            setIsEnrichmentExpanded(true);
            // Collapse enrichment section when complete
            if (statusData.status === "enrichment_complete") {
              setTimeout(() => {
                setIsEnrichmentExpanded(false);
              }, 1000);
            }
          }
          
          // Handle briefing phase
          if (statusData.result.step === "Briefing") {
            setIsBriefingExpanded(true);
            if (statusData.status === "briefing_complete" && statusData.result?.category) {
              // Update briefing status
              setResearchState((prev) => {
                const newBriefingStatus = {
                  ...prev.briefingStatus,
                  [statusData.result.category]: true
                };
                
                // Check if all briefings are complete
                const allBriefingsComplete = Object.values(newBriefingStatus).every(status => status);
                
                // Only collapse when all briefings are complete
                if (allBriefingsComplete) {
                  setTimeout(() => {
                    setIsBriefingExpanded(false);
                  }, 2000);
                }
                
                return {
                  ...prev,
                  briefingStatus: newBriefingStatus
                };
              });
            }
          }
        }

        // Handle enrichment-specific updates
        if (statusData.result?.step === "Enriching") {
          
          // Initialize enrichment counts when starting a category
          if (statusData.status === "category_start") {
            const category = statusData.result.category as keyof EnrichmentCounts;
            if (category) {
              setResearchState((prev) => ({
                ...prev,
                enrichmentCounts: {
                  ...prev.enrichmentCounts,
                  [category]: {
                    total: statusData.result.count || 0,
                    enriched: 0
                  }
                } as EnrichmentCounts
              }));
            }
          }
          // Update enriched count when a document is processed
          else if (statusData.status === "extracted") {
            const category = statusData.result.category as keyof EnrichmentCounts;
            if (category) {
              setResearchState((prev) => {
                const currentCounts = prev.enrichmentCounts?.[category];
                if (currentCounts) {
                  return {
                    ...prev,
                    enrichmentCounts: {
                      ...prev.enrichmentCounts,
                      [category]: {
                        ...currentCounts,
                        enriched: Math.min(currentCounts.enriched + 1, currentCounts.total)
                      }
                    } as EnrichmentCounts
                  };
                }
                return prev;
              });
            }
          }
          // Handle extraction errors
          else if (statusData.status === "extraction_error") {
            const category = statusData.result.category as keyof EnrichmentCounts;
            if (category) {
              setResearchState((prev) => {
                const currentCounts = prev.enrichmentCounts?.[category];
                if (currentCounts) {
                  return {
                    ...prev,
                    enrichmentCounts: {
                      ...prev.enrichmentCounts,
                      [category]: {
                        ...currentCounts,
                        total: Math.max(0, currentCounts.total - 1)
                      }
                    } as EnrichmentCounts
                  };
                }
                return prev;
              });
            }
          }
          // Update final counts when a category is complete
          else if (statusData.status === "category_complete") {
            const category = statusData.result.category as keyof EnrichmentCounts;
            if (category) {
              setResearchState((prev) => ({
                ...prev,
                enrichmentCounts: {
                  ...prev.enrichmentCounts,
                  [category]: {
                    total: statusData.result.total || 0,
                    enriched: statusData.result.enriched || 0
                  }
                } as EnrichmentCounts
              }));
            }
          }
        }

        // Handle curation-specific updates
        if (statusData.result?.step === "Curation") {
          
          // Initialize doc counts when curation starts
          if (statusData.status === "processing" && statusData.result.doc_counts) {
            setResearchState((prev) => ({
              ...prev,
              docCounts: statusData.result.doc_counts as DocCounts
            }));
          }
          // Update initial count for a category
          else if (statusData.status === "category_start") {
            const docType = statusData.result?.doc_type as keyof DocCounts;
            if (docType) {
              setResearchState((prev) => ({
                ...prev,
                docCounts: {
                  ...prev.docCounts,
                  [docType]: {
                    initial: statusData.result.initial_count,
                    kept: 0
                  } as DocCount
                } as DocCounts
              }));
            }
          }
          // Increment the kept count for a specific category
          else if (statusData.status === "document_kept") {
            const docType = statusData.result?.doc_type as keyof DocCounts;
            setResearchState((prev) => {
              if (docType && prev.docCounts?.[docType]) {
                return {
                  ...prev,
                  docCounts: {
                    ...prev.docCounts,
                    [docType]: {
                      initial: prev.docCounts[docType].initial,
                      kept: prev.docCounts[docType].kept + 1
                    }
                  } as DocCounts
                };
              }
              return prev;
            });
          }
          // Update final doc counts when curation is complete
          else if (statusData.status === "curation_complete" && statusData.result.doc_counts) {
            setResearchState((prev) => ({
              ...prev,
              docCounts: statusData.result.doc_counts as DocCounts
            }));
          }
        }

        // Handle briefing status updates
        if (statusData.status === "briefing_start") {
          setStatus({
            step: "Briefing",
            message: statusData.message
          });
        } else if (statusData.status === "briefing_complete" && statusData.result?.category) {
          const category = statusData.result.category;
          setResearchState((prev) => ({
            ...prev,
            briefingStatus: {
              ...prev.briefingStatus,
              [category]: true
            }
          }));
        }

        // Handle query updates
        if (statusData.status === "query_generating") {
          setResearchState((prev) => {
            const key = `${statusData.result.category}-${statusData.result.query_number}`;
            return {
              ...prev,
              streamingQueries: {
                ...prev.streamingQueries,
                [key]: {
                  text: statusData.result.query,
                  number: statusData.result.query_number,
                  category: statusData.result.category,
                  isComplete: false
                }
              }
            };
          });
        } else if (statusData.status === "query_generated") {
          setResearchState((prev) => {
            // Remove from streaming queries and add to completed queries
            const key = `${statusData.result.category}-${statusData.result.query_number}`;
            const { [key]: _, ...remainingStreamingQueries } = prev.streamingQueries;
            
            return {
              ...prev,
              streamingQueries: remainingStreamingQueries,
              queries: [
                ...prev.queries,
                {
                  text: statusData.result.query,
                  number: statusData.result.query_number,
                  category: statusData.result.category,
                },
              ],
            };
          });
        }
        // Handle report streaming
        else if (statusData.status === "report_chunk") {
          setOutput((prev) => ({
            summary: "Generating report...",
            details: {
              report_content: prev?.details?.report_content
                ? prev.details.report_content + statusData.result.chunk
                : statusData.result.chunk,
            },
          }));
        }
        // Handle other status updates
        else if (statusData.status === "processing") {
          setIsComplete(false);
          // Only update status.step if we're not in curation or the new step is curation
          if (!status?.step || status.step !== "Curation" || statusData.result?.step === "Curation") {
            setStatus({
              step: statusData.result?.step || "Processing",
              message: statusData.message || "Processing...",
            });
          }
          
          // Reset briefing status when starting a new research
          if (statusData.result?.step === "Briefing") {
            setResearchState((prev) => ({
              ...prev,
              briefingStatus: {
                company: false,
                industry: false,
                financial: false,
                news: false
              }
            }));
          }
          
          scrollToStatus();
        } else if (
          statusData.status === "failed" ||
          statusData.status === "error" ||
          statusData.status === "website_error"
        ) {
          setError(statusData.error || statusData.message || "Research failed");
          if (statusData.status === "website_error" && statusData.result?.continue_research) {
          } else {
            setIsResearching(false);
            setIsComplete(false);
          }
        }
      }
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Handler for 3C analysis form submission
  const handle3CAnalysisSubmit = async (formData: MarketResearchRequest) => {
    // Clear any existing errors first
    setError(null);

    // If research is complete, reset the UI first
    if (isComplete) {
      resetResearch();
      await new Promise(resolve => setTimeout(resolve, 300)); // Wait for reset animation
    }

    // Reset states
    setHasFinalReport(false);
    setReconnectAttempts(0);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    setIsResearching(true);
    setOriginalCompanyName(formData.company || formData.target_market);
    setHasScrolledToStatus(false);
    setThreeCStartTime(new Date());
    
    // Capture agent selection data
    setSelectedAgents(formData.selected_agents || []);
    setAnalysisDepth(formData.analysis_depth || 'comprehensive');
    setAgentPerformance({}); // Reset agent performance

    try {
      const url = `${API_URL}/research/3c-analysis`;

      const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      }).catch((error) => {
        console.error("Fetch error:", error);
        throw error;
      });

      console.log("3C Analysis Response received:", {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log("Error response:", errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("3C Analysis Response data:", data);

      if (data.job_id) {
        console.log("Connecting WebSocket with job_id:", data.job_id);
        connectWebSocket(data.job_id);
      } else {
        throw new Error("No job ID received");
      }
    } catch (err) {
      console.log("Caught error:", err);
      setError(err instanceof Error ? err.message : "Failed to start 3C analysis");
      setIsResearching(false);
    }
  };

  // Create a custom handler for the form that receives form data
  const handleFormSubmit = async (formData: {
    companyName: string;
    companyUrl: string;
    companyHq: string;
    companyIndustry: string;
    competitor: string;
    competitorUrl: string;
    competitorHq: string;
    competitorIndustry: string;
  }) => {

    // Clear any existing errors first
    setError(null);

    // If research is complete, reset the UI first
    if (isComplete) {
      resetResearch();
      await new Promise(resolve => setTimeout(resolve, 300)); // Wait for reset animation
    }

    // Reset states
    setHasFinalReport(false);
    setReconnectAttempts(0);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    setIsResearching(true);
    setOriginalCompanyName(formData.companyName);
    setHasScrolledToStatus(false); // Reset scroll flag when starting new research

    try {
      const url = `${API_URL}/company_analysis`;

      // Format the company URL if provided
      const formattedCompanyUrl = formData.companyUrl
        ? formData.companyUrl.startsWith('http://') || formData.companyUrl.startsWith('https://')
          ? formData.companyUrl
          : `https://${formData.companyUrl}`
        : undefined;

      // Format the competitor URL if provided
      const formattedCompetitorUrl = formData.competitorUrl
        ? formData.competitorUrl.startsWith('http://') || formData.competitorUrl.startsWith('https://')
          ? formData.competitorUrl
          : `https://${formData.competitorUrl}`
        : undefined;

      // Build competitors array
      const competitors = [];
      if (formData.competitor && formData.competitor.trim()) {
        competitors.push({
          company: formData.competitor.trim(),
          company_url: formattedCompetitorUrl,
          hq_location: formData.competitorHq || undefined,
          industry: formData.competitorIndustry || undefined,
        });
      }

      // Log the request details
      const requestData = {
        company: formData.companyName,
        company_url: formattedCompanyUrl,
        industry: formData.companyIndustry || undefined,
        hq_location: formData.companyHq || undefined,
        competitors: competitors, // Add competitors array
      };

      const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      }).catch((error) => {
        console.error("Fetch error:", error);
        throw error;
      });

      console.log("Response received:", {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log("Error response:", errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response data:", data);

      if (data.job_id) {
        console.log("Connecting WebSocket with job_id:", data.job_id);
        connectWebSocket(data.job_id);
      } else {
        throw new Error("No job ID received");
      }
    } catch (err) {
      console.log("Caught error:", err);
      setError(err instanceof Error ? err.message : "Failed to start research");
      setIsResearching(false);
    }
  };

  // Add new function to handle PDF generation
  const handleGeneratePdf = async () => {
    if (!output || isGeneratingPdf) return;
    
    setIsGeneratingPdf(true);
    try {
      console.log("Generating PDF with company name:", originalCompanyName);
      const response = await fetch(`${API_URL}/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_content: output.details.report,
          company_name: originalCompanyName || 'research_report'
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }
      
      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary link element
      const link = document.createElement('a');
      link.href = url;
      link.download = `${originalCompanyName || 'research_report'}.pdf`;
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate PDF');
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Add new function to handle copying to clipboard
  const handleCopyToClipboard = async () => {
    if (!output?.details?.report_content) return;
    
    try {
      await navigator.clipboard.writeText(output.details.report_content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setError('Failed to copy to clipboard');
    }
  };

  // Function to render progress components in order
  const renderProgressComponents = () => {
    const components = [];

    // Research Report (always at the top when available)
    if (output && output.details) {
      components.push(
        <ResearchReport
          key="report"
          output={{
            summary: output.summary,
            details: {
              report_content: output.details.report_content || '',
              competitor_analyses: output.details.competitor_analyses || {}
            }
          }}
          isResetting={isResetting}
          glassStyle={glassStyle}
          fadeInAnimation={fadeInAnimation}
          loaderColor={loaderColor}
          isGeneratingPdf={isGeneratingPdf}
          isCopied={isCopied}
          onCopyToClipboard={handleCopyToClipboard}
          onGeneratePdf={handleGeneratePdf}
        />
      );
    }


    // Research Status (always shown when researching or complete)
    if (status || isResearching || isComplete) {
      components.push(
        <div key="status" ref={statusRef}>
          <ResearchStatus
            status={status}
            error={error}
            isComplete={isComplete}
            currentPhase={currentPhase}
            isResetting={isResetting}
            glassStyle={glassStyle}
            loaderColor={loaderColor}
            statusRef={statusRef}
          />
        </div>
      );
    }

    // 3C Analysis Progress (for 3C analysis type)
    if (analysisType === '3c_analysis' && (isResearching || isComplete)) {
      components.push(
        <ThreeCAnalysisProgress
          key="3c-progress"
          analysisState={threeCAnalysisState}
          currentPhase={threeCCurrentPhase}
          startTime={threeCStartTime || undefined}
          errors={threeCErrors}
          isResetting={false}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
          websocketConnected={websocketConnected}
          selectedAgents={selectedAgents}
          analysisDepth={analysisDepth}
          agentPerformance={agentPerformance}
        />
      );
    }

    // Research Queries (for company research)
    if (analysisType === 'company_research' && shouldShowQueries && researchState.queries.length > 0) {
      components.push(
        <ResearchQueries
          key="queries"
          queries={researchState.queries}
          streamingQueries={researchState.streamingQueries}
          isExpanded={isQueriesExpanded}
          isResetting={isResetting}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
        />
      );
    }

    // Curation Extraction (for company research)
    if (analysisType === 'company_research' && researchState.docCounts) {
      components.push(
        <CurationExtraction
          key="curation"
          docCounts={researchState.docCounts}
          enrichmentCounts={researchState.enrichmentCounts}
          isEnrichmentExpanded={isEnrichmentExpanded}
          isResetting={isResetting}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
        />
      );
    }

    // Research Briefings (for company research)
    if (analysisType === 'company_research' && Object.values(researchState.briefingStatus).some(status => status)) {
      components.push(
        <ResearchBriefings
          key="briefings"
          briefingStatus={researchState.briefingStatus}
          isExpanded={isBriefingExpanded}
          isResetting={isResetting}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
        />
      );
    }

    return components;
  };

  // Add cleanup for polling interval
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Analysis Type Selector */}
        <div className={`${glassStyle.card} mb-8`}>
          <AnalysisTypeSelector
            analysisType={analysisType}
            onAnalysisTypeChange={setAnalysisType}
            isResearching={isResearching}
            glassStyle={glassStyle}
          />
        </div>

        {/* Research Forms */}
        {!isResearching && !isComplete && (
          <div className={`${fadeInAnimation} mb-8`}>
            {analysisType === 'company_research' ? (
              <ResearchForm 
                onSubmit={handleFormSubmit}
                isResearching={isResearching}
                glassStyle={glassStyle}
                loaderColor={loaderColor}
              />
            ) : (
              <MarketAnalysisForm
                onSubmit={handle3CAnalysisSubmit}
                isResearching={isResearching}
                glassStyle={glassStyle}
                loaderColor={loaderColor}
              />
            )}
          </div>
        )}

        {/* Progress Components */}
        <div className="space-y-6">
          {renderProgressComponents()}
        </div>

        {/* Reset Button */}
        {(isComplete || error) && (
          <div className="mt-8 text-center">
            <button
              onClick={resetResearch}
              disabled={isResetting}
              className={`
                px-6 py-3 rounded-lg font-medium text-white transition-all duration-300
                ${isResetting 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transform hover:scale-105 shadow-lg'
                }
              `}
            >
              {isResetting ? 'Resetting...' : 'Start New Research'}
            </button>
          </div>
        )}

        {/* WebSocket Connection Status */}
        {isResearching && (
          <div className="mt-4 text-center">
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
              <div className={`w-2 h-2 rounded-full ${websocketConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>
                {websocketConnected ? 'Connected' : 'Disconnected'}
                {reconnectAttempts > 0 && ` (Reconnect attempts: ${reconnectAttempts})`}
              </span>
              {!websocketConnected && currentJobId && (
                <button
                  onClick={retryWebSocketConnection}
                  className="ml-2 text-blue-600 hover:text-blue-800 underline"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;