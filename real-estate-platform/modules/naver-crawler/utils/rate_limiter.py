"""
요청 제한 및 차단 방지 모듈
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class RateLimiter:
    """요청 제한 및 차단 방지 클래스"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.stats_file = Path("logs/request_stats.json")
        self.stats_file.parent.mkdir(exist_ok=True)
        self.session_requests = 0
        self.total_requests = 0
        self.session_start_time = time.time()
        self.last_request_time = 0
        self.daily_stats = self.load_daily_stats()
        
    def load_daily_stats(self) -> Dict:
        """일일 통계 로드"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    
                # 오늘 날짜 확인
                today = datetime.now().strftime('%Y-%m-%d')
                if stats.get('date') == today:
                    return stats
                    
            # 새로운 날짜 또는 파일 없음
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'daily_requests': 0,
                'hourly_requests': {},
                'last_request_time': 0,
                'blocked_ips': [],
                'warning_count': 0
            }
            
        except Exception as e:
            logger.error(f"통계 파일 로드 실패: {e}")
            return self.load_daily_stats()  # 기본값 반환
    
    def save_daily_stats(self):
        """일일 통계 저장"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"통계 파일 저장 실패: {e}")
    
    def can_make_request(self) -> tuple[bool, str]:
        """요청 가능 여부 확인"""
        now = time.time()
        current_hour = datetime.now().strftime('%Y-%m-%d %H')
        
        # 일일 제한 확인
        if self.daily_stats['daily_requests'] >= self.config.get('daily_request_limit', 500):
            return False, "일일 요청 제한 초과"
        
        # 시간당 제한 확인
        hourly_count = self.daily_stats['hourly_requests'].get(current_hour, 0)
        if hourly_count >= self.config.get('hourly_request_limit', 50):
            return False, "시간당 요청 제한 초과"
        
        # 세션 제한 확인
        if self.session_requests >= self.config.get('max_requests_per_session', 30):
            return False, "세션 요청 제한 초과"
        
        # 요청 간 딜레이 확인
        min_delay = self.config.get('delay_between_requests', 5)
        if now - self.last_request_time < min_delay:
            return False, f"요청 간격 부족 ({min_delay}초 대기)"
        
        return True, "요청 가능"
    
    async def wait_if_needed(self):
        """필요시 대기"""
        can_request, reason = self.can_make_request()
        
        if not can_request:
            if "제한 초과" in reason:
                if "일일" in reason:
                    wait_time = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) - datetime.now()
                    wait_seconds = wait_time.total_seconds()
                    logger.warning(f"일일 제한 초과. {wait_seconds/3600:.1f}시간 후 재시작 가능")
                    return False
                elif "시간당" in reason:
                    wait_time = 3600 - (time.time() % 3600)
                    logger.warning(f"시간당 제한 초과. {wait_time/60:.1f}분 대기")
                    await self.sleep(wait_time)
                elif "세션" in reason:
                    wait_time = self.config.get('session_break_duration', 30)
                    logger.info(f"세션 휴식: {wait_time}초 대기")
                    await self.sleep(wait_time)
                    self.reset_session()
            elif "요청 간격" in reason:
                wait_time = self.config.get('delay_between_requests', 5) - (time.time() - self.last_request_time)
                if wait_time > 0:
                    await self.sleep(wait_time)
        
        return True
    
    async def sleep(self, seconds: float):
        """비동기 대기"""
        import asyncio
        import random
        
        # 랜덤 딜레이 추가 (봇 탐지 방지)
        random_delay = random.uniform(0.5, 1.5)
        total_delay = seconds + random_delay
        
        logger.info(f"대기 중: {total_delay:.1f}초")
        await asyncio.sleep(total_delay)
    
    def record_request(self):
        """요청 기록"""
        now = time.time()
        current_hour = datetime.now().strftime('%Y-%m-%d %H')
        
        # 통계 업데이트
        self.session_requests += 1
        self.total_requests += 1
        self.last_request_time = now
        
        # 일일/시간당 통계 업데이트
        self.daily_stats['daily_requests'] += 1
        self.daily_stats['hourly_requests'][current_hour] = self.daily_stats['hourly_requests'].get(current_hour, 0) + 1
        self.daily_stats['last_request_time'] = now
        
        # 긴 휴식 필요 확인
        if self.total_requests % self.config.get('long_break_interval', 100) == 0:
            logger.info(f"긴 휴식 필요: {self.config.get('long_break_duration', 300)}초")
            return True  # 긴 휴식 필요
        
        # 세션 휴식 필요 확인
        if self.session_requests % self.config.get('session_break_interval', 10) == 0:
            logger.info(f"세션 휴식 필요: {self.config.get('session_break_duration', 30)}초")
            return "session_break"
        
        # 통계 저장
        self.save_daily_stats()
        return False
    
    def reset_session(self):
        """세션 초기화"""
        self.session_requests = 0
        self.session_start_time = time.time()
        logger.info("세션 초기화 완료")
    
    def get_stats(self) -> Dict:
        """현재 통계 반환"""
        session_duration = time.time() - self.session_start_time
        return {
            'session_requests': self.session_requests,
            'total_requests': self.total_requests,
            'daily_requests': self.daily_stats['daily_requests'],
            'session_duration': session_duration,
            'requests_per_minute': self.session_requests / (session_duration / 60) if session_duration > 0 else 0,
            'daily_limit_remaining': self.config.get('daily_request_limit', 500) - self.daily_stats['daily_requests'],
            'current_hour_requests': self.daily_stats['hourly_requests'].get(datetime.now().strftime('%Y-%m-%d %H'), 0)
        }