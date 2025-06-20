"use client";

import React, { useState, useEffect } from "react";
import { fetchMapData } from "@/lib/map-utils";
import { PredictedBurglariesData } from "@/types/map-types";
import dynamic from "next/dynamic";
import { Maximize2 } from "lucide-react";
import { useFilter } from "@/contexts/filter-context";
import FullscreenMapModal from "@/components/map/fullscreen-map-modal";

// Import the map component dynamically to avoid SSR issues with Leaflet
const InteractiveMap = dynamic(() => import("@/components/map/interactive-map"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

interface LoadingState {
  stage: 'idle' | 'loading' | 'loaded' | 'error';
  message: string;
  progress: number;
}

const PredictedBurglariesMap = () => {
  const { selectedLevel } = useFilter();
  const [mapData, setMapData] = useState<PredictedBurglariesData | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    stage: 'idle',
    message: 'Initializing...',
    progress: 0
  });
  const [error, setError] = useState<string | null>(null);
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);

  // Fixed prediction data for February 2025
  const predictionYear = 2025;
  const predictionMonth = 2;

  // Load map data based on selected level from filter, but always February 2025
  useEffect(() => {
    const loadMapData = async () => {
      try {
        setError(null);
        setLoadingState({
          stage: 'loading',
          message: `Loading ${selectedLevel.toLowerCase()} boundaries for February 2025...`,
          progress: 50
        });
        
        // Determine detail level based on selected boundary type
        const detailLevel = selectedLevel === 'LSOA' ? 'high' : 'low';
        const data = await fetchMapData("predicted-burglaries", detailLevel, predictionYear, predictionMonth);
        setMapData(data);
        
        setLoadingState({
          stage: 'loaded',
          message: 'Map loaded!',
          progress: 100
        });
        
      } catch (err) {
        console.error("Failed to load predicted burglaries map data:", err);
        setError(err instanceof Error ? err.message : "Failed to load map data");
        setLoadingState({
          stage: 'error',
          message: 'Failed to load map data',
          progress: 0
        });
      }
    };

    loadMapData();
  }, [selectedLevel]); // Only reload when boundary level changes

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
      </div>
    );
  }

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
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Boundary type indicator */}
      <div className="absolute top-2 left-2 z-[1000] bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
        {selectedLevel} View ({mapData.boundaryCount || 0} areas)
      </div>

      {/* Fixed February 2025 indicator - moved to bottom left */}
      <div className="absolute bottom-2 left-2 z-[1000] bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
        February 2025 Predictions
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
        valueField="pred_per_km2"
        maxValue={mapData.maxValue}
        legendTitle="Predicted Burglaries (February 2025)"
        height="300px"
        selectedYear={predictionYear}
        selectedMonth={predictionMonth}
        isPredictionMap={true}
      />

      {/* Fullscreen Modal with fixed February 2025 data */}
      <FullscreenMapModal
        isOpen={isFullscreenOpen}
        onClose={handleFullscreenClose}
        endpoint="predicted-burglaries"
        valueField="pred_per_km2"
        legendTitle="Predicted Burglaries (February 2025)"
        fixedYear={predictionYear}
        fixedMonth={predictionMonth}
      />
    </div>
  );
};

export default PredictedBurglariesMap; 