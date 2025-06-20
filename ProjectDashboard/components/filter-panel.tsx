"use client";

import React from "react";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useFilter } from "@/contexts/filter-context";

const FilterPanel = () => {
  const {
    selectedLevel,
    setSelectedLevel,
    selectedYear,
    setSelectedYear,
    selectedMonth,
    setSelectedMonth,
  } = useFilter();

  // Month names for display
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handleLevelChange = (level: string) => {
    setSelectedLevel(level);
  };

  const handleYearChange = (year: number) => {
    // Special handling for 2010 (only December available)
    if (year === 2010 && selectedMonth !== 12) {
      setSelectedMonth(12);
    }
    
    // Special handling for 2025 (only up to February available)
    if (year === 2025 && selectedMonth > 2) {
      setSelectedMonth(2);
    }
    
    setSelectedYear(year);
  };

  const handleMonthChange = (month: number) => {
    // Special handling for 2010 (only December available)
    if (selectedYear === 2010 && month !== 12) {
      return; // Prevent changing from December 2010
    }
    
    // Special handling for 2025 (only up to February available)
    if (selectedYear === 2025 && month > 2) {
      return; // Prevent months after February 2025
    }
    
    setSelectedMonth(month);
  };

  // Calculate min/max month based on selected year
  const getMonthRange = () => {
    if (selectedYear === 2010) {
      return { min: 12, max: 12 }; // Only December 2010
    } else if (selectedYear === 2025) {
      return { min: 1, max: 2 }; // Only January-February 2025
    } else {
      return { min: 1, max: 12 }; // All months for other years
    }
  };

  const monthRange = getMonthRange();

  const getMonthName = (month: number) => {
    return monthNames[month - 1];
  };

  return (
    <div className="space-y-6">
      {/* Level Selection */}
      <div className="space-y-2">
        <Label className="font-semibold">Boundary Level:</Label>
        <div className="space-y-1">
          {["Ward", "LSOA"].map((level) => (
            <div key={level} className="flex items-center">
              <input
                type="radio"
                id={level}
                name="level"
                className="mr-2"
                checked={selectedLevel === level}
                onChange={() => handleLevelChange(level)}
              />
              <Label htmlFor={level}>{level}</Label>
            </div>
          ))}
        </div>
      </div>

      {/* Year & Month Sliders */}
      <div className="space-y-2">
        <Label className="font-semibold">Time Period:</Label>
        <div className="space-y-4">
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <Label htmlFor="year-slider">Year</Label>
              <span className="text-sm font-medium">{selectedYear}</span>
            </div>
            <Slider
              id="year-slider"
              value={[selectedYear]}
              min={2010}
              max={2025}
              step={1}
              onValueChange={(values) => handleYearChange(values[0])}
              className="py-4"
            />
          </div>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <Label htmlFor="month-slider">
                Month
                {selectedYear === 2010 && (
                  <span className="text-xs text-gray-500 ml-2">(Only Dec 2010 available)</span>
                )}
                {selectedYear === 2025 && (
                  <span className="text-xs text-gray-500 ml-2">(Jan-Feb 2025 only)</span>
                )}
              </Label>
              <span className="text-sm font-medium">{getMonthName(selectedMonth)}</span>
            </div>
            <Slider
              id="month-slider"
              value={[selectedMonth]}
              min={monthRange.min}
              max={monthRange.max}
              step={1}
              onValueChange={(values) => handleMonthChange(values[0])}
              className="py-4"
            />
          </div>
          <div className="text-center text-sm bg-muted rounded-md p-2">
            Viewing data for <span className="font-bold">{monthNames[selectedMonth - 1]} {selectedYear}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel; 