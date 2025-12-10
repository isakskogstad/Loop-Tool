"""
Configuration for Loop-Auto - Swedish Company Data API

All settings can be overridden via environment variables.

Data Sources:
- Bolagsverket VDM: Official company registry (OAuth2 API)
- Allabolag: Financial data, board members, corporate structure
"""

import os
from pathlib import Path


class Config:
    """Application configuration"""

    # ==========================================================================
    # PATHS
    # ==========================================================================
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "companies.db"
    LOG_DIR = BASE_DIR / "logs"

    # ==========================================================================
    # CACHE SETTINGS
    # ==========================================================================
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

    # ==========================================================================
    # RATE LIMITING FOR SCRAPERS
    # ==========================================================================
    ALLABOLAG_DELAY_SEC = float(os.getenv("ALLABOLAG_DELAY", "1.0"))
    BOLAGSVERKET_DELAY_SEC = float(os.getenv("BOLAGSVERKET_DELAY", "0.5"))

    # ==========================================================================
    # RETRY SETTINGS
    # ==========================================================================
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF", "1.5"))
    RETRY_BACKOFF_MAX = float(os.getenv("RETRY_MAX_WAIT", "30"))
    RETRY_JITTER = os.getenv("RETRY_JITTER", "true").lower() == "true"

    # Retryable HTTP status codes
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

    # ==========================================================================
    # CIRCUIT BREAKER SETTINGS
    # ==========================================================================
    CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_FAILURES", "5"))
    CIRCUIT_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_RECOVERY", "60"))
    CIRCUIT_HALF_OPEN_REQUESTS = int(os.getenv("CIRCUIT_HALF_OPEN", "3"))

    # ==========================================================================
    # PARALLEL PROCESSING
    # ==========================================================================
    MAX_PARALLEL_SOURCES = int(os.getenv("MAX_PARALLEL", "2"))
    BATCH_PARALLEL_WORKERS = int(os.getenv("BATCH_WORKERS", "5"))
    ENABLE_ASYNC_FETCH = os.getenv("ENABLE_ASYNC", "true").lower() == "true"

    # ==========================================================================
    # TIMEOUTS (seconds)
    # ==========================================================================
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
    CONNECT_TIMEOUT = int(os.getenv("CONNECT_TIMEOUT", "5"))
    SLOW_REQUEST_THRESHOLD = int(os.getenv("SLOW_THRESHOLD", "5"))

    # ==========================================================================
    # BOLAGSVERKET VDM API
    # ==========================================================================
    BOLAGSVERKET_API_KEY = os.getenv("BOLAGSVERKET_API_KEY")
    BOLAGSVERKET_BASE_URL = os.getenv(
        "BOLAGSVERKET_URL",
        "https://foretagsinfo.bolagsverket.se/api/v1"
    )

    # ==========================================================================
    # FEATURE FLAGS
    # ==========================================================================
    USE_BOLAGSVERKET = os.getenv("USE_BOLAGSVERKET", "true").lower() == "true"
    USE_ALLABOLAG = os.getenv("USE_ALLABOLAG", "true").lower() == "true"

    # Feature flags for new functionality
    ENABLE_CIRCUIT_BREAKER = os.getenv("ENABLE_CIRCUIT", "true").lower() == "true"
    ENABLE_RETRY = os.getenv("ENABLE_RETRY", "true").lower() == "true"
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

    # ==========================================================================
    # API SERVER SETTINGS
    # ==========================================================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "1"))

    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "false").lower() == "true"

    # API Authentication
    # Comma-separated list of valid API keys. If empty, auth is disabled (dev mode)
    API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

    # ==========================================================================
    # BATCH LIMITS
    # ==========================================================================
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "10"))
    BATCH_INTER_DELAY = float(os.getenv("BATCH_DELAY", "0.5"))

    # ==========================================================================
    # DATABASE SETTINGS (Supabase)
    # ==========================================================================
    # REQUIRED: Set via environment variables
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    @classmethod
    def validate_required(cls) -> None:
        """
        Validate that required credentials are set. Call at startup.

        Raises:
            ValueError: If required env vars are missing
        """
        missing = []
        warnings = []

        # Required for database
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")

        # Warn about security settings
        if cls.CORS_ORIGINS == ["*"]:
            warnings.append("CORS_ORIGINS is set to '*' - consider restricting in production")
        if not cls.API_KEYS:
            warnings.append("API_KEYS not set - API authentication disabled (dev mode)")

        # Print warnings
        for w in warnings:
            print(f"CONFIG WARNING: {w}")

        # Fail if required vars missing
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Legacy SQLite settings (deprecated, kept for backwards compatibility)
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_WAL_MODE = os.getenv("DB_WAL_MODE", "true").lower() == "true"

    # ==========================================================================
    # LOGGING SETTINGS
    # ==========================================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "console")  # 'json' or 'console'
    LOG_FILE = os.getenv("LOG_FILE", None)

    # ==========================================================================
    # USER AGENT
    # ==========================================================================
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    @classmethod
    def ensure_data_dir(cls):
        """Create data directory if needed"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def ensure_log_dir(cls):
        """Create log directory if needed"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_timeout_tuple(cls) -> tuple:
        """Get timeout as (connect, read) tuple for httpx/requests"""
        return (cls.CONNECT_TIMEOUT, cls.REQUEST_TIMEOUT)

    @classmethod
    def validate(cls) -> list:
        """
        Validate configuration and return list of warnings.

        Returns:
            List of warning messages (empty if all valid)
        """
        warnings = []

        # Check timeout values
        if cls.REQUEST_TIMEOUT < cls.SLOW_REQUEST_THRESHOLD:
            warnings.append(
                f"REQUEST_TIMEOUT ({cls.REQUEST_TIMEOUT}s) is less than "
                f"SLOW_REQUEST_THRESHOLD ({cls.SLOW_REQUEST_THRESHOLD}s)"
            )

        # Check retry settings
        if cls.MAX_RETRIES < 0:
            warnings.append("MAX_RETRIES should be >= 0")

        if cls.RETRY_BACKOFF_BASE < 1:
            warnings.append("RETRY_BACKOFF_BASE should be >= 1")

        # Check circuit breaker settings
        if cls.CIRCUIT_FAILURE_THRESHOLD < 1:
            warnings.append("CIRCUIT_FAILURE_THRESHOLD should be >= 1")

        # Check parallel settings
        if cls.BATCH_PARALLEL_WORKERS > cls.MAX_BATCH_SIZE:
            warnings.append(
                f"BATCH_PARALLEL_WORKERS ({cls.BATCH_PARALLEL_WORKERS}) is greater than "
                f"MAX_BATCH_SIZE ({cls.MAX_BATCH_SIZE})"
            )

        return warnings

    @classmethod
    def to_dict(cls) -> dict:
        """Export configuration as dictionary (for debugging/logging)"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if key.isupper() and not key.startswith('_')
        }


# Create directories on import
Config.ensure_data_dir()
