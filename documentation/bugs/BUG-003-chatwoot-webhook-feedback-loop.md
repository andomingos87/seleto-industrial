# BUG-003: Loop de Feedback em Webhooks do Chatwoot

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | BUG-003 |
| **Prioridade** | Crítica |
| **Status** | Corrigido |
| **Data de Identificação** | 2026-01-07 |
| **Data de Resolução** | 2026-01-07 |
| **Componente Afetado** | `src/api/routes/webhook.py`, `src/services/chatwoot_sync.py` |
| **Funções Afetadas** | `process_chatwoot_message()`, `_is_sdr_message()`, `_sync_message_async()` |

---

## Descrição do Problema

### Comportamento Observado

1. **Lead envia mensagem** no WhatsApp
2. **Agente responde** corretamente via WhatsApp e sincroniza a resposta para o Chatwoot
3. **Imediatamente após**, aparece a mensagem: *"Agente pausado para esta conversa. O SDR Tiago assumiu o atendimento. Use /retomar para reativar o agente."*
4. A **mensagem do agente é duplicada** no WhatsApp (enviada duas vezes)
5. O **agente é pausado automaticamente** quando não deveria

### Comportamento Esperado

1. Lead envia mensagem no WhatsApp
2. Agente responde normalmente
3. Mensagem é sincronizada para o Chatwoot (apenas para visualização do SDR)
4. O agente NÃO deve ser pausado (nenhum SDR interveio)
5. A mensagem NÃO deve ser duplicada no WhatsApp

---

## Análise de Causa Raiz

### O Loop de Feedback

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LOOP DE FEEDBACK                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Lead envia mensagem ──► WhatsApp ──► Z-API Webhook               │
│                                              │                       │
│  2. Agente processa e gera resposta          ▼                       │
│                                         Nosso Sistema                │
│  3. Resposta enviada ◄──────────────────────┘│                       │
│     │                                        │                       │
│     │                                        │                       │
│     ▼                                        ▼                       │
│  WhatsApp (OK)                    sync_message_to_chatwoot()         │
│                                              │                       │
│                                              │ POST /messages        │
│                                              │ message_type: outgoing│
│                                              │ private: false        │
│                                              ▼                       │
│                                         Chatwoot                     │
│                                              │                       │
│                                              │ Webhook message_created
│                                              │ sender.type: "user" ◄─┬── PROBLEMA!
│                                              │ (usuário da API)      │
│                                              ▼                       │
│  4. Webhook recebido ◄──────────────── Nosso Sistema                 │
│                                              │                       │
│  5. _is_sdr_message() = true ◄───────────────┘                       │
│     (sender.type == "user")                                          │
│                                                                      │
│  6. Agent pausado ERRONEAMENTE!                                      │
│                                                                      │
│  7. Mensagem enviada NOVAMENTE para WhatsApp ──► DUPLICAÇÃO!         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Evidência nos Logs

**Timestamp 14:40:05** - Agente responde normalmente:
```json
{"message": "Message processed successfully", "response_length": 486}
{"message": "Z-API message sent successfully", "phone": "5511945207618"}
```

**Timestamp 14:40:06** - Webhook do Chatwoot (PROBLEMA):
```json
{
  "event": "message_created",
  "content_in_root": "Olá, Anderson! 👋\n\nSeja bem-vindo à Seleto Industrial...",
  "sender_in_root": {"id": 1, "name": "Tiago", "type": "user"},  // ← SENDER É O USUÁRIO DA API!
  "message_type_root": "outgoing",
  "is_sdr": true  // ← INCORRETAMENTE DETECTADO COMO SDR
}
```

**Resultado:**
```json
{"message": "Agent paused for conversation", "reason": "sdr_intervention"}
{"message": "SDR message sent to WhatsApp", "message_length": 486}  // ← DUPLICAÇÃO!
```

### Causa Raiz Técnica

