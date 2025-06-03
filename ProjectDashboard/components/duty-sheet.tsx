"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

interface DutySheetProps {
  onPrint?: () => void;
}

const DutySheet = ({ onPrint }: DutySheetProps) => {
  const [showAllAreas, setShowAllAreas] = useState(false);
  
  const areas = [
    {
      name: "Camden Town",
      shift: "18:00-02:00",
      units: 4,
      priority: "High",
      notes: "Focus on market area and station surroundings"
    },
    {
      name: "Soho",
      shift: "20:00-04:00",
      units: 5,
      priority: "High",
      notes: "Entertainment district, coordinate with venue security"
    },
    {
      name: "Kensington",
      shift: "22:00-06:00",
      units: 3,
      priority: "Medium",
      notes: "Residential focus, particular attention to mews and garden entries"
    },
    {
      name: "Hackney Central",
      shift: "19:00-03:00",
      units: 3,
      priority: "Medium",
      notes: "Transport hub and surrounding streets"
    },
    {
      name: "Richmond",
      shift: "21:00-05:00",
      units: 2,
      priority: "Low",
      notes: "Riverside area and high-value residences"
    },
    {
      name: "Islington",
      shift: "19:00-01:00",
      units: 2,
      priority: "Medium",
      notes: "High street and residential mix"
    },
    {
      name: "Brixton",
      shift: "20:00-04:00",
      units: 3,
      priority: "Medium",
      notes: "Focus on transportation nodes and nightlife areas"
    },
    {
      name: "Stratford",
      shift: "18:00-02:00",
      units: 4,
      priority: "High",
      notes: "Shopping center and transportation hub"
    }
  ];

  const visibleAreas = showAllAreas ? areas : areas.slice(0, 5);

  const handlePrint = () => {
    if (onPrint) {
      onPrint();
    } else {
      window.print();
    }
  };

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority) {
      case "High":
        return "px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs";
      case "Medium":
        return "px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs";
      case "Low":
        return "px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs";
      default:
        return "px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs";
    }
  };

  return (
    <div className="space-y-4">
      <p>This duty sheet provides recommended patrol areas and schedules based on prediction models.</p>
      
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Patrol Allocations for {new Date().toLocaleDateString()}</h3>
        <div className="space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowAllAreas(!showAllAreas)}
          >
            {showAllAreas ? "Show Less" : "Show All"}
          </Button>
          <Button variant="default" size="sm" onClick={handlePrint}>
            Print Sheet
          </Button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-100">
            <tr>
              <th className="py-2 px-4 border">Area</th>
              <th className="py-2 px-4 border">Shift</th>
              <th className="py-2 px-4 border">Units Required</th>
              <th className="py-2 px-4 border">Priority</th>
              <th className="py-2 px-4 border">Special Notes</th>
            </tr>
          </thead>
          <tbody>
            {visibleAreas.map((area, index) => (
              <tr key={index}>
                <td className="py-2 px-4 border">{area.name}</td>
                <td className="py-2 px-4 border">{area.shift}</td>
                <td className="py-2 px-4 border">{area.units}</td>
                <td className="py-2 px-4 border">
                  <span className={getPriorityBadgeClass(area.priority)}>
                    {area.priority}
                  </span>
                </td>
                <td className="py-2 px-4 border">{area.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="flex flex-col md:flex-row justify-between gap-4 mt-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 flex-1">
          <h4 className="font-medium text-blue-800 mb-2">Special Operation: Weekend Coverage</h4>
          <p className="text-sm text-blue-600">Additional 15 officers deployed to high-risk areas Fri-Sun</p>
          <div className="mt-2 pt-2 border-t border-blue-200">
            <span className="text-xs text-blue-500">Authorized by: Superintendent J. Smith</span>
          </div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200 flex-1">
          <h4 className="font-medium text-purple-800 mb-2">Resources Available</h4>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-xs text-purple-700">Patrol Units:</p>
              <p className="font-bold text-purple-900">32/40</p>
            </div>
            <div>
              <p className="text-xs text-purple-700">Investigation Units:</p>
              <p className="font-bold text-purple-900">12/15</p>
            </div>
            <div>
              <p className="text-xs text-purple-700">Support Staff:</p>
              <p className="font-bold text-purple-900">14/20</p>
            </div>
            <div>
              <p className="text-xs text-purple-700">Emergency Reserve:</p>
              <p className="font-bold text-purple-900">8/10</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 text-sm text-gray-500">
        <p>This duty sheet is generated based on predictive analysis of crime patterns and available resources. Allocation may be adjusted based on real-time incidents and operational requirements.</p>
      </div>
    </div>
  );
};

export default DutySheet; 