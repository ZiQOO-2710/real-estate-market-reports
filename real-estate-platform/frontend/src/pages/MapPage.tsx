import React, { useEffect } from 'react';
import { Box, Container, Typography, Alert } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import MapComponent from '../components/Map/MapComponent';
import { RootState } from '../store';
import { MapEvent } from '../types/map';
import { setApartments } from '../store/slices/apartmentSlice';
import { sampleApartments } from '../data/sampleApartments';

const MapPage: React.FC = () => {
  const dispatch = useDispatch();
  const { isLoading } = useSelector((state: RootState) => state.map);

  // 컴포넌트 마운트시 샘플 데이터 로드
  useEffect(() => {
    dispatch(setApartments(sampleApartments));
  }, [dispatch]);

  // 지도 클릭 이벤트 핸들러
  const handleMapClick = (event: MapEvent) => {
    console.log('지도 클릭:', event);
    
    if (event.coordinates) {
      // TODO: 클릭한 위치를 기준으로 검색 등의 작업 수행
      console.log(`클릭 위치: ${event.coordinates.lat}, ${event.coordinates.lng}`);
    }
  };

  // 마커 클릭 이벤트 핸들러
  const handleMarkerClick = (data: any) => {
    console.log('마커 클릭:', data);
    
    // TODO: 마커 클릭시 상세 정보 표시 또는 다른 작업 수행
  };

  // 지도 영역 변경 이벤트 핸들러
  const handleBoundsChanged = (bounds: any) => {
    console.log('지도 영역 변경:', bounds);
    
    // TODO: 새로운 영역의 아파트 데이터 로드
  };

  // 환경변수 체크
  const kakaoApiKey = process.env.REACT_APP_KAKAO_MAP_API_KEY;
  
  if (!kakaoApiKey) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            설정 오류
          </Typography>
          <Typography variant="body2">
            Kakao Map API 키가 설정되지 않았습니다. 
            <br />
            .env 파일에 REACT_APP_KAKAO_MAP_API_KEY를 설정해주세요.
          </Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Box 
      sx={{ 
        width: '100%', 
        height: '100vh',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* 헤더 영역 (선택사항) */}
      {/* <Box 
        sx={{ 
          p: 2, 
          backgroundColor: 'primary.main', 
          color: 'white',
          zIndex: 1100
        }}
      >
        <Typography variant="h6">
          부동산 시장 분석 플랫폼
        </Typography>
      </Box> */}

      {/* 지도 영역 */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <MapComponent
          onMapClick={handleMapClick}
          onMarkerClick={handleMarkerClick}
          onBoundsChanged={handleBoundsChanged}
          height="100%"
        />
      </Box>
    </Box>
  );
};

export default MapPage;