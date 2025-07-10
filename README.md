# 아파트 실거래가 데이터 지도 시각화 (Python & Flask)

## 1. 프로젝트 개요

본 프로젝트는 사용자가 업로드한 부동산 실거래가 데이터(CSV)를 분석하고, 카카오맵 API를 통해 지도 위에 시각화하는 Python Flask 기반 웹 애플리케이션입니다. 업로드된 데이터는 Supabase DB에 저장된 아파트 정보와 매칭하여 위도/경도 좌표를 부여받고, 사용자가 입력한 기준 주소와 반경을 기준으로 필터링되어 지도에 표시됩니다.

## 2. 기술 스택

- **백엔드**: Python, Flask
- **데이터 처리**: Pandas, NumPy
- **프론트엔드**: HTML, CSS, JavaScript (Jinja2 템플릿 엔진 사용)
- **데이터베이스**: Supabase (좌표 매칭용)
- **지도 API**: Kakao Maps API (주소 검색 및 지도 시각화)
- **지오코딩**: Geopy

## 3. 주요 기능 및 흐름

1.  **데이터 업로드**: 사용자가 메인 페이지에서 실거래가 정보가 담긴 CSV 파일을 업로드합니다.
2.  **데이터 처리 및 좌표 매칭**:
    - 시스템은 업로드된 CSV 파일을 Pandas DataFrame으로 변환합니다.
    - 데이터 클리닝 및 정규화 과정을 거쳐 '전용평', '평당가' 등 분석에 필요한 파생 변수를 생성합니다.
    - 데이터의 주소 정보를 Supabase DB와 대조하여 일치하는 아파트의 위도/경도 좌표를 찾아 DataFrame에 추가합니다.
3.  **기준 주소 입력 및 필터링**:
    - 사용자는 지도 중심점으로 사용할 주소와 반경(km)을 입력합니다.
    - 시스템은 입력된 주소를 카카오맵 API를 통해 좌표로 변환합니다.
    - 변환된 중심 좌표와 반경을 기준으로 범위 내에 있는 실거래 데이터만 필터링합니다.
4.  **지도 시각화**:
    - 필터링된 실거래 데이터가 지도 위에 마커로 표시됩니다.
    - 마커 클릭 시 거래 가격, 단지명 등 상세 정보를 확인할 수 있습니다.
    - 데이터는 테이블 형태로도 제공되며, 다양한 기준으로 정렬할 수 있습니다.

## 4. 프로젝트 구조

```
.
├── app.py                   # Flask 메인 애플리케이션 파일
├── requirements.txt         # Python 의존성 목록
├── .env                     # 환경 변수 설정 파일
├── static/                  # CSS, JavaScript 등 정적 파일
│   ├── css/style.css
│   └── js/main.js
├── templates/               # HTML 템플릿 파일
│   ├── index.html           # 메인 페이지 (파일 업로드)
│   ├── analysis.html        # 업로드 데이터 분석 결과
│   ├── map.html             # 지도 시각화 페이지
│   └── select_file.html     # 기존 파일 선택 페이지
└── uploads/                 # 사용자가 업로드한 파일 저장
```

## 5. 실행 방법

1.  **프로젝트 클론 및 가상 환경 설정**
    ```bash
    git clone <repository_url>
    cd <project_directory>
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2.  **의존성 설치**
    ```bash
    pip install -r requirements.txt
    ```

3.  **.env 파일 생성 및 환경 변수 설정**
    `.env.example` 파일을 참고하여 `.env` 파일을 생성하고 아래 변수를 실제 값으로 채웁니다.
    ```
    # Supabase
    SUPABASE_URL="YOUR_SUPABASE_URL"
    SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"

    # Kakao Maps API (REST API Key)
    KAKAO_REST_API_KEY="YOUR_KAKAO_REST_API_KEY"

    # Flask Secret Key
    FLASK_SECRET_KEY="any_random_strong_secret_key"
    ```

4.  **개발 서버 실행**
    ```bash
    flask run
    # 또는 python app.py
    ```
    서버가 실행되면 웹 브라우저에서 `http://127.0.0.1:5000` (또는 `app.py`에 설정된 포트)으로 접속합니다.

## 6. 의존성 파일 생성

프로젝트에 필요한 라이브러리 목록을 `requirements.txt` 파일로 관리합니다.

```bash
pip freeze > requirements.txt
```


# 업로드 분석시 조건
# - 업로드한 CSV파일안에 '거래유형' 컬럼에서 직거래 삭제
# - '해제사유발생일' 컬럼에 날짜값이 있으면 삭제
# 위 두 조건만 추가해줘. 