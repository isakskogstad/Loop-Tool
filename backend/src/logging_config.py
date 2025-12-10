"""
Structured logging configuration for Loop-Auto.

Supports JSON format for production and console format for development.
Includes request ID correlation and source-specific loggers.
"""

import logging
import sys
import uuid
from datetime import datetime
from typing import Optional
from contextvars import ContextVar
from functools import wraps
import json
import os

# Context variable for request ID correlation
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields from record
        if hasattr(record, 'source'):
            log_data["source"] = record.source
        if hasattr(record, 'orgnr'):
            log_data["orgnr"] = record.orgnr
        if hasattr(record, 'action'):
            log_data["action"] = record.action
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, 'error'):
            log_data["error"] = record.error

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)

        # Build base message
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = f"{color}{record.levelname:8}{self.RESET}"

        # Add source if available
        source = ""
        if hasattr(record, 'source'):
            source = f"[{record.source}] "

        # Add orgnr if available
        orgnr = ""
        if hasattr(record, 'orgnr'):
            orgnr = f"({record.orgnr}) "

        # Add duration if available
        duration = ""
        if hasattr(record, 'duration_ms'):
            duration = f" [{record.duration_ms:.0f}ms]"

        message = record.getMessage()

        return f"{timestamp} {level} {source}{orgnr}{message}{duration}"


class SourceLogger:
    """Logger wrapper with source-specific context."""

    def __init__(self, logger: logging.Logger, source: str):
        self._logger = logger
        self._source = source

    def _log(self, level: int, msg: str, **kwargs):
        extra = {'source': self._source}
        extra.update(kwargs)
        self._logger.log(level, msg, extra=extra)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, **kwargs):
        extra = {'source': self._source}
        extra.update(kwargs)
        self._logger.exception(msg, extra=extra)


def setup_logging(
    level: str = "INFO",
    format_type: str = "console",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 'json' for production, 'console' for development
        log_file: Optional path to log file

    Returns:
        Root logger instance
    """
    # Get log level from string
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger("loop_auto")
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str = "loop_auto") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"loop_auto.{name}")


def get_source_logger(source: str) -> SourceLogger:
    """
    Get a source-specific logger.

    Args:
        source: Source name (allabolag, bolagsverket, orchestrator, api)

    Returns:
        SourceLogger with source context
    """
    logger = get_logger(source)
    return SourceLogger(logger, source)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for the current context.

    Args:
        request_id: Optional ID, generates new one if not provided

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = generate_request_id()
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()


def log_duration(logger: SourceLogger, action: str):
    """
    Decorator to log function duration.

    Usage:
        @log_duration(logger, "fetch_company")
        async def fetch_company(orgnr):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(f"{action} completed", action=action, duration_ms=duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(f"{action} failed: {e}", action=action, duration_ms=duration_ms, error=str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(f"{action} completed", action=action, duration_ms=duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(f"{action} failed: {e}", action=action, duration_ms=duration_ms, error=str(e))
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Pre-configured source loggers (lazy initialization)
_source_loggers = {}

def get_allabolag_logger() -> SourceLogger:
    if 'allabolag' not in _source_loggers:
        _source_loggers['allabolag'] = get_source_logger('allabolag')
    return _source_loggers['allabolag']

def get_bolagsverket_logger() -> SourceLogger:
    if 'bolagsverket' not in _source_loggers:
        _source_loggers['bolagsverket'] = get_source_logger('bolagsverket')
    return _source_loggers['bolagsverket']

def get_orchestrator_logger() -> SourceLogger:
    if 'orchestrator' not in _source_loggers:
        _source_loggers['orchestrator'] = get_source_logger('orchestrator')
    return _source_loggers['orchestrator']

def get_api_logger() -> SourceLogger:
    if 'api' not in _source_loggers:
        _source_loggers['api'] = get_source_logger('api')
    return _source_loggers['api']

def get_database_logger() -> SourceLogger:
    if 'database' not in _source_loggers:
        _source_loggers['database'] = get_source_logger('database')
    return _source_loggers['database']


# Initialize logging on module import if not already done
def init_from_config():
    """Initialize logging from config module."""
    try:
        from config import Config
        level = getattr(Config, 'LOG_LEVEL', 'INFO')
        format_type = getattr(Config, 'LOG_FORMAT', 'console')
        log_file = getattr(Config, 'LOG_FILE', None)
        setup_logging(level=level, format_type=format_type, log_file=log_file)
    except ImportError:
        # Config not available, use defaults
        setup_logging()
