"""리포트 API 라우트."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from src.agents import CompanyInfoAgent
from src.api.schemas import ErrorResponse, ReportRequest, ReportResponse
from src.reports import ReportGenerator
from src.utils.logging import get_logger

logger = get_logger("api.reports")
router = APIRouter(prefix="/reports", tags=["리포트"])


@router.post(
    "/generate",
    response_model=ReportResponse,
    responses={500: {"model": ErrorResponse}},
    summary="리포트 생성",
    description="기업 분석 결과를 지정된 형식의 리포트로 생성합니다.",
)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """리포트를 생성합니다."""
    try:
        logger.info(f"리포트 생성 요청: {request.company_name} ({request.format})")

        # 기업 분석 수행
        agent = CompanyInfoAgent()
        report_data = await agent.analyze(request.company_name)

        # 리포트 생성
        generator = ReportGenerator()
        content = await generator.generate(report_data, format=request.format)

        return ReportResponse(
            company_name=request.company_name,
            format=request.format,
            content=content,
            generated_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"리포트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/view/{company_name}",
    response_class=HTMLResponse,
    summary="HTML 리포트 뷰",
    description="기업 분석 HTML 리포트를 웹 페이지로 조회합니다.",
)
async def view_report(company_name: str) -> HTMLResponse:
    """HTML 리포트를 조회합니다."""
    try:
        logger.info(f"HTML 리포트 조회: {company_name}")

        # 기업 분석 수행
        agent = CompanyInfoAgent()
        report_data = await agent.analyze(company_name)

        # HTML 리포트 생성
        generator = ReportGenerator()
        html_content = await generator.generate(report_data, format="html")

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"리포트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
