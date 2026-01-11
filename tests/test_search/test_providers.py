"""검색 프로바이더 테스트."""

import pytest

from src.search import SearchProviderError, SerpAPIProvider, TavilyProvider


class TestSerpAPIProvider:
    """SerpAPI 프로바이더 테스트."""

    def test_provider_name(self):
        """프로바이더 이름이 올바릅니다."""
        provider = SerpAPIProvider(api_key="test-key")
        assert provider.name == "serpapi"

    def test_is_available_with_key(self):
        """API 키가 있으면 사용 가능합니다."""
        provider = SerpAPIProvider(api_key="test-key")
        assert provider.is_available is True

    def test_is_not_available_without_key(self):
        """API 키가 없으면 사용 불가합니다."""
        provider = SerpAPIProvider(api_key="")
        assert provider.is_available is False

    @pytest.mark.asyncio
    async def test_search_raises_when_not_available(self):
        """API 키가 없으면 검색 시 에러를 발생시킵니다."""
        provider = SerpAPIProvider(api_key="")

        with pytest.raises(SearchProviderError) as exc_info:
            await provider.search("test query")

        assert "API 키가 설정되지 않았습니다" in str(exc_info.value)


class TestTavilyProvider:
    """Tavily 프로바이더 테스트."""

    def test_provider_name(self):
        """프로바이더 이름이 올바릅니다."""
        provider = TavilyProvider(api_key="test-key")
        assert provider.name == "tavily"

    def test_is_available_with_key(self):
        """API 키가 있으면 사용 가능합니다."""
        provider = TavilyProvider(api_key="test-key")
        assert provider.is_available is True

    def test_is_not_available_without_key(self):
        """API 키가 없으면 사용 불가합니다."""
        provider = TavilyProvider(api_key="")
        assert provider.is_available is False

    @pytest.mark.asyncio
    async def test_search_raises_when_not_available(self):
        """API 키가 없으면 검색 시 에러를 발생시킵니다."""
        provider = TavilyProvider(api_key="")

        with pytest.raises(SearchProviderError) as exc_info:
            await provider.search("test query")

        assert "API 키가 설정되지 않았습니다" in str(exc_info.value)
