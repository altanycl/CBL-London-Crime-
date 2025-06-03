"use client";

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

  // Month names for display
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handleLevelChange = (level: string) => {
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
  };

  return (
    <div className="space-y-6">
      {/* Level Selection */}
      <div className="space-y-2">
        <Label className="font-semibold">Level:</Label>
        <div className="space-y-1">
          {["Borough", "Ward", "LSOA"].map((level) => (
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
              min={2015}
              max={2023}
              step={1}
              onValueChange={handleYearChange}
              className="py-4"
            />
          </div>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <Label htmlFor="month-slider">Month</Label>
              <span className="text-sm font-medium">{monthNames[selectedMonth - 1]}</span>
            </div>
            <Slider
              id="month-slider"
              value={[selectedMonth]}
              min={1}
              max={12}
              step={1}
              onValueChange={handleMonthChange}
              className="py-4"
            />
          </div>
          <div className="text-center text-sm bg-muted rounded-md p-2">
            Viewing data for <span className="font-bold">{monthNames[selectedMonth - 1]} {selectedYear}</span>
          </div>
        </div>
      </div>

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
    </div>
  );
};

export default FilterPanel; 