"""LLM 클라이언트 래퍼 모듈."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import Settings


class LLMClient:
    """OpenAI LLM 클라이언트 래퍼."""

    def __init__(self, settings: Settings | None = None):
        """LLM 클라이언트를 초기화합니다.

        Args:
            settings: 애플리케이션 설정. None이면 기본 설정 사용.
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        self.settings = settings
        self._model: ChatOpenAI | None = None

    @property
    def model(self) -> ChatOpenAI:
        """ChatOpenAI 모델 인스턴스를 반환합니다."""
        if self._model is None:
            self._model = ChatOpenAI(
                model=self.settings.openai_model,
                api_key=self.settings.openai_api_key,
                temperature=0.3,
            )
        return self._model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        """프롬프트에 대한 응답을 생성합니다.

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트 (선택)

        Returns:
            생성된 응답 텍스트
        """
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        response = await self.model.ainvoke(messages)
        return str(response.content)

    async def summarize(
        self,
        content: str,
        max_length: int = 500,
        language: str = "한국어",
    ) -> str:
        """콘텐츠를 요약합니다.

        Args:
            content: 요약할 콘텐츠
            max_length: 최대 글자 수
            language: 출력 언어

        Returns:
            요약된 텍스트
        """
        system = f"""당신은 기업 정보 분석 전문가입니다.
주어진 정보를 {language}로 명확하고 간결하게 요약해주세요.
최대 {max_length}자 이내로 작성하세요."""

        prompt = f"""다음 정보를 요약해주세요:

{content}

요약:"""

        return await self.generate(prompt, system=system)

    async def analyze_company(
        self,
        company_name: str,
        search_results: list[dict],
        news_items: list[dict],
        palantir_data: dict | None = None,
    ) -> str:
        """기업 정보를 종합 분석합니다.

        Args:
            company_name: 기업명
            search_results: 검색 결과 목록
            news_items: 뉴스 항목 목록
            palantir_data: Palantir에서 가져온 데이터

        Returns:
            종합 분석 리포트
        """
        system = """당신은 기업 분석 전문가입니다.
주어진 정보를 바탕으로 기업의 현황을 종합적으로 분석해주세요.
한국어로 3-5문단의 분석 리포트를 작성하세요."""

        # 컨텍스트 구성
        context_parts = []

        if search_results:
            search_text = "\n".join(
                f"- {r.get('title', '')}: {r.get('snippet', '')}"
                for r in search_results[:5]
            )
            context_parts.append(f"## 검색 결과\n{search_text}")

        if news_items:
            news_text = "\n".join(
                f"- [{n.get('source', '')}] {n.get('title', '')}"
                for n in news_items[:5]
            )
            context_parts.append(f"## 최신 뉴스\n{news_text}")

        if palantir_data:
            context_parts.append(f"## Palantir 데이터\n{palantir_data}")

        context = "\n\n".join(context_parts)

        prompt = f"""# {company_name} 기업 분석

{context}

위 정보를 바탕으로 {company_name}에 대한 종합 분석 리포트를 작성해주세요."""

        return await self.generate(prompt, system=system)
