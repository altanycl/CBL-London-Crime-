"use client";

import React, { useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import DutySheet from "@/components/duty-sheet";
import { dutySheetCache, setDutySheetCache } from "./duty-sheet-cache";
import { CalendarDays, Lightbulb, Scale, ClipboardList } from "lucide-react";

interface PopoutButtonProps {
  text: string;
  title?: string;
  children?: React.ReactNode;
  icon?: 'calendar' | 'lightbulb' | 'scales' | 'clipboard' | 'default';
}

const PopoutButton = ({ text, title, children, icon = 'default' }: PopoutButtonProps) => {
  const [dutyData, setDutyData] = React.useState<any[] | null>(dutySheetCache.value);

  React.useEffect(() => {
    if (!text.includes("Duty")) return;
    if (dutySheetCache.value) {
      setDutyData(dutySheetCache.value);
      return;
    }
    fetch("/api/duty-sheet")
      .then((res) => res.json())
      .then((result) => {
        setDutySheetCache(result.duty_sheet);
        setDutyData(result.duty_sheet);
      });
  }, [text]);

  // Memoize Tier 1 stats calculation
  const tier1Stats = useMemo(() => {
    if (!dutyData) return { count: null, hours: null };
    const tier1 = dutyData.filter((item) => item.tier === "Tier 1");
    return {
      count: tier1.length,
      hours: tier1.reduce((sum, item) => sum + (item.hours_per_week || 0), 0),
    };
  }, [dutyData]);

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
  const getPreviewContent = useMemo(() => {
    if (text.includes("Explainability")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-1"></div>
            <span>Model: LightGBM</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Top feature: Rank Last Year</span>
          </div>
        </div>
      );
    }
    
    if (text.includes("Fairness")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Non-white people including Romani people:	0.034</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            <span>Black people:	0.033</span>
          </div>
        </div>
      );
    }
    
    if (text.includes("Duty")) {
      return (
        <div className="mt-2 text-xs text-gray-600">
          <div className="flex items-center mb-1">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
            <span>Tier 1 areas: {tier1Stats.count !== null ? tier1Stats.count : "..."}</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-1"></div>
            <span>Tier 1 hours allocated: {tier1Stats.hours !== null ? tier1Stats.hours.toFixed(2) : "..."}</span>
          </div>
        </div>
      );
    }
    
    return null;
  }, [text, tier1Stats]);

  // Icon rendering logic
  let IconComponent = null;
  if (icon === 'calendar') {
    IconComponent = <CalendarDays className="w-6 h-6 text-blue-500" />;
  } else if (icon === 'lightbulb') {
    IconComponent = <Lightbulb className="w-6 h-6 text-yellow-500" />;
  } else if (icon === 'scales') {
    IconComponent = <Scale className="w-6 h-6 text-green-500" />;
  } else if (icon === 'clipboard') {
    IconComponent = <ClipboardList className="w-6 h-6 text-indigo-500" />;
  } else {
    IconComponent = <span className="w-6 h-6 flex items-center justify-center text-blue-500 font-bold text-lg">?</span>;
  }

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
              {IconComponent}
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
            {getPreviewContent}
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
                <DutySheetContent />
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Example content components for each popout type
export const ExplainabilityContent = () => (
  <div className="space-y-6">
    <p>This report explains how the prediction model works and how it arrived at its predictions.</p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="border rounded-lg p-4 bg-blue-50 shadow">
        <h4 className="font-medium mb-2 text-blue-900">Top Features (Time-based Model)</h4>
        <ul className="list-disc pl-5 space-y-2 text-sm">
          <li>rank_last_year: 1386</li>
          <li>year: 1051</li>
          <li>crime_count_lag1: 424</li>
          <li>crime_count_lag3: 343</li>
          <li>month_sin: 318</li>
        </ul>
      </div>
      <div className="border rounded-lg p-4 bg-purple-50 shadow">
        <h4 className="font-medium mb-2 text-purple-900">Top Features (Random Split Model)</h4>
        <ul className="list-disc pl-5 space-y-2 text-sm">
          <li>rank_last_year: 1351</li>
          <li>year: 1008</li>
          <li>crime_count_lag1: 400</li>
          <li>crime_count_lag3: 377</li>
          <li>month_sin: 327</li>
        </ul>
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
      <div className="flex flex-col items-center">
        <h5 className="font-semibold text-blue-900 mb-2">Feature Importance (Time-based Model)</h5>
        <img src="/data/feature_importance_time.png" alt="Feature Importance Time-based" style={{ imageRendering: 'auto' }} className="w-full max-w-[500px] max-h-[350px] rounded shadow border border-blue-100" />
      </div>
      <div className="flex flex-col items-center">
        <h5 className="font-semibold text-purple-900 mb-2">Feature Importance (Random Split Model)</h5>
        <img src="/data/feature_importance_random.png" alt="Feature Importance Random" style={{ imageRendering: 'auto' }} className="w-full max-w-[500px] max-h-[350px] rounded shadow border border-purple-100" />
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm">
        <h5 className="font-semibold text-blue-900 mb-1">Time-based Model (Last Month Hold-out)</h5>
        <p>We partition data temporally strictly—training on every month up to January and leaving February for testing—and we hyperparameter-tune using GridSearchCV and TimeSeriesSplit so that every fold "trains on the past and validates on the next month." This forward-chaining CV entirely avoids look-ahead bias such that the model never sees February until prediction time. Because it is mirroring the real-world forecast situation of continually updating on previous data to predict near-term futures, its numbers, while sometimes more erratic, represent the best possible estimate of real next-month performance.</p>
      </div>
      <div className="bg-purple-50 border border-purple-100 rounded-lg p-4 text-sm">
        <h5 className="font-semibold text-purple-900 mb-1">Random 80/20 Split Model</h5>
        <p>We randomly shuffle all rows (mixing months and wards), train on 80 % of those mixed records, and test on the remaining 20 %. Because the test set reflects the same seasonal patterns, trends, and outlier months as the training data, error metrics (MSE, RMSE, MAE, R²) tend to be more stable and consistent—this gives you the baseline performance you'd expect under standard, IID assumptions. We don't run a separate grid search here; instead, we simply reuse the best hyperparameters found via our time-based tuning.</p>
      </div>
    </div>
    <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mt-4">
      <h4 className="font-medium text-yellow-800 mb-2">Important Disclaimer</h4>
      <p className="text-yellow-700">This model is predictive only and should be used as one of several tools to guide resource allocation decisions.</p>
    </div>
  </div>
);

