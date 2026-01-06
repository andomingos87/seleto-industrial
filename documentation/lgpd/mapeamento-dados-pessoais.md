# Mapeamento de Dados Pessoais - LGPD

> TECH-031: Política de Retenção de Dados e LGPD
> Data: 2026-01-06
> Status: Documentado

## 1. Visão Geral

Este documento mapeia todos os dados pessoais armazenados no sistema Seleto Industrial SDR Agent, conforme exigido pela Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018).

### Classificação de Dados

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **Identificador Direto** | Dados que identificam diretamente uma pessoa | Nome, telefone, email, CPF, CNPJ |
| **Identificador Indireto** | Dados que podem identificar quando combinados | Cidade + Segmento + Cargo |
| **Dado Sensível** | Dados que requerem proteção especial | Não aplicável neste sistema |

---

## 2. Tabelas com Dados Pessoais

### 2.1. Tabela: `leads`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `phone` | VARCHAR | Identificador Direto | 1 ano após inatividade | Hash ou [TELEFONE] |
| `name` | VARCHAR | Identificador Direto | 1 ano após inatividade | [NOME] |
| `email` | VARCHAR | Identificador Direto | 1 ano após inatividade | [EMAIL] |
| `city` | VARCHAR | Identificador Indireto | Manter | - |
| `uf` | VARCHAR(2) | Identificador Indireto | Manter | - |
| `company` | VARCHAR | Identificador Indireto | Manter | - |
| `position` | VARCHAR | Identificador Indireto | Manter | - |
| `classification` | VARCHAR | Dado Operacional | Manter | - |
| `crm_sync_status` | VARCHAR | Dado Operacional | Manter | - |
| `created_at` | TIMESTAMP | Metadado | Manter | - |
| `updated_at` | TIMESTAMP | Metadado | Manter | - |

**Critério de Inatividade:** Lead sem interação (mensagens) há mais de 365 dias.

---

### 2.2. Tabela: `conversation_messages`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `lead_phone` | VARCHAR | Identificador Direto | 90 dias | Hash ou remover |
| `role` | VARCHAR | Metadado | Manter | - |
| `content` | TEXT | **Pode conter dados pessoais** | 90 dias | Anonimizar conteúdo |
| `timestamp` | TIMESTAMP | Metadado | Manter | - |

**Dados pessoais no content:** O conteúdo das mensagens pode conter:
- Nomes mencionados pelo usuário
- Telefones de contato
- Emails
- Endereços
- Nomes de empresas
- Informações de negócio

**Anonimização do content:**
- Substituir padrões de telefone por `[TELEFONE]`
- Substituir padrões de email por `[EMAIL]`
- Substituir nomes próprios por `[NOME]` (requer NER ou lista)
- Manter estrutura da conversa para análise agregada

---

### 2.3. Tabela: `conversation_context`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `lead_phone` | VARCHAR | Identificador Direto | 90 dias | Hash ou remover |
| `context_data` | JSONB | **Contém dados pessoais** | 90 dias | Anonimizar JSON |
| `updated_at` | TIMESTAMP | Metadado | Manter | - |

**Estrutura típica do context_data:**
```json
{
  "name": "João Silva",
  "email": "joao@empresa.com",
  "company": "Empresa LTDA",
  "city": "São Paulo",
  "product_interest": "FBM100",
  "volume": "1000 L/dia"
}
```

**Anonimização do context_data:**
- `name` → `[NOME]`
- `email` → `[EMAIL]`
- Manter dados não-identificadores (product_interest, volume)

---

### 2.4. Tabela: `empresas`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `cnpj` | VARCHAR(14) | Identificador Direto (PJ) | Conforme vínculo com lead | Hash ou [CNPJ] |
| `nome` | VARCHAR | Identificador Direto (PJ) | Conforme vínculo com lead | [EMPRESA] |
| `cidade` | VARCHAR | Identificador Indireto | Manter | - |
| `uf` | VARCHAR(2) | Identificador Indireto | Manter | - |
| `site` | VARCHAR | Identificador Indireto | Manter | - |
| `email` | VARCHAR | Identificador Direto | Conforme vínculo com lead | [EMAIL] |
| `telefone` | VARCHAR | Identificador Direto | Conforme vínculo com lead | [TELEFONE] |
| `contato` | UUID (FK) | Referência a Lead | Conforme vínculo com lead | Remover FK |
| `created_at` | TIMESTAMP | Metadado | Manter | - |
| `updated_at` | TIMESTAMP | Metadado | Manter | - |

**Nota:** CNPJ é dado de pessoa jurídica, mas a LGPD também protege dados de PJ quando vinculados a pessoas físicas.

---

### 2.5. Tabela: `orcamentos`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `lead` | UUID (FK) | Referência a Lead | Conforme lead | Remover FK |
| `resumo` | TEXT | Pode conter dados pessoais | Conforme lead | Revisar conteúdo |
| `produto` | VARCHAR | Dado Operacional | Manter | - |
| `segmento` | VARCHAR | Dado Operacional | Manter | - |
| `urgencia_compra` | VARCHAR | Dado Operacional | Manter | - |
| `volume_diario` | INTEGER | Dado Operacional | Manter | - |
| `oportunidade_pipe_id` | VARCHAR | Referência Externa | Conforme lead | Remover |
| `created_at` | TIMESTAMP | Metadado | Manter | - |
| `updated_at` | TIMESTAMP | Metadado | Manter | - |

