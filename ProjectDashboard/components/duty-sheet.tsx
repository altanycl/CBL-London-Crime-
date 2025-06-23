"use client";

<<<<<<< HEAD
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
=======
import React, { useState, useEffect, useRef } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { dutySheetCache, setDutySheetCache } from "./duty-sheet-cache";
import PopoutButton from "@/components/popout-button";
import { AllocationExplanationContent } from "@/components/popout-button";

interface DutySheetData {
  lsoa_code: string;
  ward_code: string;
  ward_name: string;
  hours_per_week: number;
  tier: string;
  lsoa_name: string;
}

const ROWS_PER_LOAD = 20;

const DutySheet = () => {
  const [data, setData] = useState<DutySheetData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [visibleRows, setVisibleRows] = useState(ROWS_PER_LOAD);
  const tableContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setVisibleRows(ROWS_PER_LOAD); // Reset visible rows on new data/search
  }, [data, searchTerm]);

  useEffect(() => {
    if (dutySheetCache.value) {
      setData(dutySheetCache.value);
      setLoading(false);
      return;
    }
    const fetchDutySheetData = async () => {
      try {
        const response = await fetch("/api/duty-sheet");
        if (!response.ok) {
          throw new Error("Failed to fetch duty sheet data");
        }
        const result = await response.json();
        setData(result.duty_sheet);
        setDutySheetCache(result.duty_sheet); // set shared cache
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };
    fetchDutySheetData();
  }, []);

  const filteredData = (Array.isArray(data) ? data : []).filter((item) => {
    const search = searchTerm.toLowerCase();
    return (
      item.ward_name.toLowerCase().includes(search) ||
      item.lsoa_code.toLowerCase().includes(search) ||
      item.ward_code.toLowerCase().includes(search)
    );
  });

  // Sort data by ward_name and then by lsoa_code
  const sortedData = [...filteredData].sort((a, b) => {
    // First, sort by ward_name
    const wardCompare = a.ward_name.localeCompare(b.ward_name);
    if (wardCompare !== 0) return wardCompare;
    // Then, sort by lsoa_code
    return a.lsoa_code.localeCompare(b.lsoa_code);
  });

  // Group data by ward_name
  const groupedData = sortedData.reduce((acc, item) => {
    if (!acc[item.ward_name]) {
      acc[item.ward_name] = [];
    }
    acc[item.ward_name].push(item);
    return acc;
  }, {} as Record<string, typeof sortedData>);

  // Sort wards by the number of LSOAs in tier 1 (descending)
  const sortedWards = Object.keys(groupedData).sort((a, b) => {
    const tier1CountA = groupedData[a].filter(item => item.tier === "Tier 1").length;
    const tier1CountB = groupedData[b].filter(item => item.tier === "Tier 1").length;
    return tier1CountB - tier1CountA;
  });

  // Infinite scroll handler
  const handleScroll = () => {
    const container = tableContainerRef.current;
    if (!container) return;
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {
      // Near bottom, load more rows
      setVisibleRows((prev) => Math.min(prev + ROWS_PER_LOAD, sortedData.length));
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Tier 1":
        return "bg-red-100 text-red-800";
      case "Tier 2":
        return "bg-yellow-100 text-yellow-800";
      case "Tier 3":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading duty sheet data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <Input
          placeholder="Search ward name or code..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div
        className="rounded-md border max-h-[400px] overflow-y-auto mb-4"
        ref={tableContainerRef}
        onScroll={handleScroll}
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Ward Code</TableHead>
              <TableHead>LSOA Code</TableHead>
              <TableHead>LSOA Name</TableHead>
              <TableHead className="text-center">Hours</TableHead>
              <TableHead>Tier</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedWards.slice(0, visibleRows).map((wardName) => (
              <React.Fragment key={wardName}>
                <TableRow className="bg-gray-50">
                  <TableCell colSpan={5} className="font-semibold text-gray-700">
                    Ward name: {wardName}
                  </TableCell>
                </TableRow>
                {groupedData[wardName].map((item, idx) => (
                  <TableRow key={item.lsoa_code}>
                    <TableCell className="font-mono">{item.ward_code}</TableCell>
                    <TableCell className="font-mono">{item.lsoa_code}</TableCell>
                    <TableCell>{item.lsoa_name}</TableCell>
                    <TableCell className="text-center">{item.hours_per_week.toFixed(2)}</TableCell>
                    <TableCell><Badge className={getTierColor(item.tier)}>{item.tier}</Badge></TableCell>
                  </TableRow>
                ))}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="text-sm text-gray-500 mb-2">
        Showing {Math.min(sortedWards.length, visibleRows)} of {sortedWards.length} wards
      </div>
      <div className="mt-4">
        <PopoutButton text="See detailed information on how allocation works" title="How Allocation Works: Detailed Explanation">
          <AllocationExplanationContent />
        </PopoutButton>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      </div>
    </div>
  );
};

export default DutySheet; 