1. **API do Chatwoot não diferencia entre mensagens enviadas via API e mensagens digitadas no UI**
2. Quando uma mensagem é enviada via API com `message_type: "outgoing"`, o Chatwoot:
   - Cria a mensagem
   - Dispara webhook `message_created`
   - Define `sender` como o **usuário autenticado pela API token** (não um bot)
3. Nossa função `_is_sdr_message()` verifica apenas `sender.type == "user"`
4. Como o usuário da API é um "user", a mensagem é erroneamente classificada como intervenção de SDR

---

## Solução Proposta

### Opção 1: Cache de Mensagens Enviadas (Recomendada)

Criar um cache TTL de mensagens enviadas pelo bot para o Chatwoot. Quando receber um webhook, verificar se a mensagem está no cache e ignorá-la.

**Vantagens:**
- Não requer mudanças na configuração do Chatwoot
- Simples de implementar
- Baixo impacto no sistema existente

**Implementação:**

```python
# src/services/chatwoot_sync.py

import hashlib
import time
from threading import Lock

# Cache de mensagens enviadas recentemente pelo bot
# Estrutura: {hash_da_mensagem: timestamp_de_envio}
_sent_messages_cache: dict[str, float] = {}
_cache_lock = Lock()
_CACHE_TTL_SECONDS = 10  # Mensagens expiram após 10 segundos


def _get_message_hash(phone: str, content: str) -> str:
    """Gera hash único para identificar uma mensagem."""
    return hashlib.sha256(f"{phone}:{content}".encode()).hexdigest()[:16]


def _register_sent_message(phone: str, content: str) -> None:
    """Registra mensagem enviada para evitar loop de feedback."""
    msg_hash = _get_message_hash(phone, content)
    with _cache_lock:
        _sent_messages_cache[msg_hash] = time.time()
        # Limpeza de entradas expiradas
        current_time = time.time()
        expired = [k for k, v in _sent_messages_cache.items() 
                   if current_time - v > _CACHE_TTL_SECONDS]
        for k in expired:
            del _sent_messages_cache[k]


def is_bot_message(phone: str, content: str) -> bool:
    """Verifica se a mensagem foi enviada recentemente pelo bot."""
    msg_hash = _get_message_hash(phone, content)
    with _cache_lock:
        if msg_hash in _sent_messages_cache:
            timestamp = _sent_messages_cache[msg_hash]
            if time.time() - timestamp <= _CACHE_TTL_SECONDS:
                return True
            else:
                del _sent_messages_cache[msg_hash]
    return False
```

**Modificação no webhook:**

```python
# src/api/routes/webhook.py - process_chatwoot_message()

from src.services.chatwoot_sync import is_bot_message

# Após extrair phone e message_content...

# Verificar se é uma mensagem enviada pelo nosso bot (evitar loop de feedback)
if is_bot_message(phone, message_content):
    logger.debug(
        "Ignoring bot's own message (feedback loop prevention)",
        extra={"phone": phone, "content_preview": message_content[:50]},
    )
    return {"status": "ignored", "reason": "bot_message_feedback_loop"}
```

### Opção 2: Filtrar por message_type

Ignorar webhooks de mensagens `outgoing` completamente, já que:
- Mensagens do bot são `outgoing` (queremos ignorar)
- Mensagens do SDR também são `outgoing` (não queremos ignorar)

**Problema:** Esta opção não é viável pois impediria a detecção de intervenções do SDR.

### Opção 3: Usar API Bot/Agent separada

Criar um usuário "bot" no Chatwoot e usar suas credenciais para enviar mensagens.

**Problema:** Requer configuração adicional no Chatwoot e mudanças de infra.

---

## Plano de Correção

### Etapa 1: Implementar Cache de Mensagens

**Arquivo:** `src/services/chatwoot_sync.py`

1. Adicionar estruturas de cache com TTL
2. Implementar função `_register_sent_message()`
3. Implementar função `is_bot_message()`
4. Modificar `_sync_message_async()` para registrar mensagens enviadas

### Etapa 2: Atualizar Webhook

