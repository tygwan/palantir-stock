"""기업 분석 API 라우트."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.agents import CompanyInfoAgent
from src.api.schemas import (
    AnalyzeRequest,
    CompanyAnalysis,
    ErrorResponse,
    NewsItem,
    NewsSearchRequest,
    StockData,
    StockIndicators,
)
from src.utils.logging import get_logger

logger = get_logger("api.analyze")
router = APIRouter(prefix="/analyze", tags=["분석"])


@router.post(
    "/company",
    response_model=CompanyAnalysis,
    responses={500: {"model": ErrorResponse}},
    summary="기업 종합 분석",
    description="지정된 기업에 대한 종합 분석을 수행합니다. 웹 검색, 뉴스, 주식 데이터, Graph RAG를 통합합니다.",
)
async def analyze_company(request: AnalyzeRequest) -> CompanyAnalysis:
    """기업 종합 분석을 수행합니다."""
    try:
        logger.info(f"기업 분석 요청: {request.company_name}")
        agent = CompanyInfoAgent()
        report = await agent.analyze(request.company_name)

        # 결과 변환
        news_items = [
            NewsItem(
                title=n.title,
                url=n.url,
                source=n.source,
                published_date=n.published_date,
                summary=n.summary,
            )
            for n in report.news
        ]

        # 주식 데이터 변환
        stock_data = None
        if request.include_stock and report.palantir_data:
            raw_stock = report.palantir_data.get("stock_data")
            if raw_stock:
                indicators = None
                if raw_stock.get("indicators"):
                    ind = raw_stock["indicators"]
                    indicators = StockIndicators(
                        rsi=ind.get("rsi"),
                        macd=ind.get("macd"),
                        bollinger=ind.get("bollinger"),
                        sma_20=ind.get("sma_20"),
                        sma_50=ind.get("sma_50"),
                    )
                stock_data = StockData(
                    ticker=raw_stock.get("ticker", ""),
                    name=raw_stock.get("name", request.company_name),
                    current_price=raw_stock.get("current_price"),
                    change_percent=raw_stock.get("change_percent"),
                    volume=raw_stock.get("volume"),
                    indicators=indicators,
                )

        return CompanyAnalysis(
            company_name=request.company_name,
            summary=report.summary,
            news=news_items,
            stock_data=stock_data,
            graph_context=report.palantir_data.get("graph_context")
            if report.palantir_data
            else None,
            palantir_data=report.palantir_data,
            sources=report.sources,
            generated_at=report.generated_at,
        )

    except Exception as e:
        logger.error(f"기업 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/news",
    response_model=list[NewsItem],
    responses={500: {"model": ErrorResponse}},
    summary="뉴스 검색",
    description="지정된 쿼리에 대한 최신 뉴스를 검색합니다.",
)
async def search_news(request: NewsSearchRequest) -> list[NewsItem]:
    """뉴스를 검색합니다."""
    try:
        logger.info(f"뉴스 검색 요청: {request.query}")
        agent = CompanyInfoAgent()
        results = await agent.quick_news(request.query)

        return [
            NewsItem(
                title=r["title"],
                url=r["url"],
                source=r.get("source", ""),
                published_date=datetime.fromisoformat(r["published_date"])
                if r.get("published_date")
                else None,
            )
            for r in results[: request.limit]
        ]

    except Exception as e:
        logger.error(f"뉴스 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
