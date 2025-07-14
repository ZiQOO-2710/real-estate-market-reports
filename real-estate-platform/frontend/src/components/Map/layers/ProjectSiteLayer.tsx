import React, { useEffect, useRef } from 'react';
import { ProjectSite, Coordinates } from '../../../types/map';

interface ProjectSiteLayerProps {
  map: any; // Kakao Map instance
  sites: ProjectSite[];
  visible: boolean;
  onMarkerClick?: (marker: any, data: ProjectSite) => void;
  editable?: boolean;
}

const ProjectSiteLayer: React.FC<ProjectSiteLayerProps> = ({
  map,
  sites,
  visible,
  onMarkerClick,
  editable = false
}) => {
  const markersRef = useRef<any[]>([]);
  const polygonsRef = useRef<any[]>([]);

  // 프로젝트 사이트 마커 이미지 생성
  const createProjectSiteMarkerImage = () => {
    const svg = `
      <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" fill="#2196F3" stroke="#ffffff" stroke-width="3" opacity="0.9"/>
        <path d="M10 16l4 4 8-8" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    
    return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
  };

  // 프로젝트 사이트 마커 생성
  const createProjectSiteMarkers = () => {
    if (!map || !window.kakao?.maps) return;

    // 기존 마커와 폴리곤 제거
    clearMarkers();

    const newMarkers: any[] = [];
    const newPolygons: any[] = [];

    sites.forEach((site) => {
      try {
        // 중심점 마커 생성
        const position = new window.kakao.maps.LatLng(
          site.coordinates.lat,
          site.coordinates.lng
        );

        const markerImage = new window.kakao.maps.MarkerImage(
          createProjectSiteMarkerImage(),
          new window.kakao.maps.Size(32, 32),
          { offset: new window.kakao.maps.Point(16, 16) }
        );

        const marker = new window.kakao.maps.Marker({
          position,
          image: markerImage,
          title: site.name,
          clickable: true
        });

        // 마커 클릭 이벤트
        window.kakao.maps.event.addListener(marker, 'click', () => {
          onMarkerClick?.(marker, site);
        });

        // 경계 폴리곤이 있는 경우 생성
        if (site.boundaryPolygon && site.boundaryPolygon.length > 0) {
          const polygonPath = site.boundaryPolygon.map(coord => 
            new window.kakao.maps.LatLng(coord.lat, coord.lng)
          );

          const polygon = new window.kakao.maps.Polygon({
            path: polygonPath,
            strokeWeight: 3,
            strokeColor: '#2196F3',
            strokeOpacity: 0.8,
            fillColor: '#2196F3',
            fillOpacity: 0.2
          });

          // 폴리곤 클릭 이벤트
          window.kakao.maps.event.addListener(polygon, 'click', () => {
            onMarkerClick?.(polygon, site);
          });

          newPolygons.push(polygon);
          polygon.setMap(visible ? map : null);
        }

        newMarkers.push(marker);
        marker.setMap(visible ? map : null);

      } catch (error) {
        console.error('프로젝트 사이트 마커 생성 오류:', error);
      }
    });

    markersRef.current = newMarkers;
    polygonsRef.current = newPolygons;
  };

  // 마커와 폴리곤 제거
  const clearMarkers = () => {
    markersRef.current.forEach(marker => {
      marker.setMap(null);
    });
    
    polygonsRef.current.forEach(polygon => {
      polygon.setMap(null);
    });
    
    markersRef.current = [];
    polygonsRef.current = [];
  };

  // 레이어 표시/숨김
  useEffect(() => {
    markersRef.current.forEach(marker => {
      marker.setMap(visible ? map : null);
    });
    
    polygonsRef.current.forEach(polygon => {
      polygon.setMap(visible ? map : null);
    });
  }, [visible, map]);

  // 사이트 데이터 변경시 마커 업데이트
  useEffect(() => {
    if (!map) return;
    createProjectSiteMarkers();

    return () => {
      clearMarkers();
    };
  }, [map, sites]);

  // 컴포넌트 언마운트시 정리
  useEffect(() => {
    return () => {
      clearMarkers();
    };
  }, []);

  return null;
};

export default ProjectSiteLayer;