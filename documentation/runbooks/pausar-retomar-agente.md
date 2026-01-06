# Runbook: Pausar/Retomar Agente SDR

## Objetivo

Este runbook descreve como pausar e retomar o agente SDR manualmente para conversas específicas. O agente é automaticamente pausado quando um SDR envia uma mensagem via Chatwoot, mas pode ser necessário controlar manualmente em alguns cenários.

## Pré-requisitos

- Acesso ao painel do Chatwoot
- Acesso ao banco de dados Supabase (para operações avançadas)
- Conhecimento do número de telefone do lead (formato E.164: 5511999999999)

## Cenários

### Quando pausar o agente?
- SDR quer assumir a conversa manualmente
- Problema técnico no agente que precisa ser isolado
- Lead solicitou atendimento humano
- Situação complexa que requer intervenção humana

### Quando retomar o agente?
- SDR concluiu o atendimento manual
- Problema técnico foi resolvido
- Lead pode voltar ao atendimento automatizado

## Passos

### Opção 1: Via Chatwoot (Recomendado)

#### Pausar Agente
1. Acesse o painel do Chatwoot
2. Abra a conversa do lead
3. **Envie qualquer mensagem** na conversa
   - O agente será automaticamente pausado quando detectar mensagem do SDR
4. O lead verá a mensagem do SDR e o agente não responderá mais automaticamente

#### Retomar Agente
1. Na conversa do Chatwoot, envie o comando: `/retomar` ou `/continuar`
2. O sistema confirmará: "Agente retomado com sucesso. O bot voltará a responder automaticamente."
3. O agente voltará a responder mensagens do lead

### Opção 2: Via API (Para integrações)

#### Pausar Agente
```bash
# Endpoint não exposto publicamente por segurança
# Use a opção via Chatwoot
```

#### Retomar Agente
```bash
# Envie mensagem de comando via webhook do Chatwoot
curl -X POST https://api.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/conversations/{CONVERSATION_ID}/messages \
  -H "Content-Type: application/json" \
  -H "api_access_token: {CHATWOOT_API_TOKEN}" \
  -d '{"content": "/retomar"}'
```

### Opção 3: Via Banco de Dados (Emergência)

#### Verificar estado atual
```sql
-- Verificar se agente está pausado para um número
SELECT
    lead_phone,
    context_data->'agent_pause_state' as pause_state
FROM conversation_context
WHERE lead_phone = '5511999999999';
```

#### Pausar Agente via SQL
```sql
-- CUIDADO: Use apenas em emergências
UPDATE conversation_context
SET context_data = jsonb_set(
    COALESCE(context_data, '{}'::jsonb),
    '{agent_pause_state}',
    '{
        "paused": true,
        "paused_at": "2026-01-06T12:00:00Z",
        "reason": "manual_intervention",
        "sender_name": "Operador"
    }'::jsonb
)
WHERE lead_phone = '5511999999999';
```

#### Retomar Agente via SQL
```sql
UPDATE conversation_context
SET context_data = jsonb_set(
    COALESCE(context_data, '{}'::jsonb),
    '{agent_pause_state}',
    '{
        "paused": false,
        "resumed_at": "2026-01-06T12:30:00Z",
        "resume_reason": "manual_intervention",
        "resumed_by": "Operador"
    }'::jsonb
)
WHERE lead_phone = '5511999999999';
```

#### Listar todas as conversas pausadas
```sql
SELECT
    lead_phone,
    context_data->'agent_pause_state'->>'paused_at' as paused_at,
    context_data->'agent_pause_state'->>'sender_name' as paused_by,
    context_data->'agent_pause_state'->>'reason' as reason
FROM conversation_context
WHERE (context_data->'agent_pause_state'->>'paused')::boolean = true
ORDER BY (context_data->'agent_pause_state'->>'paused_at') DESC;
```

## Verificação

1. **Após pausar:**
   - Envie uma mensagem de teste via WhatsApp para o número
   - Verifique que o agente NÃO responde
   - A mensagem deve aparecer apenas no Chatwoot

2. **Após retomar:**
   - Envie uma mensagem de teste via WhatsApp para o número
   - Verifique que o agente RESPONDE automaticamente
   - A resposta deve aparecer no WhatsApp e no Chatwoot

3. **Verificar logs:**
   ```bash
   # Procurar logs de pause/resume
   grep -E "paused|resumed" /var/log/seleto/app.log
   ```

## Rollback

Se o agente não estiver funcionando corretamente após alterações:

1. **Limpar cache em memória** (requer restart):
   ```bash
   # Via Docker
   docker compose restart app

   # Ou reiniciar serviço
   systemctl restart seleto-sdr
   ```

2. **Resetar estado no banco:**
   ```sql
   -- Remover estado de pause completamente
   UPDATE conversation_context
   SET context_data = context_data - 'agent_pause_state'
   WHERE lead_phone = '5511999999999';
   ```

## Troubleshooting

### Problema: Comando /retomar não funciona
1. Verifique se está enviando pelo Chatwoot (não pelo WhatsApp)
2. Verifique se o comando está exatamente como `/retomar` ou `/continuar`
3. Verifique se o agente realmente está pausado (consulte o banco)

### Problema: Agente não pausa quando SDR envia mensagem
1. Verifique se o webhook do Chatwoot está configurado corretamente
2. Verifique os logs do webhook: `POST /webhook/chatwoot`
3. Verifique se a mensagem tem `message_type: outgoing` no payload

### Problema: Agente responde mesmo pausado
1. Verifique se o cache em memória está desatualizado (reinicie o serviço)
2. Verifique o estado no banco de dados
3. Verifique se há múltiplas instâncias do serviço

### Problema: Fora do horário comercial, agente não retoma
- Comportamento esperado: fora do horário comercial, o agente auto-retoma
- Verifique configuração em `config/business_hours.yaml`
- Horário padrão: Seg-Sex 08:00-18:00 (America/Sao_Paulo)

## Comportamento Automático

O sistema possui comportamentos automáticos que devem ser considerados:

1. **Pausa automática:**
   - Quando SDR envia mensagem via Chatwoot
   - Detectado via webhook `POST /webhook/chatwoot`

2. **Retomada automática (fora do horário comercial):**
   - Quando lead envia nova mensagem fora do horário comercial
   - Horário comercial: Seg-Sex 08:00-18:00 (configurável)

3. **Cache de estado:**
   - Estado é armazenado em memória para performance
   - Persistido no Supabase para sobreviver a restarts

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Arquivos relacionados:** `src/services/agent_pause.py`, `src/services/business_hours.py`
