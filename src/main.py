"""Palantir Stock CLI 엔트리포인트."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings
from src.utils.logging import setup_logging

app = typer.Typer(
    name="ps",
    help="Palantir Stock - 웹 검색 + Palantir 기반 기업 정보 수집 에이전트",
    add_completion=False,
)
console = Console()


def validate_config() -> bool:
    """설정을 검증합니다."""
    errors = []

    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY가 설정되지 않았습니다")

    if not settings.serpapi_key and not settings.tavily_api_key:
        errors.append("SERPAPI_KEY 또는 TAVILY_API_KEY가 필요합니다")

    if errors:
        console.print("[red bold]설정 오류:[/red bold]")
        for error in errors:
            console.print(f"  [red]• {error}[/red]")
        return False

    return True


@app.command()
def analyze(
    company: str = typer.Argument(..., help="분석할 기업명"),
    output: str = typer.Option("text", "--output", "-o", help="출력 형식 (text/json)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="상세 출력"),
):
    """기업 정보를 수집하고 분석합니다."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")

    if not validate_config():
        raise typer.Exit(1)

    from src.agents import CompanyInfoAgent

    async def run():
        agent = CompanyInfoAgent(settings)
        return await agent.analyze(company)

    with console.status(f"[bold blue]{company} 정보 수집 중...[/bold blue]"):
        report = asyncio.run(run())

    if output == "json":
        console.print_json(report.model_dump_json(indent=2))
    else:
        _display_report(report)


@app.command()
def news(
    query: str = typer.Argument(..., help="뉴스 검색어"),
    limit: int = typer.Option(5, "--limit", "-n", help="결과 수"),
):
    """최신 뉴스를 검색합니다."""
    setup_logging("WARNING")

    if not validate_config():
        raise typer.Exit(1)

    from src.agents import CompanyInfoAgent

    async def run():
        agent = CompanyInfoAgent(settings)
        return await agent.quick_news(query)

    with console.status(f"[bold blue]'{query}' 뉴스 검색 중...[/bold blue]"):
        results = asyncio.run(run())

    if not results:
        console.print("[yellow]검색 결과가 없습니다.[/yellow]")
        return

    table = Table(title=f"'{query}' 관련 뉴스")
    table.add_column("제목", style="cyan", max_width=50)
    table.add_column("출처", style="green")
    table.add_column("URL", style="dim")

    for r in results[:limit]:
        table.add_row(
            r.get("title", "")[:50],
            r.get("source", "-"),
            r.get("url", "")[:40] + "...",
        )

    console.print(table)


@app.command()
def ontology():
    """Palantir 온톨로지를 탐색합니다."""
    setup_logging("INFO")

    from src.palantir import OntologyExplorer, get_foundry_client

    client = get_foundry_client(settings)

    if not client.is_available:
        console.print("[yellow]Palantir 설정이 필요합니다.[/yellow]")
        console.print("FOUNDRY_TOKEN과 FOUNDRY_HOST를 설정해주세요.")
        raise typer.Exit(1)

    async def run():
        explorer = OntologyExplorer(client)
        return await explorer.list_object_types()

    with console.status("[bold blue]온톨로지 조회 중...[/bold blue]"):
        try:
            object_types = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]온톨로지 조회 실패: {e}[/red]")
            raise typer.Exit(1)

    if not object_types:
        console.print("[yellow]조회된 객체 타입이 없습니다.[/yellow]")
        console.print("Foundry 권한을 확인해주세요.")
        return

    table = Table(title="Palantir 온톨로지 객체 타입")
    table.add_column("API Name", style="cyan")
    table.add_column("Display Name", style="green")
    table.add_column("Description")

    for ot in object_types:
        table.add_row(ot.api_name, ot.display_name, ot.description or "-")

    console.print(table)


