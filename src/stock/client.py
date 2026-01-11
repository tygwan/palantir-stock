"""주식 데이터 클라이언트."""

from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

from config.settings import Settings
from src.stock.models import StockInfo, StockPrice, StockAnalysis, TechnicalIndicator
from src.stock.indicators import TechnicalIndicators
from src.utils.logging import get_logger

logger = get_logger("stock.client")

# 한국 주식 티커 매핑 (일부 예시)
KR_TICKER_MAP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "현대자동차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "LG화학": "051910.KS",
    "삼성SDI": "006400.KS",
    "현대모비스": "012330.KS",
    "삼성물산": "028260.KS",
    "SK이노베이션": "096770.KS",
    "LG전자": "066570.KS",
}


class StockClient:
    """yfinance 기반 주식 데이터 클라이언트."""

    def __init__(self, settings: Settings | None = None):
        """클라이언트를 초기화합니다.

        Args:
            settings: 애플리케이션 설정
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        self.settings = settings
        self._indicators = TechnicalIndicators()

    def resolve_ticker(self, query: str) -> str:
        """기업명 또는 티커를 표준 티커로 변환합니다.

        Args:
            query: 기업명 또는 티커

        Returns:
            표준 티커 심볼
        """
        # 이미 티커 형식이면 그대로 반환
        if "." in query or query.isupper():
            return query

        # 한국 주식 매핑 확인
        if query in KR_TICKER_MAP:
            return KR_TICKER_MAP[query]

        # 그 외는 그대로 반환 (yfinance가 검색 시도)
        return query

    async def get_info(self, ticker: str) -> StockInfo | None:
        """주식 기본 정보를 조회합니다.

        Args:
            ticker: 티커 심볼 또는 기업명

        Returns:
            주식 기본 정보 또는 None
        """
        resolved = self.resolve_ticker(ticker)

        try:
            stock = yf.Ticker(resolved)
            info = stock.info

            if not info or "symbol" not in info:
                logger.warning(f"주식 정보를 찾을 수 없음: {resolved}")
                return None

            return StockInfo(
                ticker=info.get("symbol", resolved),
                name=info.get("longName", info.get("shortName", "")),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                currency=info.get("currency", "KRW"),
                exchange=info.get("exchange"),
                country=info.get("country"),
                website=info.get("website"),
                description=info.get("longBusinessSummary"),
            )

        except Exception as e:
            logger.error(f"주식 정보 조회 실패: {e}")
            return None

    async def get_prices(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d",
    ) -> list[StockPrice]:
        """주가 히스토리를 조회합니다.

        Args:
            ticker: 티커 심볼 또는 기업명
            period: 조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 간격 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            주가 히스토리 목록
        """
        resolved = self.resolve_ticker(ticker)

        try:
            stock = yf.Ticker(resolved)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"주가 데이터 없음: {resolved}")
                return []

            prices = []
            for date, row in hist.iterrows():
                prices.append(
                    StockPrice(
                        date=date.to_pydatetime(),
                        open=row["Open"],
                        high=row["High"],
                        low=row["Low"],
                        close=row["Close"],
                        volume=int(row["Volume"]),
                        adj_close=row.get("Adj Close"),
                    )
                )

            logger.debug(f"주가 데이터 조회: {len(prices)}개")
            return prices

        except Exception as e:
            logger.error(f"주가 데이터 조회 실패: {e}")
            return []

    async def get_current_price(self, ticker: str) -> float | None:
        """현재가를 조회합니다.

        Args:
            ticker: 티커 심볼 또는 기업명

        Returns:
            현재가 또는 None
        """
        resolved = self.resolve_ticker(ticker)

        try:
            stock = yf.Ticker(resolved)
            info = stock.info

            # 현재가 조회 (여러 필드 시도)
            price = info.get("currentPrice") or info.get("regularMarketPrice")

            if price is None:
                # 최근 종가로 대체
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]

            return price

        except Exception as e:
            logger.error(f"현재가 조회 실패: {e}")
            return None

    async def analyze(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> StockAnalysis | None:
        """주식을 종합 분석합니다.

        Args:
            ticker: 티커 심볼 또는 기업명
            period: 분석 기간

        Returns:
            주식 분석 결과 또는 None
        """
        # 기본 정보 조회
        info = await self.get_info(ticker)
        if not info:
            return None

        # 가격 데이터 조회
        prices = await self.get_prices(ticker, period=period)
        if not prices:
            return None

        # 현재가 및 등락률 계산
        current_price = prices[-1].close
        prev_price = prices[-2].close if len(prices) > 1 else current_price
        change_percent = ((current_price - prev_price) / prev_price) * 100

        # DataFrame으로 변환
        df = pd.DataFrame([p.model_dump() for p in prices])

        # 기술적 지표 계산
        indicators = []

        # RSI
        rsi = self._indicators.rsi(df["close"])
        if rsi is not None:
            signal = "sell" if rsi > 70 else "buy" if rsi < 30 else "neutral"
            indicators.append(
                TechnicalIndicator(
                    name="RSI",
                    value=round(rsi, 2),
                    signal=signal,
                    description=f"RSI {rsi:.1f} - {'과매수' if rsi > 70 else '과매도' if rsi < 30 else '중립'}",
                )
            )

        # MACD
        macd_result = self._indicators.macd(df["close"])
        if macd_result:
            signal = "buy" if macd_result["histogram"] > 0 else "sell"
            indicators.append(
                TechnicalIndicator(
                    name="MACD",
                    value=round(macd_result["macd"], 2),
                    signal=signal,
                    description=f"MACD {macd_result['macd']:.2f}, Signal {macd_result['signal']:.2f}",
                )
            )

        # 볼린저 밴드
        bb = self._indicators.bollinger_bands(df["close"])
        if bb:
            if current_price > bb["upper"]:
                signal = "sell"
                desc = "상단 밴드 돌파 (과매수)"
            elif current_price < bb["lower"]:
                signal = "buy"
                desc = "하단 밴드 돌파 (과매도)"
            else:
                signal = "neutral"
                desc = "밴드 내 거래"

            indicators.append(
                TechnicalIndicator(
                    name="Bollinger",
                    value=round(bb["middle"], 2),
                    signal=signal,
                    description=desc,
                )
            )

        # 종합 추천
        buy_signals = sum(1 for i in indicators if i.signal == "buy")
        sell_signals = sum(1 for i in indicators if i.signal == "sell")

        if buy_signals > sell_signals:
            recommendation = "매수 고려"
        elif sell_signals > buy_signals:
            recommendation = "매도 고려"
        else:
            recommendation = "중립"

        return StockAnalysis(
            info=info,
            current_price=current_price,
            change_percent=round(change_percent, 2),
            prices=prices[-30:],  # 최근 30일
            indicators=indicators,
            recommendation=recommendation,
        )


# 기본 클라이언트 인스턴스
_default_client: StockClient | None = None


def get_stock_client(settings: Settings | None = None) -> StockClient:
    """기본 주식 클라이언트를 반환합니다."""
    global _default_client

    if _default_client is None:
        _default_client = StockClient(settings)

    return _default_client
