"""하이브리드 검색기 (Vector + Graph)."""

from dataclasses import dataclass

from src.graph.client import Neo4jClient, get_neo4j_client
from src.graph.repository import GraphRepository
from src.graph.vector_store import VectorStore
from src.utils.logging import get_logger

logger = get_logger("graph.hybrid")


@dataclass
class HybridResult:
    """하이브리드 검색 결과."""

    id: str
    content: str
    source: str  # "vector" | "graph"
    score: float
    metadata: dict


class HybridRetriever:
    """Vector + Graph 하이브리드 검색기."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        graph_repo: GraphRepository | None = None,
        vector_weight: float = 0.5,
    ):
        """하이브리드 검색기를 초기화합니다.

        Args:
            vector_store: 벡터 저장소
            graph_repo: 그래프 저장소
            vector_weight: 벡터 검색 가중치 (0-1)
        """
        self._vector_store = vector_store
        self._graph_repo = graph_repo
        self.vector_weight = vector_weight
        self.graph_weight = 1 - vector_weight

    @property
    def vector_store(self) -> VectorStore:
        """벡터 저장소를 반환합니다."""
        if self._vector_store is None:
            self._vector_store = VectorStore()
        return self._vector_store

    @property
    def graph_repo(self) -> GraphRepository:
        """그래프 저장소를 반환합니다."""
        if self._graph_repo is None:
            self._graph_repo = GraphRepository()
        return self._graph_repo

    async def search(
        self,
        query: str,
        company_name: str | None = None,
        n_results: int = 10,
    ) -> list[HybridResult]:
        """하이브리드 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            company_name: 기업명 (선택)
            n_results: 결과 수

        Returns:
            하이브리드 검색 결과
        """
        results = []

        # 1. 벡터 검색
        try:
            if company_name:
                vector_results = await self.vector_store.search_by_company(
                    query=query,
                    company_name=company_name,
                    n_results=n_results,
                )
            else:
                vector_results = await self.vector_store.search(
                    query=query,
                    n_results=n_results,
                )

            for vr in vector_results:
                # 거리를 점수로 변환 (거리가 작을수록 높은 점수)
                score = 1 / (1 + vr.get("distance", 0))
                results.append(
                    HybridResult(
                        id=vr["id"],
                        content=vr.get("content", ""),
                        source="vector",
                        score=score * self.vector_weight,
                        metadata=vr.get("metadata", {}),
                    )
                )
        except Exception as e:
            logger.warning(f"벡터 검색 실패: {e}")

        # 2. 그래프 검색
        try:
            if self.graph_repo.is_available:
                graph_results = await self._search_graph(query, company_name, n_results)
                results.extend(graph_results)
        except Exception as e:
            logger.warning(f"그래프 검색 실패: {e}")

        # 3. 결과 병합 및 정렬
        merged = self._merge_results(results)

        # 점수 기준 정렬
        merged.sort(key=lambda x: x.score, reverse=True)

        return merged[:n_results]

    async def _search_graph(
        self,
        query: str,
        company_name: str | None,
        n_results: int,
    ) -> list[HybridResult]:
        """그래프에서 검색합니다."""
        results = []

        if company_name:
            # 기업 관련 문서 조회
            documents = await self.graph_repo.get_company_documents(
                company_name=company_name,
                limit=n_results,
            )

            for doc in documents:
                results.append(
                    HybridResult(
                        id=doc.id or "",
                        content=doc.title,
                        source="graph",
                        score=self.graph_weight,
                        metadata={
                            "type": doc.type,
                            "url": doc.url,
                            "date": doc.date.isoformat() if doc.date else None,
                        },
                    )
                )

            # 관련 이벤트 조회
            events = await self.graph_repo.get_company_events(
                company_name=company_name,
                limit=n_results // 2,
            )

            for event in events:
                results.append(
                    HybridResult(
                        id=event.id,
                        content=event.title,
                        source="graph",
                        score=self.graph_weight * 0.8,  # 이벤트는 약간 낮은 가중치
                        metadata={
                            "type": event.type,
                            "impact": event.impact,
                            "date": event.date.isoformat() if event.date else None,
                        },
                    )
                )

        else:
            # 텍스트 검색
            graph_results = await self.graph_repo.search_by_text(
                text=query,
                limit=n_results,
            )

            for gr in graph_results:
                node = gr["node"]
                results.append(
                    HybridResult(
                        id=node.get("name", node.get("id", "")),
                        content=node.get("description", node.get("name", "")),
                        source="graph",
                        score=self.graph_weight,
                        metadata={
                            "labels": gr["labels"],
                            **node,
                        },
                    )
                )

        return results

    def _merge_results(
        self,
        results: list[HybridResult],
    ) -> list[HybridResult]:
        """결과를 병합합니다 (중복 제거 및 점수 합산)."""
        merged: dict[str, HybridResult] = {}

        for result in results:
            key = result.id

            if key in merged:
                # 점수 합산
                merged[key].score += result.score
                # 소스 표시 업데이트
                if merged[key].source != result.source:
                    merged[key].source = "hybrid"
            else:
                merged[key] = result

        return list(merged.values())

    async def get_context_for_query(
        self,
        query: str,
        company_name: str | None = None,
        max_context_length: int = 4000,
    ) -> str:
        """쿼리에 대한 컨텍스트를 생성합니다.

        Args:
            query: 검색 쿼리
            company_name: 기업명
            max_context_length: 최대 컨텍스트 길이

        Returns:
            LLM에 전달할 컨텍스트 문자열
        """
        results = await self.search(
            query=query,
            company_name=company_name,
            n_results=10,
        )

        context_parts = []
        current_length = 0

        for result in results:
            content = f"[{result.source}] {result.content}"

            if current_length + len(content) > max_context_length:
                break

            context_parts.append(content)
            current_length += len(content)

        context = "\n\n".join(context_parts)

        logger.debug(f"컨텍스트 생성: {len(context)}자, {len(context_parts)}개 소스")
        return context
