// 검색 상태 관리 Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  SearchState, 
  SearchFilters, 
  RadiusSearchResult, 
  SearchHistory, 
  SearchSuggestion,
  ApartmentComplex,
  Coordinates 
} from '@/types';

const initialState: SearchState = {
  isSearching: false,
  query: '',
  results: null,
  history: [],
  suggestions: [],
  selectedApartment: null,
  currentCenter: { lat: 37.5665, lng: 126.9780 }, // 서울시청
  currentRadius: 3, // 3km
  filters: {
    transactionType: 'all',
  },
  error: null,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setSearching: (state, action: PayloadAction<boolean>) => {
      state.isSearching = action.payload;
      if (action.payload) {
        state.error = null;
      }
    },

    setQuery: (state, action: PayloadAction<string>) => {
      state.query = action.payload;
    },

    setSearchResults: (state, action: PayloadAction<RadiusSearchResult>) => {
      state.results = action.payload;
      state.isSearching = false;
      state.error = null;
    },

    clearSearchResults: (state) => {
      state.results = null;
      state.selectedApartment = null;
    },

    setSearchError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.isSearching = false;
    },

    addToHistory: (state, action: PayloadAction<SearchHistory>) => {
      // 중복 제거: 같은 쿼리가 있으면 제거하고 최상단에 추가
      state.history = [
        action.payload,
        ...state.history.filter(item => 
          item.query !== action.payload.query || 
          item.coordinates.lat !== action.payload.coordinates.lat ||
          item.coordinates.lng !== action.payload.coordinates.lng
        )
      ].slice(0, 20); // 최대 20개까지만 저장
    },

    clearHistory: (state) => {
      state.history = [];
    },

    removeFromHistory: (state, action: PayloadAction<string>) => {
      state.history = state.history.filter(item => item.id !== action.payload);
    },

    setSuggestions: (state, action: PayloadAction<SearchSuggestion[]>) => {
      state.suggestions = action.payload;
    },

    clearSuggestions: (state) => {
      state.suggestions = [];
    },

    selectApartment: (state, action: PayloadAction<ApartmentComplex | null>) => {
      state.selectedApartment = action.payload;
    },

    setCurrentCenter: (state, action: PayloadAction<Coordinates>) => {
      state.currentCenter = action.payload;
    },

    setCurrentRadius: (state, action: PayloadAction<number>) => {
      state.currentRadius = action.payload;
    },

    updateFilters: (state, action: PayloadAction<Partial<SearchFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    resetFilters: (state) => {
      state.filters = {
        transactionType: 'all',
      };
    },

    setFilter: (state, action: PayloadAction<{ key: keyof SearchFilters; value: any }>) => {
      const { key, value } = action.payload;
      state.filters[key] = value;
    },

    // 편의 메서드들
    setPriceRange: (state, action: PayloadAction<{ min?: number; max?: number }>) => {
      const { min, max } = action.payload;
      if (min !== undefined) state.filters.priceMin = min;
      if (max !== undefined) state.filters.priceMax = max;
    },

    setAreaRange: (state, action: PayloadAction<{ min?: number; max?: number }>) => {
      const { min, max } = action.payload;
      if (min !== undefined) state.filters.areaMin = min;
      if (max !== undefined) state.filters.areaMax = max;
    },

    setConstructionYearRange: (state, action: PayloadAction<{ min?: number; max?: number }>) => {
      const { min, max } = action.payload;
      if (min !== undefined) state.filters.constructionYearMin = min;
      if (max !== undefined) state.filters.constructionYearMax = max;
    },

    setTransactionType: (state, action: PayloadAction<'sale' | 'rent' | 'lease' | 'all'>) => {
      state.filters.transactionType = action.payload;
    },

    resetSearch: (state) => {
      return {
        ...initialState,
        history: state.history, // 히스토리는 유지
      };
    },
  },
});

export const {
  setSearching,
  setQuery,
  setSearchResults,
  clearSearchResults,
  setSearchError,
  addToHistory,
  clearHistory,
  removeFromHistory,
  setSuggestions,
  clearSuggestions,
  selectApartment,
  setCurrentCenter,
  setCurrentRadius,
  updateFilters,
  resetFilters,
  setFilter,
  setPriceRange,
  setAreaRange,
  setConstructionYearRange,
  setTransactionType,
  resetSearch,
} = searchSlice.actions;

export default searchSlice.reducer;