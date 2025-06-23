"use client";

<<<<<<< HEAD
import React, { useState } from "react";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";

const FilterPanel = () => {
  const [selectedLevel, setSelectedLevel] = useState<string>("Borough");
  const [topByLevel, setTopByLevel] = useState<number>(5);
  const [selectedYear, setSelectedYear] = useState<number>(2023);
  const [selectedMonth, setSelectedMonth] = useState<number>(6);

  // Define max values for each level
  const maxTopValues = {
    Borough: 33, // London has 33 boroughs
    Ward: 20,    // Default max for wards
    LSOA: 15     // Default max for LSOAs
  };
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb

  // Month names for display
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handleLevelChange = (level: string) => {
<<<<<<< HEAD
    console.log(`Selected level: ${level}`);
    setSelectedLevel(level);
    // Reset top value when level changes to avoid having a value higher than the max
    setTopByLevel(Math.min(topByLevel, maxTopValues[level as keyof typeof maxTopValues]));
  };

  const handleYearChange = (values: number[]) => {
    const year = values[0];
    console.log(`Year changed: ${year}`);
    setSelectedYear(year);
  };

  const handleMonthChange = (values: number[]) => {
    const month = values[0];
    console.log(`Month changed: ${month}`);
    setSelectedMonth(month);
  };

  const handleTopByLevelChange = (value: number) => {
    console.log(`Top by level changed: ${value}`);
    setTopByLevel(value);
  };

  const handleAllocationChange = (values: number[]) => {
    console.log(`Allocation changed: ${values}`);
    // Implement allocation change logic
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
  };

  return (
    <div className="space-y-6">
      {/* Level Selection */}
      <div className="space-y-2">
<<<<<<< HEAD
        <Label className="font-semibold">Level:</Label>
        <div className="space-y-1">
          {["Borough", "Ward", "LSOA"].map((level) => (
=======
        <Label className="font-semibold">Boundary Level:</Label>
        <div className="space-y-1">
          {["Ward", "LSOA"].map((level) => (
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
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

<<<<<<< HEAD
      {/* Top x by level */}
      <div className="space-y-2">
        <Label className="font-semibold">Top {selectedLevel}s to display</Label>
        <Slider
          value={[topByLevel]}
          min={1}
          max={maxTopValues[selectedLevel as keyof typeof maxTopValues]}
          step={1}
          onValueChange={(values: number[]) => handleTopByLevelChange(values[0])}
          className="py-4"
        />
        <div className="text-center text-sm bg-muted rounded-md p-2">
          Showing top <span className="font-bold">{topByLevel}</span> {selectedLevel.toLowerCase()}s
        </div>
      </div>

=======
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
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
<<<<<<< HEAD
              min={2015}
              max={2023}
              step={1}
              onValueChange={handleYearChange}
=======
              min={2010}
              max={2025}
              step={1}
              onValueChange={(values) => handleYearChange(values[0])}
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
              className="py-4"
            />
          </div>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
<<<<<<< HEAD
              <Label htmlFor="month-slider">Month</Label>
              <span className="text-sm font-medium">{monthNames[selectedMonth - 1]}</span>
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
            </div>
            <Slider
              id="month-slider"
              value={[selectedMonth]}
<<<<<<< HEAD
              min={1}
              max={12}
              step={1}
              onValueChange={handleMonthChange}
=======
              min={monthRange.min}
              max={monthRange.max}
              step={1}
              onValueChange={(values) => handleMonthChange(values[0])}
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
              className="py-4"
            />
          </div>
          <div className="text-center text-sm bg-muted rounded-md p-2">
            Viewing data for <span className="font-bold">{monthNames[selectedMonth - 1]} {selectedYear}</span>
          </div>
        </div>
      </div>
<<<<<<< HEAD

      {/* Allocation sliders */}
      <div className="space-y-2">
        <Label className="font-semibold">Allocation sliders</Label>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="patrol-slider">Patrol Units</Label>
            <Slider
              id="patrol-slider"
              defaultValue={[10]}
              min={0}
              max={50}
              step={1}
              onValueChange={(values: number[]) => handleAllocationChange(values)}
              className="py-4"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="investigation-slider">Investigation Units</Label>
            <Slider
              id="investigation-slider"
              defaultValue={[5]}
              min={0}
              max={20}
              step={1}
              onValueChange={(values: number[]) => handleAllocationChange(values)}
              className="py-4"
            />
          </div>
        </div>
      </div>
=======
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
    </div>
  );
};

export default FilterPanel; 