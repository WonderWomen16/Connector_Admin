import logging
import socket
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class DailyFileHandler(logging.Handler):
    def __init__(
        self,
        log_path: str,
        environment: str,
        hostname: str,
    ) -> None:
        super().__init__()

        self.log_path = Path(log_path)
        self.environment = environment
        self.hostname = hostname
        self.current_date = datetime.now().date()
        self._file = None

        self._open_log_file()

    def _get_log_file_path(self) -> Path:
        filename = (
            f"{self.environment}_{self.hostname}_" f"{self.current_date:%Y-%m-%d}.log"
        )

        return self.log_path / filename

    def _open_log_file(self) -> None:
        self.log_path.mkdir(parents=True, exist_ok=True)

        if self._file is not None:
            self._file.close()

        self._file = open(
            self._get_log_file_path(),
            mode="a",
            encoding="utf-8",
        )

    def _check_date(self) -> None:
        current_date = datetime.now().date()

        if current_date != self.current_date:
            self.current_date = current_date
            self._open_log_file()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._check_date()

            message = self.format(record)
            self._file.write(message + "\n")
            self._file.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

        super().close()


def configure_logging() -> None:
    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    file_handler = DailyFileHandler(
        log_path=settings.app_log_path,
        environment=settings.environment,
        hostname=socket.gethostname(),
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Application logs
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Uvicorn logs continue to use their normal terminal handlers,
    # but also write to our daily application log.
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        if file_handler not in logger.handlers:
            logger.addHandler(file_handler)
