# Processos LGPD - Seleto Industrial SDR Agent

> TECH-031: Documentação de Processos LGPD
> Data: 2026-01-06
> Versão: 1.0

## 1. Visão Geral

Este documento descreve os processos para atender aos direitos dos titulares de dados conforme a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018).

### Direitos do Titular (Art. 18 LGPD)

| Direito | Endpoint | Descrição |
|---------|----------|-----------|
| Acesso | `GET /api/lgpd/data-export/{phone}` | Confirmar existência e acessar dados |
| Correção | `PUT /api/lgpd/data-correction/{phone}` | Corrigir dados incompletos/inexatos |
| Anonimização/Exclusão | `DELETE /api/lgpd/data-deletion/{phone}` | Anonimizar ou excluir dados |
| Portabilidade | `GET /api/lgpd/data-export/{phone}` | Exportar dados em formato interoperável |

---

## 2. Processo de Solicitação de Acesso

### 2.1. Fluxo do Processo

```
Titular                    Sistema                    Operador
   │                          │                          │
   │  1. Solicita acesso      │                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │                          │  2. Valida identidade    │
   │                          │<─────────────────────────│
   │                          │                          │
   │                          │  3. Executa endpoint     │
   │                          │  GET /api/lgpd/data-export/{phone}
   │                          │                          │
   │  4. Retorna dados        │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │                          │  5. Registra auditoria   │
   │                          │─────────────────────────>│
```

### 2.2. Procedimento Operacional

1. **Recebimento da Solicitação**
   - O titular entra em contato solicitando acesso aos seus dados
   - Canais: email, WhatsApp, ou formulário

2. **Validação de Identidade**
   - Confirmar que o solicitante é o titular dos dados
   - Solicitar confirmação via telefone cadastrado
   - Registrar método de validação

3. **Execução**
   ```bash
   # Via API
   curl -X GET "https://api.seleto.com/api/lgpd/data-export/{phone}"

   # Resposta: JSON com todos os dados do titular
   ```

4. **Entrega dos Dados**
   - Formato: JSON estruturado
   - Prazo: Até 15 dias (Art. 19 LGPD)
   - Canal: Email seguro ou download via link temporário

5. **Registro**
   - Todas as solicitações são registradas em `audit_logs`
   - Manter registro por 5 anos

### 2.3. Dados Retornados

```json
{
  "phone": "5511999999999",
  "lead": {
    "id": "uuid",
    "name": "Nome do Titular",
    "email": "email@exemplo.com",
    "city": "São Paulo",
    "uf": "SP",
    "company": "Empresa LTDA",
    "classification": "quente",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "conversations": [...],
  "context": {...},
  "empresas": [...],
  "orcamentos": [...],
  "exported_at": "2026-01-06T00:00:00Z"
}
```

---

## 3. Processo de Correção de Dados

### 3.1. Fluxo do Processo

```
Titular                    Sistema                    Operador
   │                          │                          │
   │  1. Solicita correção    │                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │                          │  2. Valida identidade    │
   │                          │<─────────────────────────│
   │                          │                          │
   │                          │  3. Executa endpoint     │
   │                          │  PUT /api/lgpd/data-correction/{phone}
   │                          │                          │
   │  4. Confirma correção    │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │                          │  5. Registra auditoria   │
   │                          │─────────────────────────>│
```

### 3.2. Procedimento Operacional

1. **Recebimento da Solicitação**
   - O titular informa quais dados deseja corrigir
   - Fornecer dados corretos para substituição

2. **Validação de Identidade**
   - Confirmar que o solicitante é o titular dos dados
   - Validar os dados fornecidos

3. **Execução**
   ```bash
   curl -X PUT "https://api.seleto.com/api/lgpd/data-correction/{phone}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Nome Corrigido",
       "email": "novo.email@exemplo.com"
     }'
   ```

4. **Confirmação**
   - Informar titular sobre a correção realizada
   - Fornecer comprovante se solicitado

### 3.3. Campos Corrigíveis

| Campo | Descrição |
|-------|-----------|
| `name` | Nome do titular |
| `email` | Email de contato |
| `city` | Cidade |
| `uf` | Estado (UF) |
| `company` | Nome da empresa |

---

## 4. Processo de Exclusão/Anonimização

### 4.1. Fluxo do Processo

```
Titular                    Sistema                    Operador
   │                          │                          │
   │  1. Solicita exclusão    │                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │                          │  2. Valida identidade    │
   │                          │<─────────────────────────│
   │                          │                          │
   │                          │  3. Verifica obrigações  │
   │                          │     legais de retenção   │
   │                          │                          │
   │                          │  4. Executa endpoint     │
   │                          │  DELETE /api/lgpd/data-deletion/{phone}
   │                          │                          │
   │  5. Confirma exclusão    │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │                          │  6. Registra auditoria   │
   │                          │─────────────────────────>│
```

