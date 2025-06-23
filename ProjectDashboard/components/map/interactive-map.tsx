"use client";

<<<<<<< HEAD
import React, { useRef, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl, Tooltip } from "react-leaflet";
import { LONDON_CENTER, getColor } from "@/lib/map-utils";
import { MapFeature, MapFeatureCollection } from "@/types/map-types";
import L from "leaflet";

// Import Leaflet CSS
=======
import React, { useRef, useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl, Tooltip, Popup } from "react-leaflet";
import { LONDON_CENTER, getColor } from "@/lib/map-utils";
import { MapFeature, MapFeatureCollection } from "@/types/map-types";
import L from "leaflet";
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
import "leaflet/dist/leaflet.css";

interface InteractiveMapProps {
  features: MapFeatureCollection;
  wardBoundaries: any; // This is actually LSOA boundaries now, but we keep the prop name for compatibility
  valueField: string;
  maxValue: number;
  legendTitle: string;
  height?: string;
<<<<<<< HEAD
=======
  selectedYear?: number;
  selectedMonth?: number;
  isPredictionMap?: boolean;
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  features,
  wardBoundaries,
  valueField,
  maxValue,
  legendTitle,
<<<<<<< HEAD
  height = "300px",
}) => {
  const mapRef = useRef<L.Map>(null);
  const legendRef = useRef<HTMLDivElement>(null);

  // Style function for the GeoJSON features
=======
  height = "400px",
  selectedYear,
  selectedMonth,
  isPredictionMap = false
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const [currentZoom, setCurrentZoom] = useState(10);
  const [showBoundaries, setShowBoundaries] = useState(true);

  const boundaryType = wardBoundaries?.features?.[0]?.properties?.LSOA21CD ? "LSOA" : "Ward";
  const boundaryLabel = `${boundaryType} Boundaries`;

>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
  const featureStyle = (feature: MapFeature) => {
    const value = feature.properties[valueField] || 0;
    return {
      fillColor: getColor(value, maxValue),
<<<<<<< HEAD
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
=======
      weight: 0.7,
      opacity: 0.4,
      color: "#999",
      fillOpacity: 0.85,
    };
  };

  const lsoaStyle = () => {
    return {
      fillColor: "transparent",
      weight: 0.5,
      opacity: 0.4,
      color: "#aaa",
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      fillOpacity: 0.1,
    };
  };

<<<<<<< HEAD
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
=======
  const highlightStyle = {
    fillColor: "#87CEEB",
    weight: 2,
    opacity: 1,
    color: "#4682B4",
    fillOpacity: 0.4,
  };

  const onEachFeature = (feature: MapFeature, layer: L.Layer) => {
    const featureProperties = feature.properties;
    if (!featureProperties) return;

    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    const timeLabel = selectedYear && selectedMonth 
      ? `${monthNames[selectedMonth - 1]} ${selectedYear}`
      : "March 2024";
    
    const value = featureProperties[valueField] || 0;
    const displayValue = featureProperties.display_value !== undefined 
      ? featureProperties.display_value 
      : (featureProperties.crime_count || value);
    
    let formattedValue;
    let valueLabel;
    
    if (isPredictionMap) {
      formattedValue = Number(displayValue).toFixed(2);
      valueLabel = "February 2025 Prediction:";
    } else {
      formattedValue = Math.round(displayValue);
      valueLabel = `Burglaries in ${timeLabel}:`;
    }
    
    const areaCode = featureProperties.area_code || featureProperties.LSOA21CD || 'Unknown';
    const areaName = featureProperties.name || featureProperties.LSOA21NM || '';
    
    layer.bindTooltip(
      `<div>
        <strong>LSOA Code:</strong> ${areaCode}
        ${areaName ? `<br><strong>Name:</strong> ${areaName}` : ""}
        <br><strong>🚨 ${valueLabel}</strong> ${formattedValue}
        ${featureProperties.area_km2 ? `<br><strong>Area:</strong> ${featureProperties.area_km2.toFixed(3)} km²` : ""}
      </div>`,
      { sticky: true }
    );
  };

  const onEachBoundary = (feature: any, layer: L.Layer) => {
    if (feature.properties) {
      const isWard = feature.properties.NAME && !feature.properties.LSOA21CD;
      const crimeCount = feature.properties.crime_count || 0;
      
      const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
      ];
      const timeLabel = selectedYear && selectedMonth 
        ? `${monthNames[selectedMonth - 1]} ${selectedYear}`
        : "March 2024";
      
      let formattedValue;
      let valueLabel;
      
      if (isPredictionMap) {
        formattedValue = Number(crimeCount).toFixed(2);
        valueLabel = "February 2025 Prediction:";
      } else {
        formattedValue = Math.round(crimeCount);
        valueLabel = `Burglaries in ${timeLabel}:`;
      }
      
      const tooltipContent = `<div>
        ${isWard ? (
          `<strong>Ward:</strong> ${feature.properties.NAME || 'Unknown'}` +
          (feature.properties.BOROUGH ? `<br><strong>Borough:</strong> ${feature.properties.BOROUGH}` : '') +
          (feature.properties.GSS_CODE ? `<br><strong>Code:</strong> ${feature.properties.GSS_CODE}` : '')
        ) : (
          `${feature.properties.LSOA21CD ? `<strong>LSOA Code:</strong> ${feature.properties.LSOA21CD}` : ''}` +
          `${feature.properties.LSOA21NM ? `<br><strong>Name:</strong> ${feature.properties.LSOA21NM}` : ''}` +
          `${feature.properties.LAD20NM ? `<br><strong>Local Authority:</strong> ${feature.properties.LAD20NM}` : ''}`
        )}
        <br><strong>🚨 ${valueLabel}</strong> ${formattedValue}
      </div>`;
      
      layer.bindTooltip(tooltipContent, { sticky: true });
      
      layer.on({
        mouseover: function(e) {
          const layer = e.target;
          layer.setStyle(highlightStyle);
          layer.bringToFront();
        },
        mouseout: function(e) {
          const layer = e.target;
          layer.setStyle(lsoaStyle());
        }
      });
    }
  };

  // Update boundaries visibility based on zoom level
  useEffect(() => {
    if (mapRef.current) {
      const map = mapRef.current;
      
      const handleZoomChange = () => {
        const zoom = map.getZoom();
        setCurrentZoom(zoom);
        if (boundaryType === "LSOA") {
          setShowBoundaries(zoom >= 11);
        } else {
          setShowBoundaries(true);
        }
      };
      
      map.on('zoomend', handleZoomChange);
      handleZoomChange();
      
      return () => {
        map.off('zoomend', handleZoomChange);
      };
    }
  }, [mapRef.current, boundaryType]);

  // Fit map to boundaries when they load
  useEffect(() => {
    if (mapRef.current && wardBoundaries && wardBoundaries.features && wardBoundaries.features.length > 0) {
      try {
        const bounds = L.geoJSON(wardBoundaries).getBounds();
        mapRef.current.fitBounds(bounds, {
          padding: [20, 20],
          maxZoom: 14,
          animate: true
        });
      } catch (error) {
        // Fall back to London center if bounds calculation fails
        mapRef.current.setView(LONDON_CENTER, 10);
      }
    }
  }, [mapRef.current, wardBoundaries]);
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb

  return (
    <div style={{ height, width: "100%" }}>
      <MapContainer
        center={LONDON_CENTER}
        zoom={10}
        style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
        ref={mapRef as any}
<<<<<<< HEAD
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
=======
        zoomControl={false}
        maxBounds={[
          [51.2, -0.7],
          [51.8, 0.3]
        ]}
        maxBoundsViscosity={1.0}
        minZoom={9}
        maxZoom={16}
        preferCanvas={true}
        wheelDebounceTime={150}
        doubleClickZoom={false}
        zoomSnap={0.5}
        zoomDelta={0.5}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        <LayersControl position="bottomright">
          <LayersControl.Overlay checked name="Heatmap">
            <GeoJSON
              key={`heatmap-${features?.features?.length || 0}`}
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
              data={features as any}
              style={featureStyle}
              onEachFeature={onEachFeature}
            />
          </LayersControl.Overlay>
<<<<<<< HEAD
          <LayersControl.Overlay checked name="LSOA Boundaries">
            <GeoJSON
              data={wardBoundaries}
              style={lsoaStyle}
              onEachFeature={onEachLSOA}
            />
          </LayersControl.Overlay>
        </LayersControl>
        <div ref={legendRef} />
=======
          {wardBoundaries && wardBoundaries.features && wardBoundaries.features.length > 0 && showBoundaries && (
            <LayersControl.Overlay checked name={boundaryLabel}>
              <GeoJSON
                key={`boundaries-${wardBoundaries.features.length}`}
                data={wardBoundaries}
                style={lsoaStyle}
                onEachFeature={onEachBoundary}
              />
            </LayersControl.Overlay>
          )}
        </LayersControl>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      </MapContainer>
    </div>
  );
};

<<<<<<< HEAD
export default InteractiveMap; 
=======
export default InteractiveMap;
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
