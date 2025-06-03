"use client";

import React, { useState, useEffect } from "react";
import { fetchMapData } from "@/lib/map-utils";
import { PredictedBurglariesData } from "@/types/map-types";
import dynamic from "next/dynamic";

// Import the map component dynamically to avoid SSR issues with Leaflet
const InteractiveMap = dynamic(() => import("@/components/map/interactive-map"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

const PredictedBurglariesMap = () => {
  const [mapData, setMapData] = useState<PredictedBurglariesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMapData = async () => {
      try {
        setLoading(true);
        const data = await fetchMapData("predicted-burglaries");
        setMapData(data);
      } catch (err) {
        console.error("Failed to load predicted burglaries map data:", err);
        setError("Failed to load map data");
      } finally {
        setLoading(false);
      }
    };

    loadMapData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-gray-500">Loading map data...</p>
      </div>
    );
  }

  if (error || !mapData) {
    return (
      <div className="flex items-center justify-center w-full h-[300px] bg-gray-100 rounded-lg">
        <p className="text-red-500">{error || "Failed to load map data"}</p>
      </div>
    );
  }

  return (
    <InteractiveMap
      features={mapData.features}
      wardBoundaries={mapData.wardBoundaries}
      valueField="pred_per_km2"
      maxValue={mapData.maxValue}
      legendTitle={`Predicted Burglaries (${mapData.timeLabel})`}
      height="300px"
    />
  );
};

export default PredictedBurglariesMap; 