# Banco de Dados

> **Para o Cliente:** O banco de dados é onde todas as informações ficam guardadas de forma segura. Pense nele como um grande arquivo digital que guarda os dados de cada cliente, cada conversa, cada pedido de orçamento. Usamos o Supabase, uma tecnologia moderna e segura baseada na nuvem.

---

## Visão Geral

O sistema utiliza **Supabase** como banco de dados, que é construído sobre PostgreSQL - um dos bancos de dados mais confiáveis e utilizados no mundo.

**Por que Supabase?**
- PostgreSQL gerenciado (sem preocupação com infraestrutura)
- Row Level Security (RLS) para segurança
- API REST automática
- Real-time subscriptions
- Backups automáticos
- Dashboard visual para administração

---

## Schema do Banco de Dados

### Diagrama de Relacionamentos

```
┌─────────────────────┐
│       leads         │
├─────────────────────┤
│ id (PK)             │
│ phone (UNIQUE)      │──────┐
│ name                │      │
│ email               │      │
│ city                │      │
│ uf                  │      │
│ product             │      │
│ volume              │      │
│ urgency             │      │
│ knows_seleto        │      │
│ temperature         │      │
│ created_at          │      │
│ updated_at          │      │
└─────────────────────┘      │
                             │
┌─────────────────────┐      │
│     orcamentos      │      │
├─────────────────────┤      │
│ id (PK)             │      │
│ lead_id (FK)        │◄─────┘
│ resumo              │
│ produto             │
│ segmento            │
│ urgencia_compra     │
│ volume_diario       │
│ oportunidade_pipe_id│
│ created_at          │
│ updated_at          │
└─────────────────────┘

┌─────────────────────┐      ┌─────────────────────┐
│   conversations     │      │ conversation_context │
├─────────────────────┤      ├─────────────────────┤
│ id (PK)             │      │ id (PK)             │
│ lead_phone          │      │ lead_phone          │
│ role                │      │ key                 │
│ content             │      │ value               │
│ timestamp           │      │ created_at          │
└─────────────────────┘      └─────────────────────┘

┌─────────────────────┐      ┌─────────────────────┐
│conversation_messages│      │ technical_questions │
├─────────────────────┤      ├─────────────────────┤
│ id (PK)             │      │ id (PK)             │
│ lead_phone          │      │ phone               │
│ role                │      │ question            │
│ content             │      │ timestamp           │
│ timestamp           │      │ context             │
└─────────────────────┘      └─────────────────────┘

┌─────────────────────┐
│      empresa        │
├─────────────────────┤
│ id (PK)             │
│ nome                │
│ cidade              │
│ uf                  │
│ cnpj (UNIQUE)       │
│ site                │
│ email               │
│ telefone            │
│ contato             │
│ created_at          │
│ updated_at          │
└─────────────────────┘
```

---

## Tabelas Detalhadas

### leads

> **Para o Cliente:** Onde ficam guardados os dados de cada potencial cliente. Cada pessoa que entra em contato pelo WhatsApp tem um registro aqui.

**Propósito:** Armazenar informações de leads (potenciais clientes)

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `phone` | varchar | Não | - | Telefone (E.164, UNIQUE) |
| `name` | varchar | Sim | - | Nome completo |
| `email` | varchar | Sim | - | E-mail |
| `city` | varchar | Sim | - | Cidade |
| `uf` | varchar(2) | Sim | - | Estado (UF) |
| `product` | varchar | Sim | - | Produto de interesse |
| `volume` | varchar | Sim | - | Volume estimado |
| `urgency` | varchar | Sim | - | Nível de urgência |
| `knows_seleto` | boolean | Sim | - | Já conhece a Seleto |
| `temperature` | varchar | Sim | - | Classificação (quente/morno/frio) |
| `created_at` | timestamptz | Não | now() | Data de criação |
| `updated_at` | timestamptz | Não | now() | Última atualização |

**Índices:**
- `leads_pkey` - PRIMARY KEY em `id`
- `leads_phone_key` - UNIQUE em `phone`

**RLS Policies:**
- Habilitar RLS: `ALTER TABLE leads ENABLE ROW LEVEL SECURITY;`
- Policy service role: Full access via service_role key

