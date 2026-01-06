# Runbook: Verificar Saúde do Sistema

## Objetivo

Este runbook descreve como diagnosticar e verificar a saúde geral do sistema Seleto Industrial SDR Agent. Use este procedimento para verificações de rotina ou ao investigar problemas.

## Pré-requisitos

- Acesso ao servidor (SSH ou console)
- Acesso ao painel Supabase
- Acesso ao Chatwoot
- curl ou ferramenta HTTP instalada

## Verificações Rápidas

### 1. Health Check Básico

```bash
# Health check simples
curl http://localhost:8000/health

# Resposta esperada:
# {"status": "healthy"}
```

### 2. Health Check Detalhado

```bash
# Health check com status de integrações
curl http://localhost:8000/api/health | jq

# Resposta esperada:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2026-01-06T12:00:00Z",
#   "database": "connected",
#   "integrations": {
#     "openai": "configured",
#     "zapi": "configured",
#     "piperun": "configured",
#     "chatwoot": "configured"
#   }
# }
```

### 3. Verificar Métricas

```bash
# Endpoint Prometheus
curl http://localhost:8000/metrics

# Verificar taxa de erro
curl http://localhost:8000/metrics | grep -E "_total.*error" | head -10

# Verificar latência
curl http://localhost:8000/metrics | grep -E "duration_seconds"
```

## Checklist de Verificação

### Infraestrutura

- [ ] **Container/Processo rodando:**
  ```bash
  docker compose ps
  # ou
  systemctl status seleto-sdr
  ```

- [ ] **CPU e Memória:**
  ```bash
  docker stats seleto-sdr-app --no-stream
  # ou
  top -bn1 | head -20
  ```

- [ ] **Disco:**
  ```bash
  df -h
  ```

- [ ] **Logs recentes:**
  ```bash
  docker compose logs --tail=50 app
  ```

### Integrações

- [ ] **OpenAI:**
  ```bash
  # Verificar se API key está configurada
  grep -c "OPENAI_API_KEY" .env

  # Testar conexão (via aplicação)
  curl http://localhost:8000/api/health | jq .integrations.openai
  ```

- [ ] **Supabase:**
  ```bash
  # Testar conexão
  curl http://localhost:8000/api/health | jq .database

  # Verificar no painel Supabase
  # - Conexões ativas
  # - Queries lentas
  ```

- [ ] **Z-API (WhatsApp):**
  ```bash
  curl http://localhost:8000/api/health | jq .integrations.zapi

  # Verificar métricas
  curl http://localhost:8000/metrics | grep "whatsapp"
  ```

- [ ] **PipeRun:**
  ```bash
  curl http://localhost:8000/api/health | jq .integrations.piperun
  ```

- [ ] **Chatwoot:**
  ```bash
  curl http://localhost:8000/api/health | jq .integrations.chatwoot
  ```

### Funcionalidade

- [ ] **Recebimento de webhooks:**
  ```bash
  # Verificar logs de webhook
  grep "webhook" /var/log/seleto/app.log | tail -10

  # Verificar métricas
  curl http://localhost:8000/metrics | grep "webhook_events_total"
  ```

- [ ] **Processamento de mensagens:**
  ```bash
  # Verificar métricas de agente
  curl http://localhost:8000/metrics | grep "agent_messages_total"
  ```

- [ ] **Envio de respostas:**
  ```bash
  curl http://localhost:8000/metrics | grep "integration_requests_total.*whatsapp.*success"
  ```

## Diagnóstico de Problemas

### Alta Latência

1. **Verificar latência por endpoint:**
   ```bash
   curl http://localhost:8000/metrics | grep "http_request_duration_seconds"
   ```

2. **Verificar latência de integrações:**
   ```bash
   curl http://localhost:8000/metrics | grep "integration_request_duration_seconds"
   ```

3. **Verificar recursos:**
   ```bash
   docker stats --no-stream
   ```

4. **Ações corretivas:**
   - Reiniciar serviço se necessário
   - Verificar limites de rate da OpenAI
   - Verificar performance do Supabase

