"""
Testes para o endpoint /health
"""


def test_health_returns_200(client):
    """Verifica que /api/health retorna status 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_structure(client):
    """Verifica estrutura da resposta do /api/health."""
    response = client.get("/api/health")
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data

    assert data["status"] == "healthy"
    assert data["service"] == "seleto-sdr-agent"


def test_health_content_type(client):
    """Verifica que /api/health retorna JSON."""
    response = client.get("/api/health")
    assert response.headers["content-type"] == "application/json"
