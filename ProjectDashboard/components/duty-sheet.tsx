"use client";

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
      </div>
    </div>
  );
};

export default DutySheet; 