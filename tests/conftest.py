"""pytest fixtures."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from config.settings import Settings
from src.models.schemas import SearchResponse, SearchResult


@pytest.fixture
def mock_settings():
    """테스트용 설정을 반환합니다."""
    return Settings(
        openai_api_key="test-openai-key",
        openai_model="gpt-4o-mini",
        serpapi_key="test-serpapi-key",
        tavily_api_key="test-tavily-key",
        foundry_token="test-foundry-token",
        foundry_host="test.palantirfoundry.com",
    )


@pytest.fixture
def mock_search_results():
    """테스트용 검색 결과를 반환합니다."""
    return SearchResponse(
        query="삼성전자",
        results=[
            SearchResult(
                title="삼성전자, 반도체 실적 발표",
                url="https://example.com/news/1",
                snippet="삼성전자가 분기 실적을 발표했습니다...",
                source="serpapi",
                published_date=datetime.now(),
            ),
            SearchResult(
                title="삼성전자 주가 전망",
                url="https://example.com/news/2",
                snippet="삼성전자 주가가 상승세를 보이고 있습니다...",
                source="serpapi",
                published_date=datetime.now(),
            ),
        ],
        total_results=2,
        search_time=0.5,
        provider="serpapi",
    )


@pytest.fixture
def mock_serpapi_provider(mock_search_results):
    """테스트용 SerpAPI 프로바이더를 반환합니다."""
    provider = MagicMock()
    provider.name = "serpapi"
    provider.is_available = True
    provider.search = AsyncMock(return_value=mock_search_results)
    provider.news_search = AsyncMock(return_value=mock_search_results)
    return provider


@pytest.fixture
def mock_tavily_provider(mock_search_results):
    """테스트용 Tavily 프로바이더를 반환합니다."""
    provider = MagicMock()
    provider.name = "tavily"
    provider.is_available = True
    provider.search = AsyncMock(return_value=mock_search_results)
    provider.news_search = AsyncMock(return_value=mock_search_results)
    return provider


@pytest.fixture
def mock_llm_client():
    """테스트용 LLM 클라이언트를 반환합니다."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="테스트 응답입니다.")
    client.summarize = AsyncMock(return_value="테스트 요약입니다.")
    client.analyze_company = AsyncMock(return_value="테스트 분석 리포트입니다.")
    return client
