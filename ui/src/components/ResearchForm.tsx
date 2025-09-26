import React, { useState, useRef, useEffect } from 'react';
import { Building2, Factory, Globe, Loader2, Search, Users, Package, Info, ArrowRight, CheckCircle } from 'lucide-react';
import LocationInput from './LocationInput';
import ExamplePopup, { ExampleCompany } from './ExamplePopup';

interface FormData {
  companyName: string;
  companyUrl: string;
  companyHq: string;
  companyIndustry: string;
  companyProductCategory: string;
  competitor: string;
  competitorUrl: string;
  competitorHq: string;
  competitorIndustry: string;
  competitorProductCategory: string;
}

interface ResearchFormProps {
  onSubmit: (formData: FormData) => Promise<void>;
  isResearching: boolean;
  glassStyle: {
    card: string;
    input: string;
  };
  loaderColor: string;
}

// Default values for fallback
const DEFAULTS = {
  companyName: "House Foods",
  companyUrl: "https://housefoods.jp/company/index.html",
  companyIndustry: "Food & Beverages",
  companyProductCategory: "Curry Roux, Instant Curry",
  companyHq: "Tokyo, Japan",
  competitor: "S&B Foods",
  competitorUrl: "https://www.sbfoods.co.jp/company/",
  competitorIndustry: "Food & Beverages",
  competitorProductCategory: "Curry Roux, Spices, Seasonings",
  competitorHq: "Tokyo, Japan",
};

