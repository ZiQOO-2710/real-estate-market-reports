// 아파트 데이터 관리 Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ApartmentComplex } from '../../types/apartment';

interface ApartmentState {
  apartments: ApartmentComplex[];
  selectedApartment: ApartmentComplex | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    priceRange: [number, number];
    areaRange: [number, number];
    constructionYearRange: [number, number];
    dealTypes: string[];
    searchRadius: number;
  };
}

const initialState: ApartmentState = {
  apartments: [],
  selectedApartment: null,
  isLoading: false,
  error: null,
  filters: {
    priceRange: [0, 1000000], // 만원 단위
    areaRange: [0, 300], // ㎡ 단위
    constructionYearRange: [1970, new Date().getFullYear()],
    dealTypes: ['매매', '전세', '월세'],
    searchRadius: 5 // km
  }
};

const apartmentSlice = createSlice({
  name: 'apartment',
  initialState,
  reducers: {
    setApartments: (state, action: PayloadAction<ApartmentComplex[]>) => {
      state.apartments = action.payload;
      state.isLoading = false;
      state.error = null;
    },

    addApartments: (state, action: PayloadAction<ApartmentComplex[]>) => {
      state.apartments.push(...action.payload);
    },

    updateApartment: (state, action: PayloadAction<ApartmentComplex>) => {
      const index = state.apartments.findIndex(apt => apt.id === action.payload.id);
      if (index !== -1) {
        state.apartments[index] = action.payload;
      }
    },

    setSelectedApartment: (state, action: PayloadAction<ApartmentComplex | null>) => {
      state.selectedApartment = action.payload;
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.isLoading = false;
    },

    updateFilters: (state, action: PayloadAction<Partial<ApartmentState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    clearApartments: (state) => {
      state.apartments = [];
      state.selectedApartment = null;
    },

    resetFilters: (state) => {
      state.filters = initialState.filters;
    }
  }
});

export const {
  setApartments,
  addApartments,
  updateApartment,
  setSelectedApartment,
  setLoading,
  setError,
  updateFilters,
  clearApartments,
  resetFilters
} = apartmentSlice.actions;

export default apartmentSlice.reducer;