# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Palantir Stock - 웹 검색 기반 기업 정보 수집 및 주식 데이터 분석 에이전트 시스템.

**Core Features:**
- 실시간 웹 검색을 통한 기업 현황 데이터 수집
- Graph RAG 기반 지식 그래프 구축 및 질의
- 주식 정보 처리 및 분석 파이프라인
- Palantir AIP 통합 (선택적)

## Commands

```bash
# 의존성 설치
pip install -e ".[dev]"

# Palantir MCP 포함 설치
pip install -e ".[dev,palantir]"

# 린트 및 타입 체크
ruff check src/
mypy src/

# 테스트
pytest tests/
pytest tests/test_search.py::test_company_search -v  # 단일 테스트
pytest --cov=src tests/                               # 커버리지 포함

# 에이전트 실행
ps --company "삼성전자"
python -m src.main --company "삼성전자"

# 인프라 시작
docker-compose up -d              # neo4j + redis 전체
docker-compose up -d neo4j        # neo4j만
```

## Architecture

```
src/
├── agents/      # LangGraph 에이전트 (검색, 분석, 수집)
├── graph/       # Graph RAG 및 Neo4j 지식 그래프
├── search/      # 웹 검색 인터페이스 (SerpAPI, Tavily)
├── stock/       # 주식 데이터 처리 (yfinance, Alpha Vantage)
└── palantir/    # Palantir AIP 통합 모듈
config/          # pydantic-settings 기반 설정 (Settings 클래스)
```

**Tech Stack:** Python 3.11+, LangGraph/LangChain, Neo4j, ChromaDB, Redis, yfinance

**Data Flow:**
1. User query → LangGraph Orchestrator
2. Search/Analysis/Stock agents 병렬 실행
3. 결과 → Vector DB (ChromaDB) + Graph DB (Neo4j) 저장
4. Hybrid retrieval → LLM 생성 → 응답

## Graph RAG 구현

Vector RAG + Graph RAG 하이브리드 접근:
1. 기업 뉴스/공시 → 벡터 임베딩 저장 (ChromaDB: `./data/chroma`)
2. 기업-산업-이벤트 관계 → 지식 그래프 (Neo4j)
3. 복합 질의 시 그래프 순회 + 시맨틱 검색 조합

**Knowledge Graph Schema:**
- **노드:** Company, Industry, Event, Person, Document
- **관계:** BELONGS_TO, COMPETES_WITH, AFFECTED_BY, LED_BY, MENTIONED_IN

## Environment Variables

`.env` 파일 또는 환경변수로 설정 (`.env.example` 참조):

```bash
# 필수
OPENAI_API_KEY=           # LLM API

# 검색 (하나 이상 필요)
SERPAPI_KEY=              # SerpAPI
TAVILY_API_KEY=           # Tavily (대안)

# 그래프 DB
NEO4J_URI=                # 기본: bolt://localhost:7687
NEO4J_USER=               # 기본: neo4j
NEO4J_PASSWORD=

# 주식 데이터 (선택)
ALPHA_VANTAGE_KEY=

# Palantir AIP (선택)
FOUNDRY_TOKEN=
FOUNDRY_HOST=
```

## Palantir AIP Integration

현재 플랫폼 활성화 완료, 접근 권한 필요 상태. 상세: `docs/PALANTIR_ACCESS_GUIDE.md`

MCP 설치:
```bash
export FOUNDRY_HOST="<enrollment>.palantirfoundry.com"
export FOUNDRY_TOKEN=<token>
claude mcp add palantir-mcp \
  --scope user \
  -e FOUNDRY_TOKEN=$FOUNDRY_TOKEN \
  -- npx "-y" "palantir-mcp" "--foundry-api-url" "https://$FOUNDRY_HOST"
```

## Development Roadmap

`docs/PRD.md` 참조:
- **Phase 1:** MVP - 기업 정보 수집 에이전트 + CLI
- **Phase 2:** Graph RAG 통합
- **Phase 3:** 주식 데이터 연동
- **Phase 4:** Palantir AIP + 웹 대시보드
