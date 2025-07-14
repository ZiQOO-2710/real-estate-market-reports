// 메인 App 컴포넌트

import React, { useEffect } from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, GlobalStyles } from '@mui/material';

import store from '@/store';
import { useAppSelector, useAppDispatch } from '@/store';
import { setScreenSize } from '@/store/slices/uiSlice';

// 페이지 컴포넌트들
import Dashboard from '@/pages/Dashboard';
import MapPage from './pages/MapPage';
import Analytics from '@/pages/Analytics';
import Projects from '@/pages/Projects';
import Settings from '@/pages/Settings';

// 공통 컴포넌트들
import Layout from '@/components/Layout';
import LoadingScreen from '@/components/UI/LoadingScreen';
import NotificationContainer from '@/components/UI/NotificationContainer';

// 전역 스타일
const globalStyles = (
  <GlobalStyles
    styles={{
      '*': {
        boxSizing: 'border-box',
      },
      html: {
        height: '100%',
        fontFamily: '"Noto Sans KR", "Roboto", "Helvetica", "Arial", sans-serif',
      },
      body: {
        height: '100%',
        margin: 0,
        padding: 0,
        backgroundColor: '#f5f5f5',
      },
      '#root': {
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      },
      // 지도 관련 스타일
      '.map-container': {
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      },
      '.map-marker': {
        cursor: 'pointer',
        transition: 'transform 0.2s ease',
        '&:hover': {
          transform: 'scale(1.1)',
        },
      },
      // 스크롤바 스타일
      '*::-webkit-scrollbar': {
        width: '8px',
        height: '8px',
      },
      '*::-webkit-scrollbar-track': {
        backgroundColor: '#f1f1f1',
        borderRadius: '4px',
      },
      '*::-webkit-scrollbar-thumb': {
        backgroundColor: '#c1c1c1',
        borderRadius: '4px',
        '&:hover': {
          backgroundColor: '#a8a8a8',
        },
      },
    }}
  />
);

// 테마 생성 함수
const createAppTheme = (mode: 'light' | 'dark') => {
  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
      },
      secondary: {
        main: '#dc004e',
        light: '#ff5983',
        dark: '#9a0036',
      },
      background: {
        default: mode === 'light' ? '#f5f5f5' : '#121212',
        paper: mode === 'light' ? '#ffffff' : '#1e1e1e',
      },
      text: {
        primary: mode === 'light' ? '#333333' : '#ffffff',
        secondary: mode === 'light' ? '#666666' : '#cccccc',
      },
    },
    typography: {
      fontFamily: '"Noto Sans KR", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        marginBottom: '1rem',
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        marginBottom: '0.75rem',
      },
      h3: {
        fontSize: '1.5rem',
        fontWeight: 600,
        marginBottom: '0.5rem',
      },
      h4: {
        fontSize: '1.25rem',
        fontWeight: 500,
        marginBottom: '0.5rem',
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.6,
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.5,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: '8px',
            fontWeight: 500,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: '12px',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            '&:hover': {
              boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
            },
          },
        },
      },
    },
  });
};

// 화면 크기 감지 훅
const useScreenSize = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      let screenSize: 'mobile' | 'tablet' | 'desktop';

      if (width < 768) {
        screenSize = 'mobile';
      } else if (width < 1024) {
        screenSize = 'tablet';
      } else {
        screenSize = 'desktop';
      }

      dispatch(setScreenSize(screenSize));
    };

    // 초기 크기 설정
    handleResize();

    // 리사이즈 이벤트 리스너 추가
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [dispatch]);
};

// 메인 앱 컴포넌트 (Redux Provider 내부)
const AppContent: React.FC = () => {
  const theme = useAppSelector(state => state.ui.theme);
  const isLoading = useAppSelector(state => 
    Object.values(state.ui.loading).some(loading => loading)
  );

  // 화면 크기 감지
  useScreenSize();

  // 테마 설정
  const appTheme = React.useMemo(() => {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const currentTheme = theme === 'auto' ? systemTheme : theme;
    return createAppTheme(currentTheme);
  }, [theme]);

  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      {globalStyles}
      
      <Router>
        <Layout>
          {isLoading && <LoadingScreen />}
          
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
          
          <NotificationContainer />
        </Layout>
      </Router>
    </ThemeProvider>
  );
};

// 메인 App 컴포넌트 (Redux Provider 포함)
const App: React.FC = () => {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
};

export default App;