@app.command()
def datasets():
    """Palantir 데이터셋 목록을 조회합니다."""
    setup_logging("INFO")

    from src.palantir import DatasetManager, get_foundry_client

    client = get_foundry_client(settings)

    if not client.is_available:
        console.print("[yellow]Palantir 설정이 필요합니다.[/yellow]")
        console.print("FOUNDRY_TOKEN과 FOUNDRY_HOST를 설정해주세요.")
        raise typer.Exit(1)

    async def run():
        manager = DatasetManager(client)
        return await manager.list_datasets()

    with console.status("[bold blue]데이터셋 조회 중...[/bold blue]"):
        try:
            ds_list = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]데이터셋 조회 실패: {e}[/red]")
            raise typer.Exit(1)

    if not ds_list:
        console.print("[yellow]조회된 데이터셋이 없습니다.[/yellow]")
        return

    table = Table(title="Palantir 데이터셋")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("RID", style="dim")

    for ds in ds_list:
        table.add_row(ds.name, ds.path, ds.rid)

    console.print(table)


@app.command("stock")
def stock_analyze(
    ticker: str = typer.Argument(..., help="티커 또는 기업명 (예: 삼성전자, AAPL)"),
    period: str = typer.Option("3mo", "--period", "-p", help="분석 기간"),
):
    """주식 정보를 조회하고 분석합니다."""
    setup_logging("WARNING")

    from src.stock import get_stock_client

    async def run():
        client = get_stock_client(settings)
        return await client.analyze(ticker, period=period)

    with console.status(f"[bold blue]{ticker} 주식 분석 중...[/bold blue]"):
        try:
            analysis = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]주식 분석 실패: {e}[/red]")
            raise typer.Exit(1)

    if not analysis:
        console.print(f"[yellow]'{ticker}' 주식 정보를 찾을 수 없습니다.[/yellow]")
        return

    # 기본 정보
    console.print()
    console.print(Panel(
        f"[bold]{analysis.info.name}[/bold] ({analysis.info.ticker})\n"
        f"현재가: {analysis.current_price:,.0f} {analysis.info.currency} "
        f"({'[green]+' if analysis.change_percent > 0 else '[red]'}{analysis.change_percent:+.2f}%[/])\n"
        f"추천: [bold]{analysis.recommendation}[/bold]",
        title="주식 분석",
        border_style="blue",
    ))

    # 기술적 지표
    if analysis.indicators:
        table = Table(title="기술적 지표")
        table.add_column("지표", style="cyan")
        table.add_column("값", style="green")
        table.add_column("신호")
        table.add_column("설명")

        for ind in analysis.indicators:
            signal_color = {
                "buy": "[green]매수[/green]",
                "sell": "[red]매도[/red]",
                "neutral": "[yellow]중립[/yellow]",
            }.get(ind.signal, ind.signal)

            table.add_row(
                ind.name,
                str(ind.value),
                signal_color,
                ind.description or "",
            )

        console.print()
        console.print(table)

    # 기업 정보
    if analysis.info.sector:
        console.print()
        console.print(f"[dim]섹터: {analysis.info.sector} | 산업: {analysis.info.industry}[/dim]")


@app.command("stock-price")
def stock_price(
    ticker: str = typer.Argument(..., help="티커 또는 기업명"),
    period: str = typer.Option("1mo", "--period", "-p", help="조회 기간"),
):
    """주가 히스토리를 조회합니다."""
    setup_logging("WARNING")

    from src.stock import get_stock_client

    async def run():
        client = get_stock_client(settings)
        return await client.get_prices(ticker, period=period)

    with console.status(f"[bold blue]{ticker} 주가 조회 중...[/bold blue]"):
        try:
            prices = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]주가 조회 실패: {e}[/red]")
            raise typer.Exit(1)

    if not prices:
        console.print(f"[yellow]'{ticker}' 주가 데이터를 찾을 수 없습니다.[/yellow]")
        return

    table = Table(title=f"{ticker} 주가 ({period})")
    table.add_column("날짜", style="cyan")
    table.add_column("시가", justify="right")
    table.add_column("고가", justify="right", style="green")
    table.add_column("저가", justify="right", style="red")
    table.add_column("종가", justify="right", style="bold")
    table.add_column("거래량", justify="right")

    # 최근 10일만 표시
    for p in prices[-10:]:
        table.add_row(
            p.date.strftime("%Y-%m-%d"),
            f"{p.open:,.0f}",
            f"{p.high:,.0f}",
            f"{p.low:,.0f}",
            f"{p.close:,.0f}",
            f"{p.volume:,}",
        )

    console.print(table)
    console.print(f"[dim]총 {len(prices)}일 데이터[/dim]")


