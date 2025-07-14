import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../../store';
import { Coordinates } from '../../../types/map';

interface SearchRadiusOverlayProps {
  map: any; // Kakao Map instance
}

const SearchRadiusOverlay: React.FC<SearchRadiusOverlayProps> = ({ map }) => {
  const circlesRef = useRef<any[]>([]);
  
  // Redux state에서 검색 정보 가져오기
  const { searchCenter, searchRadii, isSearching } = useSelector(
    (state: RootState) => state.search || { 
      searchCenter: null, 
      searchRadii: [1, 3, 5], 
      isSearching: false 
    }
  );

  // 반경 원 생성
  const createRadiusCircles = (center: Coordinates, radii: number[]) => {
    if (!map || !window.kakao?.maps) return;

    // 기존 원들 제거
    clearCircles();

    const newCircles: any[] = [];

    radii.forEach((radius, index) => {
      try {
        const circle = new window.kakao.maps.Circle({
          center: new window.kakao.maps.LatLng(center.lat, center.lng),
          radius: radius * 1000, // km를 m로 변환
          strokeWeight: 2,
          strokeColor: getRadiusColor(index),
          strokeOpacity: 0.8,
          strokeStyle: index === 0 ? 'solid' : 'dashed',
          fillColor: getRadiusColor(index),
          fillOpacity: 0.1
        });

        circle.setMap(map);
        newCircles.push(circle);

        // 반경 라벨 추가
        createRadiusLabel(center, radius, index);

      } catch (error) {
        console.error('반경 원 생성 오류:', error);
      }
    });

    circlesRef.current = newCircles;
  };

  // 반경별 색상 설정
  const getRadiusColor = (index: number): string => {
    const colors = [
      '#FF5722', // 빨강 (1차 반경)
      '#FF9800', // 주황 (2차 반경)
      '#FFC107', // 노랑 (3차 반경)
      '#4CAF50', // 녹색 (4차 반경)
      '#2196F3'  // 파랑 (5차 반경)
    ];
    return colors[index] || '#9E9E9E';
  };

  // 반경 라벨 생성
  const createRadiusLabel = (center: Coordinates, radius: number, index: number) => {
    if (!window.kakao?.maps) return;

    // 라벨 위치 계산 (북동쪽 방향)
    const labelPosition = calculateLabelPosition(center, radius);
    
    const content = `
      <div style="
        background: ${getRadiusColor(index)};
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        white-space: nowrap;
      ">
        ${radius}km
      </div>
    `;

    const customOverlay = new window.kakao.maps.CustomOverlay({
      position: new window.kakao.maps.LatLng(labelPosition.lat, labelPosition.lng),
      content: content,
      yAnchor: 0.5,
      xAnchor: 0.5
    });

    customOverlay.setMap(map);
    circlesRef.current.push(customOverlay);
  };

  // 라벨 위치 계산 (반지름의 북동쪽 45도 지점)
  const calculateLabelPosition = (center: Coordinates, radiusKm: number): Coordinates => {
    const earthRadius = 6371; // 지구 반지름 (km)
    const bearing = 45; // 북동쪽 방향 (45도)
    
    const lat1 = center.lat * Math.PI / 180;
    const lng1 = center.lng * Math.PI / 180;
    const bearingRad = bearing * Math.PI / 180;
    
    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(radiusKm / earthRadius) +
      Math.cos(lat1) * Math.sin(radiusKm / earthRadius) * Math.cos(bearingRad)
    );
    
    const lng2 = lng1 + Math.atan2(
      Math.sin(bearingRad) * Math.sin(radiusKm / earthRadius) * Math.cos(lat1),
      Math.cos(radiusKm / earthRadius) - Math.sin(lat1) * Math.sin(lat2)
    );
    
    return {
      lat: lat2 * 180 / Math.PI,
      lng: lng2 * 180 / Math.PI
    };
  };

  // 중심점 마커 생성
  const createCenterMarker = (center: Coordinates) => {
    if (!map || !window.kakao?.maps) return;

    const markerImageSrc = createCenterMarkerImage();
    const markerImage = new window.kakao.maps.MarkerImage(
      markerImageSrc,
      new window.kakao.maps.Size(32, 32),
      { offset: new window.kakao.maps.Point(16, 16) }
    );

    const marker = new window.kakao.maps.Marker({
      position: new window.kakao.maps.LatLng(center.lat, center.lng),
      image: markerImage,
      title: '검색 중심점'
    });

    marker.setMap(map);
    circlesRef.current.push(marker);
  };

  // 검색 중심점 마커 이미지 생성
  const createCenterMarkerImage = (): string => {
    const svg = `
      <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" fill="#FF5722" stroke="#ffffff" stroke-width="3"/>
        <circle cx="16" cy="16" r="8" fill="#ffffff"/>
        <circle cx="16" cy="16" r="4" fill="#FF5722"/>
      </svg>
    `;
    
    return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
  };

  // 모든 오버레이 제거
  const clearCircles = () => {
    circlesRef.current.forEach(item => {
      if (item.setMap) {
        item.setMap(null);
      }
    });
    circlesRef.current = [];
  };

  // 검색 상태가 변경될 때 오버레이 업데이트
  useEffect(() => {
    if (!map) return;

    if (isSearching && searchCenter && searchRadii.length > 0) {
      // 검색 중심점 마커 생성
      createCenterMarker(searchCenter);
      
      // 반경 원들 생성
      createRadiusCircles(searchCenter, searchRadii);
    } else {
      // 검색이 비활성화되면 모든 오버레이 제거
      clearCircles();
    }

    return () => {
      clearCircles();
    };
  }, [map, isSearching, searchCenter, searchRadii]);

  // 컴포넌트 언마운트시 정리
  useEffect(() => {
    return () => {
      clearCircles();
    };
  }, []);

  return null; // 이 컴포넌트는 UI를 렌더링하지 않음
};

export default SearchRadiusOverlay;