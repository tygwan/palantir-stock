"""리포트 생성기."""

import json

from src.models.schemas import CompanyReport
from src.reports.templates import HTMLTemplate, MarkdownTemplate
from src.utils.logging import get_logger

logger = get_logger("reports.generator")


class ReportGenerator:
    """리포트 생성기."""

    def __init__(self):
        """리포트 생성기를 초기화합니다."""
        self._templates = {
            "html": HTMLTemplate(),
            "markdown": MarkdownTemplate(),
            "md": MarkdownTemplate(),
        }

    async def generate(
        self,
        report: CompanyReport,
        format: str = "html",
    ) -> str:
        """리포트를 생성합니다.

        Args:
            report: 기업 분석 리포트 데이터
            format: 출력 형식 (html, markdown, json)

        Returns:
            생성된 리포트 문자열
        """
        format_lower = format.lower()

        if format_lower == "json":
            return self._generate_json(report)

        template = self._templates.get(format_lower)
        if not template:
            logger.warning(f"지원하지 않는 형식: {format}, HTML로 대체")
            template = self._templates["html"]

        logger.info(f"리포트 생성: {report.company.name} ({format})")
        return template.render(report)

    def _generate_json(self, report: CompanyReport) -> str:
        """JSON 형식으로 리포트를 생성합니다."""
        data = {
            "company": {
                "name": report.company.name,
                "ticker": report.company.ticker,
                "industry": report.company.industry,
                "description": report.company.description,
                "market_cap": report.company.market_cap,
            },
            "summary": report.summary,
            "news": [
                {
                    "title": n.title,
                    "url": n.url,
                    "source": n.source,
                    "published_date": n.published_date.isoformat()
                    if n.published_date
                    else None,
                    "summary": n.summary,
                }
                for n in report.news
            ],
            "palantir_data": report.palantir_data,
            "sources": report.sources,
            "generated_at": report.generated_at.isoformat(),
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def get_supported_formats(self) -> list[str]:
        """지원하는 형식 목록을 반환합니다."""
        return ["html", "markdown", "json"]
