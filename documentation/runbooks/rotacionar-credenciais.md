# Runbook: Rotacionar Credenciais

## Objetivo

Este runbook descreve o processo seguro de rotação de credenciais e API keys do sistema Seleto Industrial SDR Agent. A rotação regular de credenciais é uma prática de segurança importante.

## Pré-requisitos

- Acesso ao servidor de produção ou CI/CD
- Acesso aos painéis dos serviços (OpenAI, Supabase, Z-API, PipeRun, Chatwoot)
- Credenciais de administrador para cada serviço
- Janela de manutenção acordada (recomendado: fora do horário comercial)

## Credenciais do Sistema

| Serviço | Variáveis de Ambiente | Rotação Recomendada |
|---------|----------------------|---------------------|
| OpenAI | `OPENAI_API_KEY` | A cada 90 dias ou se comprometida |
| Supabase | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | A cada 180 dias |
| Z-API (WhatsApp) | `ZAPI_INSTANCE_ID`, `ZAPI_INSTANCE_TOKEN`, `ZAPI_CLIENT_TOKEN` | A cada 90 dias |
| PipeRun | `PIPERUN_API_TOKEN` | A cada 90 dias |
| Chatwoot | `CHATWOOT_API_URL`, `CHATWOOT_API_TOKEN` | A cada 90 dias |
| Alertas | `ALERT_SLACK_WEBHOOK_URL`, `ALERT_EMAIL_*` | Quando necessário |

## Passos

### Rotação OpenAI API Key

1. **Gerar nova chave:**
   - Acesse: https://platform.openai.com/api-keys
   - Clique em "Create new secret key"
   - Nomeie: `seleto-sdr-production-YYYY-MM-DD`
   - Copie a chave imediatamente (não será mostrada novamente)

2. **Atualizar ambiente:**
   ```bash
   # Atualizar .env ou secret manager
   OPENAI_API_KEY=sk-proj-...nova-chave...
   ```

3. **Reiniciar serviço:**
   ```bash
   docker compose restart app
   # ou
   systemctl restart seleto-sdr
   ```

4. **Verificar funcionamento:**
   ```bash
   curl -X POST http://localhost:8000/webhook/text \
     -H "Content-Type: application/json" \
     -d '{"phone": "5511999999999", "text": "Olá, teste"}'
   ```

5. **Revogar chave antiga:**
   - Volte ao painel OpenAI
   - Delete a chave antiga após confirmar que a nova funciona

### Rotação Supabase Credentials

1. **Gerar nova service role key:**
   - Acesse: https://supabase.com/dashboard/project/{project}/settings/api
   - A Service Role Key pode ser regenerada em Settings > API
   - **CUIDADO:** Isso invalida a chave anterior imediatamente

