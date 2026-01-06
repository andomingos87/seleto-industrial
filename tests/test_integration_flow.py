"""
Testes de integração para fluxo completo de conversa.

Execute com: pytest tests/test_integration_flow.py -v -s

Para usar servidor de produção (fly.io):
    INTEGRATION_TEST_URL=https://seleto-industrial.fly.dev pytest tests/test_integration_flow.py -v -s

Para usar servidor local:
    INTEGRATION_TEST_URL=http://localhost:8000 pytest tests/test_integration_flow.py -v -s

Variáveis de ambiente:
    INTEGRATION_TEST_URL: URL base do servidor (padrão: http://localhost:8000)
    INTEGRATION_TEST_TIMEOUT: Timeout em segundos (padrão: 30.0)
"""

import asyncio
import os

import httpx
import pytest

from src.services.conversation_memory import conversation_memory
from src.services.data_extraction import extract_lead_data
from src.utils.validation import normalize_phone, validate_phone

# Configuração de URL e timeout via variáveis de ambiente
INTEGRATION_BASE_URL = os.environ.get(
    "INTEGRATION_TEST_URL", "http://localhost:8000"
)
INTEGRATION_TEST_TIMEOUT = float(os.environ.get("INTEGRATION_TEST_TIMEOUT", "30.0"))

# Cache de verificação do servidor (evita múltiplas verificações)
_server_check_result: dict | None = None


def _check_server_sync() -> tuple[bool, str]:
    """
    Verifica se o servidor está acessível de forma síncrona.

    Returns:
        Tuple com (disponível, mensagem)
    """
    global _server_check_result

    if _server_check_result is not None:
        return _server_check_result["available"], _server_check_result["message"]

    try:
        with httpx.Client(base_url=INTEGRATION_BASE_URL, timeout=5.0) as client:
            response = client.get("/api/health")
            if response.status_code == 200:
                result = (True, f"Servidor acessível em {INTEGRATION_BASE_URL}")
            else:
                result = (False, f"Servidor retornou status {response.status_code}")
    except httpx.ConnectError:
        result = (False, f"Não foi possível conectar ao servidor em {INTEGRATION_BASE_URL}")
    except httpx.TimeoutException:
        result = (False, f"Timeout ao conectar ao servidor em {INTEGRATION_BASE_URL}")
    except Exception as e:
        result = (False, f"Erro ao verificar servidor: {type(e).__name__}: {e}")

    _server_check_result = {"available": result[0], "message": result[1]}
    return result


def _get_skip_message() -> str:
    """Retorna mensagem de skip com instruções."""
    return (
        f"Servidor não acessível em {INTEGRATION_BASE_URL}. "
        "Para executar testes de integração:\n"
        "  1. Inicie o servidor local: uvicorn src.main:app --reload\n"
        "  2. Ou configure URL remota: INTEGRATION_TEST_URL=https://seu-servidor.com pytest ...\n"
        "  3. Ou aumente o timeout: INTEGRATION_TEST_TIMEOUT=60 pytest ..."
    )


def _skip_if_server_unavailable():
    """Pula o teste se o servidor não estiver acessível."""
    available, message = _check_server_sync()
    if not available:
        pytest.skip(_get_skip_message())
    return True


def _create_http_client() -> httpx.AsyncClient:
    """Cria cliente HTTP assíncrono com configurações padrão."""
    return httpx.AsyncClient(
        base_url=INTEGRATION_BASE_URL,
        timeout=httpx.Timeout(INTEGRATION_TEST_TIMEOUT)
    )


