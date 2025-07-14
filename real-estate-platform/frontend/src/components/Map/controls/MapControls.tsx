import React, { useState } from 'react';
import {
  Box,
  Card,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Slider,
  Typography,
  Divider,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Layers as LayersIcon,
  MyLocation as MyLocationIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Map as MapIcon,
  Satellite as SatelliteIcon,
  Traffic as TrafficIcon,
  DirectionsBike as BikeIcon,
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  RadioButtonUnchecked as RadiusIcon
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../../store';
import { 
  toggleLayerVisibility, 
  setMapType,
  setTrafficLayer,
  setBikeLayer 
} from '../../../store/slices/mapSlice';

interface MapControlsProps {
  map: any; // Kakao Map instance
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

const MapControls: React.FC<MapControlsProps> = ({ 
  map, 
  position = 'top-right' 
}) => {
  const dispatch = useDispatch();
  const { layers, viewport } = useSelector((state: RootState) => state.map);
  const [expanded, setExpanded] = useState<string | false>('layers');
  
  // 위치 기반 스타일
  const getPositionStyle = () => {
    const baseStyle = {
      position: 'absolute' as const,
      zIndex: 1000,
      m: 2
    };

    switch (position) {
      case 'top-left':
        return { ...baseStyle, top: 0, left: 0 };
      case 'top-right':
        return { ...baseStyle, top: 0, right: 0 };
      case 'bottom-left':
        return { ...baseStyle, bottom: 0, left: 0 };
      case 'bottom-right':
        return { ...baseStyle, bottom: 0, right: 0 };
      default:
        return { ...baseStyle, top: 0, right: 0 };
    }
  };

  // 현재 위치로 이동
  const moveToCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('위치 서비스가 지원되지 않습니다.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const moveLatLng = new window.kakao.maps.LatLng(latitude, longitude);
        map.setCenter(moveLatLng);
        map.setLevel(3); // 확대
      },
      (error) => {
        console.error('위치 정보를 가져올 수 없습니다:', error);
        alert('위치 정보를 가져올 수 없습니다.');
      }
    );
  };

  // 지도 확대/축소
  const zoomIn = () => {
    const level = map.getLevel();
    map.setLevel(level - 1);
  };

  const zoomOut = () => {
    const level = map.getLevel();
    map.setLevel(level + 1);
  };

  // 지도 타입 변경
  const handleMapTypeChange = (event: React.MouseEvent<HTMLElement>, newType: string | null) => {
    if (!newType || !map) return;

    let mapTypeId;
    switch (newType) {
      case 'normal':
        mapTypeId = window.kakao.maps.MapTypeId.NORMAL;
        break;
      case 'satellite':
        mapTypeId = window.kakao.maps.MapTypeId.SATELLITE;
        break;
      case 'hybrid':
        mapTypeId = window.kakao.maps.MapTypeId.HYBRID;
        break;
      default:
        mapTypeId = window.kakao.maps.MapTypeId.NORMAL;
    }

    map.setMapTypeId(mapTypeId);
    dispatch(setMapType(newType));
  };

  // 레이어 토글
  const handleLayerToggle = (layerId: string) => {
    dispatch(toggleLayerVisibility(layerId));
  };

  // 교통정보 토글
  const handleTrafficToggle = (checked: boolean) => {
    if (checked) {
      map.addOverlayMapTypeId(window.kakao.maps.MapTypeId.TRAFFIC);
    } else {
      map.removeOverlayMapTypeId(window.kakao.maps.MapTypeId.TRAFFIC);
    }
    dispatch(setTrafficLayer(checked));
  };

  // 자전거 도로 토글
  const handleBikeToggle = (checked: boolean) => {
    if (checked) {
      map.addOverlayMapTypeId(window.kakao.maps.MapTypeId.BICYCLE);
    } else {
      map.removeOverlayMapTypeId(window.kakao.maps.MapTypeId.BICYCLE);
    }
    dispatch(setBikeLayer(checked));
  };

  // 아코디언 상태 변경
  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent, 
    isExpanded: boolean
  ) => {
    setExpanded(isExpanded ? panel : false);
  };

  return (
    <Box sx={getPositionStyle()}>
      <Card elevation={4} sx={{ minWidth: 250, maxWidth: 300 }}>
        
        {/* 기본 컨트롤 */}
        <Box p={1} display="flex" gap={1} justifyContent="center">
          <Tooltip title="현재 위치">
            <IconButton onClick={moveToCurrentLocation} size="small">
              <MyLocationIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="확대">
            <IconButton onClick={zoomIn} size="small">
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="축소">
            <IconButton onClick={zoomOut} size="small">
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Divider />

        {/* 레이어 컨트롤 */}
        <Accordion 
          expanded={expanded === 'layers'} 
          onChange={handleAccordionChange('layers')}
          elevation={0}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <LayersIcon sx={{ mr: 1 }} />
            <Typography variant="body2">레이어</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box display="flex" flexDirection="column" gap={1}>
              {layers.map((layer) => (
                <FormControlLabel
                  key={layer.id}
                  control={
                    <Switch
                      checked={layer.visible}
                      onChange={() => handleLayerToggle(layer.id)}
                      size="small"
                    />
                  }
                  label={layer.name}
                />
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* 지도 타입 */}
        <Accordion 
          expanded={expanded === 'maptype'} 
          onChange={handleAccordionChange('maptype')}
          elevation={0}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <MapIcon sx={{ mr: 1 }} />
            <Typography variant="body2">지도 타입</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ToggleButtonGroup
              value="normal"
              exclusive
              onChange={handleMapTypeChange}
              size="small"
              fullWidth
            >
              <ToggleButton value="normal">
                <MapIcon fontSize="small" />
              </ToggleButton>
              <ToggleButton value="satellite">
                <SatelliteIcon fontSize="small" />
              </ToggleButton>
              <ToggleButton value="hybrid">
                하이브리드
              </ToggleButton>
            </ToggleButtonGroup>
          </AccordionDetails>
        </Accordion>

        {/* 추가 옵션 */}
        <Accordion 
          expanded={expanded === 'options'} 
          onChange={handleAccordionChange('options')}
          elevation={0}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <TrafficIcon sx={{ mr: 1 }} />
            <Typography variant="body2">추가 옵션</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    onChange={(e) => handleTrafficToggle(e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Box display="flex" alignItems="center">
                    <TrafficIcon fontSize="small" sx={{ mr: 1 }} />
                    교통정보
                  </Box>
                }
              />
              
              <FormControlLabel
                control={
                  <Switch
                    onChange={(e) => handleBikeToggle(e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Box display="flex" alignItems="center">
                    <BikeIcon fontSize="small" sx={{ mr: 1 }} />
                    자전거 도로
                  </Box>
                }
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* 검색 반경 */}
        <Accordion 
          expanded={expanded === 'search'} 
          onChange={handleAccordionChange('search')}
          elevation={0}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <SearchIcon sx={{ mr: 1 }} />
            <Typography variant="body2">검색 반경</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box px={1}>
              <Typography variant="body2" gutterBottom>
                반경: {viewport?.searchRadius || 1}km
              </Typography>
              <Slider
                value={viewport?.searchRadius || 1}
                min={0.5}
                max={10}
                step={0.5}
                marks={[
                  { value: 1, label: '1km' },
                  { value: 5, label: '5km' },
                  { value: 10, label: '10km' }
                ]}
                valueLabelDisplay="auto"
                size="small"
              />
            </Box>
          </AccordionDetails>
        </Accordion>

      </Card>
    </Box>
  );
};

export default MapControls;