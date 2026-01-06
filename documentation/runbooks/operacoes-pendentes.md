# Runbook: Gerenciar Operacoes Pendentes

> Ultima atualizacao: 2026-01-06
> Versao: 1.0
> Responsavel: Equipe de Operacoes

## Objetivo

Gerenciar operacoes pendentes de sincronizacao com o CRM (Piperun) quando ocorrem falhas de integracao.

## Pre-requisitos

- Acesso ao sistema via API
- Conhecimento de operacoes de CRM
- Permissao de administrador

## Cenarios

### 1. Verificar Status das Operacoes

```bash
# Via API
curl -X GET "https://api.seleto.com/api/pending-operations/status"

# Resposta esperada:
{
  "pending": 5,
  "processing": 1,
  "completed": 100,
  "failed": 2,
  "total": 108
}
```

### 2. Listar Operacoes Pendentes

```bash
curl -X GET "https://api.seleto.com/api/pending-operations/list?limit=50"
```

### 3. Reprocessar Todas as Pendentes

```bash
# Via API
curl -X POST "https://api.seleto.com/api/pending-operations/process"

# Via CLI
python -m src.jobs.sync_pending_operations
```

### 4. Reprocessar Operacao Especifica

```bash
curl -X POST "https://api.seleto.com/api/pending-operations/{operation_id}/retry"
```

### 5. Resetar Operacao Falha

```bash
curl -X POST "https://api.seleto.com/api/pending-operations/{operation_id}/reset"
```

### 6. Reprocessar Todas as Falhas

```bash
curl -X POST "https://api.seleto.com/api/pending-operations/retry-all-failed"
```

## Alertas

Sistema gera alertas automaticos:

| Condicao | Threshold | Acao |
|----------|-----------|------|
| Pendentes > 50 | `PENDING_ALERT_THRESHOLD=50` | Verificar CRM |
| Falhas > 10 | `FAILED_ALERT_THRESHOLD=10` | Investigar erros |

## Verificacao

1. Verificar que contagem de pendentes diminui
2. Verificar que contagem de completed aumenta
3. Verificar logs de erro para operacoes falhas
4. Confirmar sincronizacao no CRM (Piperun)

## Troubleshooting

### Operacoes Continuam Falhando

1. Verificar conectividade com Piperun
2. Verificar se token do Piperun esta valido
3. Verificar logs de erro detalhados:
   ```bash
   curl -X GET "https://api.seleto.com/api/pending-operations/{id}"
   ```

### Volume Alto de Pendentes

1. Verificar se CRM esta disponivel
2. Verificar rate limits do Piperun
3. Considerar aumentar intervalo entre retries

### Erro de Autenticacao

1. Rotacionar `PIPERUN_API_TOKEN`
2. Ver runbook: [Rotacionar Credenciais](./rotacionar-credenciais.md)

## Rollback

Nao aplicavel - operacoes pendentes nao afetam dados existentes.

## Referencias

- [Documentacao de Arquitetura](../../.context/docs/architecture.md#sistema-de-fallback-para-crm-tech-030)
- [Backlog TECH-030](../backlog.md)
