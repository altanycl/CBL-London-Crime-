"use client";

import React, { useRef, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl, Tooltip } from "react-leaflet";
import { LONDON_CENTER, getColor } from "@/lib/map-utils";
import { MapFeature, MapFeatureCollection } from "@/types/map-types";
import L from "leaflet";

// Import Leaflet CSS
import "leaflet/dist/leaflet.css";

interface InteractiveMapProps {
  features: MapFeatureCollection;
  wardBoundaries: any; // This is actually LSOA boundaries now, but we keep the prop name for compatibility
  valueField: string;
  maxValue: number;
  legendTitle: string;
  height?: string;
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  features,
  wardBoundaries,
  valueField,
  maxValue,
  legendTitle,
  height = "300px",
}) => {
  const mapRef = useRef<L.Map>(null);
  const legendRef = useRef<HTMLDivElement>(null);

  // Style function for the GeoJSON features
  const featureStyle = (feature: MapFeature) => {
    const value = feature.properties[valueField] || 0;
    return {
      fillColor: getColor(value, maxValue),
      weight: 1,
      opacity: 0.7,
      color: "white",
      fillOpacity: 0.7,
    };
  };

  // Style for LSOA boundaries
  const lsoaStyle = () => {
    return {
      fillColor: "transparent",
      weight: 1,
      opacity: 0.7,
      color: "#333",
      fillOpacity: 0.1,
    };
  };

  // Tooltip for features
  const onEachFeature = (feature: MapFeature, layer: L.Layer) => {
    if (feature.properties) {
      const value = feature.properties[valueField] || 0;
      layer.bindTooltip(
        `<div>
          <strong>${valueField === "actual_past_year" ? "Actual" : "Predicted"} Burglaries:</strong> ${value.toFixed(1)}
          ${feature.properties.area_km2 ? `<br><strong>Area:</strong> ${feature.properties.area_km2.toFixed(2)} km²` : ""}
          ${feature.properties.LSOA21CD ? `<br><strong>LSOA:</strong> ${feature.properties.LSOA21CD}` : ""}
        </div>`,
        { sticky: true }
      );
    }
  };

  // Tooltip for LSOA boundaries
  const onEachLSOA = (feature: any, layer: L.Layer) => {
    if (feature.properties) {
      const tooltipContent = `<div>
        ${feature.properties.LSOA21CD ? `<strong>LSOA Code:</strong> ${feature.properties.LSOA21CD}` : ''}
        ${feature.properties.LSOA21NM ? `<br><strong>Name:</strong> ${feature.properties.LSOA21NM}` : ''}
        ${feature.properties.LAD20NM ? `<br><strong>Local Authority:</strong> ${feature.properties.LAD20NM}` : ''}
      </div>`;
      
      layer.bindTooltip(tooltipContent, { sticky: true });
    }
  };

  // Fit map to bounds when loaded
  useEffect(() => {
    if (mapRef.current && wardBoundaries && wardBoundaries.features) {
      try {
        // Convert GeoJSON to Leaflet layers
        const geoJsonLayer = L.geoJSON(wardBoundaries);
        
        // Get bounds of the GeoJSON layer
        const bounds = geoJsonLayer.getBounds();
        
        // Check if bounds are valid
        if (bounds.isValid()) {
          // Fit map to bounds with padding
          mapRef.current.fitBounds(bounds, {
            padding: [20, 20],
            maxZoom: 12
          });
        }
      } catch (error) {
        console.error("Error fitting map to bounds:", error);
      }
    }
  }, [wardBoundaries]);

  // Create legend
  useEffect(() => {
    if (mapRef.current && legendRef.current) {
      const map = mapRef.current;
      
      // Create a custom legend control
      const LegendControl = L.Control.extend({
        options: {
          position: "bottomright"
        },
        onAdd: function() {
          const div = L.DomUtil.create("div", "info legend");
          div.style.backgroundColor = "white";
          div.style.padding = "6px 8px";
          div.style.border = "1px solid #ccc";
          div.style.borderRadius = "5px";
          div.style.lineHeight = "18px";
          div.style.color = "#555";

          const grades = [0, maxValue * 0.2, maxValue * 0.4, maxValue * 0.6, maxValue * 0.8];
          div.innerHTML = `<h4 style="margin:0 0 5px 0">${legendTitle}</h4>`;

          for (let i = 0; i < grades.length; i++) {
            div.innerHTML += `<i style="background:${getColor(grades[i] + 0.1, maxValue)}; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7"></i> `;
            div.innerHTML += `${grades[i].toFixed(0)}${grades[i + 1] ? ` &ndash; ${grades[i + 1].toFixed(0)}` : "+"}<br>`;
          }

          // Add a legend item for LSOA boundaries
          div.innerHTML += `<hr style="margin:5px 0">`;
          div.innerHTML += `<i style="border:1px solid #333; background:transparent; width:18px; height:18px; float:left; margin-right:8px;"></i> LSOA Boundary`;

          return div;
        }
      });
      
      // Add the legend to the map
      const legend = new LegendControl();
      legend.addTo(map);

      return () => {
        map.removeControl(legend);
      };
    }
  }, [maxValue, legendTitle]);

  return (
    <div style={{ height, width: "100%" }}>
      <MapContainer
        center={LONDON_CENTER}
        zoom={10}
        style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
        ref={mapRef as any}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="CartoDB Light">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>
          <LayersControl.Overlay checked name="Heatmap">
            <GeoJSON
              data={features as any}
              style={featureStyle}
              onEachFeature={onEachFeature}
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="LSOA Boundaries">
            <GeoJSON
              data={wardBoundaries}
              style={lsoaStyle}
              onEachFeature={onEachLSOA}
            />
          </LayersControl.Overlay>
        </LayersControl>
        <div ref={legendRef} />
      </MapContainer>
    </div>
  );
};

export default InteractiveMap; 