@app.command("graph-init")
def graph_init():
    """Graph DB 스키마를 초기화합니다."""
    setup_logging("INFO")

    from src.graph import get_neo4j_client

    client = get_neo4j_client(settings)

    if not client.is_available:
        console.print("[yellow]Neo4j 설정이 필요합니다.[/yellow]")
        console.print("NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD를 설정해주세요.")
        raise typer.Exit(1)

    async def run():
        await client.init_schema()
        return await client.test_connection()

    with console.status("[bold blue]Graph DB 초기화 중...[/bold blue]"):
        try:
            success = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]Graph DB 초기화 실패: {e}[/red]")
            raise typer.Exit(1)

    if success:
        console.print("[green]✓ Graph DB 스키마 초기화 완료[/green]")
    else:
        console.print("[red]✗ Graph DB 연결 실패[/red]")


@app.command("graph-stats")
def graph_stats():
    """Graph DB 및 벡터 저장소 통계를 확인합니다."""
    setup_logging("WARNING")

    table = Table(title="Graph RAG 저장소 상태")
    table.add_column("저장소", style="cyan")
    table.add_column("상태", style="green")
    table.add_column("통계")

    # Neo4j 상태
    from src.graph import get_neo4j_client
    client = get_neo4j_client(settings)

    if client.is_available:
        try:
            async def check_neo4j():
                return await client.test_connection()
            connected = asyncio.run(check_neo4j())
            table.add_row(
                "Neo4j",
                "[green]연결됨[/green]" if connected else "[red]연결 실패[/red]",
                settings.neo4j_uri,
            )
        except Exception:
            table.add_row("Neo4j", "[red]오류[/red]", "-")
    else:
        table.add_row("Neo4j", "[yellow]미설정[/yellow]", "-")

    # ChromaDB 상태
    try:
        from src.graph import VectorStore
        vs = VectorStore(settings)

        async def check_vector():
            return await vs.get_stats()
        stats = asyncio.run(check_vector())
        table.add_row(
            "ChromaDB",
            "[green]사용 가능[/green]",
            f"{stats['document_count']}개 문서",
        )
    except Exception as e:
        table.add_row("ChromaDB", "[yellow]초기화 필요[/yellow]", str(e)[:30])

    console.print(table)


@app.command("graph-search")
def graph_search(
    query: str = typer.Argument(..., help="검색 쿼리"),
    company: str = typer.Option(None, "--company", "-c", help="기업명 필터"),
    limit: int = typer.Option(10, "--limit", "-n", help="결과 수"),
):
    """하이브리드 검색 (Vector + Graph)을 수행합니다."""
    setup_logging("WARNING")

    from src.graph import HybridRetriever

    async def run():
        retriever = HybridRetriever()
        return await retriever.search(
            query=query,
            company_name=company,
            n_results=limit,
        )

    with console.status("[bold blue]하이브리드 검색 중...[/bold blue]"):
        try:
            results = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]검색 실패: {e}[/red]")
            raise typer.Exit(1)

    if not results:
        console.print("[yellow]검색 결과가 없습니다.[/yellow]")
        return

    table = Table(title=f"'{query}' 검색 결과")
    table.add_column("소스", style="cyan", width=8)
    table.add_column("점수", style="green", width=6)
    table.add_column("내용", max_width=60)

    for r in results:
        table.add_row(
            r.source,
            f"{r.score:.2f}",
            r.content[:60] + "..." if len(r.content) > 60 else r.content,
        )

    console.print(table)


