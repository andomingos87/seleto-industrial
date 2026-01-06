# Runbook: Reprocessar Mensagens com Falha

## Objetivo

Este runbook descreve como identificar e reprocessar mensagens que falharam durante o processamento pelo agente SDR. Isso pode ocorrer devido a falhas de integração, timeouts ou erros internos.

## Pré-requisitos

- Acesso aos logs do sistema
- Acesso ao banco de dados Supabase
- Acesso ao Chatwoot (para verificar histórico)
- Conhecimento do número de telefone ou período afetado

## Identificar Mensagens com Falha

### Via Logs

```bash
# Buscar erros de processamento nas últimas 24 horas
grep -E "error|failed|exception" /var/log/seleto/app.log | grep -E "process_message|webhook" | tail -100

# Buscar por número específico
grep "5511999999999" /var/log/seleto/app.log | grep -E "error|failed"

# Via Docker
docker compose logs app --since 24h | grep -E "error|failed"
```

### Via Métricas

```bash
# Verificar taxa de erro nas integrações
curl http://localhost:8000/metrics | grep -E "integration_requests_total.*error"

# Verificar mensagens com falha
curl http://localhost:8000/metrics | grep -E "webhook_events_total.*error"
```

### Via Banco de Dados

```sql
-- Verificar conversas sem resposta recente
SELECT
    c.lead_phone,
    c.last_message_at,
    c.message_count,
    cc.context_data->>'last_error' as last_error
FROM conversations c
LEFT JOIN conversation_context cc ON c.lead_phone = cc.lead_phone
WHERE c.last_message_at > NOW() - INTERVAL '24 hours'
  AND (
    cc.context_data->>'last_error' IS NOT NULL
    OR c.response_count < c.message_count
  )
ORDER BY c.last_message_at DESC;
```

### Via Chatwoot

1. Acesse o painel do Chatwoot
2. Filtre conversas "Abertas" ou "Pendentes"
3. Verifique conversas sem resposta do bot
4. Anote os números de telefone afetados

## Tipos de Falha

### 1. Falha de Integração WhatsApp (Z-API)
- **Sintoma:** Mensagem processada mas resposta não enviada
- **Log:** `Z-API message send failed`
- **Causa comum:** Rate limit, token expirado, número bloqueado

### 2. Falha de Processamento (LLM)
- **Sintoma:** Mensagem recebida mas não processada
- **Log:** `Error processing message`, `OpenAI API error`
- **Causa comum:** Timeout, quota excedida, erro de prompt

### 3. Falha de Persistência (Supabase)
- **Sintoma:** Conversa não registrada no banco
- **Log:** `Failed to save conversation`, `Supabase error`
- **Causa comum:** Conexão, constraint violation

### 4. Falha de Webhook
- **Sintoma:** Mensagem não chegou ao sistema
- **Log:** `Webhook error`, `Invalid payload`
- **Causa comum:** Formato inválido, autenticação

## Reprocessar Mensagens

### Opção 1: Via Chatwoot (Lead envia nova mensagem)

A forma mais simples é solicitar que o lead envie uma nova mensagem:

1. No Chatwoot, envie uma mensagem para o lead explicando o problema
2. O agente será pausado automaticamente
3. Após resolver o problema, use `/retomar`
4. Peça ao lead para reenviar a mensagem

### Opção 2: Reenviar via Webhook (Simulação)

Para reprocessar uma mensagem específica:

```bash
# Payload de mensagem de texto
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "event": "message",
    "messageType": "text",
    "text": {
      "message": "Conteúdo original da mensagem"
    },
    "fromMe": false,
    "momment": 1704556800000
  }'
```

### Opção 3: Reprocessar via Script

