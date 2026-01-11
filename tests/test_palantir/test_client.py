"""Palantir 클라이언트 테스트."""

import pytest

from config.settings import Settings
from src.palantir import FoundryClientWrapper


class TestFoundryClientWrapper:
    """FoundryClientWrapper 테스트."""

    def test_is_available_with_config(self):
        """토큰과 호스트가 있으면 사용 가능합니다."""
        settings = Settings(
            foundry_token="test-token",
            foundry_host="test.palantirfoundry.com",
        )
        client = FoundryClientWrapper(settings)

        assert client.is_available is True

    def test_is_not_available_without_token(self):
        """토큰이 없으면 사용 불가합니다."""
        settings = Settings(
            foundry_token="",
            foundry_host="test.palantirfoundry.com",
        )
        client = FoundryClientWrapper(settings)

        assert client.is_available is False

    def test_is_not_available_without_host(self):
        """호스트가 없으면 사용 불가합니다."""
        settings = Settings(
            foundry_token="test-token",
            foundry_host="",
        )
        client = FoundryClientWrapper(settings)

        assert client.is_available is False

    def test_client_raises_when_not_configured(self):
        """설정이 없으면 클라이언트 접근 시 에러를 발생시킵니다."""
        settings = Settings(
            foundry_token="",
            foundry_host="",
        )
        wrapper = FoundryClientWrapper(settings)

        with pytest.raises(ValueError) as exc_info:
            _ = wrapper.client

        assert "Palantir 설정이 필요합니다" in str(exc_info.value)

    def test_test_connection_returns_false_when_not_available(self):
        """설정이 없으면 연결 테스트가 False를 반환합니다."""
        settings = Settings(
            foundry_token="",
            foundry_host="",
        )
        wrapper = FoundryClientWrapper(settings)

        assert wrapper.test_connection() is False