---

### 2.6. Tabela: `audit_logs`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `entity_id` | VARCHAR | Pode ser telefone/ID | 5 anos (legal) | Já mascarado |
| `changes` | JSONB | Pode conter dados mascarados | 5 anos (legal) | Já mascarado |
| `metadata` | JSONB | Pode conter dados mascarados | 5 anos (legal) | Já mascarado |

**Nota:** Os dados em audit_logs já são mascarados pelo serviço `audit_trail.py` usando a função `mask_sensitive_data()`.

---

### 2.7. Tabela: `pending_operations`

| Campo | Tipo | Classificação | Retenção | Anonimização |
|-------|------|---------------|----------|--------------|
| `entity_id` | VARCHAR | Referência a Lead/Orcamento | Até sincronização | N/A |
| `payload` | JSONB | **Contém dados pessoais** | Até sincronização | Excluir após sync |

**Nota:** Operações pendentes devem ser sincronizadas ou excluídas. Dados sensíveis no payload são temporários.

---

## 3. Arquivos de Áudio

**Status:** Áudios NÃO são armazenados permanentemente.

O fluxo atual é:
1. Áudio recebido via webhook
2. Transcrição realizada (OpenAI Whisper)
3. Transcrição salva em `conversation_messages.content`
4. Áudio original descartado

**Implicação LGPD:** Não há necessidade de job de remoção de áudios, pois já são removidos após transcrição. Apenas transcrições precisam ser anonimizadas.

---

## 4. Períodos de Retenção

| Dado | Período | Base Legal |
|------|---------|------------|
| Mensagens/Transcrições | 90 dias | Consentimento / Interesse Legítimo |
| Contexto de Conversa | 90 dias | Consentimento / Interesse Legítimo |
| Leads Inativos | 1 ano sem interação | Interesse Legítimo |
| Audit Logs | 5 anos | Obrigação Legal (art. 16 LGPD) |
| Dados de Empresas | Conforme vínculo com lead | Interesse Legítimo |

---

## 5. Fluxo de Dados Pessoais

```
WhatsApp (Z-API)
      │
      ▼
┌─────────────────┐
│  Webhook API    │ ◄── Coleta: telefone, mensagem, áudio
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SDR Agent      │ ◄── Processa: extrai nome, email, empresa
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────────────────┐
│ leads │  │ conversation_*     │
└───────┘  └────────────────────┘
    │              │
    ▼              │
┌───────────┐      │
│ empresas  │      │
│ orcamentos│      │
└───────────┘      │
    │              │
    ▼              ▼
┌─────────────────────┐
│ Piperun CRM (Sync)  │ ◄── Exportação para sistema externo
└─────────────────────┘
```

---

## 6. Integrações Externas

### 6.1. Z-API (WhatsApp)
- **Dados enviados:** Telefone, mensagens de resposta
- **Dados recebidos:** Telefone, mensagens do usuário, áudios
- **Política de privacidade:** Responsabilidade do Z-API

### 6.2. Piperun CRM
- **Dados enviados:** Nome, telefone, email, empresa, cidade, produto de interesse
- **Dados recebidos:** IDs de oportunidade
- **Nota:** Dados sincronizados devem ser excluídos do CRM via API quando lead solicitar exclusão

### 6.3. Chatwoot
- **Dados enviados:** Telefone, nome, mensagens
- **Dados recebidos:** IDs de conversa
- **Nota:** Dados sincronizados devem ser excluídos do Chatwoot via API quando lead solicitar exclusão

### 6.4. OpenAI
- **Dados enviados:** Transcrições de áudio, contexto de conversa
- **Dados recebidos:** Respostas do modelo
- **Política:** API não retém dados após processamento (verificar contrato)

---

## 7. Ações Recomendadas

### 7.1. Jobs de Retenção (Automáticos)
- [ ] Job diário: Anonimizar transcrições > 90 dias
- [ ] Job semanal: Anonimizar leads inativos > 1 ano
- [ ] Job diário: Limpar pending_operations completadas > 7 dias
- [ ] Job mensal: Limpar audit_logs > 5 anos

### 7.2. Processos Manuais (Direitos do Titular)
- [ ] Endpoint: Exportar dados do titular (portabilidade)
- [ ] Endpoint: Corrigir dados do titular
- [ ] Endpoint: Excluir/Anonimizar dados do titular
- [ ] Processo: Solicitar exclusão em sistemas externos (CRM, Chatwoot)

### 7.3. Documentação
- [ ] Política de Privacidade atualizada
- [ ] Termo de Consentimento (se aplicável)
- [ ] Registro de Atividades de Tratamento (ROPA)

---

## 8. Responsáveis

| Área | Responsável | Contato |
|------|-------------|---------|
| DPO (Encarregado) | A definir | - |
| Desenvolvimento | Equipe Backend | - |
| Infraestrutura | DevOps | - |
| Jurídico | A definir | - |

---

## 9. Histórico de Revisões

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2026-01-06 | 1.0 | Documento inicial | Claude Code |
