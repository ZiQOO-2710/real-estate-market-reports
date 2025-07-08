/**
 * ERR_CACHE_MISS 방지를 위한 안전한 네비게이션 스크립트
 */

// 페이지 로드 시 히스토리 상태 관리
window.addEventListener('DOMContentLoaded', function() {
    // 현재 URL을 GET 요청으로 히스토리에 기록
    if (window.location.pathname === '/results') {
        // results 페이지인 경우 히스토리 엔트리를 GET으로 교체
        window.history.replaceState(
            { page: 'results', method: 'GET' }, 
            '', 
            window.location.href
        );
        console.log('[NAVIGATION] Results 페이지 히스토리 상태 설정');
    }
});

// 안전한 뒤로 가기 함수
function safeGoBack() {
    console.log('[NAVIGATION] 안전한 뒤로 가기 시작');
    console.log('[NAVIGATION] 현재 URL:', window.location.href);
    console.log('[NAVIGATION] 히스토리 길이:', window.history.length);
    
    try {
        // 결과 페이지에서는 직접 분석 페이지로 이동
        if (window.location.pathname === '/results') {
            console.log('[NAVIGATION] 결과 페이지에서 분석 페이지로 직접 이동');
            window.location.href = '/analysis';
            return;
        }
        
        // 분석 페이지에서는 홈으로 이동
        if (window.location.pathname === '/analysis') {
            console.log('[NAVIGATION] 분석 페이지에서 홈으로 이동');
            window.location.href = '/';
            return;
        }
        
        // 기타 페이지에서는 조건부 뒤로 가기
        if (window.history.length > 2 && document.referrer) {
            console.log('[NAVIGATION] 일반 뒤로 가기');
            window.history.back();
        } else {
            console.log('[NAVIGATION] 홈으로 이동');
            window.location.href = '/';
        }
        
    } catch (error) {
        console.error('[NAVIGATION] 오류 발생:', error);
        window.location.href = '/';
    }
}

// 브라우저 뒤로/앞으로 버튼 이벤트 처리
window.addEventListener('popstate', function(event) {
    console.log('[NAVIGATION] Popstate 이벤트:', event.state);
    
    // POST 요청 관련 히스토리 엔트리 감지 시 안전한 페이지로 리다이렉트
    if (event.state && event.state.method === 'POST') {
        console.log('[NAVIGATION] POST 히스토리 감지, 안전한 페이지로 이동');
        window.location.href = '/analysis';
    }
});

// 폼 제출 시 히스토리 상태 추가
function markPostRequest() {
    window.history.replaceState(
        { page: 'form_submit', method: 'POST' }, 
        '', 
        window.location.href
    );
    console.log('[NAVIGATION] POST 요청 히스토리 마킹');
}