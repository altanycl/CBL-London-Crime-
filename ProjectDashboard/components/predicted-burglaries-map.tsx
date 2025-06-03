"use client";

import React from "react";
import Image from "next/image";

const PredictedBurglariesMap = () => {
  return (
    <div className="relative w-full h-[300px] bg-gray-200 rounded-lg overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center">
        <p className="text-gray-500">
          London Map - Predicted Burglaries
          <br />
          (Map will be loaded here with prediction hotspots)
        </p>
      </div>
      {/* In a real implementation, you would use a mapping library like react-leaflet */}
      <div className="absolute inset-0 opacity-80">
        <img
          src="/london-map-predictions-placeholder.svg"
          alt="London Map Predictions Placeholder"
          className="w-full h-full object-contain"
        />
      </div>
    </div>
  );
};

export default PredictedBurglariesMap; 