2. **Atualizar ambiente:**
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=eyJ...nova-chave...
   ```

3. **Reiniciar e verificar:**
   ```bash
   docker compose restart app

   # Verificar conexão
   curl http://localhost:8000/api/health | jq .database
   ```

### Rotação Z-API (WhatsApp)

1. **Gerar novo token:**
   - Acesse: https://developer.z-api.io/
   - Navegue até sua instância
   - Regenere o Instance Token ou Client Token

2. **Atualizar ambiente:**
   ```bash
   ZAPI_INSTANCE_ID=...
   ZAPI_INSTANCE_TOKEN=...novo-token...
   ZAPI_CLIENT_TOKEN=...novo-client-token...
   ```

3. **Reiniciar e verificar:**
   ```bash
   docker compose restart app

   # Testar envio de mensagem (use número de teste)
   # Verificar logs para "Z-API message sent successfully"
   ```

### Rotação PipeRun API Token

1. **Gerar novo token:**
   - Acesse: https://crm.piperun.com/
   - Vá em Configurações > API
   - Gere um novo token de API

2. **Atualizar ambiente:**
   ```bash
   PIPERUN_API_TOKEN=...novo-token...
   PIPERUN_PIPELINE_ID=...  # geralmente não muda
   PIPERUN_STAGE_ID=...     # geralmente não muda
   PIPERUN_ORIGIN_ID=...    # geralmente não muda
   ```

3. **Reiniciar e verificar:**
   ```bash
   docker compose restart app

   # Verificar integração
   curl http://localhost:8000/api/health | jq .integrations.piperun
   ```

### Rotação Chatwoot API Token

1. **Gerar novo token:**
   - Acesse seu painel Chatwoot
   - Vá em Settings > Account Settings > API Access Tokens
   - Gere um novo token

2. **Atualizar ambiente:**
   ```bash
   CHATWOOT_API_URL=https://seu-chatwoot.com
   CHATWOOT_API_TOKEN=...novo-token...
   CHATWOOT_ACCOUNT_ID=...  # geralmente não muda
   ```

3. **Reiniciar e verificar:**
   ```bash
   docker compose restart app

   # Verificar integração
   curl http://localhost:8000/api/health | jq .integrations.chatwoot
   ```

## Verificação Geral

Após rotacionar qualquer credencial:

1. **Verificar health check:**
   ```bash
   curl http://localhost:8000/api/health | jq
   ```
   - Todos os serviços devem mostrar status "healthy" ou "connected"

2. **Verificar logs:**
   ```bash
   docker compose logs --tail=50 app | grep -E "error|failed|unauthorized"
   ```

3. **Testar fluxo completo:**
   - Enviar mensagem de teste via WhatsApp
   - Verificar resposta do agente
   - Verificar sincronização no Chatwoot
   - Verificar registro no Supabase

4. **Monitorar métricas:**
   ```bash
   curl http://localhost:8000/metrics | grep -E "integration_requests_total.*error"
   ```

## Rollback

Se a nova credencial não funcionar:

1. **Restaurar credencial anterior:**
   - Atualize o `.env` com a credencial antiga
   - Reinicie o serviço

2. **Se chave antiga foi revogada:**
   - Gere uma nova chave no painel do serviço
   - Atualize e reinicie

3. **Documentar incidente:**
   - Registre o problema encontrado
   - Atualize este runbook se necessário

## Troubleshooting

### Erro: 401 Unauthorized após rotação
1. Verifique se a nova chave foi copiada corretamente (sem espaços extras)
2. Verifique se o arquivo `.env` foi salvo
3. Verifique se o serviço foi reiniciado

### Erro: Serviço não inicia após rotação
1. Verifique sintaxe do arquivo `.env`
2. Verifique se todas as variáveis obrigatórias estão presentes
3. Verifique logs de startup: `docker compose logs app`

### Erro: Integração funciona localmente mas não em produção
1. Verifique se as credenciais foram atualizadas no ambiente correto
2. Verifique secrets no CI/CD (GitHub Actions, etc.)
3. Verifique se há cache de configuração

### Alerta de autenticação disparado (TECH-024)
- Se um alerta de auth failure for disparado durante rotação, é esperado
- Verifique se o alerta para após a rotação bem-sucedida
- Se continuar, verifique a credencial rotacionada

## Checklist de Rotação

Use este checklist para cada rotação:

- [ ] Backup da credencial atual (armazenar de forma segura)
- [ ] Gerar nova credencial no painel do serviço
- [ ] Atualizar `.env` ou secret manager
- [ ] Reiniciar serviço
- [ ] Verificar health check
- [ ] Testar funcionalidade específica
- [ ] Monitorar logs por 15 minutos
- [ ] Revogar credencial antiga
- [ ] Documentar data da rotação

## Cronograma de Rotação

Mantenha um registro das rotações:

| Data | Serviço | Executado por | Próxima rotação |
|------|---------|---------------|-----------------|
| 2026-01-06 | OpenAI | Sistema | 2026-04-06 |
| ... | ... | ... | ... |

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Arquivos relacionados:** `.env`, `src/config/settings.py`
