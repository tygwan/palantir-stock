"""엔티티 및 관계 추출기."""

import re
import uuid
from datetime import datetime

from src.graph.schema import (
    Company,
    Document,
    Event,
    Industry,
    Person,
    Relationship,
    RelationType,
)
from src.utils import LLMClient, get_logger

logger = get_logger("graph.extractor")


class EntityExtractor:
    """LLM 기반 엔티티/관계 추출기."""

    def __init__(self, llm_client: LLMClient | None = None):
        """추출기를 초기화합니다.

        Args:
            llm_client: LLM 클라이언트
        """
        self._llm = llm_client

    @property
    def llm(self) -> LLMClient:
        """LLM 클라이언트를 반환합니다."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    async def extract_entities(
        self,
        text: str,
        source_url: str | None = None,
    ) -> dict:
        """텍스트에서 엔티티를 추출합니다.

        Args:
            text: 분석할 텍스트
            source_url: 소스 URL

        Returns:
            추출된 엔티티 딕셔너리
        """
        system = """당신은 기업 정보 분석 전문가입니다.
주어진 텍스트에서 다음 엔티티를 추출해주세요:

1. 기업 (Company): 회사명, 티커, 산업
2. 인물 (Person): 이름, 직책, 소속
3. 이벤트 (Event): 유형, 날짜, 제목, 영향
4. 산업 (Industry): 산업명, 섹터

JSON 형식으로 응답해주세요."""

        prompt = f"""다음 텍스트에서 엔티티를 추출해주세요:

{text[:2000]}

JSON 형식:
{{
    "companies": [{{"name": "...", "ticker": "...", "industry": "..."}}],
    "people": [{{"name": "...", "role": "...", "company": "..."}}],
    "events": [{{"type": "...", "title": "...", "date": "...", "impact": "positive/negative/neutral"}}],
    "industries": [{{"name": "...", "sector": "..."}}]
}}"""

        try:
            response = await self.llm.generate(prompt, system=system)

            # JSON 파싱 시도
            import json

            # JSON 블록 추출
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
                return self._parse_entities(data, source_url)

        except Exception as e:
            logger.warning(f"엔티티 추출 실패: {e}")

        return {
            "companies": [],
            "people": [],
            "events": [],
            "industries": [],
            "documents": [],
        }

    def _parse_entities(self, data: dict, source_url: str | None) -> dict:
        """추출된 데이터를 파싱합니다."""
        result = {
            "companies": [],
            "people": [],
            "events": [],
            "industries": [],
            "documents": [],
        }

        # Companies
        for c in data.get("companies", []):
            if c.get("name"):
                result["companies"].append(
                    Company(
                        name=c["name"],
                        ticker=c.get("ticker"),
                        industry=c.get("industry"),
                    )
                )

        # People
        for p in data.get("people", []):
            if p.get("name"):
                result["people"].append(
                    Person(
                        name=p["name"],
                        role=p.get("role"),
                        company=p.get("company"),
                    )
                )

        # Events
        for e in data.get("events", []):
            if e.get("title"):
                result["events"].append(
                    Event(
                        id=str(uuid.uuid4()),
                        type=e.get("type", "news"),
                        title=e["title"],
                        date=self._parse_date(e.get("date")),
                        impact=e.get("impact"),
                        source=source_url,
                    )
                )

        # Industries
        for i in data.get("industries", []):
            if i.get("name"):
                result["industries"].append(
                    Industry(
                        name=i["name"],
                        sector=i.get("sector"),
                    )
                )

        return result

    def _parse_date(self, date_str: str | None) -> datetime:
        """날짜 문자열을 파싱합니다."""
        if not date_str:
            return datetime.now()

        try:
            # 다양한 날짜 형식 시도
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y년 %m월 %d일"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            return datetime.now()

        except Exception:
            return datetime.now()

    async def extract_relationships(
        self,
        entities: dict,
    ) -> list[Relationship]:
        """엔티티 간 관계를 추출합니다.

        Args:
            entities: 추출된 엔티티 딕셔너리

        Returns:
            관계 목록
        """
        relationships = []

        companies = entities.get("companies", [])
        people = entities.get("people", [])
        events = entities.get("events", [])
        industries = entities.get("industries", [])

        # Company → Industry
        for company in companies:
            if company.industry:
                # 매칭되는 산업 찾기
                for industry in industries:
                    if (
                        industry.name.lower() in company.industry.lower()
                        or company.industry.lower() in industry.name.lower()
                    ):
                        relationships.append(
                            Relationship(
                                type=RelationType.BELONGS_TO,
                                source_id=company.name,
                                target_id=industry.name,
                            )
                        )
                        break

        # Person → Company (LED_BY)
        for person in people:
            if person.company:
                for company in companies:
                    if company.name.lower() in person.company.lower():
                        relationships.append(
                            Relationship(
                                type=RelationType.LED_BY,
                                source_id=company.name,
                                target_id=person.name,
                            )
                        )
                        break

        # Company → Event (AFFECTED_BY)
        for event in events:
            for company in companies:
                # 간단한 휴리스틱: 모든 이벤트가 첫 번째 기업에 영향
                relationships.append(
                    Relationship(
                        type=RelationType.AFFECTED_BY,
                        source_id=company.name,
                        target_id=event.id,
                    )
                )
                break  # 첫 번째 기업에만 연결

        return relationships

    async def process_document(
        self,
        title: str,
        content: str,
        url: str | None = None,
        doc_type: str = "news",
    ) -> dict:
        """문서를 처리하여 엔티티와 관계를 추출합니다.

        Args:
            title: 문서 제목
            content: 문서 내용
            url: 문서 URL
            doc_type: 문서 유형

        Returns:
            추출 결과 (entities, relationships, document)
        """
        # 문서 노드 생성
        document = Document(
            id=str(uuid.uuid4()),
            type=doc_type,
            title=title,
            url=url,
            content=content[:1000] if content else None,  # 내용 일부만 저장
        )

        # 엔티티 추출
        full_text = f"{title}\n\n{content}" if content else title
        entities = await self.extract_entities(full_text, url)

        # 관계 추출
        relationships = await self.extract_relationships(entities)

        # 문서와 기업 연결
        for company in entities.get("companies", []):
            relationships.append(
                Relationship(
                    type=RelationType.MENTIONED_IN,
                    source_id=company.name,
                    target_id=document.id,
                )
            )

        entities["documents"] = [document]

        return {
            "entities": entities,
            "relationships": relationships,
            "document": document,
        }
