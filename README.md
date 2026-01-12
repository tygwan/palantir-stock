# Palantir Stock

> AI-powered enterprise intelligence agent for company analysis, stock data, and knowledge graph integration.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-green.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

웹 검색, Palantir Foundry, 주식 데이터를 통합하여 기업 정보를 실시간으로 수집하고 분석하는 AI 에이전트 시스템입니다.

## Highlights

- **Multi-Source Data Collection**: 웹 검색 + Palantir + 주식 데이터 통합
- **LangGraph Workflow**: 6단계 자동화된 분석 파이프라인
- **Graph RAG**: Neo4j + ChromaDB 하이브리드 검색
- **Technical Analysis**: RSI, MACD, 볼린저 밴드 등 기술적 지표
- **REST API + Dashboard**: FastAPI 기반 웹 서비스

## Quick Start

```bash
# 1. 설치
git clone https://github.com/tygwan/palantir-stock.git
cd palantir-stock
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. 환경 설정
cp .env.example .env
# .env 파일에 API 키 설정

# 3. 실행
ps 삼성전자              # CLI 분석
ps serve                # 웹 서버 시작
```

## Features

| 기능 | 설명 |
|------|------|
| **기업 분석** | 웹 검색 + LLM 기반 종합 분석 |
| **뉴스 수집** | 실시간 뉴스 검색 및 요약 |
| **주식 분석** | 시세 조회 + 기술적 지표 계산 |
| **Graph RAG** | 지식 그래프 기반 관계 분석 |
| **Palantir** | Foundry 온톨로지/데이터셋 연동 |
| **리포트** | HTML/Markdown/JSON 자동 생성 |
| **API** | RESTful API + Swagger 문서 |
| **대시보드** | 웹 기반 분석 인터페이스 |

## Installation

### Requirements

- Python 3.11+
- Docker (Neo4j, Redis 용)

### Setup

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -e ".[dev]"

# 인프라 시작 (선택)
docker-compose up -d
```

## Configuration

`.env` 파일을 생성하고 다음 API 키를 설정합니다:

```env
# 필수
OPENAI_API_KEY=sk-xxx

# 검색 API (하나 이상 필요)
SERPAPI_KEY=xxx
TAVILY_API_KEY=tvly-xxx

# Palantir (선택)
FOUNDRY_TOKEN=xxx
FOUNDRY_HOST=your.palantirfoundry.com

# Graph DB (선택)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

## Usage

### CLI Commands

```bash
# 기업 종합 분석
ps 삼성전자
ps 삼성전자 --output json --verbose

# 뉴스 검색
ps news 삼성전자 --limit 10

# 주식 분석
ps stock 삼성전자
ps stock AAPL --period 6mo
ps stock-price 005930.KS

# Graph RAG
ps graph-init           # 스키마 초기화
ps graph-search 반도체   # 하이브리드 검색
ps graph-stats          # 저장소 상태

# Palantir
ps ontology             # 온톨로지 조회
ps datasets             # 데이터셋 목록

# 리포트 생성
ps report 삼성전자 --output html --save report.html
ps report AAPL --output markdown

# API 서버
ps serve                # http://localhost:8000
ps serve --port 3000 --reload

# 설정 확인
ps config
```

### API Endpoints

서버 시작 후 http://localhost:8000/docs 에서 전체 API 문서 확인 가능

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/analyze` | 기업 종합 분석 |
| `POST` | `/api/news` | 뉴스 검색 |
| `GET` | `/api/stock/{ticker}` | 주식 분석 |
| `GET` | `/api/stock/{ticker}/prices` | 주가 히스토리 |
| `POST` | `/api/graph/search` | 하이브리드 검색 |
| `POST` | `/api/reports/generate` | 리포트 생성 |

### Python SDK

```python
import asyncio
from src.agents import CompanyInfoAgent
from config.settings import settings

async def main():
    agent = CompanyInfoAgent(settings)
    report = await agent.analyze("삼성전자")
    print(report.summary)

asyncio.run(main())
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│   CLI (Typer)  │  Web Dashboard  │  REST API (FastAPI)      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Agent Layer (LangGraph)                      │
│                                                              │
│  ┌─────────┐  ┌──────┐  ┌──────────┐  ┌───────┐  ┌───────┐ │
│  │ Search  │→ │ News │→ │ Palantir │→ │ Stock │→ │ Graph │ │
│  └─────────┘  └──────┘  └──────────┘  └───────┘  └───────┘ │
│                              ↓                               │
│                      ┌────────────┐                          │
│                      │ Summarize  │                          │
│                      └────────────┘                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Data Sources                              │
│  SerpAPI │ Tavily │ Palantir Foundry │ yfinance │ Neo4j    │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
palantir-stock/
├── src/
│   ├── main.py              # CLI 엔트리포인트
│   ├── agents/              # LangGraph 에이전트
│   │   ├── nodes.py         # 워크플로우 노드
│   │   └── orchestrator.py  # 오케스트레이터
│   ├── search/              # 웹 검색 (SerpAPI, Tavily)
│   ├── palantir/            # Palantir Foundry 연동
│   ├── stock/               # 주식 데이터 + 기술적 지표
│   ├── graph/               # Graph RAG (Neo4j + ChromaDB)
│   ├── api/                 # FastAPI REST API
│   └── reports/             # 리포트 생성기
├── config/
│   └── settings.py          # 설정 관리
├── tests/                   # 테스트
├── docs/                    # 문서
└── docker-compose.yml       # 인프라
```

## Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.11+ |
| **Agent** | LangGraph, LangChain |
| **LLM** | OpenAI GPT-4o |
| **Search** | SerpAPI, Tavily |
| **Enterprise** | Palantir Foundry SDK |
| **Graph DB** | Neo4j |
| **Vector DB** | ChromaDB |
| **Web** | FastAPI, Uvicorn |
| **CLI** | Typer, Rich |

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

- [x] **Phase 1**: MVP - 웹 검색 에이전트 + Palantir 연동
- [x] **Phase 2**: Graph RAG (Neo4j + ChromaDB)
- [x] **Phase 3**: 주식 데이터 + 기술적 지표
- [x] **Phase 4**: API 서버 + 대시보드 + 리포트
- [ ] **Phase 5**: 알림 시스템 + 스케줄링
- [ ] **Phase 6**: 멀티 에이전트 협업

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with LangGraph + Palantir Foundry + FastAPI**