# =============================================================================
# Testes de Integração (requerem servidor rodando)
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_connectivity():
    """
    Teste de conectividade básica com o servidor.
    Este teste pode ser executado isoladamente para verificar se o servidor está acessível.
    """
    available, message = _check_server_sync()

    if not available:
        pytest.skip(_get_skip_message())

    print(f"\n✅ {message}")
    assert available, message


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint():
    """Testa endpoint de health check."""
    _skip_if_server_unavailable()

    try:
        async with _create_http_client() as client:
            response = await client.get("/api/health")
            assert response.status_code == 200, f"Status esperado 200, recebido {response.status_code}"

            data = response.json()
            assert data["status"] == "healthy", f"Status esperado 'healthy', recebido {data.get('status')}"
            assert "timestamp" in data, "Resposta deve conter 'timestamp'"
            assert data["service"] == "seleto-sdr-agent", "Service esperado 'seleto-sdr-agent'"

            print(f"\n✅ Health endpoint funcionando ({INTEGRATION_BASE_URL})")

    except httpx.ConnectError as e:
        pytest.skip(f"Erro de conexão: {e}")
    except httpx.TimeoutException as e:
        pytest.fail(f"Timeout ({INTEGRATION_TEST_TIMEOUT}s) ao acessar health endpoint: {e}")
    except httpx.HTTPStatusError as e:
        pytest.fail(f"Erro HTTP: {e.response.status_code} - {e.response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_text_message():
    """Testa recebimento de mensagem de texto via webhook."""
    _skip_if_server_unavailable()

    try:
        async with _create_http_client() as client:
            # Z-API payload format: text message content is nested in 'text.message'
            payload = {
                "phone": "5511999999999",
                "senderName": "Teste Lead",
                "text": {
                    "message": "Olá, preciso de uma formadora de hambúrguer"
                },
                "messageId": "test-webhook-001",
                "type": "ReceivedCallback",
                "fromMe": False,
            }

            response = await client.post("/webhook/whatsapp", json=payload)
            assert response.status_code == 200, f"Status esperado 200, recebido {response.status_code}"

            response_data = response.json()
            assert response_data.get("status") == "received", (
                f"Status esperado 'received', recebido {response_data.get('status')}"
            )

            print("\n✅ Webhook de texto processado com sucesso")

    except httpx.ConnectError as e:
        pytest.skip(f"Erro de conexão: {e}")
    except httpx.TimeoutException as e:
        pytest.fail(f"Timeout ({INTEGRATION_TEST_TIMEOUT}s) ao enviar webhook: {e}")
    except httpx.HTTPStatusError as e:
        pytest.fail(f"Erro HTTP: {e.response.status_code} - {e.response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Testa fluxo completo de conversa (requer servidor rodando)."""
    _skip_if_server_unavailable()

    try:
        async with _create_http_client() as client:
            # 1. Health check
            health = await client.get("/api/health")
            assert health.status_code == 200, "Health check falhou"
            print("\n✅ 1. Health check OK")

            # 2. Primeira mensagem (Z-API format with nested text.message)
            payload1 = {
                "phone": "5511888888888",
                "senderName": "Lead Teste",
                "text": {
                    "message": "Olá, preciso de uma formadora de hambúrguer"
                },
                "messageId": "flow-test-001",
                "type": "ReceivedCallback",
                "fromMe": False,
            }
            response1 = await client.post("/webhook/whatsapp", json=payload1)
            assert response1.status_code == 200, f"Primeira mensagem falhou: {response1.status_code}"
            print("✅ 2. Primeira mensagem processada")

            # Aguardar um pouco para processamento assíncrono
            await asyncio.sleep(2)

            # 3. Segunda mensagem (fornecendo mais dados)
            payload2 = {
                "phone": "5511888888888",
                "senderName": "Lead Teste",
                "text": {
                    "message": "Sou Maria Santos, de Campinas, SP. Preciso processar uns 500 hambúrgueres por dia"
                },
                "messageId": "flow-test-002",
                "type": "ReceivedCallback",
                "fromMe": False,
            }
            response2 = await client.post("/webhook/whatsapp", json=payload2)
            assert response2.status_code == 200, f"Segunda mensagem falhou: {response2.status_code}"
            print("✅ 3. Segunda mensagem processada")

            await asyncio.sleep(2)

            print("\n✅ Fluxo completo testado com sucesso!")

    except httpx.ConnectError as e:
        pytest.skip(f"Erro de conexão durante fluxo: {e}")
    except httpx.TimeoutException as e:
        pytest.fail(f"Timeout ({INTEGRATION_TEST_TIMEOUT}s) durante fluxo de conversa: {e}")
    except httpx.HTTPStatusError as e:
        pytest.fail(f"Erro HTTP durante fluxo: {e.response.status_code} - {e.response.text}")


# =============================================================================
# Testes Locais (não requerem servidor)
# =============================================================================

@pytest.mark.asyncio
async def test_data_extraction_progressive():
    """Testa extração progressiva de dados."""
    # Primeira mensagem: nome e produto
    message1 = "Olá, sou João Silva e preciso de uma formadora de hambúrguer"
    data1 = await extract_lead_data(message1)

    assert "name" in data1 or "product" in data1, "Deveria extrair pelo menos nome ou produto"
    print(f"\n✅ Dados extraídos (1): {data1}")

    # Segunda mensagem: cidade (sem repetir dados anteriores)
    message2 = "Estou em São Paulo, SP"
    data2 = await extract_lead_data(message2, current_data=data1)

    # Não deve repetir name e product
    assert "name" not in data2 or data2.get("name") is None, "Não deveria repetir nome"
    assert "city" in data2 or "uf" in data2, "Deveria extrair cidade ou UF"
    print(f"✅ Dados extraídos (2): {data2}")


def test_phone_normalization():
    """Testa normalização de telefone."""
    test_cases = [
        ("+55 11 99999-9999", "5511999999999"),
        ("(11) 99999-9999", "11999999999"),
        ("5511999999999", "5511999999999"),
        ("11 99999-9999", "11999999999"),
    ]

    for input_phone, expected in test_cases:
        result = normalize_phone(input_phone)
        assert result == expected, f"Falhou: {input_phone} -> {result} (esperado: {expected})"
        print(f"\n✅ Normalização: {input_phone} -> {result}")


def test_phone_validation():
    """Testa validação de telefone."""
    assert validate_phone("5511999999999") == True
    assert validate_phone("11999999999") == True
    assert validate_phone("123") == False  # Muito curto
    assert validate_phone("") == False  # Vazio
    print("\n✅ Validação de telefone funcionando")


def test_conversation_memory():
    """Testa memória de conversa."""
    phone = "5511999999999"

    # Limpar memória antes do teste
    conversation_memory._conversations.pop(phone, None)
    conversation_memory._question_count.pop(phone, None)

    # Teste de primeira mensagem
    assert conversation_memory.is_first_message(phone) == True
    print("\n✅ Primeira mensagem detectada corretamente")

    # Adicionar mensagem
    conversation_memory.add_message(phone, "user", "Olá")
    assert conversation_memory.is_first_message(phone) == False
    print("✅ Mensagem adicionada à memória")

    # Teste de controle de perguntas
    conversation_memory.increment_question_count(phone)
    assert conversation_memory.get_question_count(phone) == 1
    print("✅ Contador de perguntas incrementado")

    conversation_memory.increment_question_count(phone)
    assert conversation_memory.get_question_count(phone) == 2
    print("✅ Contador de perguntas: 2")

    # Reset quando usuário responde
    conversation_memory.reset_question_count(phone)
    assert conversation_memory.get_question_count(phone) == 0
    print("✅ Contador de perguntas resetado")


if __name__ == "__main__":
    # Executar testes diretamente
    pytest.main([__file__, "-v", "-s"])
