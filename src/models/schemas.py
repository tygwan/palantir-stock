"""Pydantic 데이터 모델 정의."""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """개별 검색 결과."""

    title: str = Field(..., description="검색 결과 제목")
    url: str = Field(..., description="검색 결과 URL")
    snippet: str = Field(default="", description="검색 결과 요약")
    source: str = Field(..., description="검색 제공자 (serpapi/tavily)")
    published_date: datetime | None = Field(default=None, description="게시일")


class SearchResponse(BaseModel):
    """검색 응답 집합."""

    query: str = Field(..., description="검색 쿼리")
    results: list[SearchResult] = Field(default_factory=list, description="검색 결과 목록")
    total_results: int = Field(default=0, description="총 결과 수")
    search_time: float = Field(default=0.0, description="검색 소요 시간 (초)")
    provider: str = Field(..., description="검색 제공자")


class CompanyInfo(BaseModel):
    """기업 기본 정보."""

    name: str = Field(..., description="기업명")
    ticker: str | None = Field(default=None, description="주식 티커")
    industry: str | None = Field(default=None, description="산업 분류")
    description: str | None = Field(default=None, description="기업 설명")
    market_cap: str | None = Field(default=None, description="시가총액")


class NewsItem(BaseModel):
    """뉴스 기사 항목."""

    title: str = Field(..., description="기사 제목")
    url: str = Field(..., description="기사 URL")
    source: str = Field(..., description="출처")
    published_date: datetime | None = Field(default=None, description="게시일")
    summary: str | None = Field(default=None, description="요약")


class CompanyReport(BaseModel):
    """기업 분석 리포트."""

    company: CompanyInfo = Field(..., description="기업 정보")
    news: list[NewsItem] = Field(default_factory=list, description="관련 뉴스")
    summary: str = Field(..., description="분석 요약")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    sources: list[str] = Field(default_factory=list, description="참조 소스 URL")
    palantir_data: dict | None = Field(default=None, description="Palantir 데이터")


class AgentState(TypedDict, total=False):
    """LangGraph 에이전트 상태."""

    query: str
    company_name: str
    search_results: list[SearchResult]
    news_items: list[NewsItem]
    palantir_data: dict
    summary: str
    error: str | None
