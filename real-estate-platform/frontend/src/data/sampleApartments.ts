// 샘플 아파트 데이터

import { ApartmentComplex } from '../types/apartment';

export const sampleApartments: ApartmentComplex[] = [
  {
    id: 'apt-001',
    name: '정든한진6차',
    address: {
      road: '경기도 성남시 분당구 정자일로 95',
      jibun: '경기도 성남시 분당구 정자동 135-1',
      dong: '정자동',
      gu: '분당구',
      city: '성남시'
    },
    coordinates: {
      lat: 37.36286,
      lng: 127.115578
    },
    details: {
      totalUnits: 298,
      constructionYear: 1995,
      floors: 14,
      parkingRatio: 100
    },
    marketData: {
      lastTransactionPrice: 145000, // 14억 5천만원 (만원 단위)
      lastTransactionDate: new Date('2024-12-01'),
      currentAskingPrice: 150000,
      pricePerPyeong: 3800
    }
  },
  {
    id: 'apt-002',
    name: '분당주공아파트',
    address: {
      road: '경기도 성남시 분당구 분당로 50',
      jibun: '경기도 성남시 분당구 서현동 256',
      dong: '서현동',
      gu: '분당구',
      city: '성남시'
    },
    coordinates: {
      lat: 37.3838,
      lng: 127.1230
    },
    details: {
      totalUnits: 456,
      constructionYear: 1989,
      floors: 12,
      parkingRatio: 80
    },
    marketData: {
      lastTransactionPrice: 89000,
      lastTransactionDate: new Date('2024-11-15'),
      currentAskingPrice: 92000,
      pricePerPyeong: 2900
    }
  },
  {
    id: 'apt-003',
    name: '삼성래미안',
    address: {
      road: '경기도 성남시 분당구 판교역로 235',
      jibun: '경기도 성남시 분당구 백현동 542',
      dong: '백현동',
      gu: '분당구',
      city: '성남시'
    },
    coordinates: {
      lat: 37.3940,
      lng: 127.1110
    },
    details: {
      totalUnits: 892,
      constructionYear: 2018,
      floors: 35,
      parkingRatio: 120
    },
    marketData: {
      lastTransactionPrice: 180000,
      lastTransactionDate: new Date('2024-12-10'),
      currentAskingPrice: 185000,
      pricePerPyeong: 4200
    }
  },
  {
    id: 'apt-004',
    name: '강남힐스테이트',
    address: {
      road: '서울특별시 강남구 테헤란로 152',
      jibun: '서울특별시 강남구 역삼동 735-2',
      dong: '역삼동',
      gu: '강남구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.5006,
      lng: 127.0366
    },
    details: {
      totalUnits: 650,
      constructionYear: 2020,
      floors: 42,
      parkingRatio: 150
    },
    marketData: {
      lastTransactionPrice: 320000,
      lastTransactionDate: new Date('2024-12-05'),
      currentAskingPrice: 330000,
      pricePerPyeong: 8500
    }
  },
  {
    id: 'apt-005',
    name: '서초자이',
    address: {
      road: '서울특별시 서초구 강남대로 200',
      jibun: '서울특별시 서초구 서초동 1303-7',
      dong: '서초동',
      gu: '서초구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.4911,
      lng: 127.0185
    },
    details: {
      totalUnits: 1200,
      constructionYear: 2019,
      floors: 49,
      parkingRatio: 140
    },
    marketData: {
      lastTransactionPrice: 280000,
      lastTransactionDate: new Date('2024-11-28'),
      currentAskingPrice: 285000,
      pricePerPyeong: 7200
    }
  },
  {
    id: 'apt-006',
    name: '송파파크리오',
    address: {
      road: '서울특별시 송파구 올림픽로 300',
      jibun: '서울특별시 송파구 잠실동 40-1',
      dong: '잠실동',
      gu: '송파구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.5133,
      lng: 127.1028
    },
    details: {
      totalUnits: 850,
      constructionYear: 2017,
      floors: 38,
      parkingRatio: 130
    },
    marketData: {
      lastTransactionPrice: 210000,
      lastTransactionDate: new Date('2024-12-12'),
      currentAskingPrice: 215000,
      pricePerPyeong: 5800
    }
  },
  {
    id: 'apt-007',
    name: '광진리버파크',
    address: {
      road: '서울특별시 광진구 아차산로 789',
      jibun: '서울특별시 광진구 구의동 546-3',
      dong: '구의동',
      gu: '광진구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.5436,
      lng: 127.0783
    },
    details: {
      totalUnits: 420,
      constructionYear: 2015,
      floors: 25,
      parkingRatio: 110
    },
    marketData: {
      lastTransactionPrice: 95000,
      lastTransactionDate: new Date('2024-11-20'),
      currentAskingPrice: 98000,
      pricePerPyeong: 3200
    }
  },
  {
    id: 'apt-008',
    name: '노원상계주공',
    address: {
      road: '서울특별시 노원구 상계로 456',
      jibun: '서울특별시 노원구 상계동 389-1',
      dong: '상계동',
      gu: '노원구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.6542,
      lng: 127.0657
    },
    details: {
      totalUnits: 380,
      constructionYear: 1992,
      floors: 15,
      parkingRatio: 90
    },
    marketData: {
      lastTransactionPrice: 45000,
      lastTransactionDate: new Date('2024-11-08'),
      currentAskingPrice: 47000,
      pricePerPyeong: 1800
    }
  },
  {
    id: 'apt-009',
    name: '마포래미안푸르지오',
    address: {
      road: '서울특별시 마포구 월드컵로 240',
      jibun: '서울특별시 마포구 상암동 1654',
      dong: '상암동',
      gu: '마포구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.5667,
      lng: 126.8986
    },
    details: {
      totalUnits: 750,
      constructionYear: 2016,
      floors: 32,
      parkingRatio: 125
    },
    marketData: {
      lastTransactionPrice: 160000,
      lastTransactionDate: new Date('2024-12-03'),
      currentAskingPrice: 165000,
      pricePerPyeong: 4500
    }
  },
  {
    id: 'apt-010',
    name: '용산아이파크',
    address: {
      road: '서울특별시 용산구 한강대로 405',
      jibun: '서울특별시 용산구 한강로동 726-47',
      dong: '한강로동',
      gu: '용산구',
      city: '서울특별시'
    },
    coordinates: {
      lat: 37.5219,
      lng: 126.9707
    },
    details: {
      totalUnits: 990,
      constructionYear: 2021,
      floors: 55,
      parkingRatio: 160
    },
    marketData: {
      lastTransactionPrice: 450000,
      lastTransactionDate: new Date('2024-12-08'),
      currentAskingPrice: 460000,
      pricePerPyeong: 11000
    }
  }
];

// 크롤링 데이터에서 가져온 실제 데이터 (정든한진6차)
export const realCrawledData: ApartmentComplex = {
  id: 'apt-crawled-001',
  name: '정든한진6차',
  address: {
    road: '경기도 성남시 분당구 정자일로 95', 
    jibun: '경기도 성남시 분당구 정자동 135-1',
    dong: '정자동',
    gu: '분당구',
    city: '성남시'
  },
  coordinates: {
    lat: 37.36286,
    lng: 127.115578
  },
  details: {
    totalUnits: 298,
    constructionYear: 1995,
    floors: 14,
    parkingRatio: 100
  },
  marketData: {
    lastTransactionPrice: 140833, // 크롤링된 평균가격 (14.1억원)
    lastTransactionDate: new Date('2024-12-14'),
    currentAskingPrice: 145000,
    pricePerPyeong: 3800
  }
};