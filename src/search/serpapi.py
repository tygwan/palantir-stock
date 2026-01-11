"""SerpAPI 검색 프로바이더."""

import asyncio
import time
from datetime import datetime

from serpapi import GoogleSearch

from src.models.schemas import SearchResponse, SearchResult
from src.search.base import BaseSearchProvider, SearchProviderError
from src.utils.logging import get_logger

logger = get_logger("search.serpapi")


class SerpAPIProvider(BaseSearchProvider):
    """SerpAPI 기반 검색 프로바이더."""

    def __init__(self, api_key: str, max_results: int = 10):
        """SerpAPI 프로바이더를 초기화합니다.

        Args:
            api_key: SerpAPI API 키
            max_results: 기본 최대 결과 수
        """
        self._api_key = api_key
        self._max_results = max_results

    @property
    def name(self) -> str:
        return "serpapi"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> SearchResponse:
        """Google 웹 검색을 수행합니다."""
        if not self.is_available:
            raise SearchProviderError("SerpAPI API 키가 설정되지 않았습니다")

        max_results = max_results or self._max_results
        start_time = time.time()

        try:
            # SerpAPI는 동기 라이브러리이므로 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._execute_search(query, max_results, **kwargs),
            )
            return result

        except Exception as e:
            logger.error(f"SerpAPI 검색 실패: {e}")
            raise SearchProviderError(f"검색 실패: {e}") from e

    async def news_search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> SearchResponse:
        """Google 뉴스 검색을 수행합니다."""
        return await self.search(
            query,
            max_results=max_results,
            tbm="nws",  # 뉴스 검색 모드
            **kwargs,
        )

    def _execute_search(
        self,
        query: str,
        max_results: int,
        **kwargs,
    ) -> SearchResponse:
        """동기적으로 검색을 실행합니다."""
        start_time = time.time()

        params = {
            "q": query,
            "api_key": self._api_key,
            "num": max_results,
            "hl": kwargs.get("hl", "ko"),  # 한국어
            "gl": kwargs.get("gl", "kr"),  # 한국 지역
            **kwargs,
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        results = []

        # 일반 검색 결과 파싱
        organic_results = data.get("organic_results", [])
        for item in organic_results[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    published_date=self._parse_date(item.get("date")),
                )
            )

        # 뉴스 검색 결과 파싱
        news_results = data.get("news_results", [])
        for item in news_results[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    published_date=self._parse_date(item.get("date")),
                )
            )

        search_time = time.time() - start_time
        logger.debug(f"SerpAPI 검색 완료: {len(results)}개 결과, {search_time:.2f}초")

        return SearchResponse(
            query=query,
            results=results[:max_results],
            total_results=len(results),
            search_time=search_time,
            provider=self.name,
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """날짜 문자열을 파싱합니다."""
        if not date_str:
            return None
        try:
            # SerpAPI 날짜 형식 파싱 시도
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
