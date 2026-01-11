"""주식 API 라우트."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import ErrorResponse, StockData, StockIndicators, StockRequest
from src.stock import StockClient
from src.utils.logging import get_logger

logger = get_logger("api.stock")
router = APIRouter(prefix="/stock", tags=["주식"])


@router.post(
    "/analyze",
    response_model=StockData,
    responses={500: {"model": ErrorResponse}},
    summary="주식 분석",
    description="지정된 기업의 주식 데이터와 기술적 지표를 분석합니다.",
)
async def analyze_stock(request: StockRequest) -> StockData:
    """주식을 분석합니다."""
    try:
        logger.info(f"주식 분석 요청: {request.company_name}")
        client = StockClient()
        analysis = await client.analyze(request.company_name, period=request.period)

        # 기술적 지표 변환
        indicators = None
        if analysis.indicators:
            ind = analysis.indicators
            indicators = StockIndicators(
                rsi=ind.rsi,
                macd={
                    "macd": ind.macd,
                    "signal": ind.macd_signal,
                    "histogram": ind.macd_histogram,
                }
                if ind.macd is not None
                else None,
                bollinger={
                    "upper": ind.bollinger_upper,
                    "middle": ind.bollinger_middle,
                    "lower": ind.bollinger_lower,
                }
                if ind.bollinger_upper is not None
                else None,
                sma_20=ind.sma_20,
                sma_50=ind.sma_50,
            )

        return StockData(
            ticker=analysis.info.ticker,
            name=analysis.info.name,
            current_price=analysis.current_price,
            change_percent=analysis.change_percent,
            volume=analysis.volume,
            indicators=indicators,
        )

    except Exception as e:
        logger.error(f"주식 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/price/{company_name}",
    response_model=dict,
    responses={500: {"model": ErrorResponse}},
    summary="주가 조회",
    description="지정된 기업의 현재 주가와 기본 정보를 조회합니다.",
)
async def get_stock_price(company_name: str, period: str = "1mo") -> dict:
    """주가를 조회합니다."""
    try:
        logger.info(f"주가 조회: {company_name}")
        client = StockClient()
        history = await client.get_price_history(company_name, period=period)

        if not history:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")

        latest = history[-1]
        return {
            "company_name": company_name,
            "latest_date": latest.date.isoformat(),
            "open": latest.open,
            "high": latest.high,
            "low": latest.low,
            "close": latest.close,
            "volume": latest.volume,
            "history_count": len(history),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주가 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
