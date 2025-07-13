// 지도 관련 타입 정의

import { Coordinates, ApartmentMarker } from './apartment';

export interface MapBounds {
  northEast: Coordinates;
  southWest: Coordinates;
}

export interface MapViewport {
  center: Coordinates;
  zoom: number;
  bounds: MapBounds;
}

export interface MapMarker {
  id: string;
  position: Coordinates;
  type: 'apartment' | 'project-site' | 'search-center' | 'landmark';
  data: any;
  icon?: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  cluster?: boolean;
}

export interface MapLayer {
  id: string;
  name: string;
  visible: boolean;
  type: 'marker' | 'polygon' | 'heatmap' | 'cluster';
  data: any[];
  style?: LayerStyle;
}

export interface LayerStyle {
  color?: string;
  fillColor?: string;
  opacity?: number;
  fillOpacity?: number;
  weight?: number;
  radius?: number;
}

export interface HeatmapPoint {
  coordinates: Coordinates;
  intensity: number;
  value?: number;
}

export interface MapControl {
  id: string;
  type: 'zoom' | 'layer' | 'search' | 'filter' | 'export' | 'measure';
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  visible: boolean;
}

export interface DrawingTool {
  type: 'circle' | 'polygon' | 'rectangle' | 'marker';
  active: boolean;
  data?: any;
}

export interface MapEvent {
  type: 'click' | 'move' | 'zoom' | 'bounds-changed';
  coordinates?: Coordinates;
  zoom?: number;
  bounds?: MapBounds;
  target?: any;
}

export interface ProjectSite {
  id: string;
  name: string;
  coordinates: Coordinates;
  area?: number; // 부지 면적 (㎡)
  boundaryPolygon?: Coordinates[];
  metadata?: {
    [key: string]: any;
  };
  createdAt: Date;
  updatedAt: Date;
}

// 지도 상태 관리
export interface MapState {
  viewport: MapViewport;
  layers: MapLayer[];
  markers: MapMarker[];
  selectedMarker: MapMarker | null;
  controls: MapControl[];
  drawingTool: DrawingTool | null;
  projectSites: ProjectSite[];
  isLoading: boolean;
  mapInstance: any; // Kakao Map instance
}

// 지도 설정
export interface MapConfig {
  defaultCenter: Coordinates;
  defaultZoom: number;
  minZoom: number;
  maxZoom: number;
  mapType: 'normal' | 'satellite' | 'hybrid';
  enableScrollZoom: boolean;
  enableDoubleClickZoom: boolean;
  enableKeyboardShortcuts: boolean;
  showTrafficLayer: boolean;
  showBikeLayer: boolean;
  apiKey: string;
}

// 클러스터링 옵션
export interface ClusterOptions {
  enabled: boolean;
  maxZoom: number;
  radius: number;
  minPoints: number;
  showSingleMarker: boolean;
}

// 지도 테마
export interface MapTheme {
  id: string;
  name: string;
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
    text: string;
  };
  markerStyles: {
    apartment: LayerStyle;
    projectSite: LayerStyle;
    searchCenter: LayerStyle;
  };
}