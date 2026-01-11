"""LangGraph 에이전트 노드 정의."""

from config.settings import settings
from src.models.schemas import AgentState, NewsItem, SearchResult
from src.palantir import OntologyExplorer, get_foundry_client
from src.search import SearchProviderError, SearchProviderFactory
from src.utils import LLMClient, get_logger

logger = get_logger("agents.nodes")


async def search_node(state: AgentState) -> AgentState:
    """웹 검색을 수행하는 노드.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태
    """
    company_name = state.get("company_name", "")
    if not company_name:
        state["error"] = "기업명이 지정되지 않았습니다"
        return state

    try:
        provider = SearchProviderFactory.create(settings)
        query = f"{company_name} 기업 정보 현황"

        logger.info(f"웹 검색 시작: {query}")
        response = await provider.search(query)

        state["search_results"] = response.results
        logger.info(f"검색 완료: {len(response.results)}개 결과")

    except SearchProviderError as e:
        logger.warning(f"검색 실패: {e}")
        state["error"] = str(e)
        state["search_results"] = []

    return state


async def news_node(state: AgentState) -> AgentState:
    """뉴스 검색을 수행하는 노드.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태
    """
    company_name = state.get("company_name", "")
    if not company_name:
        return state

    try:
        provider = SearchProviderFactory.create(settings)
        query = f"{company_name} 최신 뉴스"

        logger.info(f"뉴스 검색 시작: {query}")
        response = await provider.news_search(query)

        news_items = [
            NewsItem(
                title=r.title,
                url=r.url,
                source=r.source,
                published_date=r.published_date,
                summary=r.snippet,
            )
            for r in response.results
        ]

        state["news_items"] = news_items
        logger.info(f"뉴스 검색 완료: {len(news_items)}개 기사")

    except SearchProviderError as e:
        logger.warning(f"뉴스 검색 실패: {e}")
        state["news_items"] = []

    return state


async def palantir_node(state: AgentState) -> AgentState:
    """Palantir 데이터를 조회하는 노드.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태
    """
    company_name = state.get("company_name", "")
    if not company_name:
        return state

    try:
        client = get_foundry_client(settings)

        if not client.is_available:
            logger.debug("Palantir 연결 불가능, 건너뜀")
            state["palantir_data"] = None
            return state

        explorer = OntologyExplorer(client)

        logger.info(f"Palantir 기업 검색: {company_name}")
        company_data = await explorer.find_company(company_name)

        if company_data:
            state["palantir_data"] = company_data
            logger.info("Palantir 데이터 조회 성공")
        else:
            state["palantir_data"] = None
            logger.debug("Palantir에서 기업 정보를 찾을 수 없음")

    except Exception as e:
        logger.warning(f"Palantir 조회 실패: {e}")
        state["palantir_data"] = None

    return state


async def summarize_node(state: AgentState) -> AgentState:
    """수집된 정보를 요약하는 노드.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태
    """
    company_name = state.get("company_name", "")

    search_results = state.get("search_results", [])
    news_items = state.get("news_items", [])
    palantir_data = state.get("palantir_data")

    # 데이터가 없으면 기본 메시지 반환
    if not search_results and not news_items and not palantir_data:
        state["summary"] = f"{company_name}에 대한 정보를 수집할 수 없습니다."
        return state

    try:
        llm = LLMClient(settings)

        # SearchResult 객체를 딕셔너리로 변환
        search_dicts = [
            {"title": r.title, "snippet": r.snippet, "url": r.url}
            for r in search_results
        ] if search_results else []

        news_dicts = [
            {"title": n.title, "source": n.source, "summary": n.summary}
            for n in news_items
        ] if news_items else []

        logger.info("LLM 분석 시작")
        summary = await llm.analyze_company(
            company_name=company_name,
            search_results=search_dicts,
            news_items=news_dicts,
            palantir_data=palantir_data,
        )

        state["summary"] = summary
        logger.info("분석 완료")

    except Exception as e:
        logger.error(f"요약 생성 실패: {e}")
        state["summary"] = f"{company_name} 분석 중 오류가 발생했습니다: {e}"

    return state


def should_continue(state: AgentState) -> str:
    """에러 상태에 따라 다음 노드를 결정합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        다음 노드 이름
    """
    if state.get("error"):
        return "error_handler"
    return "continue"


async def error_handler_node(state: AgentState) -> AgentState:
    """에러를 처리하는 노드.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태
    """
    error = state.get("error", "알 수 없는 오류")
    company_name = state.get("company_name", "기업")

    logger.error(f"에러 처리: {error}")

    state["summary"] = (
        f"{company_name} 분석 중 오류가 발생했습니다.\n"
        f"원인: {error}\n\n"
        "검색 API 키를 확인하거나 나중에 다시 시도해주세요."
    )

    return state
