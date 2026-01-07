# BUG-002: Mensagem do SDR no Chatwoot não é enviada para WhatsApp

## Resumo

Quando o SDR envia uma mensagem pelo Chatwoot para um lead, a mensagem **não chega** no WhatsApp do cliente. O sistema pausa o agente corretamente, mas não encaminha a mensagem para o Z-API.

---

## Status

| Campo | Valor |
|-------|-------|
| **ID** | BUG-002 |
| **Prioridade** | Alta |
| **Status** | ✅ Corrigido |
| **Data de Identificação** | 2026-01-07 |
| **Data de Correção** | 2026-01-07 |
| **Componente Afetado** | `src/api/routes/webhook.py` |
| **Função Afetada** | `process_chatwoot_message()` |

---

## Descrição do Problema

### Comportamento Esperado

```
SDR envia mensagem no Chatwoot
    ↓
Webhook chega em /webhook/chatwoot
    ↓
Sistema identifica mensagem do SDR (sender.type == "user")
    ↓
Sistema pausa o agente para esse lead ✅
    ↓
Sistema ENVIA a mensagem do SDR para o WhatsApp via Z-API ✅
    ↓
Lead recebe a mensagem no WhatsApp ✅
```

### Comportamento Atual

```
SDR envia mensagem no Chatwoot
    ↓
Webhook chega em /webhook/chatwoot
    ↓
Sistema identifica mensagem do SDR (sender.type == "user")
    ↓
Sistema pausa o agente para esse lead ✅
    ↓
❌ Mensagem NÃO é enviada para o WhatsApp
    ↓
❌ Lead não recebe nada
```

---

## Análise Técnica

### Localização do Bug

**Arquivo:** `src/api/routes/webhook.py`  
**Função:** `process_chatwoot_message()` (linhas 671-785)

### Código Atual (Problemático)

```python
# Linha 762-785
# Pause the agent for this conversation
success = pause_agent(
    phone=phone,
    reason="sdr_intervention",
    sender_name=sender_name,
    sender_id=sender_id,
)

if success:
    # Envia apenas confirmação privada no Chatwoot
    confirmation = (
        f"Agente pausado para esta conversa. "
        f"O SDR {sender_name or ''} assumiu o atendimento. "
        f"Use /retomar para reativar o agente."
    )
    asyncio.create_task(
        send_internal_message_to_chatwoot(phone, confirmation, sender_name="Sistema")
    )

return {
    "status": "agent_paused" if success else "pause_failed",
    "phone": phone,
    "sender_name": sender_name,
}
# ❌ FALTA: Enviar message_content para o WhatsApp via Z-API
```

### Causa Raiz

A função `process_chatwoot_message()` foi implementada para:
1. ✅ Detectar mensagens do SDR
2. ✅ Processar comandos (/retomar)
3. ✅ Pausar o agente
4. ❌ **NÃO envia a mensagem para o WhatsApp**

---

## Plano de Correção

### Alteração Necessária

Adicionar chamada para `send_whatsapp_message()` após pausar o agente:

```python
# Após pausar o agente, enviar a mensagem para o WhatsApp
if message_content and message_content.strip():
    try:
        success = await send_whatsapp_message(phone, message_content)
        if success:
            logger.info(
                "SDR message sent to WhatsApp",
                extra={
                    "phone": phone,
                    "sender_name": sender_name,
                    "message_length": len(message_content),
                },
            )
        else:
            logger.error(
                "Failed to send SDR message to WhatsApp",
                extra={"phone": phone},
            )
    except Exception as e:
        logger.error(
            "Error sending SDR message to WhatsApp",
            extra={"phone": phone, "error": str(e)},
            exc_info=True,
        )
```

### Arquivos a Modificar

| Arquivo | Alteração |
|---------|-----------|
| `src/api/routes/webhook.py` | Adicionar envio de mensagem para WhatsApp em `process_chatwoot_message()` |

### Dependências

A função `send_whatsapp_message` já existe em `src/services/whatsapp.py` e já está importada no arquivo webhook.py.

---

## Testes Necessários

### Teste Manual

1. Configurar webhook do Chatwoot para `/webhook/chatwoot`
2. SDR envia mensagem pelo Chatwoot
3. Verificar se:
   - [ ] Agente é pausado
   - [ ] Mensagem chega no WhatsApp do lead
   - [ ] Logs mostram envio bem-sucedido

### Teste Automatizado

Adicionar/atualizar teste em `tests/api/test_chatwoot_webhook.py`:

```python
async def test_sdr_message_sent_to_whatsapp():
    """SDR message should be forwarded to WhatsApp via Z-API."""
    # Arrange
    payload = create_sdr_message_payload(content="Olá, como posso ajudar?")
    
    # Act
    with patch("src.services.whatsapp.send_whatsapp_message") as mock_send:
        mock_send.return_value = True
        response = await process_chatwoot_message(payload)
    
    # Assert
    mock_send.assert_called_once()
    assert response["status"] == "agent_paused"
```

---

## Impacto

### Funcionalidades Afetadas

- SDR não consegue enviar mensagens para leads pelo Chatwoot
- Feature de "handoff" (passagem para humano) está incompleta
- Manual do SDR descreve funcionalidade que não funciona

### Usuários Afetados

- Equipe de SDR (vendedores)
- Leads que aguardam resposta humana

---

## Referências

- Manual do SDR: `documentation/manual-chatwoot-sdr.md`
- Código do webhook: `src/api/routes/webhook.py`
- Serviço WhatsApp: `src/services/whatsapp.py`
- Testes existentes: `tests/api/test_chatwoot_webhook.py`

---

## Histórico

| Data | Ação | Autor |
|------|------|-------|
| 2026-01-07 | Bug identificado durante teste de integração | Sistema |
| 2026-01-07 | Plano de correção documentado | Sistema |
| 2026-01-07 | Correção implementada: adicionado envio de mensagem para WhatsApp via Z-API | Sistema |
| 2026-01-07 | Corrigido modelo Pydantic para estrutura plana do Chatwoot (campos no root level) | Sistema |

