"""Neo4j 그래프 데이터베이스 클라이언트."""

from contextlib import asynccontextmanager
from functools import cached_property
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from config.settings import Settings
from src.utils.logging import get_logger

logger = get_logger("graph.client")


class Neo4jClient:
    """Neo4j 비동기 클라이언트."""

    def __init__(self, settings: Settings | None = None):
        """Neo4j 클라이언트를 초기화합니다.

        Args:
            settings: 애플리케이션 설정
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        self.settings = settings
        self._driver: AsyncDriver | None = None

    @property
    def is_available(self) -> bool:
        """Neo4j 연결이 가능한지 확인합니다."""
        return bool(
            self.settings.neo4j_uri
            and self.settings.neo4j_user
            and self.settings.neo4j_password
        )

    async def connect(self) -> AsyncDriver:
        """Neo4j에 연결합니다.

        Returns:
            AsyncDriver 인스턴스

        Raises:
            ValueError: 설정이 없는 경우
        """
        if not self.is_available:
            raise ValueError(
                "Neo4j 설정이 필요합니다. "
                "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD를 설정해주세요."
            )

        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
            logger.info(f"Neo4j 연결 완료: {self.settings.neo4j_uri}")

        return self._driver

    async def close(self) -> None:
        """연결을 종료합니다."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j 연결 종료")

    @asynccontextmanager
    async def session(self):
        """Neo4j 세션 컨텍스트 매니저."""
        driver = await self.connect()
        session = driver.session()
        try:
            yield session
        finally:
            await session.close()

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Cypher 쿼리를 실행합니다.

        Args:
            query: Cypher 쿼리
            parameters: 쿼리 파라미터

        Returns:
            쿼리 결과 목록
        """
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def test_connection(self) -> bool:
        """연결을 테스트합니다.

        Returns:
            연결 성공 여부
        """
        if not self.is_available:
            return False

        try:
            await self.execute_query("RETURN 1 AS test")
            logger.info("Neo4j 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"Neo4j 연결 테스트 실패: {e}")
            return False

    async def init_schema(self) -> None:
        """그래프 스키마를 초기화합니다 (인덱스 및 제약조건)."""
        constraints = [
            "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT industry_name IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX company_ticker IF NOT EXISTS FOR (c:Company) ON (c.ticker)",
            "CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.date)",
            "CREATE INDEX document_date IF NOT EXISTS FOR (d:Document) ON (d.date)",
        ]

        async with self.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug(f"제약조건 생성 스킵 (이미 존재): {e}")

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug(f"인덱스 생성 스킵 (이미 존재): {e}")

        logger.info("Neo4j 스키마 초기화 완료")


# 기본 클라이언트 인스턴스
_default_client: Neo4jClient | None = None


def get_neo4j_client(settings: Settings | None = None) -> Neo4jClient:
    """기본 Neo4j 클라이언트를 반환합니다.

    Args:
        settings: 애플리케이션 설정

    Returns:
        Neo4jClient 인스턴스
    """
    global _default_client

    if _default_client is None:
        _default_client = Neo4jClient(settings)

    return _default_client
