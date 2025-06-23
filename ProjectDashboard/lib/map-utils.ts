import { LatLngExpression } from "leaflet";

// London center coordinates
export const LONDON_CENTER: LatLngExpression = [51.5074, -0.1278];

<<<<<<< HEAD
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
=======
// Cache for storing map data to avoid repeated API calls
interface MapDataCache {
  [key: string]: any;
}

const mapDataCache: MapDataCache = {};
const boundaryCache: MapDataCache = {}; // Separate cache for boundaries

// Color scale for heatmaps - yellow-based scale
export const getColor = (value: number, max: number): string => {
  const effectiveMax = max > 0 ? max : 1;
  const normalizedValue = Math.min(value / effectiveMax, 1);
  
  if (normalizedValue > 0.9) return "#b10026";
  if (normalizedValue > 0.8) return "#bd0026";
  if (normalizedValue > 0.7) return "#e31a1c";
  if (normalizedValue > 0.6) return "#fc4e2a";
  if (normalizedValue > 0.5) return "#fd8d3c";
  if (normalizedValue > 0.4) return "#feb24c";
  if (normalizedValue > 0.3) return "#fed976";
  if (normalizedValue > 0.2) return "#ffeda0";
  if (normalizedValue > 0.1) return "#fff7bc";
  if (normalizedValue > 0) return "#ffffe5";
  return "#f5f5f5";
};

// Function to clear cache
export const clearMapDataCache = () => {
  Object.keys(mapDataCache).forEach(key => delete mapDataCache[key]);
  Object.keys(boundaryCache).forEach(key => delete boundaryCache[key]);
};

// Declare global interface for window.__mapCache
declare global {
  interface Window {
    __mapCache?: Record<string, any>;
    __fetchInProgress?: Record<string, Promise<any>>;
  }
}

// Function to fetch map data from API with caching support
export const fetchMapData = async (
  endpoint: string,
  detailLevel: string = "medium",
  year: number = 2024,
  month: number = 3
): Promise<any> => {
  const boundaryCacheKey = `${endpoint}-boundaries-${detailLevel}`;
  const dataCacheKey = `${endpoint}-${detailLevel}-${year}-${month}`;

  // Check both our internal cache and the component cache
  if (mapDataCache[dataCacheKey]) {
    return mapDataCache[dataCacheKey];
  }
  
  // Check the global component cache if available
  if (typeof window !== 'undefined' && window.__mapCache && window.__mapCache[dataCacheKey]) {
    // Sync our internal cache with component cache
    mapDataCache[dataCacheKey] = window.__mapCache[dataCacheKey];
    return window.__mapCache[dataCacheKey];
  }
  
  // Initialize fetch in progress tracking to avoid duplicate requests
  if (typeof window !== 'undefined') {
    if (!window.__fetchInProgress) window.__fetchInProgress = {};
    
    // If this request is already in progress, wait for it instead of making a duplicate
    const existingPromise = window.__fetchInProgress[dataCacheKey];
    if (existingPromise) {
      return existingPromise;
    }
  }

  try {
    // Create a promise for this fetch operation and track it
    const fetchPromise = (async () => {
      console.log(`Fetching map data: ${endpoint}, ${detailLevel}, ${year}-${month}`);
      const response = await fetch(
        `http://localhost:5000/api/${endpoint}?detail=${detailLevel}&year=${year}&month=${month}`
      );
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
  
      // Store in our internal cache
      mapDataCache[dataCacheKey] = data;
  
      // Store in the component cache if available
      if (typeof window !== 'undefined') {
        if (!window.__mapCache) window.__mapCache = {};
        window.__mapCache[dataCacheKey] = data;
      }
  
      if (data.wardBoundaries && !boundaryCache[boundaryCacheKey]) {
        boundaryCache[boundaryCacheKey] = data.wardBoundaries;
      }
      
      // Remove the in-progress tracking
      if (typeof window !== 'undefined' && window.__fetchInProgress) {
        delete window.__fetchInProgress[dataCacheKey];
      }
  
      return data;
    })();
    
    // Store the promise for this request
    if (typeof window !== 'undefined' && window.__fetchInProgress) {
      window.__fetchInProgress[dataCacheKey] = fetchPromise;
    }
    
    return fetchPromise;
  } catch (error) {
    // Remove the in-progress tracking on error
    if (typeof window !== 'undefined' && window.__fetchInProgress) {
      delete window.__fetchInProgress[dataCacheKey];
    }
    throw new Error(`Failed to fetch map data: ${error}`);
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
  }
}; 