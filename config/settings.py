"""설정 관리 모듈."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정."""

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Search APIs
    serpapi_key: str = ""
    tavily_api_key: str = ""

    # Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # Vector Database
    chroma_persist_dir: str = "./data/chroma"

    # Stock Data
    alpha_vantage_key: str = ""

    # Palantir (Optional)
    foundry_token: str = ""
    foundry_host: str = ""

    # App Settings
    cache_ttl: int = 3600  # 1 hour
    max_search_results: int = 10
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
