import React from 'react';
import { Github, Sparkles, TrendingUp } from 'lucide-react';

interface HeaderProps {
  glassStyle: string;
}

const Header: React.FC<HeaderProps> = ({ glassStyle }) => {
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('Failed to load Tavily logo');
    console.log('Image path:', e.currentTarget.src);
    e.currentTarget.style.display = 'none';
  };

  return (
    <div className="relative mb-16">
      <div className="text-center pt-8 pb-4">
        {/* Main Title with enhanced styling */}
        <div className="flex items-center justify-center mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-gray-900 font-['DM_Sans'] tracking-tight leading-tight">
                Company Research
                <span className="block text-4xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Agent
                </span>
              </h1>
            </div>
          </div>
        </div>
        
        {/* Enhanced subtitle */}
        <p className="text-xl text-gray-600 font-['DM_Sans'] max-w-2xl mx-auto leading-relaxed">
          Conduct comprehensive company diligence with AI-powered insights
        </p>
        
        {/* Feature highlights */}
        <div className="flex flex-wrap items-center justify-center gap-6 mt-6 text-sm text-gray-500">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <span>AI-Powered Analysis</span>
          </div>
          <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span>Competitor Insights</span>
          </div>
          <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
          <div className="flex items-center space-x-2">
            <Github className="w-4 h-4 text-purple-500" />
            <span>Open Source</span>
          </div>
        </div>
      </div>
      
      {/* Enhanced action buttons */}
      <div className="absolute top-0 right-0 flex items-center space-x-3">
        <a
          href="https://tavily.com"
          target="_blank"
          rel="noopener noreferrer"
          className={`text-gray-600 hover:text-blue-600 transition-all duration-200 ${glassStyle} rounded-xl flex items-center justify-center group`}
          style={{ width: '52px', height: '52px', padding: '4px' }}
          aria-label="Tavily Website"
        >
          <img 
            src="/tavilylogo.png" 
            alt="Tavily Logo" 
            className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-200" 
            style={{ 
              width: '44px', 
              height: '44px',
              display: 'block',
              margin: 'auto'
            }}
            onError={handleImageError}
          />
        </a>
        <a
          href="https://github.com/pogjester/company-research-agent"
          target="_blank"
          rel="noopener noreferrer"
          className={`text-gray-600 hover:text-gray-900 transition-all duration-200 ${glassStyle} rounded-xl flex items-center justify-center group`}
          style={{ width: '48px', height: '48px', padding: '12px' }}
          aria-label="GitHub Repository"
        >
          <Github 
            className="w-6 h-6 group-hover:scale-110 transition-transform duration-200" 
          />
        </a>
      </div>
    </div>
  );
};

export default Header; 