"""Logger configuration."""
import logging
from datetime import UTC, datetime
from functools import lru_cache

from pkg_resources import get_distribution
from pythonjsonlogger import jsonlogger


class ElkJsonFormatter(jsonlogger.JsonFormatter):
    """Json log formatter for python log subsystem."""

    def add_fields(
        self: jsonlogger.JsonFormatter,
        log_record: dict[str, str],
        record: logging.LogRecord,
        message_dict: dict[str, str],
    ) -> None:
        """Allow to add custom fields to log record.

        :param log_record: Custom fields to add to log record.
        :param record: LogRecord logging contains general information about log record.
        :param message_dict: LogRecord message instance
        """
        super().add_fields(log_record, record, message_dict)  # type: ignore[misc]

        log_record["@timestamp"] = datetime.now(tz=UTC).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["app"] = get_distribution("CBAIT").project_name
        log_record["app_version"] = get_distribution("CBAIT").version


@lru_cache
def _init_logger(logger: logging.Logger) -> None:
    """Initialize logger.

    :param logger: Logger to initialize.
    :type logger: logging.Logger
    """
    formatter: ElkJsonFormatter = ElkJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(levelno)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )  # type: ignore[no-untyped-call]

    handler: logging.Handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


@lru_cache
def get_logger() -> logging.Logger:
    """Get configured logger.

    :return: Configured logger.
    :rtype: logging.Logger
    """
    logger: logging.Logger = logging.getLogger(get_distribution("CBAIT").project_name)
    _init_logger(logger)
    return logger