const ResearchForm: React.FC<ResearchFormProps> = ({
  onSubmit,
  isResearching,
  glassStyle,
  loaderColor
}) => {
  const [formData, setFormData] = useState<FormData>({
    companyName: "",
    companyUrl: "",
    companyHq: "",
    companyIndustry: "",
    companyProductCategory: "",
    competitor: "",
    competitorUrl: "",
    competitorHq: "",
    competitorIndustry: "",
    competitorProductCategory: "",
  });

  const [showExampleSuggestion, setShowExampleSuggestion] = useState(true);
  const [isExampleAnimating, setIsExampleAnimating] = useState(false);
  const [wasResearching, setWasResearching] = useState(false);
  const [currentStep, setCurrentStep] = useState<'company' | 'competitor' | 'review'>('company');
  const [formProgress, setFormProgress] = useState(0);

  const formRef = useRef<HTMLDivElement>(null);
  const exampleRef = useRef<HTMLDivElement>(null);

  // Calculate form progress
  useEffect(() => {
    const totalFields = 10;
    const filledFields = Object.values(formData).filter(value => value.trim() !== '').length;
    setFormProgress((filledFields / totalFields) * 100);
  }, [formData]);

  useEffect(() => {
    if (formData.companyName) {
      setShowExampleSuggestion(false);
    } else if (!isExampleAnimating) {
      setShowExampleSuggestion(true);
    }
  }, [formData.companyName, isExampleAnimating]);

  useEffect(() => {
    if (wasResearching && !isResearching) {
      setTimeout(() => {
        setFormData({
          companyName: "",
          companyUrl: "",
          companyHq: "",
          companyIndustry: "",
          companyProductCategory: "",
          competitor: "",
          competitorUrl: "",
          competitorHq: "",
          competitorIndustry: "",
          competitorProductCategory: "",
        });
        setShowExampleSuggestion(true);
        setCurrentStep('company');
        setFormProgress(0);
      }, 1000);
    }
    setWasResearching(isResearching);
  }, [isResearching, wasResearching]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('Form submitted! Current step:', currentStep);
    console.log('Event target:', e.target);
    
    // Only proceed if we're on the review step and user explicitly clicked submit
    if (currentStep !== 'review') {
      console.log('Form submitted but not on review step, ignoring');
      return;
    }

    // Fallback to defaults if field is empty
    const finalFormData = {
      companyName: formData.companyName || DEFAULTS.companyName,
      companyUrl: formData.companyUrl || DEFAULTS.companyUrl,
      companyIndustry: formData.companyIndustry || DEFAULTS.companyIndustry,
      companyProductCategory: formData.companyProductCategory || DEFAULTS.companyProductCategory,
      companyHq: formData.companyHq || DEFAULTS.companyHq,
      competitor: formData.competitor || DEFAULTS.competitor,
      competitorUrl: formData.competitorUrl || DEFAULTS.competitorUrl,
      competitorIndustry: formData.competitorIndustry || DEFAULTS.competitorIndustry,
      competitorProductCategory: formData.competitorProductCategory || DEFAULTS.competitorProductCategory,
      competitorHq: formData.competitorHq || DEFAULTS.competitorHq,
    };

    console.log('Proceeding with form submission');
    await onSubmit(finalFormData);
  };

  const fillExampleData = (example: ExampleCompany) => {
    setIsExampleAnimating(true);
    if (exampleRef.current && formRef.current) {
      const exampleRect = exampleRef.current.getBoundingClientRect();
      const formRect = formRef.current.getBoundingClientRect();
      const moveX = formRect.left + 20 - exampleRect.left;
      const moveY = formRect.top + 20 - exampleRect.top;
      exampleRef.current.style.transform = `translate(${moveX}px, ${moveY}px) scale(0.6)`;
      exampleRef.current.style.opacity = '0';
    }
    setTimeout(() => {
      const newFormData = {
        companyName: example.name,
        companyUrl: example.url,
        companyHq: example.hq,
        companyIndustry: example.industry,
        companyProductCategory: "Curry Roux, Instant Curry",
        competitor: "S&B Foods",
        competitorUrl: "https://www.sbfoods.co.jp/company/",
        competitorHq: "Tokyo, Japan",
        competitorIndustry: "Food & Beverages",
        competitorProductCategory: "Curry Roux, Spices, Seasonings",
      };
      setFormData(newFormData);
      // Remove automatic submission - let user review and submit manually
      // if (!isResearching) onSubmit(newFormData);
      setIsExampleAnimating(false);
    }, 500);
  };

  const nextStep = () => {
    if (currentStep === 'company') setCurrentStep('competitor');
    else if (currentStep === 'competitor') setCurrentStep('review');
  };

  // Add useEffect to track step changes and prevent auto-submission
  useEffect(() => {
    console.log('Step changed to:', currentStep);
    // Ensure no auto-submission when moving to review step
  }, [currentStep]);

  const prevStep = () => {
    if (currentStep === 'competitor') setCurrentStep('company');
    else if (currentStep === 'review') setCurrentStep('competitor');
  };

  const isCompanyComplete = formData.companyName.trim() !== '';
  const isCompetitorComplete = formData.competitor.trim() !== '';

  return (
    <div className="relative" ref={formRef}>
      <ExamplePopup
        visible={showExampleSuggestion}
        onExampleSelect={fillExampleData}
        glassStyle={glassStyle}
        exampleRef={exampleRef}
      />

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 ${currentStep === 'company' ? 'text-blue-600' : isCompanyComplete ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'company' ? 'bg-blue-100' : isCompanyComplete ? 'bg-green-100' : 'bg-gray-100'}`}>
                {isCompanyComplete ? <CheckCircle className="w-5 h-5" /> : <span className="text-sm font-semibold">1</span>}
              </div>
              <span className="text-sm font-medium">Company Info</span>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
            <div className={`flex items-center space-x-2 ${currentStep === 'competitor' ? 'text-blue-600' : isCompetitorComplete ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'competitor' ? 'bg-blue-100' : isCompetitorComplete ? 'bg-green-100' : 'bg-gray-100'}`}>
                {isCompetitorComplete ? <CheckCircle className="w-5 h-5" /> : <span className="text-sm font-semibold">2</span>}
              </div>
              <span className="text-sm font-medium">Competitor</span>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
            <div className={`flex items-center space-x-2 ${currentStep === 'review' ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'review' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                <span className="text-sm font-semibold">3</span>
              </div>
              <span className="text-sm font-medium">Review</span>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            {Math.round(formProgress)}% Complete
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${formProgress}%` }}
          />
        </div>
      </div>

      <div className={`${glassStyle.card} backdrop-blur-2xl bg-white/90 border-gray-200/50 shadow-xl`}>
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Company Section */}
          {(currentStep === 'company' || currentStep === 'review') && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-800 font-['DM_Sans'] flex items-center">
                  <Building2 className="w-6 h-6 mr-3 text-blue-600" />
                  Main Company
                </h3>
                {isCompanyComplete && (
                  <div className="flex items-center text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Complete
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Company Name */}
                <div className="lg:col-span-2">
                  <InputWithIcon
                    id="companyName"
                    label="Company Name *"
                    value={formData.companyName}
                    onChange={(v) => setFormData((p) => ({ ...p, companyName: v }))}
                    placeholder={DEFAULTS.companyName}
                    Icon={Building2}
                    glassStyle={glassStyle}
                    required={true}
                    helpText="Enter the main company you want to research"
                  />
                </div>
                
                {/* Company URL */}
                <InputWithIcon
                  id="companyUrl"
                  label="Company Website"
                  value={formData.companyUrl}
                  onChange={(v) => setFormData((p) => ({ ...p, companyUrl: v }))}
                  placeholder={DEFAULTS.companyUrl}
                  Icon={Globe}
                  glassStyle={glassStyle}
                  helpText="Optional: Company's official website"
                />
                
                {/* Company HQ */}
                <LocationInput
                  value={formData.companyHq}
                  onChange={(v) => setFormData((p) => ({ ...p, companyHq: v }))}
                  className={`${glassStyle.input}`}
                  placeholder={DEFAULTS.companyHq}
                />
                
                {/* Company Industry */}
                <InputWithIcon
                  id="companyIndustry"
                  label="Industry"
                  value={formData.companyIndustry}
                  onChange={(v) => setFormData((p) => ({ ...p, companyIndustry: v }))}
                  placeholder={DEFAULTS.companyIndustry}
                  Icon={Factory}
                  glassStyle={glassStyle}
                  helpText="e.g., Technology, Healthcare, Finance"
                />
                
                {/* Company Product Category */}
                <InputWithIcon
                  id="companyProductCategory"
                  label="Product Categories"
                  value={formData.companyProductCategory}
                  onChange={(v) => setFormData((p) => ({ ...p, companyProductCategory: v }))}
                  placeholder={DEFAULTS.companyProductCategory}
                  Icon={Package}
                  glassStyle={glassStyle}
                  helpText="Specific products or services to focus on"
                />
              </div>
            </div>
          )}

          {/* Competitor Section */}
          {(currentStep === 'competitor' || currentStep === 'review') && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-800 font-['DM_Sans'] flex items-center">
                  <Users className="w-6 h-6 mr-3 text-purple-600" />
                  Competitor Analysis
                </h3>
                {isCompetitorComplete && (
                  <div className="flex items-center text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Complete
                  </div>
                )}
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Competitor Analysis</p>
                    <p>Provide details about a competitor to compare against your main company. This helps generate more targeted insights.</p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <InputWithIcon
                  id="competitor"
                  label="Competitor Name"
                  value={formData.competitor}
                  onChange={(v) => setFormData((p) => ({ ...p, competitor: v }))}
                  placeholder={DEFAULTS.competitor}
                  Icon={Users}
                  glassStyle={glassStyle}
                  helpText="Name of the competing company"
                />
                
                <InputWithIcon
                  id="competitorUrl"
                  label="Competitor Website"
                  value={formData.competitorUrl}
                  onChange={(v) => setFormData((p) => ({ ...p, competitorUrl: v }))}
                  placeholder={DEFAULTS.competitorUrl}
                  Icon={Globe}
                  glassStyle={glassStyle}
                  helpText="Optional: Competitor's website"
                />
                
                <LocationInput
                  value={formData.competitorHq}
                  onChange={(v) => setFormData((p) => ({ ...p, competitorHq: v }))}
                  className={`${glassStyle.input}`}
                  placeholder={DEFAULTS.competitorHq}
                />
                
                <InputWithIcon
                  id="competitorIndustry"
                  label="Competitor Industry"
                  value={formData.competitorIndustry}
                  onChange={(v) => setFormData((p) => ({ ...p, competitorIndustry: v }))}
                  placeholder={DEFAULTS.competitorIndustry}
                  Icon={Factory}
                  glassStyle={glassStyle}
                  helpText="Industry classification"
                />
                
                <InputWithIcon
                  id="competitorProductCategory"
                  label="Competitor Products"
                  value={formData.competitorProductCategory}
                  onChange={(v) => setFormData((p) => ({ ...p, competitorProductCategory: v }))}
                  placeholder={DEFAULTS.competitorProductCategory}
                  Icon={Package}
                  glassStyle={glassStyle}
                  helpText="Products or services they offer"
                />
              </div>
            </div>
          )}

          {/* Review Section */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-800 font-['DM_Sans'] flex items-center">
                <CheckCircle className="w-6 h-6 mr-3 text-green-600" />
                Review & Submit
              </h3>
              
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">Main Company</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Name:</strong> {formData.companyName || DEFAULTS.companyName}</p>
                    <p><strong>Industry:</strong> {formData.companyIndustry || DEFAULTS.companyIndustry}</p>
                    <p><strong>Products:</strong> {formData.companyProductCategory || DEFAULTS.companyProductCategory}</p>
                    <p><strong>Location:</strong> {formData.companyHq || DEFAULTS.companyHq}</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">Competitor</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Name:</strong> {formData.competitor || DEFAULTS.competitor}</p>
                    <p><strong>Industry:</strong> {formData.competitorIndustry || DEFAULTS.competitorIndustry}</p>
                    <p><strong>Products:</strong> {formData.competitorProductCategory || DEFAULTS.competitorProductCategory}</p>
                    <p><strong>Location:</strong> {formData.competitorHq || DEFAULTS.competitorHq}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <div className="flex space-x-3">
              {currentStep !== 'company' && (
                <button
                  type="button"
                  onClick={prevStep}
                  className="px-6 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  Previous
                </button>
              )}
            </div>
            
            <div className="flex space-x-3">
              {currentStep !== 'review' ? (
                <button
                  type="button"
                  onClick={nextStep}
                  disabled={!isCompanyComplete && currentStep === 'company'}
                  className="px-6 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  Next Step
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isResearching}
                  className="relative group px-8 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 transition-all duration-200 font-medium shadow-lg hover:shadow-xl"
                >
                  {isResearching ? (
                    <>
                      <Loader2 className="animate-spin mr-2 h-5 w-5 inline" style={{ stroke: loaderColor }} />
                      Starting Research...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-5 w-5 inline" />
                      Start Research
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResearchForm;

// Enhanced InputWithIcon component with help text
const InputWithIcon = ({
  id,
  label,
  value,
  onChange,
  placeholder,
  Icon,
  glassStyle,
  required = false,
  helpText,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  Icon: React.FC<any>;
  glassStyle: any;
  required?: boolean;
  helpText?: string;
}) => (
  <div className="relative group">
    <label
      htmlFor={id}
      className="block text-base font-medium text-gray-700 mb-2.5 transition-all duration-200 group-hover:text-gray-900 font-['DM_Sans']"
    >
      {label}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
    <div className="relative">
      <Icon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 stroke-[#468BFF]" strokeWidth={1.5} />
      <input
        required={required}
        id={id}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`${glassStyle.input} pl-12 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200`}
        placeholder={placeholder}
      />
    </div>
    {helpText && (
      <p className="mt-1 text-sm text-gray-500">{helpText}</p>
    )}
  </div>
);