### Alta Taxa de Erro

1. **Identificar integração com erro:**
   ```bash
   curl http://localhost:8000/metrics | grep "_total.*error"
   ```

2. **Verificar logs de erro:**
   ```bash
   grep -E "error|exception|failed" /var/log/seleto/app.log | tail -50
   ```

3. **Verificar alertas:**
   ```bash
   # Se Slack configurado, verificar canal de alertas
   # Verificar email de alertas
   ```

### Serviço Não Responde

1. **Verificar se está rodando:**
   ```bash
   docker compose ps
   docker compose logs --tail=100 app
   ```

2. **Verificar porta:**
   ```bash
   netstat -tlnp | grep 8000
   # ou
   ss -tlnp | grep 8000
   ```

3. **Reiniciar serviço:**
   ```bash
   docker compose restart app
   ```

### Problemas de Banco de Dados

1. **Verificar conexão:**
   ```bash
   curl http://localhost:8000/api/health | jq .database
   ```

2. **Verificar no Supabase:**
   - Acessar painel: https://supabase.com/dashboard
   - Verificar Database > Connections
   - Verificar Logs

3. **Queries lentas:**
   ```sql
   -- No Supabase SQL Editor
   SELECT * FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```

## Monitoramento Contínuo

### Configurar Alertas (TECH-024)

O sistema possui alertas configurados para:
- Taxa de erro > 10%
- Latência P95 > 10s
- Falha de autenticação

Configuração em `src/config/settings.py`:
```python
ALERT_SLACK_WEBHOOK_URL = "..."
ALERT_ERROR_RATE_THRESHOLD = 0.10
ALERT_LATENCY_THRESHOLD_SECONDS = 10.0
```

### Dashboard de Métricas

Se Prometheus/Grafana configurado:
1. Acessar Grafana
2. Verificar dashboard "Seleto SDR"
3. Painéis importantes:
   - Request Rate
   - Error Rate
   - Latency P50/P95/P99
   - Integration Status

### Logs Centralizados

Padrões de log importantes:
```bash
# Erros críticos
grep "CRITICAL" app.log

# Falhas de integração
grep "integration.*failed" app.log

# Timeouts
grep "timeout" app.log

# Rate limits
grep "429\|rate.limit" app.log
```

## Relatório de Status

Use este template para reportar status:

```markdown
## Status Report - [DATA]

### Resumo
- **Status Geral:** [Healthy/Degraded/Down]
- **Uptime:** [XX horas/dias]
- **Última verificação:** [TIMESTAMP]

### Métricas (últimas 24h)
- **Requisições totais:** XXXX
- **Taxa de erro:** X.XX%
- **Latência P95:** XXXms

### Integrações
| Serviço | Status | Última verificação |
|---------|--------|-------------------|
| OpenAI | OK/Error | HH:MM |
| Supabase | OK/Error | HH:MM |
| Z-API | OK/Error | HH:MM |
| PipeRun | OK/Error | HH:MM |
| Chatwoot | OK/Error | HH:MM |

### Incidentes
- [Nenhum / Descrever incidentes]

### Ações Pendentes
- [Nenhuma / Listar ações]
```

## Verificação Periódica

### Diária
- [ ] Health check básico
- [ ] Verificar logs de erro
- [ ] Verificar alertas recebidos

### Semanal
- [ ] Health check detalhado
- [ ] Análise de métricas
- [ ] Revisão de logs

### Mensal
- [ ] Relatório de status completo
- [ ] Verificação de credenciais próximas de expirar
- [ ] Revisão de capacidade

## Contatos de Emergência

| Serviço | Suporte |
|---------|---------|
| OpenAI | https://help.openai.com |
| Supabase | https://supabase.com/support |
| Z-API | https://developer.z-api.io/suporte |
| PipeRun | Suporte via CRM |
| Chatwoot | https://www.chatwoot.com/docs |

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Arquivos relacionados:** `src/services/metrics.py`, `src/services/alerts.py`
