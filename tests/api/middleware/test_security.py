"""
Tests for security headers middleware (TECH-027).

Tests verify that all security headers are correctly added to responses:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy
- Referrer-Policy
- Permissions-Policy
- Strict-Transport-Security (production only)
"""

from unittest.mock import MagicMock, patch
import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from fastapi import FastAPI

from src.api.middleware.security import SecurityHeadersMiddleware


# Create a minimal FastAPI app for testing
def create_test_app():
    """Create a test FastAPI app with security middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    return app


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_x_content_type_options_header_is_nosniff(self):
        """X-Content-Type-Options should be 'nosniff'."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_header_is_deny(self):
        """X-Frame-Options should be 'DENY' to prevent clickjacking."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection_header_is_enabled(self):
        """X-XSS-Protection should enable browser XSS filtering."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_content_security_policy_header_is_set(self):
        """Content-Security-Policy should restrict resource loading."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_referrer_policy_header_is_set(self):
        """Referrer-Policy should control referrer information."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_header_restricts_features(self):
        """Permissions-Policy should restrict browser features."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        permissions = response.headers.get("Permissions-Policy")
        assert permissions is not None
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions

    def test_hsts_header_not_present_in_development(self):
        """HSTS header should NOT be present in development environment."""
        with patch("src.api.middleware.security.settings") as mock_settings:
            mock_settings.APP_ENV = "development"

            app = create_test_app()
            client = TestClient(app)
            response = client.get("/test")

            # HSTS should NOT be set in development
            assert response.headers.get("Strict-Transport-Security") is None

    def test_hsts_header_present_in_production(self):
        """HSTS header should be present in production environment."""
        with patch("src.api.middleware.security.settings") as mock_settings:
            mock_settings.APP_ENV = "production"

            app = create_test_app()
            client = TestClient(app)
            response = client.get("/test")

            hsts = response.headers.get("Strict-Transport-Security")
            assert hsts is not None
            assert "max-age=31536000" in hsts
            assert "includeSubDomains" in hsts

    def test_headers_applied_to_all_endpoints(self):
        """Security headers should be applied to all endpoints."""
        app = create_test_app()
        client = TestClient(app)

        # Test multiple endpoints
        endpoints = ["/test", "/health"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert response.headers.get("X-Frame-Options") == "DENY"

    def test_headers_applied_to_error_responses(self):
        """Security headers should be applied even to error responses."""
        app = create_test_app()
        client = TestClient(app)

        # Request non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Headers should still be present
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_middleware_class_has_correct_constants(self):
        """Middleware class should have correct security constant values."""
        # HSTS value
        assert "max-age=31536000" in SecurityHeadersMiddleware.HSTS_VALUE
        assert "includeSubDomains" in SecurityHeadersMiddleware.HSTS_VALUE

        # CSP value
        assert "default-src 'self'" in SecurityHeadersMiddleware.CSP_VALUE
        assert "frame-ancestors 'none'" in SecurityHeadersMiddleware.CSP_VALUE


class TestSecurityHeadersIntegration:
    """Integration tests for security headers with the actual app."""

    def test_security_headers_on_health_check(self):
        """Health check endpoint should have security headers."""
        app = create_test_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

        # All non-HSTS headers should be present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_security_headers_on_post_request(self):
        """POST requests should also have security headers."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.post("/submit")
        async def submit_endpoint():
            return {"submitted": True}

        client = TestClient(app)
        response = client.post("/submit")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


class TestCSPDirectives:
    """Tests for Content-Security-Policy directives."""

    def test_csp_default_src_self(self):
        """CSP default-src should be 'self'."""
        csp = SecurityHeadersMiddleware.CSP_VALUE
        assert "default-src 'self'" in csp

    def test_csp_script_src_self(self):
        """CSP script-src should be 'self'."""
        csp = SecurityHeadersMiddleware.CSP_VALUE
        assert "script-src 'self'" in csp

    def test_csp_style_src_allows_inline(self):
        """CSP style-src should allow inline styles for UI compatibility."""
        csp = SecurityHeadersMiddleware.CSP_VALUE
        assert "style-src 'self' 'unsafe-inline'" in csp

    def test_csp_img_src_allows_data_uri(self):
        """CSP img-src should allow data URIs for inline images."""
        csp = SecurityHeadersMiddleware.CSP_VALUE
        assert "img-src 'self' data:" in csp

    def test_csp_frame_ancestors_none(self):
        """CSP frame-ancestors should be 'none' to prevent framing."""
        csp = SecurityHeadersMiddleware.CSP_VALUE
        assert "frame-ancestors 'none'" in csp
