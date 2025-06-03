"use client";

import React from "react";
import Image from "next/image";

const PastBurglariesMap = () => {
  return (
    <div className="relative w-full h-[300px] bg-gray-200 rounded-lg overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center">
        <p className="text-gray-500">
          London Choropleth Map - Past Burglaries
          <br />
          (Map will be loaded here)
        </p>
      </div>
      {/* In a real implementation, you would use a mapping library like react-leaflet */}
      <div className="absolute inset-0 opacity-80">
        <img
          src="/london-map-placeholder.svg"
          alt="London Map Placeholder"
          className="w-full h-full object-contain"
        />
      </div>
    </div>
  );
};

export default PastBurglariesMap; 