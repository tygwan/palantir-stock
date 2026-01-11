"""검색 프로바이더 추상 인터페이스."""

from abc import ABC, abstractmethod

from src.models.schemas import SearchResponse


class BaseSearchProvider(ABC):
    """검색 프로바이더 추상 기본 클래스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """프로바이더 이름을 반환합니다."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """API 키가 설정되어 있는지 확인합니다."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs,
    ) -> SearchResponse:
        """일반 웹 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            **kwargs: 추가 옵션

        Returns:
            검색 응답
        """
        pass

    @abstractmethod
    async def news_search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs,
    ) -> SearchResponse:
        """뉴스 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            **kwargs: 추가 옵션

        Returns:
            검색 응답
        """
        pass


class SearchProviderError(Exception):
    """검색 프로바이더 오류."""

    pass
