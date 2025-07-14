import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Box, Alert, CircularProgress, Backdrop } from '@mui/material';
import { MapState, MapEvent, MapConfig, Coordinates } from '../../types/map';
import { ApartmentComplex } from '../../types/apartment';
import { 
  setMapInstance, 
  setViewport, 
  setSelectedMarker,
  addMarkers,
  setLoading 
} from '../../store/slices/mapSlice';
import { RootState } from '../../store';
import ApartmentLayer from './layers/ApartmentLayer';
import ProjectSiteLayer from './layers/ProjectSiteLayer';
import MapControls from './controls/MapControls';
import MapInfoPanel from './panels/MapInfoPanel';
import SearchRadiusOverlay from './overlays/SearchRadiusOverlay';

// Kakao Map API 타입 선언
declare global {
  interface Window {
    kakao: any;
  }
}

interface MapComponentProps {
  onMarkerClick?: (marker: any) => void;
  onMapClick?: (event: MapEvent) => void;
  onBoundsChanged?: (bounds: any) => void;
  className?: string;
  height?: string | number;
}

const MapComponent: React.FC<MapComponentProps> = ({
  onMarkerClick,
  onMapClick,
  onBoundsChanged,
  className,
  height = '100vh'
}) => {
  const dispatch = useDispatch();
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  
  // Redux state
  const { 
    viewport, 
    markers, 
    selectedMarker, 
    layers,
    isLoading,
    projectSites 
  } = useSelector((state: RootState) => state.map);
  
  const [apiLoaded, setApiLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 지도 설정
  const mapConfig: MapConfig = {
    defaultCenter: { lat: 37.5665, lng: 126.9780 }, // 서울 시청
    defaultZoom: 11,
    minZoom: 6,
    maxZoom: 21,
    mapType: 'normal',
    enableScrollZoom: true,
    enableDoubleClickZoom: true,
    enableKeyboardShortcuts: true,
    showTrafficLayer: false,
    showBikeLayer: false,
    apiKey: process.env.REACT_APP_KAKAO_MAP_API_KEY || ''
  };

  // Kakao Map API 로드
  useEffect(() => {
    const loadKakaoMapAPI = () => {
      if (window.kakao && window.kakao.maps) {
        setApiLoaded(true);
        return;
      }

      const script = document.createElement('script');
      script.async = true;
      script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${mapConfig.apiKey}&autoload=false&libraries=services,clusterer,drawing`;
      
      script.onload = () => {
        window.kakao.maps.load(() => {
          setApiLoaded(true);
        });
      };
      
      script.onerror = () => {
        setError('Kakao Map API 로드에 실패했습니다.');
      };
      
      document.head.appendChild(script);
    };

    if (!mapConfig.apiKey) {
      setError('Kakao Map API 키가 설정되지 않았습니다.');
      return;
    }

    loadKakaoMapAPI();
  }, [mapConfig.apiKey]);

  // 지도 초기화
  useEffect(() => {
    if (!apiLoaded || !mapContainer.current || mapInstance.current) return;

    try {
      dispatch(setLoading(true));

      const options = {
        center: new window.kakao.maps.LatLng(
          mapConfig.defaultCenter.lat, 
          mapConfig.defaultCenter.lng
        ),
        level: mapConfig.defaultZoom,
        mapTypeId: window.kakao.maps.MapTypeId.NORMAL
      };

      const map = new window.kakao.maps.Map(mapContainer.current, options);
      mapInstance.current = map;
      
      // Redux store에 지도 인스턴스 저장
      dispatch(setMapInstance(map));

      // 지도 컨트롤 설정
      setupMapControls(map);

      // 지도 이벤트 리스너 등록
      setupMapEventListeners(map);

      // 초기 뷰포트 설정
      dispatch(setViewport({
        center: mapConfig.defaultCenter,
        zoom: mapConfig.defaultZoom,
        bounds: {
          northEast: { lat: 0, lng: 0 },
          southWest: { lat: 0, lng: 0 }
        }
      }));

      dispatch(setLoading(false));
      
    } catch (err) {
      setError('지도 초기화에 실패했습니다.');
      dispatch(setLoading(false));
    }
  }, [apiLoaded, dispatch]);

  // 지도 컨트롤 설정
  const setupMapControls = (map: any) => {
    // 확대/축소 컨트롤
    const zoomControl = new window.kakao.maps.ZoomControl();
    map.addControl(zoomControl, window.kakao.maps.ControlPosition.TOPRIGHT);

    // 지도 타입 컨트롤
    const mapTypeControl = new window.kakao.maps.MapTypeControl();
    map.addControl(mapTypeControl, window.kakao.maps.ControlPosition.BOTTOMRIGHT);
  };

  // 지도 이벤트 리스너 설정
  const setupMapEventListeners = (map: any) => {
    // 클릭 이벤트
    window.kakao.maps.event.addListener(map, 'click', (mouseEvent: any) => {
      const latlng = mouseEvent.latLng;
      const coordinates: Coordinates = {
        lat: latlng.getLat(),
        lng: latlng.getLng()
      };

      const mapEvent: MapEvent = {
        type: 'click',
        coordinates,
        target: mouseEvent
      };

      onMapClick?.(mapEvent);
    });

    // 지도 이동 이벤트
    window.kakao.maps.event.addListener(map, 'dragend', () => {
      updateViewport(map);
    });

    // 줌 변경 이벤트
    window.kakao.maps.event.addListener(map, 'zoom_changed', () => {
      updateViewport(map);
    });

    // 영역 변경 이벤트
    window.kakao.maps.event.addListener(map, 'bounds_changed', () => {
      const bounds = map.getBounds();
      onBoundsChanged?.(bounds);
    });
  };

  // 뷰포트 업데이트
  const updateViewport = (map: any) => {
    const center = map.getCenter();
    const level = map.getLevel();
    const bounds = map.getBounds();

    const newViewport = {
      center: {
        lat: center.getLat(),
        lng: center.getLng()
      },
      zoom: level,
      bounds: {
        northEast: {
          lat: bounds.getNorthEast().getLat(),
          lng: bounds.getNorthEast().getLng()
        },
        southWest: {
          lat: bounds.getSouthWest().getLat(),
          lng: bounds.getSouthWest().getLng()
        }
      }
    };

    dispatch(setViewport(newViewport));
  };

  // 마커 클릭 핸들러
  const handleMarkerClick = (marker: any, data: any) => {
    dispatch(setSelectedMarker({ ...marker, data }));
    onMarkerClick?.(data);
  };

  // 에러 상태 렌더링
  if (error) {
    return (
      <Box className={className} height={height} display="flex" alignItems="center" justifyContent="center">
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  // 로딩 상태 렌더링
  if (!apiLoaded) {
    return (
      <Box className={className} height={height} display="flex" alignItems="center" justifyContent="center">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box className={className} height={height} position="relative">
      {/* 지도 컨테이너 */}
      <div 
        ref={mapContainer} 
        style={{ 
          width: '100%', 
          height: '100%',
          borderRadius: '8px',
          overflow: 'hidden'
        }} 
      />

      {/* 지도가 로드된 후 레이어들 렌더링 */}
      {mapInstance.current && (
        <>
          {/* 아파트 데이터 레이어 */}
          <ApartmentLayer
            map={mapInstance.current}
            visible={layers.find(l => l.id === 'apartments')?.visible ?? true}
            onMarkerClick={handleMarkerClick}
          />

          {/* 프로젝트 사이트 레이어 */}
          <ProjectSiteLayer
            map={mapInstance.current}
            sites={projectSites}
            visible={layers.find(l => l.id === 'project-sites')?.visible ?? true}
            onMarkerClick={handleMarkerClick}
          />

          {/* 검색 반경 오버레이 */}
          <SearchRadiusOverlay map={mapInstance.current} />
        </>
      )}

      {/* 지도 컨트롤들 */}
      <MapControls map={mapInstance.current} />

      {/* 정보 패널 */}
      {selectedMarker && (
        <MapInfoPanel 
          marker={selectedMarker}
          onClose={() => dispatch(setSelectedMarker(null))}
        />
      )}

      {/* 로딩 오버레이 */}
      <Backdrop
        open={isLoading}
        sx={{ 
          position: 'absolute', 
          zIndex: 1000,
          backgroundColor: 'rgba(255, 255, 255, 0.7)'
        }}
      >
        <CircularProgress />
      </Backdrop>
    </Box>
  );
};

export default MapComponent;