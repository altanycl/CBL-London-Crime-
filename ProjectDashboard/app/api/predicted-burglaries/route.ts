import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    // Read the prediction data
    const predictionDataPath = path.join(process.cwd(), '../../outputs/next_month_predictions.csv');
    const wardBoundariesPath = path.join(process.cwd(), '../../London-wards-2018-ESRI/London_Ward.shp');
    
    // For demonstration, we'll return mock data since we can't directly read shapefiles in Node.js
    // In a real implementation, you would use a Python script to convert these to GeoJSON
    
    // Mock data based on the structure we expect from the Python scripts
    const mockData = {
      features: {
        type: "FeatureCollection",
        features: Array.from({ length: 50 }, (_, i) => ({
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [[[0, 0], [0, 0.01], [0.01, 0.01], [0.01, 0], [0, 0]].map(coord => [
              -0.1278 + coord[0] + (Math.random() * 0.2 - 0.1),
              51.5074 + coord[1] + (Math.random() * 0.2 - 0.1)
            ])]
          },
          properties: {
            cell_id: i,
            pred_per_km2: Math.floor(Math.random() * 40),
            area_km2: 0.25
          }
        }))
      },
      maxValue: 40,
      timeLabel: "Predictions for Jan 2024",
      wardBoundaries: {
        type: "FeatureCollection",
        features: Array.from({ length: 10 }, (_, i) => ({
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [[[0, 0], [0, 0.05], [0.05, 0.05], [0.05, 0], [0, 0]].map(coord => [
              -0.1278 + coord[0] + (Math.random() * 0.3 - 0.15),
              51.5074 + coord[1] + (Math.random() * 0.3 - 0.15)
            ])]
          },
          properties: {
            NAME: `Ward ${i + 1}`
          }
        }))
      }
    };

    return NextResponse.json(mockData);
  } catch (error) {
    console.error('Error fetching predicted burglaries data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch predicted burglaries data' },
      { status: 500 }
    );
  }
} 