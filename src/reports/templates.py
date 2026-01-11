"""리포트 템플릿 정의."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.models.schemas import CompanyReport


class BaseTemplate(ABC):
    """리포트 템플릿 기본 클래스."""

    @abstractmethod
    def render(self, report: CompanyReport) -> str:
        """리포트를 렌더링합니다."""
        pass


class MarkdownTemplate(BaseTemplate):
    """마크다운 리포트 템플릿."""

    def render(self, report: CompanyReport) -> str:
        """마크다운 리포트를 생성합니다."""
        lines = [
            f"# {report.company.name} 분석 리포트",
            "",
            f"*생성일: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
            "## 요약",
            "",
            report.summary or "분석 요약이 없습니다.",
            "",
        ]

        # 기업 정보
        if report.company:
            lines.extend(
                [
                    "## 기업 정보",
                    "",
                    f"- **기업명**: {report.company.name}",
                ]
            )
            if report.company.ticker:
                lines.append(f"- **티커**: {report.company.ticker}")
            if report.company.industry:
                lines.append(f"- **산업**: {report.company.industry}")
            if report.company.market_cap:
                lines.append(f"- **시가총액**: {report.company.market_cap}")
            lines.append("")

        # 뉴스
        if report.news:
            lines.extend(
                [
                    "## 최신 뉴스",
                    "",
                ]
            )
            for i, news in enumerate(report.news[:10], 1):
                date_str = (
                    news.published_date.strftime("%Y-%m-%d")
                    if news.published_date
                    else ""
                )
                lines.append(f"{i}. [{news.title}]({news.url})")
                if date_str:
                    lines.append(f"   - 출처: {news.source} | {date_str}")
                else:
                    lines.append(f"   - 출처: {news.source}")
                if news.summary:
                    lines.append(f"   - {news.summary}")
            lines.append("")

        # Palantir 데이터
        if report.palantir_data:
            lines.extend(
                [
                    "## 추가 데이터",
                    "",
                ]
            )

            # 주식 데이터
            stock_data = report.palantir_data.get("stock_data")
            if stock_data:
                lines.extend(
                    [
                        "### 주식 데이터",
                        "",
                    ]
                )
                if stock_data.get("current_price"):
                    lines.append(f"- **현재가**: {stock_data['current_price']:,.0f}")
                if stock_data.get("change_percent"):
                    lines.append(f"- **변동률**: {stock_data['change_percent']:.2f}%")

                indicators = stock_data.get("indicators", {})
                if indicators:
                    if indicators.get("rsi"):
                        lines.append(f"- **RSI**: {indicators['rsi']:.2f}")
                    if indicators.get("macd"):
                        lines.append(f"- **MACD**: {indicators['macd']:.4f}")
                lines.append("")

            # 그래프 컨텍스트
            graph_context = report.palantir_data.get("graph_context")
            if graph_context:
                lines.extend(
                    [
                        "### 지식 그래프 컨텍스트",
                        "",
                        graph_context,
                        "",
                    ]
                )

        # 소스
        if report.sources:
            lines.extend(
                [
                    "## 참조 소스",
                    "",
                ]
            )
            for source in report.sources[:20]:
                lines.append(f"- {source}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "*이 리포트는 Palantir Stock AI 에이전트에 의해 자동 생성되었습니다.*",
            ]
        )

        return "\n".join(lines)


class HTMLTemplate(BaseTemplate):
    """HTML 리포트 템플릿."""

    def render(self, report: CompanyReport) -> str:
        """HTML 리포트를 생성합니다."""
        news_html = ""
        for news in report.news[:10]:
            date_str = (
                news.published_date.strftime("%Y-%m-%d") if news.published_date else ""
            )
            news_html += f"""
            <div class="news-item">
                <a href="{news.url}" target="_blank" class="news-title">{news.title}</a>
                <div class="news-meta">{news.source} {f'| {date_str}' if date_str else ''}</div>
                {f'<div class="news-summary">{news.summary}</div>' if news.summary else ''}
            </div>
            """

        stock_html = ""
        if report.palantir_data and report.palantir_data.get("stock_data"):
            stock = report.palantir_data["stock_data"]
            indicators = stock.get("indicators", {})
            change_class = "positive" if stock.get("change_percent", 0) >= 0 else "negative"

            stock_html = f"""
            <div class="card">
                <h2>주식 데이터</h2>
                <div class="stock-grid">
                    <div class="stock-item">
                        <span class="label">현재가</span>
                        <span class="value">{stock.get('current_price', 0):,.0f}</span>
                    </div>
                    <div class="stock-item">
                        <span class="label">변동률</span>
                        <span class="value {change_class}">{stock.get('change_percent', 0):.2f}%</span>
                    </div>
                    {f'<div class="stock-item"><span class="label">RSI</span><span class="value">{indicators.get("rsi", 0):.2f}</span></div>' if indicators.get('rsi') else ''}
                    {f'<div class="stock-item"><span class="label">MACD</span><span class="value">{indicators.get("macd", 0):.4f}</span></div>' if indicators.get('macd') else ''}
                </div>
            </div>
            """

        graph_html = ""
        if report.palantir_data and report.palantir_data.get("graph_context"):
            graph_html = f"""
            <div class="card">
                <h2>지식 그래프 컨텍스트</h2>
                <div class="graph-context">{report.palantir_data['graph_context']}</div>
            </div>
            """

        sources_html = ""
        if report.sources:
            sources_list = "".join(
                f'<a href="{s}" target="_blank" class="source-link">{s[:50]}...</a>'
                for s in report.sources[:10]
            )
            sources_html = f"""
            <div class="card">
                <h2>참조 소스</h2>
                <div class="sources">{sources_list}</div>
            </div>
            """

        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.company.name} 분석 리포트</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent-blue: #00d9ff;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --accent-yellow: #ffc107;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--bg-card);
        }}

        h1 {{
            font-size: 2.5rem;
            color: var(--accent-blue);
            margin-bottom: 0.5rem;
        }}

        .generated-at {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        .card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--bg-card);
        }}

        .card h2 {{
            font-size: 1.2rem;
            color: var(--accent-blue);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--bg-card);
        }}

        .summary {{
            font-size: 1.05rem;
            white-space: pre-wrap;
        }}

        .news-item {{
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--bg-card);
        }}

        .news-item:last-child {{
            border-bottom: none;
        }}

        .news-title {{
            color: var(--accent-yellow);
            text-decoration: none;
            font-weight: 500;
        }}

        .news-title:hover {{
            text-decoration: underline;
        }}

        .news-meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}

        .news-summary {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}

        .stock-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }}

        .stock-item {{
            background: var(--bg-card);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }}

        .stock-item .label {{
            display: block;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }}

        .stock-item .value {{
            font-size: 1.25rem;
            font-weight: bold;
        }}

        .stock-item .value.positive {{
            color: var(--accent-green);
        }}

        .stock-item .value.negative {{
            color: var(--accent-red);
        }}

        .graph-context {{
            font-size: 0.95rem;
            white-space: pre-wrap;
            background: var(--bg-card);
            padding: 1rem;
            border-radius: 8px;
        }}

        .sources {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .source-link {{
            font-size: 0.8rem;
            color: var(--accent-blue);
            text-decoration: none;
            background: var(--bg-card);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }}

        .source-link:hover {{
            background: var(--bg-primary);
        }}

        footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--bg-card);
            color: var(--text-secondary);
            font-size: 0.8rem;
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .card {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report.company.name}</h1>
            <p class="generated-at">생성일: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="card">
            <h2>분석 요약</h2>
            <div class="summary">{report.summary or '분석 요약이 없습니다.'}</div>
        </div>

        {stock_html}

        <div class="card">
            <h2>최신 뉴스</h2>
            {news_html if news_html else '<p style="color: var(--text-secondary);">뉴스가 없습니다.</p>'}
        </div>

        {graph_html}

        {sources_html}

        <footer>
            <p>이 리포트는 Palantir Stock AI 에이전트에 의해 자동 생성되었습니다.</p>
        </footer>
    </div>
</body>
</html>
        """
