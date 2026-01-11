# Palantir Stock

웹 검색 + Palantir Foundry 기반 기업 정보 수집 및 분석 에이전트 시스템.

## Features

- **실시간 웹 검색**: SerpAPI / Tavily를 통한 기업 뉴스 및 정보 수집
- **Palantir 통합**: Foundry SDK를 통한 온톨로지 및 데이터셋 접근
- **LangGraph 워크플로우**: 검색 → 뉴스 → Palantir → 요약 파이프라인
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

### 설정 확인

```bash
ps config
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        CLI (Typer)                           │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                 Agent Layer (LangGraph)                      │
│  search_node → news_node → palantir_node → summarize_node   │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                      Data Sources                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ SerpAPI     │  │ Tavily      │  │ Palantir Foundry    │  │
│  │ (Google)    │  │ (AI Search) │  │ (Ontology/Datasets) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
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
│   ├── graph/               # Graph RAG (Phase 2)
│   └── stock/               # 주식 데이터 (Phase 3)
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
- [ ] **Phase 2**: Graph RAG 통합 (Neo4j 지식 그래프)
- [ ] **Phase 3**: 주식 데이터 연동 (yfinance, Alpha Vantage)
- [ ] **Phase 4**: 웹 대시보드 + 고급 기능

## Tech Stack

| 카테고리 | 기술 |
|---------|------|
| Language | Python 3.11+ |
| Agent Framework | LangGraph, LangChain |
| LLM | OpenAI GPT-4o |
| Search | SerpAPI, Tavily |
| Enterprise Data | Palantir Foundry SDK |
| Graph DB | Neo4j (Phase 2) |
| Vector DB | ChromaDB (Phase 2) |
| CLI | Typer, Rich |

## License

MIT
