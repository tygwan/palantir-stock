"""Graph RAG API 라우트."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import ErrorResponse, GraphSearchRequest
from src.graph import HybridRetriever, Neo4jClient
from src.utils.logging import get_logger

logger = get_logger("api.graph")
router = APIRouter(prefix="/graph", tags=["그래프"])


@router.post(
    "/search",
    response_model=list[dict],
    responses={500: {"model": ErrorResponse}},
    summary="Graph RAG 검색",
    description="지식 그래프와 벡터 검색을 결합한 하이브리드 검색을 수행합니다.",
)
async def search_graph(request: GraphSearchRequest) -> list[dict]:
    """Graph RAG 검색을 수행합니다."""
    try:
        logger.info(f"Graph 검색 요청: {request.query}")
        retriever = HybridRetriever()
        results = await retriever.search(
            query=request.query,
            company_name=request.company_name,
            n_results=request.limit,
        )

        return [
            {
                "content": r.content,
                "source": r.source,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"Graph 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=dict,
    responses={500: {"model": ErrorResponse}},
    summary="그래프 통계",
    description="지식 그래프의 노드 및 관계 통계를 조회합니다.",
)
async def get_graph_stats() -> dict:
    """그래프 통계를 조회합니다."""
    try:
        logger.info("그래프 통계 조회")
        client = Neo4jClient()
        await client.connect()

        try:
            # 노드 카운트
            node_counts = {}
            for label in ["Company", "Industry", "Event", "Person", "Document"]:
                result = await client.execute_query(
                    f"MATCH (n:{label}) RETURN count(n) as count"
                )
                records = [r async for r in result]
                node_counts[label.lower()] = records[0]["count"] if records else 0

            # 관계 카운트
            rel_result = await client.execute_query(
                "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count"
            )
            rel_counts = {}
            async for record in rel_result:
                rel_counts[record["type"]] = record["count"]

            return {
                "nodes": node_counts,
                "relationships": rel_counts,
                "total_nodes": sum(node_counts.values()),
                "total_relationships": sum(rel_counts.values()),
            }
        finally:
            await client.close()

    except Exception as e:
        logger.error(f"그래프 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/init",
    response_model=dict,
    responses={500: {"model": ErrorResponse}},
    summary="그래프 스키마 초기화",
    description="Neo4j 그래프 데이터베이스의 스키마(인덱스, 제약조건)를 초기화합니다.",
)
async def init_graph_schema() -> dict:
    """그래프 스키마를 초기화합니다."""
    try:
        logger.info("그래프 스키마 초기화")
        client = Neo4jClient()
        await client.connect()

        try:
            await client.init_schema()
            return {"status": "success", "message": "그래프 스키마가 초기화되었습니다"}
        finally:
            await client.close()

    except Exception as e:
        logger.error(f"그래프 스키마 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
