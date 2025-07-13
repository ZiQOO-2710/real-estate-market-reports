// Redux Store 설정

import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import mapSlice from './slices/mapSlice';
import searchSlice from './slices/searchSlice';
import uiSlice from './slices/uiSlice';
import userSlice from './slices/userSlice';

export const store = configureStore({
  reducer: {
    map: mapSlice,
    search: searchSlice,
    ui: uiSlice,
    user: userSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // 날짜나 지도 인스턴스 등 비직렬화 가능한 값들 무시
        ignoredActions: [
          'map/setMapInstance',
          'search/setSearchResults',
        ],
        ignoredPaths: [
          'map.mapInstance',
          'search.results.timestamp',
        ],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// 타입이 지정된 hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

export default store;