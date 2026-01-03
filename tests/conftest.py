"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Fixture que fornece um cliente de teste para a API."""
    return TestClient(app)
