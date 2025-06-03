export interface MapFeatureProperties {
  cell_id: number;
  actual_past_year?: number;
  pred_per_km2?: number;
  pred_burglaries_per_m2?: number;
  area_km2?: number;
  residual?: number;
  ward?: string;
  LSOA21CD?: string;
  NAME?: string;
  [key: string]: any;
}

export interface MapFeature {
  type: "Feature";
  geometry: any;
  properties: MapFeatureProperties;
}

export interface MapFeatureCollection {
  type: "FeatureCollection";
  features: MapFeature[];
}

export interface MapData {
  features: MapFeatureCollection;
  maxValue: number;
  timeLabel: string;
}

export interface PastBurglariesData extends MapData {
  wardBoundaries: any;
}

export interface PredictedBurglariesData extends MapData {
  wardBoundaries: any;
} 