"use client";

import React, { useState, useEffect, useRef } from "react";
import { fetchMapData } from "@/lib/map-utils";
import dynamic from "next/dynamic";
import { X, Maximize2 } from "lucide-react";
import { useFilter } from "@/contexts/filter-context";

// Extend Window interface to include our cache
declare global {
  interface Window {
    __mapCache?: Record<string, any>;
  }
}

// Import the map component dynamically to avoid SSR issues with Leaflet
const InteractiveMap = dynamic(() => import("@/components/map/interactive-map"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-full bg-gray-100">
      <p className="text-gray-500">Loading detailed map...</p>
    </div>
  ),
});

interface FullscreenMapModalProps {
  isOpen: boolean;
  onClose: () => void;
  endpoint: string;
  valueField: string;
  legendTitle: string;
  fixedYear?: number;
  fixedMonth?: number;
}

interface LoadingState {
  stage: 'idle' | 'loading' | 'loaded' | 'error';
  message: string;
  progress: number;
}

const FullscreenMapModal: React.FC<FullscreenMapModalProps> = ({
  isOpen,
  onClose,
  endpoint,
  valueField,
  legendTitle,
  fixedYear,
  fixedMonth
}) => {
  const { selectedLevel, selectedYear, selectedMonth } = useFilter();
  const [mapData, setMapData] = useState<any>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    stage: 'idle',
    message: 'Initializing...',
    progress: 0
  });
  const [isFromCache, setIsFromCache] = useState(false);

  // Use fixed year/month if provided, otherwise use selected values from context
  const yearToUse = fixedYear !== undefined ? fixedYear : selectedYear;
  const monthToUse = fixedMonth !== undefined ? fixedMonth : selectedMonth;

  // Helper function to get month name
  const getMonthName = (month: number) => {
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    return monthNames[month - 1];
  };

  useEffect(() => {
    if (!isOpen) {
      // Only reset state when modal is closed, don't fetch data
      return;
    }

    // Track if the component is still mounted
    let isMounted = true;
    
    const loadFullscreenMap = async () => {
      try {
        // First check if we already have this data in cache
        const cacheKey = `${endpoint}-${selectedLevel === 'LSOA' ? 'high' : 'low'}-${yearToUse}-${monthToUse}`;
        
        // Look for cached data in window.__mapCache
        if (!window.__mapCache) window.__mapCache = {};
        
        if (window.__mapCache[cacheKey]) {
          console.log('Using component cached data:', cacheKey);
          if (isMounted) {
            setMapData(window.__mapCache[cacheKey]);
            setIsFromCache(true);
            setLoadingState({
              stage: 'loaded',
              message: `Detailed ${selectedLevel.toLowerCase()} map loaded from local cache!`,
              progress: 100
            });
          }
          return;
        }
        
        if (isMounted) {
          setLoadingState({
            stage: 'loading',
            message: `Loading fullscreen ${selectedLevel.toLowerCase()} boundaries for ${getMonthName(monthToUse)} ${yearToUse}...`,
            progress: 50
          });
        }

        // Use correct detail level based on selected boundary type
        // Ward = low detail (all wards), LSOA = high detail (all LSOAs)
        const detailLevel = selectedLevel === 'LSOA' ? 'high' : 'low';
        const startTime = Date.now();
        const data = await fetchMapData(endpoint, detailLevel, yearToUse, monthToUse);
        const loadTime = Date.now() - startTime;
        
        // If component unmounted during fetch, don't update state
        if (!isMounted) return;
        
        // Check if data was loaded from cache (fast load time indicates cache hit)
        const fromCache = loadTime < 500; // Less than half second suggests cache hit
        setIsFromCache(fromCache);
        
        // Store in our component cache to avoid future fetches
        window.__mapCache[cacheKey] = data;
        
        setMapData(data);
        setLoadingState({
          stage: 'loaded',
          message: fromCache ? `Detailed ${selectedLevel.toLowerCase()} map loaded from cache!` : `Detailed ${selectedLevel.toLowerCase()} map loaded!`,
          progress: 100
        });

      } catch (error) {
        console.error('Error loading fullscreen map:', error);
        if (isMounted) {
          setLoadingState({
            stage: 'error',
            message: 'Failed to load detailed map',
            progress: 0
          });
        }
      }
    };

    loadFullscreenMap();
    
    // Cleanup function to handle component unmounting during fetch
    return () => {
      isMounted = false;
    };
  }, [isOpen, endpoint, selectedLevel, yearToUse, monthToUse]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-4 bg-white rounded-lg shadow-2xl z-[9999] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
          <div className="flex items-center space-x-2">
            <Maximize2 className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-800">
              {legendTitle} - {selectedLevel} Detailed View
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            {loadingState.stage === 'loaded' && mapData && (
              <span className="text-sm text-gray-600">
                {mapData.boundaryCount || 0} {selectedLevel.toLowerCase()} boundaries
              </span>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              aria-label="Close fullscreen"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 relative">
          {loadingState.stage === 'loading' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 z-10">
              <div className="w-64 mb-4">
                <div className="bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-300" 
                    style={{ width: `${loadingState.progress}%` }}
                  ></div>
                </div>
              </div>
              <p className="text-gray-600 text-center mb-2">{loadingState.message}</p>
              <p className="text-sm text-gray-500">Loading {selectedLevel.toLowerCase()} boundaries for detailed view...</p>
            </div>
          )}

          {loadingState.stage === 'error' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50">
              <p className="text-red-500 mb-4">Failed to load detailed map</p>
              <button 
                onClick={() => window.location.reload()} 
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Retry
              </button>
            </div>
          )}

          {loadingState.stage === 'loaded' && mapData && (
            <InteractiveMap
              features={mapData.features}
              wardBoundaries={mapData.wardBoundaries}
              valueField={valueField}
              maxValue={mapData.maxValue}
              legendTitle={legendTitle}
              height="100%"
              selectedYear={yearToUse}
              selectedMonth={monthToUse}
              isPredictionMap={endpoint === "predicted-burglaries"}
            />
          )}
          
          {/* Fixed prediction indicator for February 2025 */}
          {fixedYear === 2025 && fixedMonth === 2 && loadingState.stage === 'loaded' && (
            <div className="absolute bottom-4 left-4 z-[1000] bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
              February 2025 Predictions
            </div>
          )}

          {/* Loading indicator badge */}
          {loadingState.stage === 'loaded' && isFromCache && (
            <div className="absolute top-2 right-2 bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
              Loaded from cache
            </div>
          )}

          {/* Area count indicator */}
          {loadingState.stage === 'loaded' && mapData && (
            <div className="absolute bottom-2 right-2 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
              {mapData.boundaryCount || 0} {selectedLevel.toLowerCase()} boundaries
            </div>
          )}
          
          {/* Cache indicators, sources etc */}
          {loadingState.stage === 'loaded' && mapData && mapData.dataSource && (
            <div className="absolute bottom-2 left-2 bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs flex flex-col space-y-1">
              <div>Data: {mapData.dataSource}</div>
              {mapData.timeLabel && <div>Time: {mapData.timeLabel}</div>}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t bg-gray-50 rounded-b-lg">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>🗺️ Fullscreen {selectedLevel.toLowerCase()} view</span>
              {mapData && (
                <span>
                  Detail level: {mapData.detailLevel || (selectedLevel === 'LSOA' ? 'high' : 'low')} 
                  ({mapData.boundaryCount || 0} areas)
                </span>
              )}
              {isFromCache && (
                <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                  ⚡ Loaded from cache
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {selectedLevel === 'LSOA' && (
                <span className="text-xs text-gray-500">💡 LSOA boundaries appear at zoom 11+</span>
              )}
              <span>Press</span>
              <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">Esc</kbd>
              <span>to close</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default FullscreenMapModal; 