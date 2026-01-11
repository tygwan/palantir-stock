"""API 스키마 정의."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """기업 분석 요청."""

    company_name: str = Field(..., description="분석할 기업명", min_length=1)
    include_stock: bool = Field(default=True, description="주식 데이터 포함 여부")
    include_graph: bool = Field(default=True, description="Graph RAG 포함 여부")


class NewsSearchRequest(BaseModel):
    """뉴스 검색 요청."""

    query: str = Field(..., description="검색 쿼리", min_length=1)
    limit: int = Field(default=10, ge=1, le=50, description="결과 개수")


class StockRequest(BaseModel):
    """주식 분석 요청."""

    company_name: str = Field(..., description="기업명 또는 티커")
    period: str = Field(default="3mo", description="기간 (1mo, 3mo, 6mo, 1y)")


class GraphSearchRequest(BaseModel):
    """Graph RAG 검색 요청."""

    query: str = Field(..., description="검색 쿼리")
    company_name: str | None = Field(default=None, description="특정 기업 필터")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수")


class ReportRequest(BaseModel):
    """리포트 생성 요청."""

    company_name: str = Field(..., description="기업명")
    format: str = Field(default="html", description="출력 형식 (html, markdown, json)")


class NewsItem(BaseModel):
    """뉴스 항목."""

    title: str
    url: str
    source: str
    published_date: datetime | None = None
    summary: str | None = None


class StockIndicators(BaseModel):
    """주식 기술적 지표."""

    rsi: float | None = None
    macd: dict | None = None
    bollinger: dict | None = None
    sma_20: float | None = None
    sma_50: float | None = None


class StockData(BaseModel):
    """주식 데이터."""

    ticker: str
    name: str
    current_price: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    indicators: StockIndicators | None = None


class CompanyAnalysis(BaseModel):
    """기업 분석 결과."""

    company_name: str
    summary: str
    news: list[NewsItem] = []
    stock_data: StockData | None = None
    graph_context: str | None = None
    palantir_data: dict | None = None
    sources: list[str] = []
    generated_at: datetime


class ReportResponse(BaseModel):
    """리포트 응답."""

    company_name: str
    format: str
    content: str
    generated_at: datetime


class HealthResponse(BaseModel):
    """헬스체크 응답."""

    status: str = "ok"
    version: str = "1.0.0"
    services: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """에러 응답."""

    error: str
    detail: str | None = None