```python
# scripts/reprocess_message.py
import asyncio
from src.agents.sdr_agent import SDRAgent
from src.services.conversation_memory import get_conversation_memory

async def reprocess_message(phone: str, message: str):
    """Reprocessar uma mensagem manualmente."""
    agent = SDRAgent()
    memory = get_conversation_memory()

    # Carregar contexto existente
    context = await memory.get_context(phone)

    # Processar mensagem
    response = await agent.process_message(phone, message, context)

    print(f"Resposta: {response}")
    return response

# Uso
asyncio.run(reprocess_message("5511999999999", "Qual formadora vocês recomendam?"))
```

### Opção 4: Reprocessar em Lote

```python
# scripts/reprocess_batch.py
import asyncio
from datetime import datetime, timedelta
from supabase import create_client

async def get_failed_messages(since_hours: int = 24):
    """Obter mensagens que falharam nas últimas X horas."""
    # Implementação depende de como erros são registrados
    pass

async def reprocess_batch(phone_list: list[str]):
    """Reprocessar mensagens para lista de números."""
    for phone in phone_list:
        try:
            # Buscar última mensagem do lead
            # Reprocessar
            pass
        except Exception as e:
            print(f"Erro ao reprocessar {phone}: {e}")
            continue
```

## Verificação

Após reprocessar:

1. **Verificar resposta:**
   ```bash
   # Verificar nos logs
   grep "5511999999999" /var/log/seleto/app.log | tail -10
   ```

2. **Verificar no Chatwoot:**
   - Abrir a conversa
   - Confirmar que a resposta apareceu

3. **Verificar métricas:**
   ```bash
   curl http://localhost:8000/metrics | grep "success"
   ```

4. **Verificar no banco:**
   ```sql
   SELECT * FROM conversations
   WHERE lead_phone = '5511999999999'
   ORDER BY updated_at DESC LIMIT 1;
   ```

## Rollback

Se o reprocessamento causar problemas:

1. **Pausar agente para o número:**
   ```sql
   UPDATE conversation_context
   SET context_data = jsonb_set(
       context_data,
       '{agent_pause_state}',
       '{"paused": true, "reason": "rollback"}'::jsonb
   )
   WHERE lead_phone = '5511999999999';
   ```

2. **Notificar SDR para assumir:**
   - Abrir conversa no Chatwoot
   - SDR deve assumir manualmente

3. **Investigar causa raiz:**
   - Analisar logs completos
   - Verificar se há padrão de falha

## Troubleshooting

### Erro: "Rate limit exceeded" ao reprocessar
1. Aguarde alguns minutos entre reprocessamentos
2. Implemente backoff exponencial no script
3. Verifique limites da API OpenAI

### Erro: "Conversation context not found"
1. Verifique se o número está no formato correto (E.164)
2. Crie contexto inicial se necessário:
   ```sql
   INSERT INTO conversation_context (lead_phone, context_data)
   VALUES ('5511999999999', '{}')
   ON CONFLICT (lead_phone) DO NOTHING;
   ```

### Erro: "WhatsApp number blocked"
1. Verifique status do número no Z-API
2. Pode ser necessário contato com suporte Z-API
3. Considere usar outro canal para contato

### Mensagem reprocessada mas resposta duplicada
1. O sistema pode ter enviado resposta anteriormente
2. Verifique histórico no Chatwoot antes de reprocessar
3. Use flag de deduplicação se disponível

## Prevenção

Para evitar mensagens com falha:

1. **Monitorar métricas:**
   - Configure alertas para taxa de erro > 10%
   - Monitore latência P95

2. **Verificar integrações:**
   - Health check regular das APIs
   - Alertas para falhas de autenticação

3. **Backup e retry:**
   - O sistema possui retry automático com backoff
   - Mensagens são persistidas antes do processamento

## Logs Relevantes

```bash
# Padrões de log para buscar
grep "Webhook received" app.log      # Mensagem recebida
grep "process_message" app.log       # Início de processamento
grep "message sent" app.log          # Resposta enviada
grep "error|failed" app.log          # Erros
grep "retry" app.log                 # Tentativas de retry
```

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Arquivos relacionados:** `src/api/routes/webhook.py`, `src/agents/sdr_agent.py`
