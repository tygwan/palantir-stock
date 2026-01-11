"""기술적 지표 계산."""

import pandas as pd
import numpy as np

from src.utils.logging import get_logger

logger = get_logger("stock.indicators")


class TechnicalIndicators:
    """기술적 지표 계산 클래스."""

    def rsi(
        self,
        prices: pd.Series,
        period: int = 14,
    ) -> float | None:
        """RSI (Relative Strength Index)를 계산합니다.

        Args:
            prices: 종가 시리즈
            period: 계산 기간 (기본 14일)

        Returns:
            RSI 값 (0-100) 또는 None
        """
        if len(prices) < period + 1:
            return None

        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1])

        except Exception as e:
            logger.warning(f"RSI 계산 실패: {e}")
            return None

    def macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> dict | None:
        """MACD (Moving Average Convergence Divergence)를 계산합니다.

        Args:
            prices: 종가 시리즈
            fast: 단기 EMA 기간 (기본 12)
            slow: 장기 EMA 기간 (기본 26)
            signal: 시그널 라인 기간 (기본 9)

        Returns:
            MACD 결과 딕셔너리 또는 None
        """
        if len(prices) < slow + signal:
            return None

        try:
            exp1 = prices.ewm(span=fast, adjust=False).mean()
            exp2 = prices.ewm(span=slow, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

            return {
                "macd": float(macd_line.iloc[-1]),
                "signal": float(signal_line.iloc[-1]),
                "histogram": float(histogram.iloc[-1]),
            }

        except Exception as e:
            logger.warning(f"MACD 계산 실패: {e}")
            return None

    def bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> dict | None:
        """볼린저 밴드를 계산합니다.

        Args:
            prices: 종가 시리즈
            period: 이동평균 기간 (기본 20)
            std_dev: 표준편차 배수 (기본 2)

        Returns:
            볼린저 밴드 결과 딕셔너리 또는 None
        """
        if len(prices) < period:
            return None

        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)

            return {
                "upper": float(upper.iloc[-1]),
                "middle": float(middle.iloc[-1]),
                "lower": float(lower.iloc[-1]),
                "bandwidth": float((upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1] * 100),
            }

        except Exception as e:
            logger.warning(f"볼린저 밴드 계산 실패: {e}")
            return None

    def sma(
        self,
        prices: pd.Series,
        period: int = 20,
    ) -> float | None:
        """단순 이동평균 (SMA)을 계산합니다.

        Args:
            prices: 종가 시리즈
            period: 이동평균 기간

        Returns:
            SMA 값 또는 None
        """
        if len(prices) < period:
            return None

        try:
            return float(prices.rolling(window=period).mean().iloc[-1])
        except Exception as e:
            logger.warning(f"SMA 계산 실패: {e}")
            return None

    def ema(
        self,
        prices: pd.Series,
        period: int = 20,
    ) -> float | None:
        """지수 이동평균 (EMA)을 계산합니다.

        Args:
            prices: 종가 시리즈
            period: EMA 기간

        Returns:
            EMA 값 또는 None
        """
        if len(prices) < period:
            return None

        try:
            return float(prices.ewm(span=period, adjust=False).mean().iloc[-1])
        except Exception as e:
            logger.warning(f"EMA 계산 실패: {e}")
            return None

    def stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> dict | None:
        """스토캐스틱 오실레이터를 계산합니다.

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            k_period: %K 기간 (기본 14)
            d_period: %D 기간 (기본 3)

        Returns:
            스토캐스틱 결과 딕셔너리 또는 None
        """
        if len(close) < k_period + d_period:
            return None

        try:
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()

            k = 100 * (close - lowest_low) / (highest_high - lowest_low)
            d = k.rolling(window=d_period).mean()

            return {
                "k": float(k.iloc[-1]),
                "d": float(d.iloc[-1]),
            }

        except Exception as e:
            logger.warning(f"스토캐스틱 계산 실패: {e}")
            return None

    def atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> float | None:
        """ATR (Average True Range)을 계산합니다.

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: ATR 기간 (기본 14)

        Returns:
            ATR 값 또는 None
        """
        if len(close) < period + 1:
            return None

        try:
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()

            return float(atr.iloc[-1])

        except Exception as e:
            logger.warning(f"ATR 계산 실패: {e}")
            return None
