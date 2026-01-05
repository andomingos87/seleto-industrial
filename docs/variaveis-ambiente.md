# Variáveis de Ambiente

> **Para o Cliente:** As variáveis de ambiente são como "configurações secretas" do sistema. Elas guardam senhas, chaves de acesso e outras informações que não podem ficar visíveis no código. É como a combinação de um cofre - precisa estar correta para o sistema funcionar.

---

## Visão Geral

O sistema usa variáveis de ambiente para:
- 🔐 **Credenciais** - API keys e tokens
- ⚙️ **Configurações** - Comportamento do sistema
- 🌐 **URLs** - Endereços de serviços externos

**Arquivo de configuração:** `.env` (nunca commit no git!)

---

## Configuração Inicial

### 1. Criar arquivo .env

```bash
# Copiar o exemplo
cp .env.example .env

# Editar com suas credenciais
code .env  # ou vim, nano, notepad
```

### 2. Preencher variáveis obrigatórias

No mínimo, você precisa de:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

---

## Referência Completa

### Aplicação

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `APP_NAME` | Não | "Seleto Industrial SDR Agent" | Nome da aplicação |
| `APP_ENV` | Não | "development" | Ambiente (development/staging/production) |
| `DEBUG` | Não | false | Modo debug (true/false) |
| `HOST` | Não | "0.0.0.0" | Host do servidor |
| `PORT` | Não | 8000 | Porta do servidor |

**Exemplo:**
```env
APP_NAME="Seleto Industrial SDR Agent"
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

---

### OpenAI (Obrigatório)

> **Para o Cliente:** A OpenAI fornece a inteligência artificial. Sem essas credenciais, o sistema não consegue "pensar" e gerar respostas.

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `OPENAI_API_KEY` | **Sim** | - | Chave da API OpenAI |
| `OPENAI_MODEL` | Não | "gpt-4o" | Modelo a usar |

**Como obter:**
1. Acesse [platform.openai.com](https://platform.openai.com)
2. Crie conta ou faça login
3. Vá em API Keys → Create new secret key
4. Copie a chave (só aparece uma vez!)

**Exemplo:**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
```

---

### Supabase (Obrigatório)

> **Para o Cliente:** O Supabase é o banco de dados. Sem ele, o sistema não consegue guardar informações dos leads e conversas.

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SUPABASE_URL` | **Sim** | - | URL do projeto Supabase |
| `SUPABASE_ANON_KEY` | Não | - | Chave anônima (não usada) |
| `SUPABASE_SERVICE_ROLE_KEY` | **Sim** | - | Chave de serviço (admin) |

**Como obter:**
1. Acesse [supabase.com](https://supabase.com)
2. Crie projeto ou selecione existente
3. Vá em Settings → API
4. Copie URL e service_role key

**Exemplo:**
```env
SUPABASE_URL=https://xyzproject.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **Atenção:** Use `service_role`, NÃO a `anon` key!

---

### Z-API (WhatsApp)

> **Para o Cliente:** O Z-API conecta o sistema ao WhatsApp. Sem ele, você pode testar o sistema mas não consegue enviar/receber mensagens reais.

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `ZAPI_INSTANCE_ID` | Para WhatsApp | - | ID da instância |
| `ZAPI_INSTANCE_TOKEN` | Para WhatsApp | - | Token da instância |
| `ZAPI_CLIENT_TOKEN` | Para WhatsApp | - | Token do cliente |

