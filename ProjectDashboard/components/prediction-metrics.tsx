"use client";

import React from "react";
import { BarChart2, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";

const timeBasedStats = {
  mse: 0.4158,
  rmse: 0.6448,
  mae: 0.3183,
  r2: 0.6707,
};
const randomSplitStats = {
  mse: 0.8619,
  rmse: 0.9284,
  mae: 0.5134,
  r2: 0.6194,
};

const MetricCard = ({ title, stats, accent }: { title: React.ReactNode; stats: any; accent: string }) => (
  <div className={`bg-white border shadow-md rounded-xl p-4 flex flex-col gap-2 ${accent}`}>
    <div className="flex items-center gap-2 mb-1">
      <BarChart2 className="w-5 h-5 text-blue-500" />
      <h4 className="text-base font-semibold">{title}</h4>
    </div>
    <div className="flex flex-wrap gap-4 text-xs font-mono mt-1">
      <div className="flex items-center gap-1"><AlertCircle className="w-4 h-4 text-red-400" />MSE: <span className="font-bold">{stats.mse}</span></div>
      <div className="flex items-center gap-1"><TrendingUp className="w-4 h-4 text-purple-400" />RMSE: <span className="font-bold">{stats.rmse}</span></div>
      <div className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-400" />MAE: <span className="font-bold">{stats.mae}</span></div>
      <div className="flex items-center gap-1"><span className="text-yellow-600 font-bold">R²:</span> <span className="font-bold">{stats.r2}</span></div>
    </div>
  </div>
);

const PredictionMetrics = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricCard title="Time-based Model (Last Month Hold-out)" stats={timeBasedStats} accent="border-blue-100" />
        <MetricCard 
          title={
            <>
              Random 80/20 Split
              <br />
              (LightGBM)
            </>
          } 
          stats={randomSplitStats} 
          accent="border-purple-100" 
        />
      </div>
      <div className="bg-gradient-to-br from-blue-50 to-white border border-blue-100 p-4 rounded-xl shadow flex flex-col items-center mt-4">
        <h4 className="font-semibold mb-2 text-blue-900">Predicted vs Actual Values</h4>
        <div className="w-full flex justify-center bg-white rounded-lg shadow-inner p-2 border border-gray-200">
          <img
            src="/data/predicted_vs_actual.png"
            alt="Predicted vs Actual Plot"
            className="max-h-[280px] w-auto rounded"
          />
        </div>
      </div>
    </div>
  );
};

export default PredictionMetrics; 