import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReportViewer from './ReportViewer';
import LoadingState from './LoadingState';
import { SharedReport } from '../types';

const SharedReportViewer: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<SharedReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSharedReport = async () => {
      if (!reportId) {
        setError('Invalid report ID');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/shared-reports/${reportId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            setError('Report not found or has expired');
          } else if (response.status === 403) {
            setError('This report is not publicly accessible');
          } else {
            setError('Failed to load report');
          }
          setLoading(false);
          return;
        }

        const sharedReport: SharedReport = await response.json();
        
        // Check if report has expired
        if (sharedReport.expiresAt && new Date(sharedReport.expiresAt) < new Date()) {
          setError('This report has expired');
          setLoading(false);
          return;
        }

        setReport(sharedReport);
      } catch (err) {
        console.error('Error fetching shared report:', err);
        setError('Failed to load report');
      } finally {
        setLoading(false);
      }
    };

    fetchSharedReport();
  }, [reportId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingState message="Loading shared report..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">📄</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Report Not Available</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <a
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Home
          </a>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Report Not Found</h1>
          <p className="text-gray-600 mb-4">The requested report could not be found.</p>
          <a
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        {/* Shared Report Header */}
        <div className="mb-6 text-center">
          <div className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-2">
            📤 Shared Report
          </div>
          <p className="text-gray-600">
            This report was shared on {new Date(report.generatedAt).toLocaleDateString()}
            {report.expiresAt && (
              <span className="ml-2">
                • Expires on {new Date(report.expiresAt).toLocaleDateString()}
              </span>
            )}
          </p>
        </div>

        {/* Report Content */}
        <ReportViewer
          report={report.content}
          reportTitle={report.title}
          analysisType={report.analysisType}
          targetMarket={report.targetMarket}
          generatedAt={report.generatedAt}
          // Don't pass jobId for shared reports to disable sharing button
        />
      </div>
    </div>
  );
};

export default SharedReportViewer;