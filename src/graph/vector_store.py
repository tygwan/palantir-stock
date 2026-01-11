"""ChromaDB 벡터 저장소."""

import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import Settings
from src.utils.logging import get_logger

logger = get_logger("graph.vector_store")


class VectorStore:
    """ChromaDB 기반 벡터 저장소."""

    COLLECTION_NAME = "palantir_stock"

    def __init__(self, settings: Settings | None = None):
        """벡터 저장소를 초기화합니다.

        Args:
            settings: 애플리케이션 설정
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        self.settings = settings
        self._client: chromadb.Client | None = None
        self._collection = None

    @property
    def client(self) -> chromadb.Client:
        """ChromaDB 클라이언트를 반환합니다."""
        if self._client is None:
            persist_dir = Path(self.settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
            logger.info(f"ChromaDB 초기화: {persist_dir}")

        return self._client

    @property
    def collection(self):
        """기본 컬렉션을 반환합니다."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Palantir Stock 문서 임베딩"},
            )
            logger.debug(f"컬렉션 로드: {self.COLLECTION_NAME}")

        return self._collection

    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        """문서를 벡터 저장소에 추가합니다.

        Args:
            document_id: 문서 ID
            content: 문서 내용
            metadata: 메타데이터

        Returns:
            임베딩 ID
        """
        embedding_id = document_id or str(uuid.uuid4())

        self.collection.add(
            ids=[embedding_id],
            documents=[content],
            metadatas=[metadata or {}],
        )

        logger.debug(f"문서 임베딩 추가: {embedding_id}")
        return embedding_id

    async def add_documents(
        self,
        documents: list[dict],
    ) -> list[str]:
        """여러 문서를 벡터 저장소에 추가합니다.

        Args:
            documents: 문서 목록 [{"id": ..., "content": ..., "metadata": ...}]

        Returns:
            임베딩 ID 목록
        """
        if not documents:
            return []

        ids = [d.get("id", str(uuid.uuid4())) for d in documents]
        contents = [d["content"] for d in documents]
        metadatas = [d.get("metadata", {}) for d in documents]

        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas,
        )

        logger.info(f"문서 {len(documents)}개 임베딩 추가")
        return ids

    async def search(
        self,
        query: str,
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[dict]:
        """쿼리로 유사 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            n_results: 결과 수
            where: 필터 조건

        Returns:
            검색 결과 목록
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

        # 결과 포맷팅
        documents = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            documents.append({
                "id": doc_id,
                "content": docs[i] if i < len(docs) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 0,
            })

        logger.debug(f"벡터 검색 결과: {len(documents)}개")
        return documents

    async def search_by_company(
        self,
        query: str,
        company_name: str,
        n_results: int = 10,
    ) -> list[dict]:
        """기업 필터로 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            company_name: 기업명
            n_results: 결과 수

        Returns:
            검색 결과 목록
        """
        return await self.search(
            query=query,
            n_results=n_results,
            where={"company": company_name},
        )

    async def delete_document(self, document_id: str) -> None:
        """문서를 삭제합니다.

        Args:
            document_id: 문서 ID
        """
        self.collection.delete(ids=[document_id])
        logger.debug(f"문서 임베딩 삭제: {document_id}")

    async def get_stats(self) -> dict:
        """저장소 통계를 반환합니다."""
        count = self.collection.count()
        return {
            "collection": self.COLLECTION_NAME,
            "document_count": count,
        }
