"use client";

import React from "react";
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
    </div>
  );
};

export default PredictionMetrics; 