**Exemplo de Registro:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "phone": "5511999999999",
  "name": "João Silva",
  "email": "joao@empresa.com",
  "city": "São Paulo",
  "uf": "SP",
  "product": "FBM100",
  "volume": "500kg/dia",
  "urgency": "alta",
  "knows_seleto": true,
  "temperature": "quente",
  "created_at": "2026-01-05T10:00:00Z",
  "updated_at": "2026-01-05T12:30:00Z"
}
```

---

### orcamentos

> **Para o Cliente:** Cada vez que um cliente demonstra interesse em um orçamento, registramos aqui. Um mesmo cliente pode ter vários orçamentos ao longo do tempo.

**Propósito:** Armazenar solicitações de orçamento vinculadas a leads

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `lead_id` | uuid | Não | - | FK para leads.id |
| `resumo` | text | Sim | - | Resumo do orçamento |
| `produto` | varchar | Sim | - | Produto solicitado |
| `segmento` | varchar | Sim | - | Segmento de mercado |
| `urgencia_compra` | varchar | Sim | - | Urgência da compra |
| `volume_diario` | varchar | Sim | - | Volume diário estimado |
| `oportunidade_pipe_id` | varchar | Sim | - | ID no PipeRun CRM |
| `created_at` | timestamptz | Não | now() | Data de criação |
| `updated_at` | timestamptz | Não | now() | Última atualização |

**Índices:**
- `orcamentos_pkey` - PRIMARY KEY em `id`
- `orcamentos_lead_id_idx` - INDEX em `lead_id`

**Foreign Keys:**
- `orcamentos_lead_id_fkey` - REFERENCES leads(id) ON DELETE CASCADE

**Exemplo de Registro:**
```json
{
  "id": "456e7890-a12b-34c5-d678-901234567890",
  "lead_id": "123e4567-e89b-12d3-a456-426614174000",
  "resumo": "Cliente interessado em máquina de hambúrguer para restaurante",
  "produto": "FBM100",
  "segmento": "Food Service",
  "urgencia_compra": "30 dias",
  "volume_diario": "200 unidades",
  "oportunidade_pipe_id": "PIPE-12345",
  "created_at": "2026-01-05T12:00:00Z",
  "updated_at": "2026-01-05T12:00:00Z"
}
```

---

### empresa

> **Para o Cliente:** Informações das empresas dos clientes. Quando um cliente fornece o CNPJ, conseguimos identificar a empresa e evitar duplicatas.

**Propósito:** Armazenar informações de empresas

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `nome` | varchar | Sim | - | Nome da empresa |
| `cidade` | varchar | Sim | - | Cidade |
| `uf` | varchar(2) | Sim | - | Estado (UF) |
| `cnpj` | varchar(14) | Sim | - | CNPJ (UNIQUE quando preenchido) |
| `site` | varchar | Sim | - | Website |
| `email` | varchar | Sim | - | E-mail corporativo |
| `telefone` | varchar | Sim | - | Telefone |
| `contato` | varchar | Sim | - | Nome do contato |
| `created_at` | timestamptz | Não | now() | Data de criação |
| `updated_at` | timestamptz | Não | now() | Última atualização |

**Índices:**
- `empresa_pkey` - PRIMARY KEY em `id`
- `empresa_cnpj_key` - UNIQUE em `cnpj` (quando não nulo)

**Exemplo de Registro:**
```json
{
  "id": "789a0123-b456-78c9-d012-345678901234",
  "nome": "ABC Foods Ltda",
  "cidade": "Campinas",
  "uf": "SP",
  "cnpj": "12345678000190",
  "site": "www.abcfoods.com.br",
  "email": "contato@abcfoods.com.br",
  "telefone": "1932001234",
  "contato": "Maria Santos",
  "created_at": "2026-01-05T09:00:00Z",
  "updated_at": "2026-01-05T09:00:00Z"
}
```

---

### conversations

> **Para o Cliente:** O histórico completo de todas as conversas. Cada mensagem enviada e recebida fica salva aqui, permitindo continuidade no atendimento.

**Propósito:** Armazenar histórico de mensagens de conversas

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `lead_phone` | varchar | Não | - | Telefone do lead |
| `role` | varchar | Não | - | "user" ou "assistant" |
| `content` | text | Não | - | Conteúdo da mensagem |
| `timestamp` | timestamptz | Não | now() | Data/hora da mensagem |

**Índices:**
- `conversations_pkey` - PRIMARY KEY em `id`
- `conversations_lead_phone_idx` - INDEX em `lead_phone`
- `conversations_timestamp_idx` - INDEX em `timestamp`

**Exemplo de Registro:**
```json
{
  "id": "abc12345-d678-90ef-ghij-klmnopqrstuv",
  "lead_phone": "5511999999999",
  "role": "user",
  "content": "Olá, gostaria de saber mais sobre a FBM100",
  "timestamp": "2026-01-05T10:30:00Z"
}
```

---

### conversation_context

> **Para o Cliente:** Informações extras sobre cada conversa que não são mensagens, como preferências identificadas ou flags especiais.

**Propósito:** Armazenar contexto adicional de conversas (chave-valor)

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `lead_phone` | varchar | Não | - | Telefone do lead |
| `key` | varchar | Não | - | Chave do contexto |
| `value` | text | Sim | - | Valor do contexto |
| `created_at` | timestamptz | Não | now() | Data de criação |

**Índices:**
- `conversation_context_pkey` - PRIMARY KEY em `id`
- `conversation_context_phone_key_idx` - INDEX em (lead_phone, key)

**Exemplo de Uso:**
```json
{
  "id": "ctx12345-6789-abcd-efgh-ijklmnopqrst",
  "lead_phone": "5511999999999",
  "key": "preferred_product",
  "value": "FBM100",
  "created_at": "2026-01-05T10:35:00Z"
}
```

---

### conversation_messages

> **Para o Cliente:** Uma tabela alternativa para mensagens, usada em alguns fluxos específicos do sistema.

**Propósito:** Armazenamento alternativo de mensagens (compatibilidade)

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `lead_phone` | varchar | Não | - | Telefone do lead |
| `role` | varchar | Não | - | "user" ou "assistant" |
| `content` | text | Não | - | Conteúdo da mensagem |
| `timestamp` | timestamptz | Não | now() | Data/hora da mensagem |

---

### technical_questions

> **Para o Cliente:** Perguntas técnicas avançadas que o sistema não pode responder são salvas aqui para que sua equipe de engenharia possa dar seguimento.

**Propósito:** Registrar perguntas técnicas para follow-up

| Coluna | Tipo | Nulo | Padrão | Descrição |
|--------|------|------|--------|-----------|
| `id` | uuid | Não | gen_random_uuid() | Identificador único |
| `phone` | varchar | Não | - | Telefone do solicitante |
| `question` | text | Não | - | Pergunta técnica |
| `timestamp` | timestamptz | Não | now() | Data/hora do registro |
| `context` | text | Sim | - | Contexto adicional |

**Exemplo de Registro:**
```json
{
  "id": "tech12345-6789-abcd-efgh-ijklmnopqrst",
  "phone": "5511999999999",
  "question": "Qual a voltagem do motor da FBM100?",
  "timestamp": "2026-01-05T11:00:00Z",
  "context": "Cliente perguntou sobre especificações elétricas"
}
```

---

## Normalização de Dados

### Telefone (E.164)

> **Para o Cliente:** Todos os telefones são guardados no mesmo formato, facilitando buscas e evitando duplicatas.

**Formato:** Apenas dígitos, prefixo de país incluído

| Input | Output |
|-------|--------|
| `(11) 99999-9999` | `5511999999999` |
| `11999999999` | `5511999999999` |
| `+55 11 99999-9999` | `5511999999999` |

**Implementação:**
```python
def normalize_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11:  # DDD + 9 dígitos
        return f"55{digits}"
    return digits
