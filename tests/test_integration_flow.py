"""
Testes de integração para fluxo completo de conversa.

Execute com: pytest tests/test_integration_flow.py -v -s
"""

import asyncio
from typing import Dict, Any

import httpx
import pytest

from src.services.conversation_memory import conversation_memory
from src.services.data_extraction import extract_lead_data
from src.utils.validation import normalize_phone, validate_phone


@pytest.mark.asyncio
async def test_health_endpoint():
    """Testa endpoint de health check."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "seleto-sdr-agent"
        print("✅ Health endpoint funcionando")


@pytest.mark.asyncio
async def test_webhook_text_message():
    """Testa recebimento de mensagem de texto via webhook."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        payload = {
            "phone": "5511999999999",
            "senderName": "Teste Lead",
            "message": "Olá, preciso de uma formadora de hambúrguer",
            "messageId": "test-webhook-001",
            "messageType": "text",
        }
        
        response = await client.post("/webhook/whatsapp", json=payload)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get("status") == "received"
        print("✅ Webhook de texto processado com sucesso")


@pytest.mark.asyncio
async def test_data_extraction_progressive():
    """Testa extração progressiva de dados."""
    # Primeira mensagem: nome e produto
    message1 = "Olá, sou João Silva e preciso de uma formadora de hambúrguer"
    data1 = await extract_lead_data(message1)
    
    assert "name" in data1 or "product" in data1, "Deveria extrair pelo menos nome ou produto"
    print(f"✅ Dados extraídos (1): {data1}")
    
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
        print(f"✅ Normalização: {input_phone} -> {result}")


def test_phone_validation():
    """Testa validação de telefone."""
    assert validate_phone("5511999999999") == True
    assert validate_phone("11999999999") == True
    assert validate_phone("123") == False  # Muito curto
    assert validate_phone("") == False  # Vazio
    print("✅ Validação de telefone funcionando")


def test_conversation_memory():
    """Testa memória de conversa."""
    phone = "5511999999999"
    
    # Limpar memória antes do teste
    conversation_memory._conversations.pop(phone, None)
    conversation_memory._question_count.pop(phone, None)
    
    # Teste de primeira mensagem
    assert conversation_memory.is_first_message(phone) == True
    print("✅ Primeira mensagem detectada corretamente")
    
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


@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Testa fluxo completo de conversa (requer servidor rodando)."""
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            # 1. Health check
            health = await client.get("/api/health")
            assert health.status_code == 200
            print("\n✅ 1. Health check OK")
            
            # 2. Primeira mensagem
            payload1 = {
                "phone": "5511888888888",
                "senderName": "Lead Teste",
                "message": "Olá, preciso de uma formadora de hambúrguer",
                "messageId": "flow-test-001",
                "messageType": "text",
            }
            response1 = await client.post("/webhook/whatsapp", json=payload1)
            assert response1.status_code == 200
            print("✅ 2. Primeira mensagem processada")
            
            # Aguardar um pouco para processamento assíncrono
            await asyncio.sleep(2)
            
            # 3. Segunda mensagem (fornecendo mais dados)
            payload2 = {
                "phone": "5511888888888",
                "senderName": "Lead Teste",
                "message": "Sou Maria Santos, de Campinas, SP. Preciso processar uns 500 hambúrgueres por dia",
                "messageId": "flow-test-002",
                "messageType": "text",
            }
            response2 = await client.post("/webhook/whatsapp", json=payload2)
            assert response2.status_code == 200
            print("✅ 3. Segunda mensagem processada")
            
            await asyncio.sleep(2)
            
            print("\n✅ Fluxo completo testado com sucesso!")
            
    except httpx.ConnectError:
        pytest.skip("Servidor não está rodando. Execute: uvicorn src.main:app --reload")


if __name__ == "__main__":
    # Executar testes diretamente
    pytest.main([__file__, "-v", "-s"])