**Como obter:**
1. Acesse [z-api.io](https://z-api.io)
2. Crie instância
3. Conecte WhatsApp (QR Code)
4. Copie credenciais do dashboard

**Exemplo:**
```env
ZAPI_INSTANCE_ID=3C8A1B2D4E5F6G7H8I9J
ZAPI_INSTANCE_TOKEN=A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
ZAPI_CLIENT_TOKEN=Q1R2S3T4U5V6W7X8Y9Z0A1B2C3D4E5F6
```

---

### Chatwoot (Opcional)

> **Para o Cliente:** O Chatwoot é uma interface visual para acompanhar as conversas. É opcional - o sistema funciona sem ele.

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `CHATWOOT_API_URL` | Não | - | URL da API Chatwoot |
| `CHATWOOT_API_TOKEN` | Não | - | Token de acesso |
| `CHATWOOT_ACCOUNT_ID` | Não | - | ID da conta |

**Exemplo:**
```env
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
CHATWOOT_ACCOUNT_ID=12345
```

---

### PipeRun CRM (Opcional)

> **Para o Cliente:** O PipeRun é o CRM para gestão de vendas. A integração ainda está em desenvolvimento.

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `PIPERUN_API_URL` | Não | https://api.pipe.run/v1 | URL da API |
| `PIPERUN_API_TOKEN` | Não | - | Token de acesso |
| `PIPERUN_PIPELINE_ID` | Não | - | ID do pipeline |
| `PIPERUN_STAGE_ID` | Não | - | ID do estágio inicial |
| `PIPERUN_ORIGIN_ID` | Não | - | ID da origem |

**Exemplo:**
```env
PIPERUN_API_URL=https://api.pipe.run/v1
PIPERUN_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
PIPERUN_PIPELINE_ID=123
PIPERUN_STAGE_ID=456
PIPERUN_ORIGIN_ID=789
```

---

### Logging

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `LOG_LEVEL` | Não | "INFO" | Nível de log (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FORMAT` | Não | "json" | Formato (json/text) |

**Exemplo:**
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Níveis de Log:**
- `DEBUG` - Tudo, muito verboso
- `INFO` - Informações gerais
- `WARNING` - Alertas
- `ERROR` - Apenas erros

---

## Arquivo .env Completo

```env
# ============================================
# SELETO INDUSTRIAL SDR AGENT
# Arquivo de Configuração
# ============================================

# --------------------------------------------
# APLICAÇÃO
# --------------------------------------------
APP_NAME="Seleto Industrial SDR Agent"
APP_ENV=development
DEBUG=false
HOST=0.0.0.0
PORT=8000

# --------------------------------------------
# LOGGING
# --------------------------------------------
LOG_LEVEL=INFO
LOG_FORMAT=json

# --------------------------------------------
# OPENAI (OBRIGATÓRIO)
# --------------------------------------------
OPENAI_API_KEY=sk-proj-sua-chave-aqui
OPENAI_MODEL=gpt-4o

# --------------------------------------------
# SUPABASE (OBRIGATÓRIO)
# --------------------------------------------
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key

# --------------------------------------------
# Z-API - WHATSAPP (OPCIONAL)
# --------------------------------------------
ZAPI_INSTANCE_ID=
ZAPI_INSTANCE_TOKEN=
ZAPI_CLIENT_TOKEN=

# --------------------------------------------
# CHATWOOT (OPCIONAL)
# --------------------------------------------
CHATWOOT_API_URL=
CHATWOOT_API_TOKEN=
CHATWOOT_ACCOUNT_ID=

# --------------------------------------------
# PIPERUN CRM (OPCIONAL)
# --------------------------------------------
PIPERUN_API_URL=https://api.pipe.run/v1
PIPERUN_API_TOKEN=
PIPERUN_PIPELINE_ID=
PIPERUN_STAGE_ID=
PIPERUN_ORIGIN_ID=
```

---

## Validação

### Verificar se configuração está correta

```bash
# Ativar ambiente virtual
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Testar carregamento
python -c "
from src.config.settings import settings
print('✅ APP_NAME:', settings.APP_NAME)
print('✅ OPENAI:', 'configurado' if settings.OPENAI_API_KEY else '❌ faltando')
print('✅ SUPABASE:', 'configurado' if settings.SUPABASE_URL else '❌ faltando')
"
```

### Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `ValidationError: OPENAI_API_KEY` | Variável não definida | Adicionar no .env |
| `Invalid API key` | Key incorreta | Verificar/regenerar key |
| `File not found: .env` | Arquivo não existe | `cp .env.example .env` |

---

## Boas Práticas

### ✅ Faça

- Mantenha `.env` fora do git (está no `.gitignore`)
- Use `.env.example` como template documentado
- Rotacione keys periodicamente
- Use keys diferentes por ambiente (dev/prod)

### ❌ Não Faça

- Commitar `.env` no repositório
- Compartilhar keys por email/chat
- Usar keys de produção em desenvolvimento
- Deixar keys em código fonte

---

## Ambientes Diferentes

### Desenvolvimento

```env
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### Staging

```env
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
```

### Produção

```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
```

---

## Gerenciamento em Cloud

### Railway

```bash
# Via CLI
railway variables set OPENAI_API_KEY=sk-...
railway variables set SUPABASE_URL=https://...
```

### Render

Dashboard → Environment → Add Environment Variable

### Docker

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - .env
```

---

## Troubleshooting

### "ValidationError: field required"

```
pydantic.error_wrappers.ValidationError: 1 validation error
OPENAI_API_KEY
  field required
```

**Solução:** Definir a variável no `.env`

### "Invalid API key"

**Solução:** Verificar se copiou a key completa, sem espaços

### ".env não carrega"

**Solução:**
1. Verificar se arquivo existe: `ls -la .env`
2. Verificar permissões
3. Verificar se está na raiz do projeto

---

[← Voltar ao Índice](./README.md) | [Anterior: Estrutura de Pastas](./estrutura-pastas.md) | [Próximo: Glossário →](./glossario.md)
