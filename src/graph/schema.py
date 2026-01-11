"""지식 그래프 스키마 정의."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """노드 타입."""

    COMPANY = "Company"
    INDUSTRY = "Industry"
    EVENT = "Event"
    PERSON = "Person"
    DOCUMENT = "Document"


class RelationType(str, Enum):
    """관계 타입."""

    BELONGS_TO = "BELONGS_TO"        # Company → Industry
    COMPETES_WITH = "COMPETES_WITH"  # Company → Company
    AFFECTED_BY = "AFFECTED_BY"      # Company → Event
    LED_BY = "LED_BY"                # Company → Person
    MENTIONED_IN = "MENTIONED_IN"    # Company → Document
    WORKS_AT = "WORKS_AT"            # Person → Company
    RELATED_TO = "RELATED_TO"        # 일반 관계


class BaseNode(BaseModel):
    """노드 기본 클래스."""

    id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    properties: dict[str, Any] = Field(default_factory=dict)

    def to_cypher_properties(self) -> dict:
        """Cypher 쿼리용 프로퍼티 딕셔너리를 반환합니다."""
        props = self.model_dump(exclude={"properties"})
        props.update(self.properties)
        # None 값 제거
        return {k: v for k, v in props.items() if v is not None}


class Company(BaseNode):
    """기업 노드."""

    name: str = Field(..., description="기업명")
    ticker: str | None = Field(default=None, description="주식 티커")
    industry: str | None = Field(default=None, description="산업 분류")
    market_cap: str | None = Field(default=None, description="시가총액")
    description: str | None = Field(default=None, description="기업 설명")
    country: str | None = Field(default=None, description="국가")
    website: str | None = Field(default=None, description="웹사이트")


class Industry(BaseNode):
    """산업 노드."""

    name: str = Field(..., description="산업명")
    sector: str | None = Field(default=None, description="섹터")
    description: str | None = Field(default=None, description="설명")


class Event(BaseNode):
    """이벤트 노드."""

    id: str = Field(..., description="이벤트 ID")
    type: str = Field(..., description="이벤트 유형")
    title: str = Field(..., description="이벤트 제목")
    date: datetime = Field(..., description="이벤트 날짜")
    description: str | None = Field(default=None, description="설명")
    impact: str | None = Field(default=None, description="영향도 (positive/negative/neutral)")
    source: str | None = Field(default=None, description="출처")


class Person(BaseNode):
    """인물 노드."""

    name: str = Field(..., description="이름")
    role: str | None = Field(default=None, description="직책")
    company: str | None = Field(default=None, description="소속 기업")
    description: str | None = Field(default=None, description="설명")


class Document(BaseNode):
    """문서 노드."""

    id: str = Field(..., description="문서 ID")
    type: str = Field(..., description="문서 유형 (news/report/filing)")
    title: str = Field(..., description="제목")
    url: str | None = Field(default=None, description="URL")
    date: datetime = Field(default_factory=datetime.now, description="게시일")
    source: str | None = Field(default=None, description="출처")
    content: str | None = Field(default=None, description="내용")
    embedding_id: str | None = Field(default=None, description="벡터 임베딩 ID")


class Relationship(BaseModel):
    """관계 모델."""

    type: RelationType = Field(..., description="관계 유형")
    source_id: str = Field(..., description="소스 노드 ID")
    target_id: str = Field(..., description="타겟 노드 ID")
    properties: dict[str, Any] = Field(default_factory=dict, description="관계 속성")

    def to_cypher_properties(self) -> dict:
        """Cypher 쿼리용 프로퍼티 딕셔너리를 반환합니다."""
        return {k: v for k, v in self.properties.items() if v is not None}