```

---

### CNPJ

> **Para o Cliente:** CNPJs também são padronizados, removendo pontos e traços para garantir unicidade.

**Formato:** Apenas dígitos, 14 caracteres

| Input | Output |
|-------|--------|
| `12.345.678/0001-90` | `12345678000190` |
| `12345678000190` | `12345678000190` |

**Implementação:**
```python
def normalize_cnpj(cnpj: str) -> str:
    digits = re.sub(r'\D', '', cnpj)
    return digits if len(digits) == 14 else ''
```

---

### UF (Estado)

**Formato:** 2 letras maiúsculas

| Input | Output |
|-------|--------|
| `sp` | `SP` |
| `São Paulo` | `` (inválido) |
| `SP` | `SP` |

---

## Queries Comuns

### Buscar Lead por Telefone

```sql
SELECT * FROM leads
WHERE phone = '5511999999999';
```

### Histórico de Conversa

```sql
SELECT role, content, timestamp
FROM conversations
WHERE lead_phone = '5511999999999'
ORDER BY timestamp ASC;
```

### Orçamentos de um Lead

```sql
SELECT o.*
FROM orcamentos o
JOIN leads l ON o.lead_id = l.id
WHERE l.phone = '5511999999999'
ORDER BY o.created_at DESC;
```

### Leads por Temperatura

```sql
SELECT * FROM leads
WHERE temperature = 'quente'
ORDER BY updated_at DESC;
```

### Contagem por Temperatura

```sql
SELECT temperature, COUNT(*) as total
FROM leads
WHERE temperature IS NOT NULL
GROUP BY temperature;
```

### Perguntas Técnicas Pendentes

```sql
SELECT tq.*, l.name as lead_name
FROM technical_questions tq
LEFT JOIN leads l ON tq.phone = l.phone
ORDER BY tq.timestamp DESC;
```

---

## Migrations

> **Para o Cliente:** Migrations são scripts que criam e alteram a estrutura do banco de dados. Elas garantem que o banco seja criado da mesma forma em qualquer ambiente.

**Localização:** Gerenciadas via Supabase Dashboard ou CLI

### Exemplo de Migration

```sql
-- Criar tabela leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR NOT NULL UNIQUE,
    name VARCHAR,
    email VARCHAR,
    city VARCHAR,
    uf VARCHAR(2),
    product VARCHAR,
    volume VARCHAR,
    urgency VARCHAR,
    knows_seleto BOOLEAN,
    temperature VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Habilitar RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Criar policy para service role
