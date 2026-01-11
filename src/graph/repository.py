"""그래프 저장소 - 노드/관계 CRUD 작업."""

from datetime import datetime
from typing import Any
import uuid

from src.graph.client import Neo4jClient, get_neo4j_client
from src.graph.schema import (
    Company,
    Document,
    Event,
    Industry,
    NodeType,
    Person,
    Relationship,
    RelationType,
)
from src.utils.logging import get_logger

logger = get_logger("graph.repository")


class GraphRepository:
    """그래프 데이터 저장소."""

    def __init__(self, client: Neo4jClient | None = None):
        """저장소를 초기화합니다.

        Args:
            client: Neo4j 클라이언트
        """
        self._client = client or get_neo4j_client()

    @property
    def is_available(self) -> bool:
        """저장소 사용 가능 여부."""
        return self._client.is_available

    # ==================== Company ====================

    async def create_company(self, company: Company) -> Company:
        """기업 노드를 생성합니다."""
        props = company.to_cypher_properties()

        query = """
        MERGE (c:Company {name: $name})
        SET c += $props
        RETURN c
        """

        await self._client.execute_query(
            query,
            {"name": company.name, "props": props},
        )

        logger.debug(f"기업 생성: {company.name}")
        return company

    async def get_company(self, name: str) -> Company | None:
        """기업을 조회합니다."""
        query = """
        MATCH (c:Company {name: $name})
        RETURN c
        """

        result = await self._client.execute_query(query, {"name": name})

        if result:
            data = result[0]["c"]
            return Company(**data)
        return None

    async def find_companies(
        self,
        industry: str | None = None,
        limit: int = 10,
    ) -> list[Company]:
        """기업 목록을 조회합니다."""
        if industry:
            query = """
            MATCH (c:Company)-[:BELONGS_TO]->(i:Industry {name: $industry})
            RETURN c
            LIMIT $limit
            """
            params = {"industry": industry, "limit": limit}
        else:
            query = """
            MATCH (c:Company)
            RETURN c
            LIMIT $limit
            """
            params = {"limit": limit}

        result = await self._client.execute_query(query, params)
        return [Company(**r["c"]) for r in result]

    async def get_competitors(self, company_name: str) -> list[Company]:
        """경쟁사를 조회합니다."""
        query = """
        MATCH (c:Company {name: $name})-[:COMPETES_WITH]-(competitor:Company)
        RETURN DISTINCT competitor
        """

        result = await self._client.execute_query(query, {"name": company_name})
        return [Company(**r["competitor"]) for r in result]

    # ==================== Industry ====================

    async def create_industry(self, industry: Industry) -> Industry:
        """산업 노드를 생성합니다."""
        props = industry.to_cypher_properties()

        query = """
        MERGE (i:Industry {name: $name})
        SET i += $props
        RETURN i
        """

        await self._client.execute_query(
            query,
            {"name": industry.name, "props": props},
        )

        logger.debug(f"산업 생성: {industry.name}")
        return industry

    # ==================== Event ====================

    async def create_event(self, event: Event) -> Event:
        """이벤트 노드를 생성합니다."""
        if not event.id:
            event.id = str(uuid.uuid4())

        props = event.to_cypher_properties()
        # datetime을 문자열로 변환
        if "date" in props and isinstance(props["date"], datetime):
            props["date"] = props["date"].isoformat()

        query = """
        MERGE (e:Event {id: $id})
        SET e += $props
        RETURN e
        """

        await self._client.execute_query(
            query,
            {"id": event.id, "props": props},
        )

        logger.debug(f"이벤트 생성: {event.title}")
        return event

    async def get_company_events(
        self,
        company_name: str,
        limit: int = 10,
    ) -> list[Event]:
        """기업 관련 이벤트를 조회합니다."""
        query = """
        MATCH (c:Company {name: $name})-[:AFFECTED_BY]->(e:Event)
        RETURN e
        ORDER BY e.date DESC
        LIMIT $limit
        """

        result = await self._client.execute_query(
            query,
            {"name": company_name, "limit": limit},
        )
        return [Event(**r["e"]) for r in result]

    # ==================== Person ====================

    async def create_person(self, person: Person) -> Person:
        """인물 노드를 생성합니다."""
        props = person.to_cypher_properties()

        query = """
        MERGE (p:Person {name: $name})
        SET p += $props
        RETURN p
        """

        await self._client.execute_query(
            query,
            {"name": person.name, "props": props},
        )

        logger.debug(f"인물 생성: {person.name}")
        return person

    async def get_company_leaders(self, company_name: str) -> list[Person]:
        """기업 경영진을 조회합니다."""
        query = """
        MATCH (c:Company {name: $name})-[:LED_BY]->(p:Person)
        RETURN p
        """

        result = await self._client.execute_query(query, {"name": company_name})
        return [Person(**r["p"]) for r in result]

    # ==================== Document ====================

    async def create_document(self, document: Document) -> Document:
        """문서 노드를 생성합니다."""
        if not document.id:
            document.id = str(uuid.uuid4())

        props = document.to_cypher_properties()
        if "date" in props and isinstance(props["date"], datetime):
            props["date"] = props["date"].isoformat()

        query = """
        MERGE (d:Document {id: $id})
        SET d += $props
        RETURN d
        """

        await self._client.execute_query(
            query,
            {"id": document.id, "props": props},
        )

        logger.debug(f"문서 생성: {document.title}")
        return document

    async def get_company_documents(
        self,
        company_name: str,
        doc_type: str | None = None,
        limit: int = 10,
    ) -> list[Document]:
        """기업 관련 문서를 조회합니다."""
        if doc_type:
            query = """
            MATCH (c:Company {name: $name})-[:MENTIONED_IN]->(d:Document {type: $type})
            RETURN d
            ORDER BY d.date DESC
            LIMIT $limit
            """
            params = {"name": company_name, "type": doc_type, "limit": limit}
        else:
            query = """
            MATCH (c:Company {name: $name})-[:MENTIONED_IN]->(d:Document)
            RETURN d
            ORDER BY d.date DESC
            LIMIT $limit
            """
            params = {"name": company_name, "limit": limit}

        result = await self._client.execute_query(query, params)
        return [Document(**r["d"]) for r in result]

    # ==================== Relationships ====================

    async def create_relationship(self, rel: Relationship) -> None:
        """관계를 생성합니다."""
        # 동적 관계 타입 지원
        query = f"""
        MATCH (a {{name: $source_id}})
        MATCH (b {{name: $target_id}})
        MERGE (a)-[r:{rel.type.value}]->(b)
        SET r += $props
        """

        await self._client.execute_query(
            query,
            {
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "props": rel.to_cypher_properties(),
            },
        )

        logger.debug(f"관계 생성: {rel.source_id} -[{rel.type.value}]-> {rel.target_id}")

    async def link_company_to_industry(
        self,
        company_name: str,
        industry_name: str,
    ) -> None:
        """기업을 산업에 연결합니다."""
        rel = Relationship(
            type=RelationType.BELONGS_TO,
            source_id=company_name,
            target_id=industry_name,
        )
        await self.create_relationship(rel)

    async def link_companies_as_competitors(
        self,
        company1: str,
        company2: str,
    ) -> None:
        """두 기업을 경쟁사로 연결합니다."""
        rel = Relationship(
            type=RelationType.COMPETES_WITH,
            source_id=company1,
            target_id=company2,
        )
        await self.create_relationship(rel)

    async def link_company_to_event(
        self,
        company_name: str,
        event_id: str,
    ) -> None:
        """기업을 이벤트에 연결합니다."""
        query = """
        MATCH (c:Company {name: $company_name})
        MATCH (e:Event {id: $event_id})
        MERGE (c)-[:AFFECTED_BY]->(e)
        """
        await self._client.execute_query(
            query,
            {"company_name": company_name, "event_id": event_id},
        )

    async def link_company_to_document(
        self,
        company_name: str,
        document_id: str,
    ) -> None:
        """기업을 문서에 연결합니다."""
        query = """
        MATCH (c:Company {name: $company_name})
        MATCH (d:Document {id: $document_id})
        MERGE (c)-[:MENTIONED_IN]->(d)
        """
        await self._client.execute_query(
            query,
            {"company_name": company_name, "document_id": document_id},
        )

    # ==================== Graph Queries ====================

    async def get_company_graph(
        self,
        company_name: str,
        depth: int = 2,
    ) -> dict:
        """기업 중심 그래프를 조회합니다."""
        query = """
        MATCH path = (c:Company {name: $name})-[*1..$depth]-(related)
        RETURN path
        LIMIT 100
        """

        result = await self._client.execute_query(
            query,
            {"name": company_name, "depth": depth},
        )

        # 노드와 관계 추출
        nodes = set()
        relationships = []

        for record in result:
            path = record.get("path", {})
            # 경로에서 노드와 관계 추출 로직
            # (실제 구현은 neo4j 드라이버 버전에 따라 다름)

        return {
            "nodes": list(nodes),
            "relationships": relationships,
        }

    async def search_by_text(
        self,
        text: str,
        node_types: list[NodeType] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """텍스트로 노드를 검색합니다."""
        if node_types:
            labels = ":".join(t.value for t in node_types)
            query = f"""
            MATCH (n:{labels})
            WHERE n.name CONTAINS $text OR n.description CONTAINS $text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
        else:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS $text OR n.description CONTAINS $text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """

        result = await self._client.execute_query(
            query,
            {"text": text, "limit": limit},
        )

        return [{"node": r["n"], "labels": r["labels"]} for r in result]
