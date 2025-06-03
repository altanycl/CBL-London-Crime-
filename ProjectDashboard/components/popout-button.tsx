"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import DutySheet from "@/components/duty-sheet";

interface PopoutButtonProps {
  text: string;
  title?: string;
  children?: React.ReactNode;
}

const PopoutButton = ({ text, title, children }: PopoutButtonProps) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      // Dialog will handle the click
    }
  };

  // Extract the main topic from the text for the icon
  const getTopic = () => {
    if (text.includes("Explainability")) return "E";
    if (text.includes("Fairness")) return "F";
    if (text.includes("Duty")) return "D";
    return "?";
  };

  // Get preview content based on the type of report
  const getPreviewContent = () => {
    if (text.includes("Explainability")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-1"></div>
            <span>Model: LightGBM</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Top feature: Previous incidents</span>
          </div>
        </div>
      );
    }
    
    if (text.includes("Fairness")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Equal Opportunity: 0.92</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Demographic Parity: 0.89</span>
          </div>
        </div>
      );
    }
    
    if (text.includes("Duty")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
            <span>High priority areas: 3</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></div>
            <span>Units allocated: 24/32</span>
          </div>
        </div>
      );
    }
    
    return null;
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <div
          className="flex flex-col h-full bg-white hover:bg-blue-50 rounded-lg cursor-pointer transition-colors border border-gray-200 shadow-sm p-3"
          onKeyDown={handleKeyDown}
          tabIndex={0}
          role="button"
          aria-label={text}
        >
          <div className="flex items-center">
            <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center mr-3">
              <span className="text-blue-800 font-semibold text-lg">{getTopic()}</span>
            </div>
            <div className="flex-grow">
              <h3 className="text-gray-800 font-medium">{text.replace("Popout for ", "")}</h3>
              <p className="text-gray-500 text-xs">Click to view detailed information</p>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </div>
          
          {/* Preview content */}
          <div className="mt-3 border-t pt-2">
            {getPreviewContent()}
          </div>
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title || text}</DialogTitle>
          <DialogDescription>
            Detailed information for {text.toLowerCase().replace("popout for ", "")}
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          {children || (
            <div className="space-y-4">
              {text.includes("Explainability") && (
                <ExplainabilityContent />
              )}
              {text.includes("Fairness") && (
                <FairnessContent />
              )}
              {text.includes("Duty Sheet") && (
                <DutySheet />
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Example content components for each popout type
const ExplainabilityContent = () => (
  <div className="space-y-4">
    <p>This report explains how the prediction model works and how it arrived at its predictions.</p>
    
    <div className="border rounded-lg p-4 bg-gray-50">
      <h4 className="font-medium mb-2">Key Features Influencing Predictions</h4>
      <ul className="list-disc pl-5 space-y-2">
        <li>Previous burglary incidents in the area (Importance: 0.32)</li>
        <li>Proximity to transport hubs (Importance: 0.24)</li>
        <li>Population density (Importance: 0.18)</li>
        <li>Time of year and holiday periods (Importance: 0.15)</li>
        <li>Lighting and visibility conditions (Importance: 0.11)</li>
      </ul>
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-2">Model Architecture</h4>
        <p>LightGBM with gradient boosting and 500 estimators</p>
        <p className="text-sm text-gray-500 mt-2">Trained on 5 years of historical data with cross-validation</p>
      </div>
      
      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-2">Feature Engineering</h4>
        <p>Data preprocessed using temporal and spatial aggregation</p>
        <p className="text-sm text-gray-500 mt-2">Includes derived features from geographical and time-based patterns</p>
      </div>
    </div>
    
    <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
      <h4 className="font-medium text-yellow-800 mb-2">Important Disclaimer</h4>
      <p className="text-yellow-700">This model is predictive only and should be used as one of several tools to guide resource allocation decisions.</p>
    </div>
  </div>
);

const FairnessContent = () => (
  <div className="space-y-4">
    <p>This report analyzes the fairness of our predictive model across different demographics and areas.</p>
    
    <div className="border rounded-lg p-4 bg-gray-50">
      <h4 className="font-medium mb-2">Fairness Metrics</h4>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm font-medium">Equal Opportunity</p>
          <p className="text-xl font-bold text-green-600">0.92</p>
        </div>
        <div>
          <p className="text-sm font-medium">Demographic Parity</p>
          <p className="text-xl font-bold text-green-600">0.89</p>
        </div>
        <div>
          <p className="text-sm font-medium">Predictive Parity</p>
          <p className="text-xl font-bold text-yellow-600">0.78</p>
        </div>
        <div>
          <p className="text-sm font-medium">Treatment Equality</p>
          <p className="text-xl font-bold text-green-600">0.94</p>
        </div>
      </div>
    </div>
    
    <div className="border rounded-lg p-4">
      <h4 className="font-medium mb-2">Demographic Distribution Analysis</h4>
      <p>The model has been evaluated across different demographic groups to ensure fair predictions.</p>
      <div className="h-40 w-full bg-gray-100 mt-2 flex items-center justify-center">
        <p className="text-gray-500">Demographic fairness chart placeholder</p>
      </div>
    </div>
    
    <div className="border rounded-lg p-4">
      <h4 className="font-medium mb-2">Area-Based Fairness</h4>
      <p>Analysis of prediction quality across different London boroughs</p>
      <div className="mt-2 space-y-2">
        <div className="grid grid-cols-12 items-center gap-2">
          <div className="col-span-2 text-sm">Westminster</div>
          <div className="col-span-8">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-green-600 h-2.5 rounded-full" style={{ width: '95%' }}></div>
            </div>
          </div>
          <div className="col-span-2 text-sm text-right">95%</div>
        </div>
        <div className="grid grid-cols-12 items-center gap-2">
          <div className="col-span-2 text-sm">Camden</div>
          <div className="col-span-8">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-green-600 h-2.5 rounded-full" style={{ width: '92%' }}></div>
            </div>
          </div>
          <div className="col-span-2 text-sm text-right">92%</div>
        </div>
        <div className="grid grid-cols-12 items-center gap-2">
          <div className="col-span-2 text-sm">Hackney</div>
          <div className="col-span-8">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-yellow-500 h-2.5 rounded-full" style={{ width: '83%' }}></div>
            </div>
          </div>
          <div className="col-span-2 text-sm text-right">83%</div>
        </div>
        <div className="grid grid-cols-12 items-center gap-2">
          <div className="col-span-2 text-sm">Southwark</div>
          <div className="col-span-8">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-green-600 h-2.5 rounded-full" style={{ width: '88%' }}></div>
            </div>
          </div>
          <div className="col-span-2 text-sm text-right">88%</div>
        </div>
        <div className="grid grid-cols-12 items-center gap-2">
          <div className="col-span-2 text-sm">Tower Hamlets</div>
          <div className="col-span-8">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-yellow-500 h-2.5 rounded-full" style={{ width: '81%' }}></div>
            </div>
          </div>
          <div className="col-span-2 text-sm text-right">81%</div>
        </div>
      </div>
    </div>
  </div>
);

export default PopoutButton; 