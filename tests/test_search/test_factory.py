"""SearchProviderFactory 테스트."""

import pytest

from config.settings import Settings
from src.search import SearchProviderError, SearchProviderFactory, SerpAPIProvider, TavilyProvider


def test_factory_prefers_tavily():
    """Tavily와 SerpAPI 모두 있을 때 Tavily를 우선 선택합니다."""
    settings = Settings(
        serpapi_key="test-serpapi",
        tavily_api_key="test-tavily",
    )

    provider = SearchProviderFactory.create(settings)

    assert isinstance(provider, TavilyProvider)
    assert provider.name == "tavily"


def test_factory_fallback_to_serpapi():
    """Tavily가 없으면 SerpAPI를 사용합니다."""
    settings = Settings(
        serpapi_key="test-serpapi",
        tavily_api_key="",
    )

    provider = SearchProviderFactory.create(settings)

    assert isinstance(provider, SerpAPIProvider)
    assert provider.name == "serpapi"


def test_factory_raises_when_no_api_key():
    """API 키가 없으면 에러를 발생시킵니다."""
    settings = Settings(
        serpapi_key="",
        tavily_api_key="",
    )

    with pytest.raises(SearchProviderError) as exc_info:
        SearchProviderFactory.create(settings)

    assert "검색 API 키가 설정되지 않았습니다" in str(exc_info.value)


def test_factory_create_all():
    """모든 사용 가능한 프로바이더를 생성합니다."""
    settings = Settings(
        serpapi_key="test-serpapi",
        tavily_api_key="test-tavily",
    )

    providers = SearchProviderFactory.create_all(settings)

    assert len(providers) == 2
    assert any(isinstance(p, TavilyProvider) for p in providers)
    assert any(isinstance(p, SerpAPIProvider) for p in providers)


def test_factory_create_all_empty():
    """API 키가 없으면 빈 리스트를 반환합니다."""
    settings = Settings(
        serpapi_key="",
        tavily_api_key="",
    )

    providers = SearchProviderFactory.create_all(settings)

    assert providers == []
