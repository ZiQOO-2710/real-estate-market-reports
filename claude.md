# Claude 작업 기록

## 사용자 설정
- 사용자명: 지쿠
- 언어: 한글 응답 요청
- 작업 기록을 claude.md에 저장하여 내용 기억

## 작업 내용
- 초기 설정 완료 (2025-07-09)
- 프로젝트 구조 분석 및 정리 완료 (2025-07-09)

### 프로젝트 분석 결과
- **프로젝트 유형**: 아파트 실거래가 데이터 지도 시각화 웹 애플리케이션
- **기술 스택**: Python Flask, Supabase, Kakao Maps API, Pandas
- **주요 기능**: CSV 업로드, 데이터 분석, 지도 시각화

### 정리 작업 내용
- **백업 폴더 생성**: backup_20250709_115341/
- **이동한 파일들**:
  - __pycache__/ (Python 컴파일 파일)
  - debug_app.py, simple_debug.py, simple_web_debug.py (디버그 파일)
  - analyze_templates.py (분석용 임시 파일)
  - venv/ (가상환경)
  - GEMINI.md (임시 문서)
  - cleanup/ (기존 백업 폴더)
- **업로드 폴더 정리**: 중복 CSV 파일을 uploads/backup/ 폴더로 이동

### 현재 정리된 프로젝트 구조
```
/home/ksj27/projects/
├── app.py                 # 메인 애플리케이션
├── config.py              # 설정 파일
├── data_processing.py     # 데이터 처리 모듈
├── map_utils.py           # 지도 유틸리티
├── requirements.txt       # 의존성 목록
├── README.md             # 프로젝트 설명서
├── Analysis_Report.md    # 분석 보고서
├── DB_README.md          # 데이터베이스 설명서
├── claude.md             # 작업 기록
├── static/               # 정적 파일
├── templates/            # HTML 템플릿
├── uploads/              # 업로드 파일
└── backup_20250709_115341/ # 백업 폴더
```