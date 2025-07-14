// 지도 상태 관리 Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { MapState, MapViewport, MapMarker, MapLayer, ProjectSite, Coordinates } from '@/types';

const initialState: MapState = {
  viewport: {
    center: { lat: 37.5665, lng: 126.9780 }, // 서울시청
    zoom: 12,
    bounds: {
      northEast: { lat: 37.6, lng: 127.0 },
      southWest: { lat: 37.5, lng: 126.9 },
    },
  },
  layers: [
    {
      id: 'apartments',
      name: '아파트',
      visible: true,
      type: 'marker',
      data: [],
    },
    {
      id: 'project-sites',
      name: '프로젝트 부지',
      visible: true,
      type: 'marker',
      data: [],
    },
  ],
  markers: [],
  selectedMarker: null,
  controls: [
    { id: 'zoom', type: 'zoom', position: 'top-right', visible: true },
    { id: 'layer', type: 'layer', position: 'top-left', visible: true },
  ],
  drawingTool: null,
  projectSites: [],
  isLoading: false,
  mapInstance: null,
};

const mapSlice = createSlice({
  name: 'map',
  initialState,
  reducers: {
    setViewport: (state, action: PayloadAction<MapViewport>) => {
      state.viewport = action.payload;
    },

    setCenter: (state, action: PayloadAction<Coordinates>) => {
      state.viewport.center = action.payload;
    },

    setZoom: (state, action: PayloadAction<number>) => {
      state.viewport.zoom = action.payload;
    },

    setBounds: (state, action: PayloadAction<any>) => {
      state.viewport.bounds = action.payload;
    },

    setMapInstance: (state, action: PayloadAction<any>) => {
      state.mapInstance = action.payload;
    },

    addMarkers: (state, action: PayloadAction<MapMarker[]>) => {
      state.markers = [...state.markers, ...action.payload];
    },

    updateMarkers: (state, action: PayloadAction<MapMarker[]>) => {
      state.markers = action.payload;
    },

    clearMarkers: (state) => {
      state.markers = [];
    },

    selectMarker: (state, action: PayloadAction<MapMarker | null>) => {
      state.selectedMarker = action.payload;
    },

    setSelectedMarker: (state, action: PayloadAction<MapMarker | null>) => {
      state.selectedMarker = action.payload;
    },

    setMapType: (state, action: PayloadAction<string>) => {
      // 지도 타입 변경은 컴포넌트에서 직접 처리
    },

    setTrafficLayer: (state, action: PayloadAction<boolean>) => {
      // 교통정보 레이어 상태 저장 (필요시)
    },

    setBikeLayer: (state, action: PayloadAction<boolean>) => {
      // 자전거 도로 레이어 상태 저장 (필요시)
    },

    addLayer: (state, action: PayloadAction<MapLayer>) => {
      state.layers.push(action.payload);
    },

    updateLayer: (state, action: PayloadAction<{ id: string; updates: Partial<MapLayer> }>) => {
      const { id, updates } = action.payload;
      const layerIndex = state.layers.findIndex(layer => layer.id === id);
      if (layerIndex !== -1) {
        state.layers[layerIndex] = { ...state.layers[layerIndex], ...updates };
      }
    },

    toggleLayerVisibility: (state, action: PayloadAction<string>) => {
      const layerId = action.payload;
      const layer = state.layers.find(layer => layer.id === layerId);
      if (layer) {
        layer.visible = !layer.visible;
      }
    },

    addProjectSite: (state, action: PayloadAction<ProjectSite>) => {
      state.projectSites.push(action.payload);
    },

    updateProjectSite: (state, action: PayloadAction<ProjectSite>) => {
      const index = state.projectSites.findIndex(site => site.id === action.payload.id);
      if (index !== -1) {
        state.projectSites[index] = action.payload;
      }
    },

    deleteProjectSite: (state, action: PayloadAction<string>) => {
      state.projectSites = state.projectSites.filter(site => site.id !== action.payload);
    },

    setDrawingTool: (state, action: PayloadAction<any>) => {
      state.drawingTool = action.payload;
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    resetMap: (state) => {
      return { ...initialState, mapInstance: state.mapInstance };
    },
  },
});

export const {
  setViewport,
  setCenter,
  setZoom,
  setBounds,
  setMapInstance,
  addMarkers,
  updateMarkers,
  clearMarkers,
  selectMarker,
  setSelectedMarker,
  setMapType,
  setTrafficLayer,
  setBikeLayer,
  addLayer,
  updateLayer,
  toggleLayerVisibility,
  addProjectSite,
  updateProjectSite,
  deleteProjectSite,
  setDrawingTool,
  setLoading,
  resetMap,
} = mapSlice.actions;

export default mapSlice.reducer;