export const FairnessContent = () => (
  <div className="space-y-6">
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">Demographic Correlation Analysis</h3>
      <p className="text-sm text-blue-800">
        We used the 2021 census data to find the correlation(s) between the percentage of different (combinations of) ethnic groups in an LSOA and burglaries that happened in that LSOA from 2021 onward. The table below shows the correlation and p-value for each group. Most correlations are low (|r| &lt; 0.1), but there is a moderate correlation for people of Arab descent (r ≈ 0.15, p ≪ 0.05). This may reflect a slight historical bias against people of Arab descent in the dataset, and could indicate that the model may also have such a bias. Police and users should consider this when planning schedules and policies.
      </p>
    </div>
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border rounded-lg bg-white">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-2 text-left">Ethnicity Group</th>
            <th className="px-4 py-2 text-left">Correlation with true data</th>
            <th className="px-4 py-2 text-left">P-Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="px-4 py-2">Non-white people including Romani people</td>
            <td className="px-4 py-2">0.034</td>
            <td className="px-4 py-2">0.0166</td>
          </tr>
          <tr>
            <td className="px-4 py-2">Black people</td>
            <td className="px-4 py-2">0.033</td>
            <td className="px-4 py-2">0.0202</td>
          </tr>
          <tr>
            <td className="px-4 py-2">White people</td>
            <td className="px-4 py-2">-0.034</td>
            <td className="px-4 py-2">0.0166</td>
          </tr>
          <tr>
            <td className="px-4 py-2">Asian Subcontinent people</td>
            <td className="px-4 py-2">-0.084</td>
            <td className="px-4 py-2">3.08e-9</td>
          </tr>
          <tr>
            <td className="px-4 py-2">Other Asian people</td>
            <td className="px-4 py-2">0.090</td>
            <td className="px-4 py-2">2.69e-10</td>
          </tr>
          <tr>
            <td className="px-4 py-2">Arab people</td>
            <td className="px-4 py-2">0.153</td>
            <td className="px-4 py-2">1.17e-27</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
      <h4 className="font-semibold text-yellow-800 mb-2">Interpretation & Recommendation</h4>
      <p className="text-yellow-700 text-sm">
        While most ethnic group correlations are low, the moderate correlation for Arab descent suggests a possible bias in historical data and potentially in the model. We recommend that police and users review these findings and consider more progressive or bias-aware approaches to resource allocation and policing.
      </p>
    </div>
  </div>
);

export const DutySheetContent = () => <DutySheet />;

