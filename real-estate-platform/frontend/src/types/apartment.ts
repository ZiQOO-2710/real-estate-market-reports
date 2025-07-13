// 아파트 관련 타입 정의

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Address {
  road: string;
  jibun: string;
  dong: string;
  gu: string;
  city: string;
  postalCode?: string;
}

export interface ApartmentDetails {
  totalUnits: number;
  constructionYear: number;
  floors: number;
  parkingRatio: number;
  buildingCount?: number;
  complexArea?: number;
}

export interface MarketData {
  lastTransactionPrice?: number;
  lastTransactionDate?: Date;
  currentAskingPrice?: number;
  pricePerPyeong?: number;
  pricePerSqm?: number;
  rentPrice?: number;
  depositPrice?: number;
}

export interface PriceHistory {
  date: Date;
  price: number;
  priceType: 'transaction' | 'asking' | 'rent';
  area?: number;
  floor?: number;
}

export interface ApartmentComplex {
  id: string;
  name: string;
  address: Address;
  coordinates: Coordinates;
  details: ApartmentDetails;
  marketData: MarketData;
  priceHistory?: PriceHistory[];
  images?: string[];
  amenities?: string[];
  transportation?: TransportationInfo[];
  lastUpdated: Date;
}

export interface TransportationInfo {
  type: 'subway' | 'bus' | 'station';
  name: string;
  distance: number; // meters
  walkTime: number; // minutes
}

export interface ApartmentUnit {
  id: string;
  complexId: string;
  area: number; // 전용면적 (㎡)
  floor: number;
  direction: string; // 향
  roomCount: number;
  bathCount: number;
  price?: number;
  rentPrice?: number;
  depositPrice?: number;
  transactionDate?: Date;
  transactionType: 'sale' | 'rent' | 'lease';
}

// 지도 마커용 간소화된 아파트 정보
export interface ApartmentMarker {
  id: string;
  name: string;
  coordinates: Coordinates;
  price?: number;
  pricePerPyeong?: number;
  status: 'sale' | 'rent' | 'lease' | 'sold';
}

// 아파트 목록 조회 응답
export interface ApartmentListResponse {
  apartments: ApartmentComplex[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// 아파트 검색 필터
export interface ApartmentFilter {
  priceMin?: number;
  priceMax?: number;
  areaMin?: number;
  areaMax?: number;
  constructionYearMin?: number;
  constructionYearMax?: number;
  transactionType?: 'sale' | 'rent' | 'lease' | 'all';
  sortBy?: 'price' | 'area' | 'date' | 'name';
  sortOrder?: 'asc' | 'desc';
}