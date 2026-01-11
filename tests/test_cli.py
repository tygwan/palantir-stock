"""CLI 테스트."""

from typer.testing import CliRunner

from src.main import app

runner = CliRunner()


def test_config_command():
    """config 명령어가 정상 동작합니다."""
    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert "설정" in result.stdout


def test_analyze_without_api_key(monkeypatch):
    """API 키 없이 analyze 명령어 실행 시 에러를 표시합니다."""
    # 환경변수 제거
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("SERPAPI_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    result = runner.invoke(app, ["analyze", "삼성전자"])

    # 설정 오류로 종료
    assert result.exit_code == 1


def test_news_without_api_key(monkeypatch):
    """API 키 없이 news 명령어 실행 시 에러를 표시합니다."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("SERPAPI_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    result = runner.invoke(app, ["news", "삼성전자"])

    assert result.exit_code == 1


def test_ontology_without_palantir_config(monkeypatch):
    """Palantir 설정 없이 ontology 명령어 실행 시 안내 메시지를 표시합니다."""
    monkeypatch.setenv("FOUNDRY_TOKEN", "")
    monkeypatch.setenv("FOUNDRY_HOST", "")

    result = runner.invoke(app, ["ontology"])

    assert result.exit_code == 1
    assert "Palantir" in result.stdout


def test_datasets_without_palantir_config(monkeypatch):
    """Palantir 설정 없이 datasets 명령어 실행 시 안내 메시지를 표시합니다."""
    monkeypatch.setenv("FOUNDRY_TOKEN", "")
    monkeypatch.setenv("FOUNDRY_HOST", "")

    result = runner.invoke(app, ["datasets"])

    assert result.exit_code == 1
    assert "Palantir" in result.stdout
