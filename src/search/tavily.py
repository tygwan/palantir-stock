"""Tavily 검색 프로바이더."""

import time
from datetime import datetime

from tavily import TavilyClient

from src.models.schemas import SearchResponse, SearchResult
from src.search.base import BaseSearchProvider, SearchProviderError
from src.utils.logging import get_logger

logger = get_logger("search.tavily")


class TavilyProvider(BaseSearchProvider):
    """Tavily 기반 검색 프로바이더."""

    def __init__(self, api_key: str, max_results: int = 10):
        """Tavily 프로바이더를 초기화합니다.

        Args:
            api_key: Tavily API 키
            max_results: 기본 최대 결과 수
        """
        self._api_key = api_key
        self._max_results = max_results
        self._client: TavilyClient | None = None

    @property
    def name(self) -> str:
        return "tavily"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    @property
    def client(self) -> TavilyClient:
        """Tavily 클라이언트를 반환합니다."""
        if self._client is None:
            self._client = TavilyClient(api_key=self._api_key)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> SearchResponse:
        """Tavily 웹 검색을 수행합니다."""
        if not self.is_available:
            raise SearchProviderError("Tavily API 키가 설정되지 않았습니다")

        max_results = max_results or self._max_results
        start_time = time.time()

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=kwargs.get("search_depth", "basic"),
                include_answer=kwargs.get("include_answer", False),
            )

            results = self._parse_results(response)
            search_time = time.time() - start_time

            logger.debug(f"Tavily 검색 완료: {len(results)}개 결과, {search_time:.2f}초")

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"Tavily 검색 실패: {e}")
            raise SearchProviderError(f"검색 실패: {e}") from e

    async def news_search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> SearchResponse:
        """Tavily 뉴스 검색을 수행합니다."""
        if not self.is_available:
            raise SearchProviderError("Tavily API 키가 설정되지 않았습니다")

        max_results = max_results or self._max_results
        start_time = time.time()

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                topic="news",
                search_depth=kwargs.get("search_depth", "basic"),
            )

            results = self._parse_results(response)
            search_time = time.time() - start_time

            logger.debug(f"Tavily 뉴스 검색 완료: {len(results)}개 결과, {search_time:.2f}초")

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"Tavily 뉴스 검색 실패: {e}")
            raise SearchProviderError(f"검색 실패: {e}") from e

    def _parse_results(self, response: dict) -> list[SearchResult]:
        """Tavily 응답을 파싱합니다."""
        results = []

        for item in response.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name,
                    published_date=self._parse_date(item.get("published_date")),
                )
            )

        return results

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """날짜 문자열을 파싱합니다."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
