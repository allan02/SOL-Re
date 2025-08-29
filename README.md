# 🏦 신한은행 스테이블코인 인텔리전스

신한은행 직원들을 위한 스테이블코인 정보 분석 및 상담 지원 시스템입니다.

## 📋 프로젝트 개요

이 프로젝트는 신한은행 직원들이 스테이블코인 관련 정보를 쉽게 조회하고 분석할 수 있도록 도와주는 AI 기반 웹 애플리케이션입니다.

### 🎯 주요 기능

#### 영업점 직원 서비스
- **📚 스테이블코인 용어 백과사전**: RAG 기반 용어 검색 및 설명
- **📰 뉴스 & QA**: 최신 스테이블코인 뉴스 조회 및 질의응답

#### 본부부서 직원 서비스
- **🌍 규제 분석**: 국가별 스테이블코인 규제 동향 분석
- **🏛️ 비즈니스 분석**: 메이저 금융사 현황 및 리스크 분석

## 🚀 시작하기

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd shinhan-stable-coin-intelligence

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 API 키들을 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. 애플리케이션 실행

```bash
streamlit run main.py
```

브라우저에서 `http://localhost:8501`로 접속하여 애플리케이션을 사용할 수 있습니다.

## 🏗️ 프로젝트 구조

```
shinhan-stable-coin-intelligence/
├── main.py                          # 메인 Streamlit 앱
├── requirements.txt                 # Python 의존성
├── README.md                       # 프로젝트 문서
├── pages/                          # 페이지 모듈
│   ├── __init__.py
│   ├── branch_employee.py          # 영업점 직원 페이지
│   └── headquarters_employee.py    # 본부부서 직원 페이지
└── utils/                          # 유틸리티 모듈
    ├── __init__.py
    ├── dictionary.py               # 용어 백과사전 RAG
    ├── simple_news_analysis.py     # 뉴스 분석
    ├── regulation_analysis.py      # 규제 분석
    └── business_case_analysis.py   # 비즈니스 분석
```

## 🔧 기술 스택

- **Frontend**: Streamlit
- **AI/ML**: LangChain, LangGraph
- **LLM**: OpenAI GPT-3.5-turbo
- **Vector Database**: FAISS
- **Search**: Tavily Search API
- **Language**: Python 3.8+

## 📚 사용법

### 영업점 직원

1. 사이드바에서 "🏪 영업점 직원" 선택
2. **용어 백과사전** 탭에서 스테이블코인 관련 용어 검색
3. **뉴스 & QA** 탭에서 최신 뉴스 기반 질의응답

### 본부부서 직원

1. 사이드바에서 "🏢 본부부서 직원" 선택
2. **규제 분석** 탭에서 국가별 규제 동향 분석
3. **비즈니스 분석** 탭에서 경쟁사 현황 및 리스크 분석

## 🤝 협업 가이드

### Git 워크플로우

1. **브랜치 생성**: `git checkout -b feature/your-feature-name`
2. **변경사항 커밋**: `git commit -m "feat: add new feature"`
3. **푸시**: `git push origin feature/your-feature-name`
4. **Pull Request 생성**: GitHub에서 PR 생성

### 코드 컨벤션

- **함수명**: snake_case 사용
- **클래스명**: PascalCase 사용
- **상수**: UPPER_SNAKE_CASE 사용
- **주석**: 한국어로 작성

### 커밋 메시지 형식

```
type: description

feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드 프로세스 또는 보조 도구 변경
```

## 🔒 보안

- API 키는 `.env` 파일에 저장하고 절대 Git에 커밋하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있습니다
- 프로덕션 환경에서는 환경 변수를 안전하게 관리하세요

## 📝 라이선스

이 프로젝트는 신한은행 내부 사용을 위한 프로젝트입니다.

## 🆘 문제 해결

### 일반적인 문제

1. **API 키 오류**: `.env` 파일이 올바르게 설정되었는지 확인
2. **의존성 오류**: `pip install -r requirements.txt` 재실행
3. **포트 충돌**: 다른 Streamlit 앱이 실행 중인지 확인

### 지원

문제가 발생하면 이슈를 생성하거나 개발팀에 문의하세요.
