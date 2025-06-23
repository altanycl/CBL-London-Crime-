"use client";

import React, { useState, useEffect } from "react";
import { fetchMapData } from "@/lib/map-utils";
import { PastBurglariesData } from "@/types/map-types";
import dynamic from "next/dynamic";
<<<<<<< HEAD
=======
import { Maximize2 } from "lucide-react";
import { useFilter } from "@/contexts/filter-context";
import FullscreenMapModal from "@/components/map/fullscreen-map-modal";

// Ensure window.__mapCache is defined for all components
declare global {
  interface Window {
    __mapCache?: Record<string, any>;
  }
}
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb

// Import the map component dynamically to avoid SSR issues with Leaflet
const InteractiveMap = dynamic(() => import("@/components/map/interactive-map"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

<<<<<<< HEAD
const PastBurglariesMap = () => {
  const [mapData, setMapData] = useState<PastBurglariesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMapData = async () => {
      try {
        setLoading(true);
        const data = await fetchMapData("past-burglaries");
        setMapData(data);
      } catch (err) {
        console.error("Failed to load past burglaries map data:", err);
        setError("Failed to load map data");
      } finally {
        setLoading(false);
=======
interface LoadingState {
  stage: 'idle' | 'loading' | 'loaded' | 'error';
  message: string;
  progress: number;
}

const PastBurglariesMap = () => {
  const { selectedLevel, selectedYear, selectedMonth } = useFilter();
  const [mapData, setMapData] = useState<PastBurglariesData | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    stage: 'idle',
    message: 'Initializing...',
    progress: 0
  });
  const [error, setError] = useState<string | null>(null);
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);

  // Load map data based on selected level from filter
  useEffect(() => {
    let isMounted = true;
    
    const loadMapData = async () => {
      try {
        if (isMounted) {
          setError(null);
          setLoadingState({
            stage: 'loading',
            message: `Loading ${selectedLevel.toLowerCase()} boundaries for ${getMonthName(selectedMonth)} ${selectedYear}...`,
            progress: 50
          });
        }
        
        // Initialize map cache if not exists
        if (!window.__mapCache) window.__mapCache = {};
        
        // Determine detail level based on selected boundary type
        const detailLevel = selectedLevel === 'LSOA' ? 'high' : 'low';
        
        // Generate cache key
        const cacheKey = `past-burglaries-${detailLevel}-${selectedYear}-${selectedMonth}`;
        
        // Check if data already in component cache
        if (window.__mapCache[cacheKey]) {
          if (isMounted) {
            setMapData(window.__mapCache[cacheKey]);
            setLoadingState({
              stage: 'loaded',
              message: 'Map loaded from cache!',
              progress: 100
            });
          }
          return;
        }
        
        // Fetch new data if not in cache
        const data = await fetchMapData("past-burglaries", detailLevel, selectedYear, selectedMonth);
        
        // If component unmounted during fetch, don't update state
        if (!isMounted) return;
        
        // Store in our component cache
        window.__mapCache[cacheKey] = data;
        
        setMapData(data);
        setLoadingState({
          stage: 'loaded',
          message: 'Map loaded!',
          progress: 100
        });
        
      } catch (err) {
        console.error("Failed to load past burglaries map data:", err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load map data");
          setLoadingState({
            stage: 'error',
            message: 'Failed to load map data',
            progress: 0
          });
        }
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      }
    };

    loadMapData();
<<<<<<< HEAD
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-gray-500">Loading map data...</p>
=======
    
    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [selectedLevel, selectedYear, selectedMonth]); // Reload when any filter changes

  // Helper function to get month name
  const getMonthName = (month: number) => {
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    return monthNames[month - 1];
  };

  const handleFullscreenOpen = () => {
    setIsFullscreenOpen(true);
  };

  const handleFullscreenClose = () => {
    setIsFullscreenOpen(false);
  };

  if (loadingState.stage === 'error' || error) {
    return (
      <div className="flex flex-col items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-red-500 mb-2">{error || "Failed to load map data"}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      </div>
    );
  }

<<<<<<< HEAD
  if (error || !mapData) {
    return (
      <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-red-500">{error || "Failed to load map data"}</p>
=======
  if (loadingState.stage === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <div className="w-full max-w-xs mb-4">
          <div className="bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
              style={{ width: `${loadingState.progress}%` }}
            ></div>
          </div>
        </div>
        <p className="text-gray-500 text-center">{loadingState.message}</p>
        <p className="text-xs text-gray-400 mt-1">{loadingState.progress}%</p>
      </div>
    );
  }

  if (!mapData) {
  return (
      <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-red-500">No map data available</p>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      </div>
    );
  }

  return (
<<<<<<< HEAD
    <InteractiveMap
      features={mapData.features}
      wardBoundaries={mapData.wardBoundaries}
      valueField="actual_past_year"
      maxValue={mapData.maxValue}
      legendTitle={`Past Burglaries (${mapData.timeLabel})`}
      height="300px"
    />
=======
    <div className="relative">
      {/* Boundary type indicator */}
      <div className="absolute top-2 left-2 z-[1000] bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
        {selectedLevel} View ({mapData.boundaryCount || 0} areas)
      </div>

      {/* Fullscreen button */}
      <button
        onClick={handleFullscreenOpen}
        className="absolute top-2 right-2 z-[1000] bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg shadow-lg transition-colors"
        title={`View detailed ${selectedLevel.toLowerCase()} map in fullscreen`}
        aria-label="Open fullscreen detailed view"
      >
        <Maximize2 className="w-4 h-4" />
      </button>

      <InteractiveMap
        features={mapData.features}
        wardBoundaries={mapData.wardBoundaries}
        valueField="actual_past_year"
        maxValue={mapData.maxValue}
        legendTitle={`Past Burglaries (${mapData.timeLabel})`}
        height="300px"
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        isPredictionMap={false}
      />

      {/* Fullscreen Modal */}
      <FullscreenMapModal
        isOpen={isFullscreenOpen}
        onClose={handleFullscreenClose}
        endpoint="past-burglaries"
        valueField="actual_past_year"
        legendTitle={`Past Burglaries (${mapData.timeLabel})`}
      />
    </div>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
  );
};

export default PastBurglariesMap; 