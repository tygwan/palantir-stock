"""주식 데이터 모델."""

from datetime import datetime
from pydantic import BaseModel, Field


class StockPrice(BaseModel):
    """주가 데이터."""

    date: datetime = Field(..., description="날짜")
    open: float = Field(..., description="시가")
    high: float = Field(..., description="고가")
    low: float = Field(..., description="저가")
    close: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")
    adj_close: float | None = Field(default=None, description="수정 종가")


class StockInfo(BaseModel):
    """주식 기본 정보."""

    ticker: str = Field(..., description="티커 심볼")
    name: str = Field(..., description="기업명")
    sector: str | None = Field(default=None, description="섹터")
    industry: str | None = Field(default=None, description="산업")
    market_cap: float | None = Field(default=None, description="시가총액")
    currency: str = Field(default="KRW", description="통화")
    exchange: str | None = Field(default=None, description="거래소")
    country: str | None = Field(default=None, description="국가")
    website: str | None = Field(default=None, description="웹사이트")
    description: str | None = Field(default=None, description="기업 설명")


class TechnicalIndicator(BaseModel):
    """기술적 지표."""

    name: str = Field(..., description="지표명")
    value: float = Field(..., description="현재 값")
    signal: str = Field(..., description="신호 (buy/sell/neutral)")
    description: str | None = Field(default=None, description="설명")


class StockAnalysis(BaseModel):
    """주식 종합 분석."""

    info: StockInfo = Field(..., description="기본 정보")
    current_price: float = Field(..., description="현재가")
    change_percent: float = Field(..., description="등락률 (%)")
    prices: list[StockPrice] = Field(default_factory=list, description="가격 히스토리")
    indicators: list[TechnicalIndicator] = Field(
        default_factory=list, description="기술적 지표"
    )
    recommendation: str | None = Field(default=None, description="추천 의견")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="분석 시간")
