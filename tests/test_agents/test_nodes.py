"""에이전트 노드 테스트."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.nodes import search_node, news_node, summarize_node, error_handler_node
from src.models.schemas import AgentState


@pytest.fixture
def initial_state():
    """초기 에이전트 상태를 반환합니다."""
    return AgentState(
        query="삼성전자",
        company_name="삼성전자",
        search_results=[],
        news_items=[],
        palantir_data=None,
        summary="",
        error=None,
    )


class TestSearchNode:
    """search_node 테스트."""

    @pytest.mark.asyncio
    async def test_search_node_without_company_name(self):
        """기업명이 없으면 에러를 설정합니다."""
        state = AgentState(
            query="",
            company_name="",
            search_results=[],
            news_items=[],
            palantir_data=None,
            summary="",
            error=None,
        )

        result = await search_node(state)

        assert result["error"] == "기업명이 지정되지 않았습니다"

    @pytest.mark.asyncio
    async def test_search_node_with_provider_error(self, initial_state, mock_search_results):
        """검색 실패 시 빈 결과와 에러를 설정합니다."""
        from src.search import SearchProviderError

        with patch("src.agents.nodes.SearchProviderFactory") as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.search.side_effect = SearchProviderError("테스트 에러")
            mock_factory.create.return_value = mock_provider

            result = await search_node(initial_state)

        assert result["search_results"] == []
        assert "테스트 에러" in result["error"]


class TestErrorHandlerNode:
    """error_handler_node 테스트."""

    @pytest.mark.asyncio
    async def test_error_handler_creates_summary(self):
        """에러 핸들러가 요약을 생성합니다."""
        state = AgentState(
            query="삼성전자",
            company_name="삼성전자",
            search_results=[],
            news_items=[],
            palantir_data=None,
            summary="",
            error="검색 API 오류",
        )

        result = await error_handler_node(state)

        assert "삼성전자" in result["summary"]
        assert "오류" in result["summary"]
        assert "검색 API 오류" in result["summary"]
