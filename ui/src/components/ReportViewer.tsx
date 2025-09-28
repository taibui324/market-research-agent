import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Download, Share2, Printer, FileText, Globe, FileDown } from 'lucide-react';
// Temporarily disable these imports to fix the app crash
// import jsPDF from 'jspdf';
// import html2canvas from 'html2canvas';

interface ReportViewerProps {
  report: string;
  reportTitle?: string;
  analysisType?: string;
  targetMarket?: string;
  generatedAt?: string;
  jobId?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  report,
  reportTitle = 'Market Research Report',
  analysisType = '3C Analysis',
  targetMarket = '',
  generatedAt,
  jobId
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  // Generate filename with timestamp
  const generateFilename = (extension: string): string => {
    const timestamp = generatedAt ? new Date(generatedAt).toISOString().slice(0, 19).replace(/[:.]/g, '-') : new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
    const marketSegment = targetMarket ? `_${targetMarket.toLowerCase().replace(/\s+/g, '-')}` : '';
    return `${analysisType.toLowerCase().replace(/\s+/g, '-')}-report${marketSegment}_${timestamp}.${extension}`;
  };

  // Export as Markdown
  const exportAsMarkdown = () => {
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = generateFilename('md');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Export as HTML
  const exportAsHTML = () => {
    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${reportTitle}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2563eb;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        h1 {
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0.5rem;
        }
        h2 {
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 0.25rem;
        }
        ul, ol {
            padding-left: 1.5rem;
        }
        li {
            margin-bottom: 0.5rem;
        }
        blockquote {
            border-left: 4px solid #3b82f6;
            margin: 1rem 0;
            padding-left: 1rem;
            color: #6b7280;
        }
        code {
            background-color: #f3f4f6;
            padding: 0.125rem 0.25rem;
            border-radius: 0.25rem;
            font-family: 'Monaco', 'Menlo', monospace;
        }
        pre {
            background-color: #f3f4f6;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #d1d5db;
            padding: 0.75rem;
            text-align: left;
        }
        th {
            background-color: #f9fafb;
            font-weight: 600;
        }
        .report-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e5e7eb;
        }
        .report-meta {
            color: #6b7280;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }
        @media print {
            body {
                padding: 1rem;
            }
            .no-print {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>${reportTitle}</h1>
        <div class="report-meta">
            <p><strong>Analysis Type:</strong> ${analysisType}</p>
            ${targetMarket ? `<p><strong>Target Market:</strong> ${targetMarket}</p>` : ''}
            ${generatedAt ? `<p><strong>Generated:</strong> ${new Date(generatedAt).toLocaleString()}</p>` : ''}
        </div>
    </div>
    <div class="report-content">
        ${report}
    </div>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = generateFilename('html');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Export as PDF - temporarily disabled
  const exportAsPDF = async () => {
    alert('PDF export is temporarily disabled. Please use HTML or Markdown export instead.');
    // TODO: Re-enable when jsPDF import issue is resolved
    /*
    if (!reportRef.current) return;

    setIsExporting(true);
    try {
      const html2canvas = await import('html2canvas');
      const jsPDF = await import('jspdf');
      
      const canvas = await html2canvas.default(reportRef.current, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff'
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF.default('p', 'mm', 'a4');
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 30;

      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
      pdf.save(generateFilename('pdf'));
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsExporting(false);
    }
    */
  };

  // Generate shareable URL
  const generateShareUrl = async () => {
    if (!jobId) {
      alert('Report sharing is not available for this report.');
      return;
    }

    try {
      // Import API service dynamically to avoid circular dependencies
      const { apiService } = await import('../services/api');
      const response = await apiService.createShareableReport(jobId, 30); // 30 days expiration
      
      if (response.success && response.data) {
        const shareableUrl = `${window.location.origin}/shared-report/${response.data.shareId}`;
        setShareUrl(shareableUrl);
        setShowShareModal(true);
        
        // Copy to clipboard
        await navigator.clipboard.writeText(shareableUrl);
      } else {
        throw new Error(response.error || 'Failed to create shareable link');
      }
    } catch (error) {
      console.error('Error generating share URL:', error);
      alert('Failed to generate share URL. Please try again.');
    }
  };

  // Print report
  const printReport = () => {
    window.print();
  };

  // Copy share URL to clipboard
  const copyShareUrl = async () => {
    if (shareUrl) {
      try {
        await navigator.clipboard.writeText(shareUrl);
        alert('Share URL copied to clipboard!');
      } catch (error) {
        console.error('Error copying to clipboard:', error);
      }
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Export Controls */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200 no-print">
        <div className="flex flex-wrap gap-3 items-center justify-between">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={exportAsMarkdown}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <FileText size={16} />
              Export Markdown
            </button>
            
            <button
              onClick={exportAsHTML}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Globe size={16} />
              Export HTML
            </button>
            
            <button
              onClick={exportAsPDF}
              disabled={isExporting}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileDown size={16} />
              {isExporting ? 'Generating PDF...' : 'Export PDF'}
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={printReport}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Printer size={16} />
              Print
            </button>
            
            {jobId && (
              <button
                onClick={generateShareUrl}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <Share2 size={16} />
                Share
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Report Content */}
      <div 
        ref={reportRef}
        className="bg-white rounded-lg shadow-sm border border-gray-200 print:shadow-none print:border-none"
      >
        {/* Report Header */}
        <div className="p-6 border-b border-gray-200 print:border-gray-400">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{reportTitle}</h1>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Analysis Type:</strong> {analysisType}</p>
            {targetMarket && <p><strong>Target Market:</strong> {targetMarket}</p>}
            {generatedAt && (
              <p><strong>Generated:</strong> {new Date(generatedAt).toLocaleString()}</p>
            )}
          </div>
        </div>

        {/* Markdown Content */}
        <div className="p-6 prose prose-lg max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
              h1: ({ children }) => (
                <h1 className="text-2xl font-bold text-blue-600 mt-8 mb-4 pb-2 border-b border-gray-200">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl font-semibold text-blue-600 mt-6 mb-3 pb-1 border-b border-gray-100">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold text-gray-800 mt-5 mb-2">
                  {children}
                </h3>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-inside space-y-2 my-4 text-gray-700">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside space-y-2 my-4 text-gray-700">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="leading-relaxed">{children}</li>
              ),
              p: ({ children }) => (
                <p className="mb-4 leading-relaxed text-gray-700">{children}</p>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-blue-500 pl-4 my-4 italic text-gray-600">
                  {children}
                </blockquote>
              ),
              code: ({ children }) => (
                <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4">
                  {children}
                </pre>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border-collapse border border-gray-300">
                    {children}
                  </table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border border-gray-300 px-4 py-2 bg-gray-50 font-semibold text-left">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-gray-300 px-4 py-2">{children}</td>
              ),
            }}
          >
            {report}
          </ReactMarkdown>
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 no-print">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Share Report</h3>
            <p className="text-gray-600 mb-4">
              Share this report with others using the link below:
            </p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={shareUrl || ''}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
              />
              <button
                onClick={copyShareUrl}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Copy
              </button>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowShareModal(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Print Styles */}
      <style jsx>{`
        @media print {
          .no-print {
            display: none !important;
          }
          
          body {
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
          }
          
          .prose h1,
          .prose h2,
          .prose h3 {
            break-after: avoid;
            page-break-after: avoid;
          }
          
          .prose p,
          .prose li {
            orphans: 3;
            widows: 3;
          }
          
          .prose table {
            break-inside: avoid;
          }
        }
      `}</style>
    </div>
  );
};

export default ReportViewer;