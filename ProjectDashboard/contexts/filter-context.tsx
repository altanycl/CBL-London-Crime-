"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

interface FilterContextType {
  selectedLevel: string;
  setSelectedLevel: (level: string) => void;
  selectedYear: number;
  setSelectedYear: (year: number) => void;
  selectedMonth: number;
  setSelectedMonth: (month: number) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export const useFilter = () => {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error("useFilter must be used within a FilterProvider");
  }
  return context;
};

interface FilterProviderProps {
  children: ReactNode;
}

export const FilterProvider: React.FC<FilterProviderProps> = ({ children }) => {
  const [selectedLevel, setSelectedLevel] = useState<string>("Ward");
  const [selectedYear, setSelectedYear] = useState<number>(2024);
  const [selectedMonth, setSelectedMonth] = useState<number>(3);

  return (
    <FilterContext.Provider
      value={{
        selectedLevel,
        setSelectedLevel,
        selectedYear,
        setSelectedYear,
        selectedMonth,
        setSelectedMonth,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}; 