**Arquivo:** `src/api/routes/webhook.py`

1. Importar função `is_bot_message`
2. Adicionar verificação antes de processar `message_created`
3. Ignorar mensagens identificadas como do bot

### Etapa 3: Testes

1. Testar fluxo normal de conversa (sem intervenção)
2. Testar intervenção do SDR (deve pausar e funcionar)
3. Verificar que não há mais duplicação
4. Verificar que não há mais pausas automáticas incorretas

---

## Testes de Validação

### Cenário 1: Conversa Normal (Sem SDR)

| Passo | Ação | Resultado Esperado |
|-------|------|-------------------|
| 1 | Lead envia "oi" no WhatsApp | Mensagem aparece no Chatwoot |
| 2 | Agente responde | Resposta aparece no Chatwoot (1x) |
| 3 | Verificar WhatsApp | Apenas 1 mensagem do agente |
| 4 | Verificar status do agente | NÃO pausado |

### Cenário 2: Intervenção do SDR

| Passo | Ação | Resultado Esperado |
|-------|------|-------------------|
| 1 | SDR digita mensagem no Chatwoot | Mensagem enviada para WhatsApp |
| 2 | Verificar status | Agente PAUSADO |
| 3 | Lead responde | Agente NÃO responde |
| 4 | SDR digita "retomar" | Agente RETOMADO |
| 5 | Lead envia nova mensagem | Agente responde normalmente |

### Cenário 3: Retomada Automática

| Passo | Ação | Resultado Esperado |
|-------|------|-------------------|
| 1 | SDR pausa o agente | Agente pausado |
| 2 | Esperar horário comercial terminar | - |
| 3 | Lead envia mensagem fora do horário | Agente responde (auto-retomada) |

---

## Impacto

### Sistemas Afetados

- Webhook do Chatwoot
- Sincronização de mensagens para Chatwoot
- Fluxo de pausa/retomada do agente

### Riscos de Regressão

- Possível delay na detecção de mensagens do SDR (mitigado pelo TTL curto de 10s)
- Cache pode crescer em situações de alto volume (mitigado pela limpeza automática)

---

## Correção Implementada

### Arquivos Modificados

1. **`src/services/chatwoot_sync.py`**
   - Adicionado cache de mensagens enviadas com TTL de 15 segundos
   - Nova função `_register_sent_message()` para registrar mensagens do bot
   - Nova função `is_bot_message()` para verificar se uma mensagem é do bot
   - Modificado `_sync_message_async()` para registrar mensagens do bot antes de enviar

2. **`src/api/routes/webhook.py`**
   - Importada função `is_bot_message`
   - Adicionada verificação no início de `process_chatwoot_message()` para ignorar mensagens do bot

### Código Principal

```python
# src/services/chatwoot_sync.py

def is_bot_message(phone: str, content: str) -> bool:
    """
    Check if a message was recently sent by the bot.
    Used to prevent webhook feedback loops.
    """
    if not content:
        return False
    msg_hash = _get_message_hash(phone, content)
    with _sent_messages_lock:
        if msg_hash in _sent_messages_cache:
            timestamp = _sent_messages_cache[msg_hash]
            if time.time() - timestamp <= _SENT_MESSAGES_TTL_SECONDS:
                return True
    return False

# src/api/routes/webhook.py - process_chatwoot_message()

# BUG-003 FIX: Check if this is a message we sent ourselves
if is_bot_message(phone, message_content):
    logger.debug(
        "Ignoring bot's own message (feedback loop prevention)",
        extra={"phone": phone},
    )
    return {"status": "ignored", "reason": "bot_message_feedback_loop"}
```

---

## Histórico

| Data | Evento | Responsável |
|------|--------|-------------|
| 2026-01-07 | Bug identificado durante teste de integração | Usuário |
| 2026-01-07 | Análise de causa raiz documentada | Sistema |
| 2026-01-07 | Plano de correção definido | Sistema |
| 2026-01-07 | Correção implementada e deployada | Sistema |