CREATE POLICY "Service role full access" ON leads
    FOR ALL USING (true);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

---

## Backup e Recuperação

> **Para o Cliente:** O Supabase faz backups automáticos diários. Se precisar recuperar dados, é só entrar em contato.

**Política de Backup:**
- Backups automáticos diários
- Retenção de 7 dias (plano gratuito) ou 30 dias (plano pago)
- Point-in-time recovery disponível em planos pagos

**Recuperação:**
1. Acessar dashboard Supabase
2. Ir em Settings > Database > Backups
3. Selecionar ponto de restauração
4. Confirmar recuperação

---

## Performance

### Índices Recomendados

```sql
-- Já criados automaticamente via UNIQUE/PRIMARY KEY
-- leads.phone (UNIQUE)
-- empresa.cnpj (UNIQUE)

-- Índices adicionais para performance
CREATE INDEX IF NOT EXISTS idx_conversations_phone_time
ON conversations(lead_phone, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_orcamentos_lead
ON orcamentos(lead_id);

CREATE INDEX IF NOT EXISTS idx_leads_temperature
ON leads(temperature) WHERE temperature IS NOT NULL;
```

### Boas Práticas

1. **Use os índices existentes** - Sempre busque por phone ou id
2. **Limite resultados** - Use LIMIT em queries de histórico
3. **Evite SELECT *** - Selecione apenas colunas necessárias
4. **Normalize antes de buscar** - Telefone/CNPJ devem estar normalizados

---

## Acesso via Código

### Usando Supabase Client

```python
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Buscar lead
result = supabase.table("leads").select("*").eq("phone", "5511999999999").execute()
lead = result.data[0] if result.data else None

# Inserir lead
result = supabase.table("leads").insert({
    "phone": "5511999999999",
    "name": "João Silva"
}).execute()

# Atualizar lead
result = supabase.table("leads").update({
    "temperature": "quente"
}).eq("phone", "5511999999999").execute()

# Upsert (insert ou update)
result = supabase.table("leads").upsert({
    "phone": "5511999999999",
    "name": "João Silva",
    "city": "São Paulo"
}).execute()
```

---

## Troubleshooting

### Erro: "duplicate key value violates unique constraint"

**Causa:** Tentando inserir registro com phone/cnpj que já existe

**Solução:** Use upsert em vez de insert
```python
supabase.table("leads").upsert(data).execute()
```

### Erro: "foreign key violation"

**Causa:** Tentando criar orçamento para lead inexistente

**Solução:** Verifique se o lead existe antes de criar orçamento
```python
lead = get_lead_by_phone(phone)
if lead:
    create_orcamento(lead["id"], data)
```

### Performance lenta em histórico

**Causa:** Muitas mensagens sem paginação

**Solução:** Use limit e offset
```python
result = supabase.table("conversations")\
    .select("*")\
    .eq("lead_phone", phone)\
    .order("timestamp", desc=True)\
    .limit(50)\
    .execute()
```

---

[← Voltar ao Índice](./README.md) | [Anterior: Serviços](./servicos.md) | [Próximo: Integrações →](./integracoes.md)
