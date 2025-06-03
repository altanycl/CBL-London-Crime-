import { LatLngExpression } from "leaflet";

// London center coordinates
export const LONDON_CENTER: LatLngExpression = [51.5074, -0.1278];

// Color scale for heatmaps
export const getColor = (value: number, max: number): string => {
  // YlOrRd color scale similar to the one used in the Python scripts
  const normalizedValue = Math.min(value / max, 1);
  
  if (normalizedValue > 0.8) return "#bd0026"; // Dark red
  if (normalizedValue > 0.6) return "#f03b20"; // Red
  if (normalizedValue > 0.4) return "#fd8d3c"; // Orange
  if (normalizedValue > 0.2) return "#feb24c"; // Light orange
  if (normalizedValue > 0) return "#fed976";   // Yellow
  return "#ffffb2";                            // Very light yellow
};

// Function to fetch map data from API
export const fetchMapData = async (endpoint: string) => {
  try {
    const response = await fetch(`/api/${endpoint}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch map data: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching map data:", error);
    return null;
  }
}; 