@app.command()
def config():
    """현재 설정을 확인합니다."""
    table = Table(title="Palantir Stock 설정")
    table.add_column("설정", style="cyan")
    table.add_column("값", style="green")
    table.add_column("상태")

    # OpenAI
    table.add_row(
        "OpenAI API",
        "***설정됨***" if settings.openai_api_key else "미설정",
        "[green]OK[/green]" if settings.openai_api_key else "[red]MISSING[/red]",
    )

    table.add_row(
        "OpenAI 모델",
        settings.openai_model,
        "[green]OK[/green]",
    )

    # Search APIs
    table.add_row(
        "SerpAPI",
        "***설정됨***" if settings.serpapi_key else "미설정",
        "[green]OK[/green]" if settings.serpapi_key else "[yellow]OPTIONAL[/yellow]",
    )

    table.add_row(
        "Tavily API",
        "***설정됨***" if settings.tavily_api_key else "미설정",
        "[green]OK[/green]" if settings.tavily_api_key else "[yellow]OPTIONAL[/yellow]",
    )

    # Palantir
    table.add_row(
        "Palantir Host",
        settings.foundry_host if settings.foundry_host else "미설정",
        "[green]OK[/green]" if settings.foundry_host else "[yellow]OPTIONAL[/yellow]",
    )

    table.add_row(
        "Palantir Token",
        "***설정됨***" if settings.foundry_token else "미설정",
        "[green]OK[/green]" if settings.foundry_token else "[yellow]OPTIONAL[/yellow]",
    )

    # Neo4j
    table.add_row(
        "Neo4j",
        settings.neo4j_uri if settings.neo4j_password else "미설정",
        "[green]OK[/green]" if settings.neo4j_password else "[yellow]OPTIONAL[/yellow]",
    )

    # ChromaDB
    table.add_row(
        "ChromaDB",
        settings.chroma_persist_dir,
        "[green]OK[/green]",
    )

    # 검색 API 체크
    has_search = settings.serpapi_key or settings.tavily_api_key
    if not has_search:
        table.add_row(
            "[red]검색 API[/red]",
            "[red]미설정[/red]",
            "[red]REQUIRED (하나 이상 필요)[/red]",
        )

    console.print(table)

    # 요약
    console.print()
    if settings.openai_api_key and has_search:
        console.print("[green]✓ 기본 설정 완료. 분석 기능 사용 가능.[/green]")
    else:
        console.print("[red]✗ 필수 설정이 누락되었습니다.[/red]")

    if settings.foundry_token and settings.foundry_host:
        console.print("[green]✓ Palantir 연동 설정 완료.[/green]")
    else:
        console.print("[yellow]△ Palantir 연동 미설정 (선택사항)[/yellow]")


def _display_report(report):
    """리포트를 화면에 표시합니다."""
    from src.models.schemas import CompanyReport

    # 헤더
    console.print()
    console.print(
        Panel(
            report.summary,
            title=f"[bold]{report.company.name} 분석 리포트[/bold]",
            border_style="blue",
        )
    )

    # 뉴스 섹션
    if report.news:
        console.print()
        console.print("[bold]📰 최신 뉴스[/bold]")
        for item in report.news[:5]:
            console.print(f"  • {item.title}")
            if item.source:
                console.print(f"    [dim]출처: {item.source}[/dim]")

    # 소스 섹션
    if report.sources:
        console.print()
        console.print(f"[dim]참조 소스: {len(report.sources)}개[/dim]")

    # Palantir 데이터
    if report.palantir_data:
        console.print()
        console.print("[bold]🔷 Palantir 데이터[/bold]")
        console.print(f"  {report.palantir_data}")

    # 생성 시간
    console.print()
    console.print(f"[dim]생성: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


if __name__ == "__main__":
    app()
