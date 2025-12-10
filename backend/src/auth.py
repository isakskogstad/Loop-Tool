"""
API Key Authentication for Loop-Auto.

Supports two modes:
1. Supabase: API keys stored in api_keys table (production)
2. Environment: API_KEYS env variable for fallback/development
"""

import os
from typing import Optional
from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/request-key",  # API key request endpoint
    "/debug/auth",  # Debug endpoint for auth troubleshooting
}


def get_api_keys_from_env() -> set:
    """
    Get valid API keys from environment variable (fallback).

    Returns:
        Set of valid API keys
    """
    keys_str = os.environ.get("API_KEYS", "")
    if not keys_str:
        return set()
    return {k.strip() for k in keys_str.split(",") if k.strip()}


def is_public_endpoint(path: str) -> bool:
    """Check if endpoint is public (no auth required)."""
    # Check exact matches
    if path in PUBLIC_ENDPOINTS:
        return True
    # Check prefixes
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    # Admin endpoints with token are public (they validate via token)
    if path.startswith("/admin/approve/") or path.startswith("/admin/reject/"):
        return True
    return False


async def validate_api_key_db(api_key: str) -> bool:
    """
    Validate API key against Supabase database.

    Args:
        api_key: The API key to validate

    Returns:
        True if valid and active, False otherwise
    """
    try:
        from .supabase_client import get_db

        db = get_db()

        # Check if key exists and is active
        result = db.client.table('api_keys') \
            .select('id, status') \
            .eq('api_key', api_key) \
            .eq('status', 'active') \
            .execute()

        if result.data:
            # Update usage statistics (non-blocking)
            try:
                db.client.rpc('increment_api_key_usage', {'key_value': api_key}).execute()
            except Exception:
                pass  # Don't fail request if stats update fails
            return True
        return False
    except Exception:
        # Fall back to env validation on error
        return False


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> Optional[str]:
    """
    Verify API key from X-API-Key header.

    Validates against:
    1. Supabase api_keys table (primary)
    2. API_KEYS environment variable (fallback)

    Args:
        request: FastAPI request object
        api_key: API key from header

    Returns:
        The validated API key

    Raises:
        HTTPException: If key is missing or invalid
    """
    # Skip auth for public endpoints
    if is_public_endpoint(request.url.path):
        return None

    # Check for API key
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Try Supabase validation first
    if await validate_api_key_db(api_key):
        return api_key

    # Fallback to environment variable
    env_keys = get_api_keys_from_env()
    if env_keys and api_key in env_keys:
        return api_key

    # If no keys configured anywhere, allow all requests (development mode)
    if not env_keys:
        # Check if we have any keys in Supabase
        try:
            from .supabase_client import get_db
            db = get_db()
            result = db.client.table('api_keys').select('id').limit(1).execute()
            if not result.data:
                # No keys in DB either, allow request (dev mode)
                return api_key
        except Exception:
            pass

    raise HTTPException(
        status_code=403,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"}
    )


def require_api_key():
    """
    Dependency that requires API key authentication.

    Usage:
        @app.get("/protected", dependencies=[Depends(require_api_key())])
        async def protected_endpoint():
            ...
    """
    return Security(verify_api_key)
