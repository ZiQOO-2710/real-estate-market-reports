// 검색 관련 타입 정의

import { Coordinates, ApartmentComplex } from './apartment';

export interface SearchParams {
  center: Coordinates;
  radius: number; // km
  address?: string;
  filters?: SearchFilters;
}

export interface SearchFilters {
  priceMin?: number;
  priceMax?: number;
  areaMin?: number;
  areaMax?: number;
  constructionYearMin?: number;
  constructionYearMax?: number;
  transactionType?: 'sale' | 'rent' | 'lease' | 'all';
  keywords?: string[];
}

export interface RadiusSearchResult {
  center: Coordinates;
  radius: number;
  apartments: ApartmentComplex[];
  summary: SearchSummary;
  radiusAnalysis: RadiusAnalysis[];
}

export interface SearchSummary {
  totalCount: number;
  averagePrice: number;
  medianPrice: number;
  priceRange: {
    min: number;
    max: number;
  };
  averageArea: number;
  constructionYearDistribution: {
    [year: string]: number;
  };
  transactionTypeDistribution: {
    sale: number;
    rent: number;
    lease: number;
  };
}

export interface RadiusAnalysis {
  radius: number; // km
  count: number;
  averagePrice: number;
  pricePerSqm: number;
  topApartments: ApartmentComplex[];
}

export interface AddressSearchResult {
  address: string;
  coordinates: Coordinates;
  addressType: 'road' | 'jibun' | 'building';
  confidence: number;
}

export interface SearchHistory {
  id: string;
  query: string;
  coordinates: Coordinates;
  radius: number;
  filters?: SearchFilters;
  resultCount: number;
  searchDate: Date;
  userId?: string;
}

// 자동완성용 검색 제안
export interface SearchSuggestion {
  id: string;
  text: string;
  type: 'address' | 'apartment' | 'district' | 'landmark';
  coordinates?: Coordinates;
  count?: number; // 해당 지역의 아파트 수
}

// 검색 상태 관리
export interface SearchState {
  isSearching: boolean;
  query: string;
  results: RadiusSearchResult | null;
  history: SearchHistory[];
  suggestions: SearchSuggestion[];
  selectedApartment: ApartmentComplex | null;
  currentCenter: Coordinates;
  currentRadius: number;
  filters: SearchFilters;
  error: string | null;
}

// API 응답 타입
export interface SearchApiResponse {
  success: boolean;
  data: RadiusSearchResult;
  message?: string;
  timestamp: Date;
}

export interface ExportOptions {
  format: 'csv' | 'excel' | 'json';
  includeImages: boolean;
  includePriceHistory: boolean;
  includeTransportation: boolean;
}

export interface ExportResult {
  fileUrl: string;
  fileName: string;
  fileSize: number;
  expiresAt: Date;
}