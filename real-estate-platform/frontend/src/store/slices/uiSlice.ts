// UI 상태 관리 Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  // 사이드바 및 패널 상태
  leftSidebarOpen: boolean;
  rightPanelOpen: boolean;
  leftSidebarWidth: number;
  rightPanelWidth: number;
  
  // 모달 상태
  modals: {
    apartmentDetail: boolean;
    searchFilter: boolean;
    projectSite: boolean;
    export: boolean;
    settings: boolean;
  };
  
  // 로딩 상태
  loading: {
    search: boolean;
    apartments: boolean;
    export: boolean;
    map: boolean;
  };
  
  // 토스트/알림
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    duration?: number;
    timestamp: Date;
  }>;
  
  // 테마 및 설정
  theme: 'light' | 'dark' | 'auto';
  language: 'ko' | 'en';
  
  // 현재 활성 탭/페이지
  activeTab: 'search' | 'analytics' | 'projects' | 'settings';
  
  // 툴팁 및 도움말
  showTutorial: boolean;
  tutorialStep: number;
  
  // 화면 크기 정보
  screenSize: 'mobile' | 'tablet' | 'desktop';
  isMobile: boolean;
  
  // 기타 UI 상태
  mapFullscreen: boolean;
  showSearchResults: boolean;
  showAnalyticsPanel: boolean;
}

const initialState: UIState = {
  leftSidebarOpen: true,
  rightPanelOpen: false,
  leftSidebarWidth: 320,
  rightPanelWidth: 400,
  
  modals: {
    apartmentDetail: false,
    searchFilter: false,
    projectSite: false,
    export: false,
    settings: false,
  },
  
  loading: {
    search: false,
    apartments: false,
    export: false,
    map: false,
  },
  
  notifications: [],
  
  theme: 'light',
  language: 'ko',
  
  activeTab: 'search',
  
  showTutorial: false,
  tutorialStep: 0,
  
  screenSize: 'desktop',
  isMobile: false,
  
  mapFullscreen: false,
  showSearchResults: false,
  showAnalyticsPanel: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // 사이드바 및 패널 제어
    toggleLeftSidebar: (state) => {
      state.leftSidebarOpen = !state.leftSidebarOpen;
    },

    setLeftSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.leftSidebarOpen = action.payload;
    },

    toggleRightPanel: (state) => {
      state.rightPanelOpen = !state.rightPanelOpen;
    },

    setRightPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.rightPanelOpen = action.payload;
    },

    setLeftSidebarWidth: (state, action: PayloadAction<number>) => {
      state.leftSidebarWidth = action.payload;
    },

    setRightPanelWidth: (state, action: PayloadAction<number>) => {
      state.rightPanelWidth = action.payload;
    },

    // 모달 제어
    openModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = true;
    },

    closeModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = false;
    },

    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(key => {
        state.modals[key as keyof UIState['modals']] = false;
      });
    },

    // 로딩 상태 제어
    setLoading: (state, action: PayloadAction<{ key: keyof UIState['loading']; value: boolean }>) => {
      const { key, value } = action.payload;
      state.loading[key] = value;
    },

    setLoadingStates: (state, action: PayloadAction<Partial<UIState['loading']>>) => {
      state.loading = { ...state.loading, ...action.payload };
    },

    // 알림 관리
    addNotification: (state, action: PayloadAction<Omit<UIState['notifications'][0], 'id' | 'timestamp'>>) => {
      const notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date(),
      };
      state.notifications.push(notification);
    },

    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },

    clearNotifications: (state) => {
      state.notifications = [];
    },

    // 테마 및 언어
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },

    setLanguage: (state, action: PayloadAction<'ko' | 'en'>) => {
      state.language = action.payload;
    },

    // 탭/페이지 제어
    setActiveTab: (state, action: PayloadAction<UIState['activeTab']>) => {
      state.activeTab = action.payload;
    },

    // 튜토리얼 제어
    setShowTutorial: (state, action: PayloadAction<boolean>) => {
      state.showTutorial = action.payload;
      if (!action.payload) {
        state.tutorialStep = 0;
      }
    },

    nextTutorialStep: (state) => {
      state.tutorialStep += 1;
    },

    setTutorialStep: (state, action: PayloadAction<number>) => {
      state.tutorialStep = action.payload;
    },

    // 화면 크기 업데이트
    setScreenSize: (state, action: PayloadAction<UIState['screenSize']>) => {
      state.screenSize = action.payload;
      state.isMobile = action.payload === 'mobile';
      
      // 모바일에서는 사이드바 자동 닫기
      if (state.isMobile) {
        state.leftSidebarOpen = false;
        state.rightPanelOpen = false;
      }
    },

    // 기타 UI 상태
    toggleMapFullscreen: (state) => {
      state.mapFullscreen = !state.mapFullscreen;
    },

    setMapFullscreen: (state, action: PayloadAction<boolean>) => {
      state.mapFullscreen = action.payload;
    },

    setShowSearchResults: (state, action: PayloadAction<boolean>) => {
      state.showSearchResults = action.payload;
    },

    setShowAnalyticsPanel: (state, action: PayloadAction<boolean>) => {
      state.showAnalyticsPanel = action.payload;
    },

    // 편의 메서드들
    showSuccessNotification: (state, action: PayloadAction<{ title: string; message: string }>) => {
      const notification = {
        ...action.payload,
        type: 'success' as const,
        id: Date.now().toString(),
        timestamp: new Date(),
        duration: 5000,
      };
      state.notifications.push(notification);
    },

    showErrorNotification: (state, action: PayloadAction<{ title: string; message: string }>) => {
      const notification = {
        ...action.payload,
        type: 'error' as const,
        id: Date.now().toString(),
        timestamp: new Date(),
        duration: 10000,
      };
      state.notifications.push(notification);
    },

    // 초기화
    resetUI: () => initialState,
  },
});

export const {
  toggleLeftSidebar,
  setLeftSidebarOpen,
  toggleRightPanel,
  setRightPanelOpen,
  setLeftSidebarWidth,
  setRightPanelWidth,
  openModal,
  closeModal,
  closeAllModals,
  setLoading,
  setLoadingStates,
  addNotification,
  removeNotification,
  clearNotifications,
  setTheme,
  setLanguage,
  setActiveTab,
  setShowTutorial,
  nextTutorialStep,
  setTutorialStep,
  setScreenSize,
  toggleMapFullscreen,
  setMapFullscreen,
  setShowSearchResults,
  setShowAnalyticsPanel,
  showSuccessNotification,
  showErrorNotification,
  resetUI,
} = uiSlice.actions;

export default uiSlice.reducer;