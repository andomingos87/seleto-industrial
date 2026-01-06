# Runbook: Solicitacoes LGPD

> Ultima atualizacao: 2026-01-06
> Versao: 1.0
> Responsavel: Equipe de Operacoes

## Objetivo

Atender solicitacoes de titulares de dados conforme Lei Geral de Protecao de Dados (LGPD).

## Pre-requisitos

- Acesso ao sistema via API
- Validacao de identidade do titular
- Registro da solicitacao

## Prazos Legais

| Solicitacao | Prazo LGPD | Prazo Interno |
|-------------|------------|---------------|
| Acesso | 15 dias | 5 dias uteis |
| Correcao | 15 dias | 5 dias uteis |
| Exclusao | 15 dias | 5 dias uteis |
| Portabilidade | 15 dias | 5 dias uteis |

## Procedimentos

### 1. Solicitacao de Acesso (Data Export)

**Quando usar**: Titular quer saber quais dados temos sobre ele.

```bash
# Substituir {phone} pelo telefone do titular (ex: 5511999999999)
curl -X GET "https://api.seleto.com/api/lgpd/data-export/{phone}"

# Resposta: JSON com todos os dados do titular
{
  "phone": "5511999999999",
  "lead": { ... },
  "conversations": [ ... ],
  "context": { ... },
  "orcamentos": [ ... ],
  "empresas": [ ... ]
}
```

**Entrega**: Enviar JSON formatado via email seguro ou link temporario.

### 2. Solicitacao de Correcao

**Quando usar**: Titular quer corrigir dados incorretos.

```bash
curl -X PUT "https://api.seleto.com/api/lgpd/data-correction/{phone}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nome Correto",
    "email": "email.correto@example.com",
    "city": "Sao Paulo",
    "uf": "SP"
  }'
```

**Nota**: Apenas campos fornecidos serao atualizados.

### 3. Solicitacao de Exclusao/Anonimizacao

**Quando usar**: Titular quer que seus dados sejam removidos.

```bash
# Anonimizacao (recomendado - mantem registro para obrigacoes legais)
curl -X DELETE "https://api.seleto.com/api/lgpd/data-deletion/{phone}?hard_delete=false"

# Exclusao total (use apenas se necessario)
curl -X DELETE "https://api.seleto.com/api/lgpd/data-deletion/{phone}?hard_delete=true"
```

**Resultado da Anonimizacao**:
- Telefone: `5511999999999` -> `ANON-9999`
- Nome: `Joao Silva` -> `[NOME]`
- Email: `joao@email.com` -> `[EMAIL]`

### 4. Portabilidade

**Quando usar**: Titular quer levar dados para outro controlador.

Usar o mesmo endpoint de data-export - formato JSON e interoperavel.

### 5. Executar Jobs de Retencao (Manual)

```bash
# Via API
curl -X POST "https://api.seleto.com/api/lgpd/run-retention-jobs"

# Via CLI
python -m src.jobs.data_retention_job --all
```

### 6. Verificar Configuracao de Retencao

```bash
curl -X GET "https://api.seleto.com/api/lgpd/retention-config"

# Resposta:
{
  "TRANSCRIPT_RETENTION_DAYS": 90,
  "CONTEXT_RETENTION_DAYS": 90,
  "LEAD_INACTIVITY_DAYS": 365,
  "PENDING_OPERATIONS_RETENTION_DAYS": 7
}
```

## Verificacao

1. Todas as solicitacoes sao registradas em `audit_logs`
2. Verificar log apos cada operacao:
   ```bash
   # Consultar logs de auditoria LGPD
   SELECT * FROM audit_logs
   WHERE entity_type = 'lgpd'
   ORDER BY timestamp DESC;
   ```

## Checklist de Atendimento

- [ ] Solicitacao recebida e registrada
- [ ] Identidade do titular validada
- [ ] Operacao executada via API
- [ ] Resultado verificado
- [ ] Resposta enviada ao titular
- [ ] Prazo cumprido (< 15 dias)

## Troubleshooting

### Telefone Nao Encontrado

Se o endpoint retornar vazio, significa que nao temos dados do titular.
Responder ao titular informando que nao ha dados registrados.

### Erro de Validacao

Verificar se o telefone esta no formato correto (apenas digitos, 10-13 caracteres).

### Auditoria Nao Registrada

Verificar conexao com Supabase e tabela `audit_logs`.

## Rollback

**Anonimizacao**: NAO reversivel por design (dados originais nao podem ser recuperados).

**Correcao**: Manter dados anteriores no log de auditoria para referencia.

## Referencias

- [Processos LGPD Detalhados](../lgpd/processos-lgpd.md)
- [Mapeamento de Dados Pessoais](../lgpd/mapeamento-dados-pessoais.md)
- [Documentacao de Seguranca](../../.context/docs/security.md)
