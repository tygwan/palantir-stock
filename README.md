# Palantir Stock

웹 검색 + Palantir Foundry 기반 기업 정보 수집 및 분석 에이전트 시스템.

## Features

- **실시간 웹 검색**: SerpAPI / Tavily를 통한 기업 뉴스 및 정보 수집
- **Palantir 통합**: Foundry SDK를 통한 온톨로지 및 데이터셋 접근
- **LangGraph 워크플로우**: 검색 → 뉴스 → Palantir → 요약 파이프라인
- **Graph RAG**: Neo4j + ChromaDB 기반 하이브리드 검색
- **주식 분석**: yfinance + 기술적 지표 (RSI, MACD, 볼린저 밴드)
- **REST API**: FastAPI 기반 API 서버
- **웹 대시보드**: 실시간 기업 분석 대시보드
- **리포트 생성**: HTML/Markdown/JSON 형식 자동 리포트
- **CLI 인터페이스**: Rich 기반 터미널 UI

## Installation

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -e ".[dev]"
```

## Configuration

`.env.example`을 `.env`로 복사하고 API 키를 설정합니다:

```bash
cp .env.example .env
```

```env
# 필수
OPENAI_API_KEY=sk-xxx

# 검색 API (하나 이상 필요)
SERPAPI_KEY=xxx
TAVILY_API_KEY=tvly-xxx

# Palantir (선택)
FOUNDRY_TOKEN=xxx
FOUNDRY_HOST=your.palantirfoundry.com
```

## Usage

### 기업 분석

```bash
# 기본 분석
ps 삼성전자

# JSON 출력
ps 삼성전자 --output json

# 상세 로그
ps 삼성전자 --verbose
```

### 뉴스 검색

```bash
ps news 삼성전자
ps news "삼성전자 실적" --limit 10
```

### Palantir 연동

```bash
# 온톨로지 객체 타입 조회
ps ontology

# 데이터셋 목록 조회
ps datasets
```

### 주식 분석

```bash
# 주식 종합 분석 (RSI, MACD, 볼린저 밴드)
ps stock 삼성전자
ps stock AAPL --period 6mo

# 주가 히스토리
ps stock-price 삼성전자

# Graph RAG 검색
ps graph-search "반도체 실적"
ps graph-stats
```

### API 서버 & 대시보드

```bash
# API 서버 시작
ps serve

# 커스텀 포트
ps serve --port 3000

# 개발 모드 (자동 리로드)
ps serve --reload
```

서버 시작 후:
- 대시보드: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 리포트 생성

```bash
# HTML 리포트
ps report 삼성전자 --output html --save report.html

# Markdown 리포트
ps report AAPL --output markdown --save report.md

# JSON 리포트
ps report 삼성전자 --output json
```

### 설정 확인

```bash
ps config
```

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                   User Interface Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │ CLI (Typer)  │  │ Web Dashboard│  │ REST API (FastAPI)    │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘    │
└─────────┼─────────────────┼──────────────────────┼────────────────┘
          │                 │                      │
          └─────────────────┴──────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                    Agent Layer (LangGraph)                         │
│  search → news → palantir → stock → graph_rag → summarize          │
└───────────────────────────┬───────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                      Storage Layer                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │ Neo4j      │  │ ChromaDB   │  │ Reports    │                   │
│  │ (Graph DB) │  │ (VectorDB) │  │ (HTML/MD)  │                   │
│  └────────────┘  └────────────┘  └────────────┘                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                    External Data Sources                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐              │
│  │ SerpAPI │ │ Tavily  │ │ Palantir    │ │yfinance │              │
│  │         │ │         │ │ Foundry     │ │         │              │
│  └─────────┘ └─────────┘ └─────────────┘ └─────────┘              │
└───────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
palantir-stock/
├── src/
│   ├── main.py              # CLI 엔트리포인트
│   ├── models/              # Pydantic 데이터 모델
│   ├── utils/               # LLM, 로깅 유틸리티
│   ├── search/              # 검색 프로바이더 (SerpAPI, Tavily)
│   ├── palantir/            # Palantir Foundry 연동
│   ├── agents/              # LangGraph 에이전트
│   ├── graph/               # Graph RAG (Neo4j + ChromaDB)
│   ├── stock/               # 주식 데이터 (yfinance + 지표)
│   ├── api/                 # FastAPI REST API
│   │   ├── main.py          # FastAPI 앱 + 대시보드
│   │   ├── routes/          # API 라우트
│   │   └── schemas.py       # API 스키마
│   └── reports/             # 리포트 생성
│       ├── generator.py     # 리포트 생성기
│       └── templates.py     # HTML/Markdown 템플릿
├── config/
│   └── settings.py          # pydantic-settings 설정
├── tests/                   # pytest 테스트
├── docs/
│   ├── PRD.md              # 제품 요구사항
│   └── PALANTIR_ACCESS_GUIDE.md
└── docker-compose.yml       # Neo4j, Redis
```

## Development

```bash
# 린트
ruff check src/

# 타입 체크
mypy src/

# 테스트
pytest tests/ -v

# 커버리지
pytest --cov=src tests/
```

## Roadmap

- [x] **Phase 1**: MVP - 웹 검색 에이전트 + Palantir 연동 + CLI
- [x] **Phase 2**: Graph RAG 통합 (Neo4j 지식 그래프 + ChromaDB)
- [x] **Phase 3**: 주식 데이터 연동 (yfinance + 기술적 지표)
- [x] **Phase 4**: 웹 대시보드 + API 서버 + 리포트 생성

## Tech Stack

| 카테고리 | 기술 |
|---------|------|
| Language | Python 3.11+ |
| Agent Framework | LangGraph, LangChain |
| LLM | OpenAI GPT-4o |
| Search | SerpAPI, Tavily |
| Enterprise Data | Palantir Foundry SDK |
| Graph DB | Neo4j |
| Vector DB | ChromaDB |
| Web Framework | FastAPI, Uvicorn |
| CLI | Typer, Rich |

## License

MIT
