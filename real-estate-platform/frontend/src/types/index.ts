// 모든 타입 정의 내보내기

export * from './apartment';
export * from './search';
export * from './map';

// 공통 타입들
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  timestamp: Date;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasMore: boolean;
}

// 사용자 관련 타입
export interface User {
  id: string;
  email: string;
  name: string;
  company?: string;
  role: 'admin' | 'user' | 'viewer';
  preferences: UserPreferences;
  createdAt: Date;
  lastLoginAt?: Date;
}

export interface UserPreferences {
  defaultMapCenter: { lat: number; lng: number };
  defaultMapZoom: number;
  defaultSearchRadius: number;
  theme: 'light' | 'dark' | 'auto';
  language: 'ko' | 'en';
  notifications: {
    email: boolean;
    browser: boolean;
    priceAlerts: boolean;
  };
}

// 에러 타입
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// 로딩 상태
export interface LoadingState {
  [key: string]: boolean;
}

// 환경 변수 타입
export interface EnvironmentConfig {
  API_URL: string;
  KAKAO_API_KEY: string;
  GOOGLE_MAPS_API_KEY?: string;
  NODE_ENV: 'development' | 'production' | 'test';
  VERSION: string;
}

// 애플리케이션 전체 상태
export interface RootState {
  map: any;
  search: any;
  user: any;
  ui: any;
}