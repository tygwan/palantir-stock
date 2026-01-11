"""LangGraph 에이전트 오케스트레이터."""

from datetime import datetime

from langgraph.graph import END, StateGraph

from config.settings import Settings, settings
from src.agents.nodes import (
    error_handler_node,
    news_node,
    palantir_node,
    search_node,
    should_continue,
    summarize_node,
)
from src.models.schemas import AgentState, CompanyInfo, CompanyReport
from src.utils.logging import get_logger

logger = get_logger("agents.orchestrator")


def create_company_info_graph() -> StateGraph:
    """기업 정보 수집 LangGraph 워크플로우를 생성합니다.

    Returns:
        컴파일된 StateGraph
    """
    graph = StateGraph(AgentState)

    # 노드 추가
    graph.add_node("search", search_node)
    graph.add_node("news", news_node)
    graph.add_node("palantir", palantir_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("error_handler", error_handler_node)

    # 엔트리 포인트 설정
    graph.set_entry_point("search")

    # 조건부 엣지 (검색 실패 시 에러 핸들러로)
    graph.add_conditional_edges(
        "search",
        should_continue,
        {
            "continue": "news",
            "error_handler": "error_handler",
        },
    )

    # 순차적 엣지
    graph.add_edge("news", "palantir")
    graph.add_edge("palantir", "summarize")
    graph.add_edge("summarize", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


class CompanyInfoAgent:
    """기업 정보 수집 에이전트."""

    def __init__(self, settings: Settings | None = None):
        """에이전트를 초기화합니다.

        Args:
            settings: 애플리케이션 설정
        """
        self.settings = settings or globals()["settings"]
        self._graph = None

    @property
    def graph(self):
        """LangGraph 워크플로우를 반환합니다."""
        if self._graph is None:
            self._graph = create_company_info_graph()
        return self._graph

    async def analyze(self, company_name: str) -> CompanyReport:
        """기업을 분석합니다.

        Args:
            company_name: 분석할 기업명

        Returns:
            기업 분석 리포트
        """
        logger.info(f"기업 분석 시작: {company_name}")

        # 초기 상태 설정
        initial_state: AgentState = {
            "query": company_name,
            "company_name": company_name,
            "search_results": [],
            "news_items": [],
            "palantir_data": None,
            "summary": "",
            "error": None,
        }

        # 워크플로우 실행
        result = await self.graph.ainvoke(initial_state)

        # 결과를 CompanyReport로 변환
        report = CompanyReport(
            company=CompanyInfo(name=company_name),
            news=result.get("news_items", []),
            summary=result.get("summary", ""),
            generated_at=datetime.now(),
            sources=[r.url for r in result.get("search_results", [])],
            palantir_data=result.get("palantir_data"),
        )

        logger.info(f"기업 분석 완료: {company_name}")
        return report

    async def quick_search(self, query: str) -> list[dict]:
        """빠른 검색을 수행합니다.

        Args:
            query: 검색 쿼리

        Returns:
            검색 결과 목록
        """
        from src.search import SearchProviderFactory

        try:
            provider = SearchProviderFactory.create(self.settings)
            response = await provider.search(query)

            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                }
                for r in response.results
            ]
        except Exception as e:
            logger.error(f"빠른 검색 실패: {e}")
            return []

    async def quick_news(self, query: str) -> list[dict]:
        """빠른 뉴스 검색을 수행합니다.

        Args:
            query: 검색 쿼리

        Returns:
            뉴스 결과 목록
        """
        from src.search import SearchProviderFactory

        try:
            provider = SearchProviderFactory.create(self.settings)
            response = await provider.news_search(query)

            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "published_date": (
                        r.published_date.isoformat() if r.published_date else None
                    ),
                }
                for r in response.results
            ]
        except Exception as e:
            logger.error(f"뉴스 검색 실패: {e}")
            return []
