"use client";

import React from "react";

const PoliceAllocation = () => {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="font-semibold">Recommendation + Money Saved & Reallocated</h3>
      </div>
      
      <div className="bg-white rounded-lg p-3 shadow-sm">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Current Budget:</span>
            <span className="font-semibold">£1,250,000</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Optimized Budget:</span>
            <span className="font-semibold text-green-600">£1,125,000</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Savings:</span>
            <span className="font-semibold text-green-600">£125,000</span>
          </div>
          <div className="h-1 w-full bg-gray-200 rounded-full">
            <div className="h-1 bg-green-500 rounded-full" style={{ width: '10%' }}></div>
          </div>
          <div className="text-xs text-gray-500 text-right">10% savings</div>
        </div>
      </div>

      <div className="bg-white rounded-lg p-3 shadow-sm">
        <h4 className="text-sm font-semibold mb-2">Resource Allocation</h4>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs">Patrol Units:</span>
            <span className="text-xs font-medium">28 → 32</span>
          </div>
          <div className="h-2 w-full bg-gray-200 rounded-full">
            <div className="h-2 bg-blue-500 rounded-full" style={{ width: '75%' }}></div>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs">Investigation Units:</span>
            <span className="text-xs font-medium">15 → 12</span>
          </div>
          <div className="h-2 w-full bg-gray-200 rounded-full">
            <div className="h-2 bg-purple-500 rounded-full" style={{ width: '40%' }}></div>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs">Community Support:</span>
            <span className="text-xs font-medium">10 → 14</span>
          </div>
          <div className="h-2 w-full bg-gray-200 rounded-full">
            <div className="h-2 bg-yellow-500 rounded-full" style={{ width: '60%' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PoliceAllocation; 