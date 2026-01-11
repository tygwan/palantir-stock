"""FastAPI 메인 애플리케이션."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.api.routes import analyze_router, graph_router, reports_router, stock_router
from src.api.schemas import HealthResponse
from src.utils.logging import get_logger

logger = get_logger("api.main")

# 정적 파일 경로
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리."""
    logger.info("API 서버 시작")
    yield
    logger.info("API 서버 종료")


def create_app() -> FastAPI:
    """FastAPI 앱을 생성합니다."""
    app = FastAPI(
        title="Palantir Stock API",
        description="웹 검색 기반 기업 정보 수집 및 주식 데이터 분석 API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(analyze_router)
    app.include_router(stock_router)
    app.include_router(graph_router)
    app.include_router(reports_router)

    # 정적 파일 (존재하는 경우)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root():
        """대시보드 메인 페이지."""
        return get_dashboard_html()

    @app.get("/health", response_model=HealthResponse, tags=["시스템"])
    async def health_check() -> HealthResponse:
        """서비스 상태를 확인합니다."""
        services = {
            "openai": bool(settings.openai_api_key),
            "serpapi": bool(settings.serpapi_key),
            "tavily": bool(settings.tavily_api_key),
            "neo4j": bool(settings.neo4j_uri),
            "foundry": bool(settings.foundry_token),
        }

        return HealthResponse(
            status="ok",
            version="1.0.0",
            services=services,
        )

    return app


def get_dashboard_html() -> str:
    """대시보드 HTML을 반환합니다."""
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palantir Stock - 기업 분석 대시보드</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen" x-data="dashboard()">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <h1 class="text-2xl font-bold text-blue-400">Palantir Stock</h1>
            <div class="flex items-center space-x-4">
                <a href="/docs" class="text-sm text-gray-400 hover:text-white">API Docs</a>
                <span class="text-gray-500">|</span>
                <span class="text-sm text-green-400" x-text="status"></span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">
        <!-- Search Section -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 class="text-lg font-semibold mb-4">기업 분석</h2>
            <div class="flex space-x-4">
                <input
                    type="text"
                    x-model="companyName"
                    @keyup.enter="analyzeCompany"
                    placeholder="기업명 입력 (예: 삼성전자, AAPL)"
                    class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2
                           focus:outline-none focus:border-blue-500"
                >
                <button
                    @click="analyzeCompany"
                    :disabled="loading"
                    class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600
                           px-6 py-2 rounded-lg font-medium transition"
                >
                    <span x-show="!loading">분석</span>
                    <span x-show="loading" x-cloak>분석 중...</span>
                </button>
                <button
                    @click="generateReport"
                    :disabled="!result || loading"
                    class="bg-green-600 hover:bg-green-700 disabled:bg-gray-600
                           px-6 py-2 rounded-lg font-medium transition"
                >
                    리포트
                </button>
            </div>
        </div>

        <!-- Error Message -->
        <div x-show="error" x-cloak class="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-8">
            <p class="text-red-400" x-text="error"></p>
        </div>

        <!-- Results Section -->
        <div x-show="result" x-cloak class="space-y-6">
            <!-- Summary -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-4 text-blue-400" x-text="result?.company_name"></h3>
                <p class="text-gray-300 whitespace-pre-wrap" x-text="result?.summary"></p>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Stock Data -->
                <div class="bg-gray-800 rounded-lg p-6" x-show="result?.stock_data">
                    <h4 class="text-md font-semibold mb-4 text-green-400">주식 데이터</h4>
                    <div class="space-y-2" x-show="result?.stock_data">
                        <div class="flex justify-between">
                            <span class="text-gray-400">티커</span>
                            <span x-text="result?.stock_data?.ticker"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">현재가</span>
                            <span x-text="result?.stock_data?.current_price?.toLocaleString()"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">변동률</span>
                            <span :class="result?.stock_data?.change_percent >= 0 ? 'text-green-400' : 'text-red-400'"
                                  x-text="(result?.stock_data?.change_percent || 0).toFixed(2) + '%'"></span>
                        </div>
                        <div class="flex justify-between" x-show="result?.stock_data?.indicators?.rsi">
                            <span class="text-gray-400">RSI</span>
                            <span x-text="result?.stock_data?.indicators?.rsi?.toFixed(2)"></span>
                        </div>
                    </div>
                </div>

                <!-- News -->
                <div class="bg-gray-800 rounded-lg p-6">
                    <h4 class="text-md font-semibold mb-4 text-yellow-400">최신 뉴스</h4>
                    <div class="space-y-3 max-h-64 overflow-y-auto">
                        <template x-for="news in result?.news || []" :key="news.url">
                            <a :href="news.url" target="_blank"
                               class="block p-3 bg-gray-700 rounded hover:bg-gray-600 transition">
                                <p class="font-medium text-sm" x-text="news.title"></p>
                                <p class="text-xs text-gray-400 mt-1" x-text="news.source"></p>
                            </a>
                        </template>
                        <p x-show="!result?.news?.length" class="text-gray-500">뉴스가 없습니다.</p>
                    </div>
                </div>
            </div>

            <!-- Graph Context -->
            <div class="bg-gray-800 rounded-lg p-6" x-show="result?.graph_context">
                <h4 class="text-md font-semibold mb-4 text-purple-400">Graph RAG 컨텍스트</h4>
                <p class="text-gray-300 text-sm whitespace-pre-wrap" x-text="result?.graph_context"></p>
            </div>

            <!-- Sources -->
            <div class="bg-gray-800 rounded-lg p-6" x-show="result?.sources?.length">
                <h4 class="text-md font-semibold mb-4 text-gray-400">참조 소스</h4>
                <div class="flex flex-wrap gap-2">
                    <template x-for="(source, idx) in result?.sources || []" :key="idx">
                        <a :href="source" target="_blank"
                           class="text-xs text-blue-400 hover:underline truncate max-w-xs"
                           x-text="source"></a>
                    </template>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
            <button @click="getGraphStats"
                    class="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition">
                <div class="text-purple-400 font-semibold">Graph 통계</div>
                <div class="text-sm text-gray-400">지식 그래프 현황</div>
            </button>
            <button @click="window.open('/docs', '_blank')"
                    class="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition">
                <div class="text-blue-400 font-semibold">API 문서</div>
                <div class="text-sm text-gray-400">Swagger UI</div>
            </button>
            <button @click="window.open('/redoc', '_blank')"
                    class="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition">
                <div class="text-green-400 font-semibold">ReDoc</div>
                <div class="text-sm text-gray-400">API 레퍼런스</div>
            </button>
            <button @click="checkHealth"
                    class="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition">
                <div class="text-yellow-400 font-semibold">서비스 상태</div>
                <div class="text-sm text-gray-400">헬스체크</div>
            </button>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 border-t border-gray-700 px-6 py-4 mt-8">
        <div class="max-w-7xl mx-auto text-center text-sm text-gray-500">
            Palantir Stock v1.0.0 | LangGraph + Neo4j + ChromaDB
        </div>
    </footer>

    <script>
        function dashboard() {
            return {
                companyName: '',
                loading: false,
                error: null,
                result: null,
                status: '연결됨',

                async analyzeCompany() {
                    if (!this.companyName.trim()) return;

                    this.loading = true;
                    this.error = null;
                    this.result = null;

                    try {
                        const response = await fetch('/analyze/company', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                company_name: this.companyName,
                                include_stock: true,
                                include_graph: true
                            })
                        });

                        if (!response.ok) {
                            const err = await response.json();
                            throw new Error(err.detail || '분석 실패');
                        }

                        this.result = await response.json();
                    } catch (e) {
                        this.error = e.message;
                    } finally {
                        this.loading = false;
                    }
                },

                async generateReport() {
                    if (!this.result) return;
                    window.open(`/reports/view/${encodeURIComponent(this.result.company_name)}`, '_blank');
                },

                async getGraphStats() {
                    try {
                        const response = await fetch('/graph/stats');
                        const stats = await response.json();
                        alert(JSON.stringify(stats, null, 2));
                    } catch (e) {
                        alert('통계 조회 실패: ' + e.message);
                    }
                },

                async checkHealth() {
                    try {
                        const response = await fetch('/health');
                        const health = await response.json();
                        alert(JSON.stringify(health, null, 2));
                    } catch (e) {
                        alert('헬스체크 실패: ' + e.message);
                    }
                }
            };
        }
    </script>
</body>
</html>
"""


# 앱 인스턴스 생성
app = create_app()
