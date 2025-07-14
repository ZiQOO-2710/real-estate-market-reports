import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  Box,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  Home as HomeIcon,
  LocationOn as LocationIcon,
  TrendingUp as TrendingUpIcon,
  CalendarToday as CalendarIcon,
  Info as InfoIcon,
  Launch as LaunchIcon,
  Share as ShareIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon
} from '@mui/icons-material';
import { MapMarker } from '../../../types/map';
import { ApartmentComplex } from '../../../types/apartment';

interface MapInfoPanelProps {
  marker: MapMarker;
  onClose: () => void;
  position?: 'left' | 'right';
}

const MapInfoPanel: React.FC<MapInfoPanelProps> = ({
  marker,
  onClose,
  position = 'right'
}) => {
  const apartment = marker.data as ApartmentComplex;

  // 패널 위치 스타일
  const getPanelStyle = () => {
    const baseStyle = {
      position: 'absolute' as const,
      top: 16,
      width: 350,
      maxHeight: 'calc(100vh - 32px)',
      zIndex: 1200,
      overflow: 'auto'
    };

    return position === 'left' 
      ? { ...baseStyle, left: 16 }
      : { ...baseStyle, right: 16 };
  };

  // 가격 포맷팅
  const formatPrice = (price?: number): string => {
    if (!price) return '정보없음';
    
    const billion = Math.floor(price / 10000);
    const million = Math.floor((price % 10000) / 1000);
    
    if (billion > 0 && million > 0) {
      return `${billion}억 ${million}천만원`;
    } else if (billion > 0) {
      return `${billion}억원`;
    } else if (million > 0) {
      return `${million}천만원`;
    } else {
      return `${price}만원`;
    }
  };

  // 평수 계산
  const calculatePyeong = (sqm?: number): string => {
    if (!sqm) return '정보없음';
    return `${(sqm / 3.3058).toFixed(1)}평`;
  };

  // 준공년도에서 연수 계산
  const getAgeFromYear = (year?: number): string => {
    if (!year) return '정보없음';
    const age = new Date().getFullYear() - year;
    return `${age}년차`;
  };

  if (marker.type !== 'apartment') {
    return (
      <Card elevation={8} sx={getPanelStyle()}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Typography variant="h6" gutterBottom>
              {marker.data?.name || '정보없음'}
            </Typography>
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {marker.type === 'project-site' ? '프로젝트 사이트' : '기타 마커'}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={8} sx={getPanelStyle()}>
      {/* 헤더 */}
      <CardContent sx={{ pb: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography variant="h6" gutterBottom>
              {apartment.name}
            </Typography>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <LocationIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {apartment.address.road || apartment.address.jibun}
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* 상태 태그들 */}
        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          <Chip 
            label={apartment.details.constructionYear ? getAgeFromYear(apartment.details.constructionYear) : '정보없음'} 
            size="small" 
            variant="outlined" 
          />
          <Chip 
            label={`${apartment.details.totalUnits || 0}세대`} 
            size="small" 
            variant="outlined" 
          />
          <Chip 
            label={`${apartment.details.floors || 0}층`} 
            size="small" 
            variant="outlined" 
          />
        </Box>
      </CardContent>

      <Divider />

      {/* 시장 정보 */}
      <CardContent sx={{ py: 2 }}>
        <Typography variant="subtitle2" gutterBottom color="primary">
          <TrendingUpIcon sx={{ mr: 1, fontSize: 16 }} />
          시장 정보
        </Typography>
        
        <List dense>
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="최근 거래가"
              secondary={formatPrice(apartment.marketData?.lastTransactionPrice)}
            />
          </ListItem>
          
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="현재 호가"
              secondary={formatPrice(apartment.marketData?.currentAskingPrice)}
            />
          </ListItem>
          
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="평당 가격"
              secondary={formatPrice(apartment.marketData?.pricePerPyeong)}
            />
          </ListItem>
          
          {apartment.marketData?.lastTransactionDate && (
            <ListItem sx={{ px: 0 }}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                <CalendarIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="최근 거래일"
                secondary={new Date(apartment.marketData.lastTransactionDate).toLocaleDateString()}
              />
            </ListItem>
          )}
        </List>
      </CardContent>

      <Divider />

      {/* 단지 정보 */}
      <CardContent sx={{ py: 2 }}>
        <Typography variant="subtitle2" gutterBottom color="primary">
          <HomeIcon sx={{ mr: 1, fontSize: 16 }} />
          단지 정보
        </Typography>
        
        <List dense>
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="주차비율"
              secondary={apartment.details.parkingRatio ? `${apartment.details.parkingRatio}%` : '정보없음'}
            />
          </ListItem>
          
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="준공년월"
              secondary={apartment.details.constructionYear || '정보없음'}
            />
          </ListItem>
          
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary="세대수"
              secondary={`${apartment.details.totalUnits || 0}세대`}
            />
          </ListItem>
        </List>
      </CardContent>

      <Divider />

      {/* 액션 버튼들 */}
      <CardActions sx={{ p: 2, gap: 1 }}>
        <Tooltip title="관심 단지 추가">
          <IconButton size="small" color="primary">
            <FavoriteBorderIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="공유하기">
          <IconButton size="small">
            <ShareIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="상세정보">
          <IconButton size="small">
            <InfoIcon />
          </IconButton>
        </Tooltip>
        
        <Box flex={1} />
        
        <Button 
          variant="contained" 
          size="small"
          startIcon={<LaunchIcon />}
          onClick={() => {
            // TODO: 상세 페이지로 이동
            console.log('상세 정보 보기:', apartment.id);
          }}
        >
          상세보기
        </Button>
      </CardActions>
    </Card>
  );
};

export default MapInfoPanel;