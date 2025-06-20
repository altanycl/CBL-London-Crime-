"use client";

import React, { useRef, useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl, Tooltip, Popup } from "react-leaflet";
import { LONDON_CENTER, getColor } from "@/lib/map-utils";
import { MapFeature, MapFeatureCollection } from "@/types/map-types";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface InteractiveMapProps {
  features: MapFeatureCollection;
  wardBoundaries: any; // This is actually LSOA boundaries now, but we keep the prop name for compatibility
  valueField: string;
  maxValue: number;
  legendTitle: string;
  height?: string;
  selectedYear?: number;
  selectedMonth?: number;
  isPredictionMap?: boolean;
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  features,
  wardBoundaries,
  valueField,
  maxValue,
  legendTitle,
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

  const featureStyle = (feature: MapFeature) => {
    const value = feature.properties[valueField] || 0;
    return {
      fillColor: getColor(value, maxValue),
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
      fillOpacity: 0.1,
    };
  };

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

  return (
    <div style={{ height, width: "100%" }}>
      <MapContainer
        center={LONDON_CENTER}
        zoom={10}
        style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
        ref={mapRef as any}
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
              data={features as any}
              style={featureStyle}
              onEachFeature={onEachFeature}
            />
          </LayersControl.Overlay>
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
      </MapContainer>
    </div>
  );
};

export default InteractiveMap;