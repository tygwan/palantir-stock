"""검색 프로바이더 팩토리."""

from config.settings import Settings
from src.search.base import BaseSearchProvider, SearchProviderError
from src.search.serpapi import SerpAPIProvider
from src.search.tavily import TavilyProvider
from src.utils.logging import get_logger

logger = get_logger("search.factory")


class SearchProviderFactory:
    """검색 프로바이더 팩토리."""

    @staticmethod
    def create(settings: Settings | None = None) -> BaseSearchProvider:
        """설정에 따라 검색 프로바이더를 생성합니다.

        Tavily를 우선 사용하고, 없으면 SerpAPI를 사용합니다.

        Args:
            settings: 애플리케이션 설정

        Returns:
            검색 프로바이더

        Raises:
            SearchProviderError: 사용 가능한 API 키가 없는 경우
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        # Tavily 우선 (AI 에이전트에 최적화)
        if settings.tavily_api_key:
            logger.info("Tavily 프로바이더 사용")
            return TavilyProvider(
                api_key=settings.tavily_api_key,
                max_results=settings.max_search_results,
            )

        # SerpAPI 대안
        if settings.serpapi_key:
            logger.info("SerpAPI 프로바이더 사용")
            return SerpAPIProvider(
                api_key=settings.serpapi_key,
                max_results=settings.max_search_results,
            )

        raise SearchProviderError(
            "검색 API 키가 설정되지 않았습니다. "
            "TAVILY_API_KEY 또는 SERPAPI_KEY를 설정해주세요."
        )

    @staticmethod
    def create_all(settings: Settings | None = None) -> list[BaseSearchProvider]:
        """모든 사용 가능한 프로바이더를 생성합니다.

        Args:
            settings: 애플리케이션 설정

        Returns:
            사용 가능한 프로바이더 목록
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        providers = []

        if settings.tavily_api_key:
            providers.append(
                TavilyProvider(
                    api_key=settings.tavily_api_key,
                    max_results=settings.max_search_results,
                )
            )

        if settings.serpapi_key:
            providers.append(
                SerpAPIProvider(
                    api_key=settings.serpapi_key,
                    max_results=settings.max_search_results,
                )
            )

        return providers