export const AllocationExplanationContent = () => (
  <div className="space-y-4 text-sm">
    <ol className="list-decimal pl-5 space-y-2">
      <li>
        <span className="font-semibold">Crime forecasts & score-to-hours conversion:</span> we predict the number of burglaries in the next month for each LSOA using LightGBM. Those raw forecasts are turned into a <span className="font-semibold">risk score</span> by squaring each prediction and normalizing so that all scores in a ward sum to 1. Finally, we allocate weekly patrol hours by:
        <ul className="list-disc pl-5 mt-1">
          <li><span className="font-semibold">Hot wards</span> (contain a top-3% LSOA): every LSOA gets a 20 h baseline, and the remaining hours (800 – 20×N) are split in proportion to those normalized squared scores.</li>
          <li><span className="font-semibold">Cold wards:</span> the wards that contain only tier 3 LSOAs. We make no specific reallocation but we have a suggestion to keep a 20 hours per lsoa baseline</li>
        </ul>
      </li>
      <li>
        <span className="font-semibold">Three risk tiers:</span>
        <ul className="list-disc pl-5 mt-1">
          <li><span className="font-semibold">Tier 1:</span> top 1% of forecasts</li>
          <li><span className="font-semibold">Tier 2:</span> next 2% (1–3%)</li>
          <li><span className="font-semibold">Tier 3:</span> remaining 97%</li>
        </ul>
      </li>
      <li>
        <span className="font-semibold">Ward selection:</span> only wards with at least one Tier 1 or Tier 2 area receive a new patrol-hour recommendation.
      </li>
      <li>
        <span className="font-semibold">Cold-ward status quo:</span> wards without any Tier 1/2 areas have 20h allocated for each LSOA.
      </li>
      <li>
        <span className="font-semibold">Squared weighting rationale:</span> squaring the forecast makes an area with twice the predicted crimes receive four times the extra patrol time, focusing resources on the riskiest spots.
      </li>
      <li>
        <span className="font-semibold">Quality checks & oversight:</span> every ward still sums to 800 h, no hot-ward LSOA falls below 20 h, and supervisors should review suggestions against real-world events.
      </li>
    </ol>
  </div>
);

export const MajorEventsPolicePresenceContent = () => (
  <div className="space-y-6 text-sm">
    <p>
      <b>Special operations and increased police presence will be scheduled on the following dates:</b>
    </p>
    <div className="space-y-4">
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">January 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>1 Jan:</b> London New Year's Day Parade (West End)</li>
          <li><b>15 Jan:</b> Arsenal vs Tottenham Hotspur (North London Derby @ Emirates Stadium)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">February 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>2 Feb:</b> Chinese New Year Parade (Trafalgar Square → Chinatown)</li>
          <li><b>20–24 Feb:</b> London Fashion Week (various venues)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">March 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>1 Mar:</b> The BRIT Awards (The O2 Arena)</li>
          <li><b>16 Mar:</b> Carabao Cup Final (Wembley Stadium)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">April 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>13 Apr:</b> EFL Trophy Final (Wembley Stadium)</li>
          <li><b>27 Apr:</b> London Marathon (Greenwich Park → St James's Park)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">May 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>17 May:</b> FA Cup Final (Wembley Stadium)</li>
          <li><b>24 May:</b> Field Day Festival (Brockwell Park, Brixton)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">June 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>14 Jun:</b> Trooping the Colour (Horse Guards Parade)</li>
          <li><b>20–21 Jun:</b> Dua Lipa "Radical Optimism" shows (Wembley Stadium)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">July 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>5 Jul:</b> Pride in London Parade (Park Lane → Trafalgar Square)</li>
          <li><b>11–13 Jul:</b> Wireless Festival (Finsbury Park)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">August 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>9 Aug:</b> FA Community Shield (Wembley Stadium)</li>
          <li><b>23–25 Aug:</b> Notting Hill Carnival (Ladbroke Grove area)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">September 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>13–21 Sep:</b> London Design Festival (city-wide)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">October 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>15–19 Oct:</b> Frieze London & Frieze Masters (Regent's Park)</li>
          <li><b>8–19 Oct:</b> BFI London Film Festival (multiple venues)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">November 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>8 Nov:</b> Lord Mayor's Show (City of London)</li>
          <li><b>28 Nov–7 Dec:</b> London International Animation Festival (Barbican Centre)</li>
        </ul>
      </div>
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-md p-3">
        <h3 className="font-semibold text-blue-900 mb-1">December 2025</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>Late Nov–early Jan:</b> Winter Wonderland (Hyde Park)</li>
          <li><b>31 Dec:</b> London New Year's Eve Fireworks (Thames/Westminster)</li>
        </ul>
      </div>
    </div>
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <h3 className="font-semibold mb-2">Why? Research Evidence</h3>
      <ul className="list-disc pl-5 space-y-2">
        <li>
          <b>Block's Pinkerton analysis</b> found a <b>7.4% increase</b> in property crimes (e.g. burglaries) on NFL home-game days versus away days. <a href="https://pinkerton.com" target="_blank" rel="noopener noreferrer" className="underline text-blue-700">pinkerton.com</a>
        </li>
        <li>
          <b>Baumann et al. (2012)</b> observed roughly a <b>10% rise</b> in property crime during Olympic host years. <a href="https://researchgate.net" target="_blank" rel="noopener noreferrer" className="underline text-blue-700">researchgate.net</a>
        </li>
      </ul>
      <p className="mt-2">
        These patterns reflect how large crowds and diverted guardianship create more opportunities for offenders—so on dates with major football matches, festivals, or concerts, special operations attention is warranted.
      </p>
    </div>
  </div>
);

export default PopoutButton; 