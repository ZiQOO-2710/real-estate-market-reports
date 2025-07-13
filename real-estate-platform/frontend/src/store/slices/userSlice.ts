// 사용자 상태 관리 Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User, UserPreferences } from '@/types';

interface UserState {
  currentUser: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // 사용자 설정
  preferences: UserPreferences;
  
  // 저장된 프로젝트와 즐겨찾기
  savedProjects: string[];
  favoriteApartments: string[];
  recentSearches: string[];
  
  // 권한 정보
  permissions: string[];
  subscription: {
    plan: 'free' | 'basic' | 'premium' | 'enterprise';
    expiresAt: Date | null;
    features: string[];
  };
}

const defaultPreferences: UserPreferences = {
  defaultMapCenter: { lat: 37.5665, lng: 126.9780 },
  defaultMapZoom: 12,
  defaultSearchRadius: 3,
  theme: 'light',
  language: 'ko',
  notifications: {
    email: true,
    browser: true,
    priceAlerts: false,
  },
};

const initialState: UserState = {
  currentUser: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  
  preferences: defaultPreferences,
  
  savedProjects: [],
  favoriteApartments: [],
  recentSearches: [],
  
  permissions: [],
  subscription: {
    plan: 'free',
    expiresAt: null,
    features: ['basic_search', 'map_view'],
  },
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // 인증 관련
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (action.payload) {
        state.error = null;
      }
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.isLoading = false;
    },

    loginSuccess: (state, action: PayloadAction<User>) => {
      state.currentUser = action.payload;
      state.isAuthenticated = true;
      state.isLoading = false;
      state.error = null;
      
      // 사용자 설정이 있으면 병합
      if (action.payload.preferences) {
        state.preferences = { ...defaultPreferences, ...action.payload.preferences };
      }
    },

    loginFailure: (state, action: PayloadAction<string>) => {
      state.currentUser = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = action.payload;
    },

    logout: (state) => {
      state.currentUser = null;
      state.isAuthenticated = false;
      state.error = null;
      state.savedProjects = [];
      state.favoriteApartments = [];
      // 기본 설정으로 리셋
      state.preferences = defaultPreferences;
    },

    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.currentUser) {
        state.currentUser = { ...state.currentUser, ...action.payload };
      }
    },

    // 사용자 설정 관리
    updatePreferences: (state, action: PayloadAction<Partial<UserPreferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },

    setDefaultMapCenter: (state, action: PayloadAction<{ lat: number; lng: number }>) => {
      state.preferences.defaultMapCenter = action.payload;
    },

    setDefaultMapZoom: (state, action: PayloadAction<number>) => {
      state.preferences.defaultMapZoom = action.payload;
    },

    setDefaultSearchRadius: (state, action: PayloadAction<number>) => {
      state.preferences.defaultSearchRadius = action.payload;
    },

    setThemePreference: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.preferences.theme = action.payload;
    },

    setLanguagePreference: (state, action: PayloadAction<'ko' | 'en'>) => {
      state.preferences.language = action.payload;
    },

    updateNotificationPreferences: (state, action: PayloadAction<Partial<UserPreferences['notifications']>>) => {
      state.preferences.notifications = { 
        ...state.preferences.notifications, 
        ...action.payload 
      };
    },

    // 저장된 데이터 관리
    addSavedProject: (state, action: PayloadAction<string>) => {
      if (!state.savedProjects.includes(action.payload)) {
        state.savedProjects.push(action.payload);
      }
    },

    removeSavedProject: (state, action: PayloadAction<string>) => {
      state.savedProjects = state.savedProjects.filter(id => id !== action.payload);
    },

    setSavedProjects: (state, action: PayloadAction<string[]>) => {
      state.savedProjects = action.payload;
    },

    addFavoriteApartment: (state, action: PayloadAction<string>) => {
      if (!state.favoriteApartments.includes(action.payload)) {
        state.favoriteApartments.push(action.payload);
      }
    },

    removeFavoriteApartment: (state, action: PayloadAction<string>) => {
      state.favoriteApartments = state.favoriteApartments.filter(id => id !== action.payload);
    },

    setFavoriteApartments: (state, action: PayloadAction<string[]>) => {
      state.favoriteApartments = action.payload;
    },

    addRecentSearch: (state, action: PayloadAction<string>) => {
      // 중복 제거하고 최상단에 추가
      state.recentSearches = [
        action.payload,
        ...state.recentSearches.filter(search => search !== action.payload)
      ].slice(0, 10); // 최대 10개까지만 저장
    },

    clearRecentSearches: (state) => {
      state.recentSearches = [];
    },

    // 권한 및 구독 관리
    setPermissions: (state, action: PayloadAction<string[]>) => {
      state.permissions = action.payload;
    },

    updateSubscription: (state, action: PayloadAction<Partial<UserState['subscription']>>) => {
      state.subscription = { ...state.subscription, ...action.payload };
    },

    // 편의 메서드들
    hasPermission: (state, action: PayloadAction<string>) => {
      return state.permissions.includes(action.payload);
    },

    hasFeature: (state, action: PayloadAction<string>) => {
      return state.subscription.features.includes(action.payload);
    },

    isPremiumUser: (state) => {
      return ['premium', 'enterprise'].includes(state.subscription.plan);
    },

    // 초기화
    resetUserState: () => initialState,
  },
});

export const {
  setLoading,
  setError,
  loginSuccess,
  loginFailure,
  logout,
  updateUser,
  updatePreferences,
  setDefaultMapCenter,
  setDefaultMapZoom,
  setDefaultSearchRadius,
  setThemePreference,
  setLanguagePreference,
  updateNotificationPreferences,
  addSavedProject,
  removeSavedProject,
  setSavedProjects,
  addFavoriteApartment,
  removeFavoriteApartment,
  setFavoriteApartments,
  addRecentSearch,
  clearRecentSearches,
  setPermissions,
  updateSubscription,
  resetUserState,
} = userSlice.actions;

export default userSlice.reducer;