// 문서 로드 완료 시 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('부동산 거래 데이터 분석 시스템이 로드되었습니다.');
    
    // 파일 업로드 관련 이벤트 처리
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                console.log(`파일이 선택되었습니다: ${fileName}`);
            }
        });
    }
    
    // 숫자 셀 스타일 적용
    applyNumberCellStyles();

    const uploadBtn = document.querySelector('form[action="/upload"] button[type="submit"]');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            const loadingDiv = document.getElementById('loading');
            if (loadingDiv) loadingDiv.style.display = 'block';
            // 타이머 시작
            let elapsed = 0;
            const elapsedSpan = document.getElementById('elapsed');
            if (elapsedSpan) elapsedSpan.textContent = elapsed;
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(function() {
                elapsed += 1;
                if (elapsedSpan) elapsedSpan.textContent = elapsed;
            }, 1000);
        });
    }

});

// 숫자 데이터 셀에 클래스 적용
function applyNumberCellStyles() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                const cellText = cell.textContent.trim();
                // 숫자만 포함된 셀 (쉼표 허용)
                if (/^[\d,]+$/.test(cellText)) {
                    cell.classList.add('number-cell');
                }
            });
        });
    });
}

// 특정 행 강조 효과
function highlightRow(rowIndex) {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        
        // 기존 하이라이트 제거
        rows.forEach(row => row.classList.remove('highlight'));
        
        // 선택한 행에 하이라이트 적용
        if (rows[rowIndex]) {
            rows[rowIndex].classList.add('highlight');
            
            // 5초 후 하이라이트 제거
            setTimeout(() => {
                rows[rowIndex].classList.remove('highlight');
            }, 5000);
        }
    });
}

// CSV 파일 내용 검증
function validateCsvFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const contents = e.target.result;
            const lines = contents.split('\n');
            
            if (lines.length < 2) {
                reject('파일에 데이터가 충분하지 않습니다.');
                return;
            }
            
            const headers = lines[0].split(',');
            if (headers.length < 10) {
                reject('CSV 파일의 컬럼 수가 충분하지 않습니다.');
                return;
            }
            
            resolve(true);
        };
        
        reader.onerror = function() {
            reject('파일을 읽는 동안 오류가 발생했습니다.');
        };
        
        reader.readAsText(file);
    });
} 