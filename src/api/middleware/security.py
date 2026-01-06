"""
Security middleware for FastAPI.

Provides security headers for all HTTP responses (TECH-027).

Headers added:
- Strict-Transport-Security (HSTS): Forces HTTPS for future requests
- X-Content-Type-Options: Prevents MIME type sniffing
- X-Frame-Options: Prevents clickjacking attacks
- X-XSS-Protection: Enables browser XSS filtering
- Content-Security-Policy: Restricts resource loading
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Restricts browser features
"""

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Security headers help protect against common web vulnerabilities:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME sniffing
    - Protocol downgrade attacks

    Note: HTTPS is enforced at the infrastructure level (Fly.io force_https=true).
    This middleware adds additional security headers for defense in depth.
    """

    # HSTS max-age: 1 year (31536000 seconds)
    # includeSubDomains: Apply to all subdomains
    # preload: Allow inclusion in browser HSTS preload lists
    HSTS_VALUE = "max-age=31536000; includeSubDomains"

    # Content Security Policy (CSP)
    # - default-src 'self': Only allow resources from same origin
    # - script-src 'self': Only allow scripts from same origin
    # - style-src 'self' 'unsafe-inline': Allow inline styles (needed for some UIs)
    # - img-src 'self' data:: Allow images from same origin and data URIs
    # - frame-ancestors 'none': Prevent framing (same as X-Frame-Options: DENY)
    CSP_VALUE = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)

        # Only add HSTS in production (not in development with HTTP)
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = self.HSTS_VALUE

        # Always add these headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = self.CSP_VALUE
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