### 4.2. Procedimento Operacional

1. **Recebimento da Solicitação**
   - O titular solicita exclusão de seus dados
   - Informar sobre consequências (perda de histórico)

2. **Validação de Identidade**
   - Confirmar que o solicitante é o titular dos dados
   - Obter consentimento explícito para exclusão

3. **Verificação de Obrigações Legais**
   - Verificar se há obrigações de retenção (contratos, fiscal)
   - Se houver, informar titular e aplicar anonimização parcial

4. **Execução**
   ```bash
   # Anonimização (recomendado)
   curl -X DELETE "https://api.seleto.com/api/lgpd/data-deletion/{phone}"

   # Exclusão permanente (quando permitido)
   curl -X DELETE "https://api.seleto.com/api/lgpd/data-deletion/{phone}?hard_delete=true"
   ```

5. **Confirmação**
   - Informar titular sobre a ação realizada
   - Fornecer protocolo de atendimento

### 4.3. Tipos de Exclusão

| Tipo | Descrição | Uso |
|------|-----------|-----|
| **Anonimização** | Substitui dados por placeholders | Recomendado - preserva estatísticas |
| **Exclusão Permanente** | Remove todos os registros | Somente quando não há obrigações legais |

### 4.4. Dados Anonimizados

Após anonimização:
- `phone`: `ANON-9999` (últimos 4 dígitos preservados)
- `name`: `[NOME]`
- `email`: `[EMAIL]`
- Mensagens: Dados pessoais substituídos por placeholders

---

## 5. Processo de Portabilidade

### 5.1. Fluxo do Processo

Utiliza o mesmo endpoint de Acesso (`GET /api/lgpd/data-export/{phone}`).

### 5.2. Formato de Exportação

- **Formato:** JSON estruturado
- **Encoding:** UTF-8
- **Estrutura:** Conforme seção 2.3

### 5.3. Instruções para Transferência

1. Exportar dados via endpoint
2. Fornecer arquivo JSON ao titular
3. O titular pode fornecer o arquivo ao novo controlador
4. Formato interoperável permite importação em outros sistemas

---

## 6. Jobs de Retenção Automática

### 6.1. Configuração

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| `TRANSCRIPT_RETENTION_DAYS` | 90 | Dias para reter mensagens |
| `CONTEXT_RETENTION_DAYS` | 90 | Dias para reter contexto |
| `LEAD_INACTIVITY_DAYS` | 365 | Dias de inatividade para anonimização |
| `AUDIT_RETENTION_DAYS` | 90 | Dias para reter audit logs |

### 6.2. Execução dos Jobs

```bash
# Executar todos os jobs
python -m src.jobs.data_retention_job --all

# Apenas jobs diários
python -m src.jobs.data_retention_job --daily

# Apenas jobs semanais
python -m src.jobs.data_retention_job --weekly

# Via API
curl -X POST "https://api.seleto.com/api/lgpd/run-retention-jobs?job_type=all"
```

### 6.3. Agendamento Recomendado (Cron)

```cron
# Jobs diários - 3h da manhã
0 3 * * * /path/to/python -m src.jobs.data_retention_job --daily

# Jobs semanais - Domingo 4h da manhã
0 4 * * 0 /path/to/python -m src.jobs.data_retention_job --weekly
```

---

## 7. Trilha de Auditoria

### 7.1. O que é Registrado

Todas as operações LGPD são registradas na tabela `audit_logs`:

| Campo | Descrição |
|-------|-----------|
| `action` | `API_CALL` |
| `entity_type` | `lgpd` |
| `metadata.service` | `lgpd` |
| `metadata.endpoint` | Endpoint chamado |
| `metadata.method` | GET, PUT, DELETE, POST |
| `metadata.status_code` | Código HTTP |
| `timestamp` | Data/hora da operação |

### 7.2. Consulta de Audit Logs

```sql
SELECT * FROM audit_logs
WHERE entity_type = 'lgpd'
ORDER BY timestamp DESC
LIMIT 100;
```

---

## 8. Prazos Legais

| Direito | Prazo LGPD | Prazo Interno |
|---------|------------|---------------|
| Acesso | 15 dias | 5 dias úteis |
| Correção | Imediato ou 15 dias | 3 dias úteis |
| Exclusão | 15 dias | 5 dias úteis |
| Portabilidade | 15 dias | 5 dias úteis |

---

## 9. Contatos

| Função | Responsável | Contato |
|--------|-------------|---------|
| DPO (Encarregado) | A definir | - |
| Suporte Técnico | Equipe Backend | - |
| Jurídico | A definir | - |

---

## 10. Histórico de Revisões

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2026-01-06 | 1.0 | Documento inicial | Claude Code |
