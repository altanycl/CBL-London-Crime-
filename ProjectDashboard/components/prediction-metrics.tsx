"use client";

import React from "react";
<<<<<<< HEAD
import Image from "next/image";

const PredictionMetrics = () => {
  return (
    <div className="space-y-4">
      <div className="bg-black text-white p-2 rounded text-xs font-mono">
        LightGBM : RMSE=20.191, MAE=16.210, MAPE=8.60%
      </div>
      <div className="relative w-full h-[200px] bg-gray-100 rounded-lg overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-gray-500 text-sm">
            Prediction metrics chart
            <br />
            (Chart will be loaded here)
          </p>
        </div>
        {/* In a real implementation, you would use a charting library like recharts */}
        <div className="absolute inset-0 opacity-80">
          <img
            src="/metrics-chart-placeholder.svg"
            alt="Metrics Chart Placeholder"
            className="w-full h-full object-contain"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-100 p-3 rounded-lg">
          <h4 className="text-sm font-semibold">Accuracy</h4>
          <p className="text-2xl font-bold text-blue-600">91.4%</p>
        </div>
        <div className="bg-gray-100 p-3 rounded-lg">
          <h4 className="text-sm font-semibold">Precision</h4>
          <p className="text-2xl font-bold text-green-600">87.2%</p>
        </div>
        <div className="bg-gray-100 p-3 rounded-lg">
          <h4 className="text-sm font-semibold">Recall</h4>
          <p className="text-2xl font-bold text-yellow-600">83.9%</p>
        </div>
        <div className="bg-gray-100 p-3 rounded-lg">
          <h4 className="text-sm font-semibold">F1 Score</h4>
          <p className="text-2xl font-bold text-purple-600">85.5%</p>
        </div>
      </div>
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
    </div>
  );
};

export default PredictionMetrics; 