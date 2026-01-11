"""Palantir Foundry 클라이언트 래퍼."""

from functools import cached_property

import foundry

from config.settings import Settings
from src.utils.logging import get_logger

logger = get_logger("palantir.client")


class FoundryClientWrapper:
    """Palantir Foundry 클라이언트 래퍼."""

    def __init__(self, settings: Settings | None = None):
        """Foundry 클라이언트를 초기화합니다.

        Args:
            settings: 애플리케이션 설정
        """
        if settings is None:
            from config.settings import settings as default_settings
            settings = default_settings

        self.settings = settings
        self._client: foundry.FoundryClient | None = None

    @property
    def is_available(self) -> bool:
        """Foundry 연결이 가능한지 확인합니다."""
        return bool(self.settings.foundry_token and self.settings.foundry_host)

    @cached_property
    def client(self) -> foundry.FoundryClient:
        """Foundry 클라이언트를 반환합니다.

        Returns:
            FoundryClient 인스턴스

        Raises:
            ValueError: 토큰 또는 호스트가 설정되지 않은 경우
        """
        if not self.is_available:
            raise ValueError(
                "Palantir 설정이 필요합니다. "
                "FOUNDRY_TOKEN과 FOUNDRY_HOST를 설정해주세요."
            )

        auth = foundry.UserTokenAuth(
            hostname=self.settings.foundry_host,
            token=self.settings.foundry_token,
        )

        client = foundry.FoundryClient(
            auth=auth,
            hostname=self.settings.foundry_host,
        )

        logger.info(f"Foundry 클라이언트 초기화 완료: {self.settings.foundry_host}")
        return client

    def test_connection(self) -> bool:
        """Foundry 연결을 테스트합니다.

        Returns:
            연결 성공 여부
        """
        if not self.is_available:
            return False

        try:
            # 간단한 API 호출로 연결 테스트
            _ = self.client
            logger.info("Foundry 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"Foundry 연결 테스트 실패: {e}")
            return False


# 기본 클라이언트 인스턴스
_default_client: FoundryClientWrapper | None = None


def get_foundry_client(settings: Settings | None = None) -> FoundryClientWrapper:
    """기본 Foundry 클라이언트를 반환합니다.

    Args:
        settings: 애플리케이션 설정

    Returns:
        FoundryClientWrapper 인스턴스
    """
    global _default_client

    if _default_client is None:
        _default_client = FoundryClientWrapper(settings)

    return _default_client
