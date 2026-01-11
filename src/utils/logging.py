"""로깅 설정 모듈."""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

_console = Console()
_configured = False


def setup_logging(level: str = "INFO") -> logging.Logger:
    """애플리케이션 로깅을 설정합니다.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

    Returns:
        설정된 루트 로거
    """
    global _configured

    if _configured:
        return logging.getLogger("palantir_stock")

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=_console,
                rich_tracebacks=True,
                show_path=False,
            )
        ],
    )

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)

    _configured = True
    return logging.getLogger("palantir_stock")


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거를 반환합니다.

    Args:
        name: 모듈 이름

    Returns:
        해당 모듈의 로거
    """
    if not _configured:
        setup_logging()
    return logging.getLogger(f"palantir_stock.{name}")
