# Integrações Externas

> **Para o Cliente:** O sistema não trabalha sozinho - ele se conecta com vários outros serviços para funcionar. É como uma equipe onde cada membro tem uma especialidade: um cuida do WhatsApp, outro da inteligência artificial, outro do banco de dados, e assim por diante.

---

## Visão Geral das Integrações

```
┌─────────────────────────────────────────────────────────────────┐
│                    Seleto Industrial SDR Agent                   │
└─────────────────────────────────────────────────────────────────┘
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │  Z-API  │ │ OpenAI  │ │Supabase │ │Chatwoot │ │ PipeRun │
   │WhatsApp │ │  GPT-4o │ │Database │ │  Chat   │ │   CRM   │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

| Integração | Propósito | Status |
|------------|-----------|--------|
| **Z-API** | WhatsApp (envio/recebimento) | Implementado |
| **OpenAI** | IA (GPT-4o + Whisper) | Implementado |
| **Supabase** | Banco de dados | Implementado |
| **Chatwoot** | Interface de chat | Implementado |
| **PipeRun** | CRM | Planejado |

---

## Z-API (WhatsApp)

> **Para o Cliente:** O Z-API é o "carteiro" do sistema. Ele recebe as mensagens do WhatsApp e entrega para nós, e também leva nossas respostas de volta para o cliente.

### O que é Z-API?

Z-API é um serviço brasileiro que permite integrar sistemas com o WhatsApp de forma oficial e estável. Funciona como uma "ponte" entre seu número de WhatsApp e aplicações.

### Configuração

**Variáveis de Ambiente:**
```env
ZAPI_INSTANCE_ID=sua-instancia-id
ZAPI_INSTANCE_TOKEN=seu-token-de-instancia
ZAPI_CLIENT_TOKEN=seu-client-token
```

**Como obter as credenciais:**
1. Acesse [z-api.io](https://z-api.io)
2. Crie uma conta
3. Crie uma nova instância
4. Conecte seu WhatsApp escaneando o QR Code
5. Copie as credenciais do dashboard

### Configuração de Webhooks

No painel do Z-API, configure:

| Webhook | URL | Eventos |
|---------|-----|---------|
| Received | `https://seu-servidor/webhook/text` | Mensagens de texto |
| ReceivedAudio | `https://seu-servidor/webhook/audio` | Mensagens de áudio |

### Endpoints Utilizados

**Envio de Mensagem:**
```
POST https://api.z-api.io/instances/{INSTANCE_ID}/token/{TOKEN}/send-text
Headers:
  Client-Token: {CLIENT_TOKEN}
  Content-Type: application/json
Body:
  {
    "phone": "5511999999999",
    "message": "Texto da mensagem"
  }
```

### Implementação no Sistema

**Arquivo:** `src/services/whatsapp.py`

```python
class WhatsAppService:
    async def send_message(
        self,
        phone: str,
        text: str,
        max_retries: int = 3
    ) -> bool:
        """Envia mensagem com retry automático"""
```

**Características:**
- Retry com exponential backoff (1s, 2s, 4s)
- Normalização automática de telefone
- Logging detalhado de erros
- Timeout configurável

### Payload do Webhook (Recebido)

```json
{
  "phone": "5511999999999",
  "senderName": "João Silva",
  "text": {
    "message": "Olá, gostaria de informações"
  },
  "messageId": "3EB0123456789ABCDEF",
  "type": "ReceivedCallback",
  "fromMe": false,
  "instanceId": "instance-abc123",
  "timestamp": 1704456000
}
```

### Limitações Conhecidas

- Não suporta headers customizados nos webhooks
- Rate limiting da própria API do WhatsApp
- Delay ocasional em horários de pico

### Troubleshooting Z-API

| Problema | Causa Provável | Solução |
|----------|----------------|---------|
| Mensagem não enviada | Token inválido | Verificar ZAPI_CLIENT_TOKEN |
| Webhook não recebido | URL incorreta | Verificar configuração no painel |
| Erro 401 | Credenciais expiradas | Reconectar WhatsApp |
| Erro 429 | Rate limit | Aguardar e implementar backoff |

---

## OpenAI

> **Para o Cliente:** A OpenAI é a empresa por trás do ChatGPT. Usamos a mesma tecnologia para que o sistema consiga entender e responder as mensagens de forma inteligente, como se fosse um atendente humano.

### Serviços Utilizados

| Serviço | Modelo | Uso |
|---------|--------|-----|
| **Chat Completion** | GPT-4o | Respostas do agente |
| **Whisper** | whisper-1 | Transcrição de áudio |

### Configuração

**Variáveis de Ambiente:**
```env
OPENAI_API_KEY=sk-sua-chave-api
OPENAI_MODEL=gpt-4o
```

**Como obter a API Key:**
1. Acesse [platform.openai.com](https://platform.openai.com)
2. Crie uma conta ou faça login
3. Vá em API Keys
4. Crie uma nova chave
5. Configure billing (é pago por uso)

### Chat Completion (GPT-4o)

**Uso Principal:** Geração de respostas do agente SDR

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Olá, quero saber da FBM100"}
    ],
    temperature=0.7,
    max_tokens=500
)
```

**Parâmetros Utilizados:**
- `model`: "gpt-4o" (mais capaz e multimodal)
- `temperature`: 0.7 (balanceado entre criatividade e consistência)
- `max_tokens`: Limite de tokens na resposta

### Whisper (Transcrição)

**Uso:** Converter áudios do WhatsApp em texto

```python
from openai import OpenAI

client = OpenAI()

# Baixa o áudio
audio_content = httpx.get(audio_url).content

# Transcreve
transcription = client.audio.transcriptions.create(
    model="whisper-1",
    file=("audio.ogg", audio_content, "audio/ogg"),
    language="pt"
)
```

**Formatos Suportados:**
- MP3, MP4, MPEG
- OGG (usado pelo WhatsApp)
- WAV, WEBM

### Custos Estimados

| Operação | Custo Aproximado |
|----------|------------------|
| GPT-4o (input) | $2.50 / 1M tokens |
| GPT-4o (output) | $10.00 / 1M tokens |
| Whisper | $0.006 / minuto |

**Estimativa por conversa:**
- ~500 tokens input + ~200 tokens output
- Custo médio: $0.003 por mensagem processada

### Boas Práticas

1. **Cache de prompts** - System prompt carregado uma vez
2. **Limite de histórico** - Max 20 mensagens para contexto
3. **Timeout** - 30s para evitar travamentos
4. **Retry** - Backoff exponencial em erros 429/500

### Troubleshooting OpenAI

| Problema | Causa | Solução |
|----------|-------|---------|
| Erro 401 | API Key inválida | Verificar OPENAI_API_KEY |
| Erro 429 | Rate limit | Implementar retry com backoff |
| Erro 500 | Problema na OpenAI | Aguardar e tentar novamente |
| Timeout | Resposta lenta | Aumentar timeout ou reduzir contexto |

---

## Supabase

> **Para o Cliente:** O Supabase é onde todos os dados ficam guardados na nuvem. É seguro, faz backups automáticos, e permite que o sistema funcione de qualquer lugar.

### O que é Supabase?

Supabase é uma alternativa open-source ao Firebase, construída sobre PostgreSQL. Oferece:
- Banco de dados PostgreSQL gerenciado
- API REST automática
- Autenticação
- Storage para arquivos
- Real-time subscriptions

### Configuração

**Variáveis de Ambiente:**
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...  # Opcional
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...  # Obrigatório
```

**Como configurar:**
1. Acesse [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em Settings > API
4. Copie URL e Service Role Key

### SDK Python

```python
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# CRUD Operations
supabase.table("leads").select("*").execute()
supabase.table("leads").insert(data).execute()
supabase.table("leads").update(data).eq("id", id).execute()
supabase.table("leads").delete().eq("id", id).execute()
```

### Tabelas Utilizadas

| Tabela | Propósito |
|--------|-----------|
| `leads` | Dados de potenciais clientes |
| `orcamentos` | Pedidos de orçamento |
| `empresa` | Informações de empresas |
| `conversations` | Histórico de mensagens |
| `conversation_context` | Contexto adicional |
| `technical_questions` | Perguntas para engenharia |

### Row Level Security (RLS)

> **Para o Cliente:** É uma camada extra de segurança que garante que cada dado só seja acessado por quem tem permissão.

**Configuração:**
```sql
-- Habilitar RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Policy para service role (acesso total)
CREATE POLICY "Service role access" ON leads
  FOR ALL USING (true);
```

### Plano e Limites

| Recurso | Free Tier | Pro |
|---------|-----------|-----|
| Banco de dados | 500MB | 8GB+ |
| Bandwidth | 2GB | 50GB+ |
| Conexões | 50 | 200+ |
| Backups | 7 dias | 30 dias |

### Troubleshooting Supabase

| Problema | Causa | Solução |
|----------|-------|---------|
| Erro 401 | Key inválida | Verificar SUPABASE_SERVICE_ROLE_KEY |
| Connection refused | URL incorreta | Verificar SUPABASE_URL |
| RLS blocking | Policy incorreta | Verificar políticas de RLS |
| Timeout | Pool esgotado | Reutilizar conexões (singleton) |

---

## Chatwoot

> **Para o Cliente:** O Chatwoot é uma interface visual onde sua equipe pode ver todas as conversas acontecendo. É como ter uma "central de atendimento" onde você acompanha o que o robô está conversando com os clientes.

### O que é Chatwoot?

Chatwoot é uma plataforma open-source de atendimento ao cliente. Permite:
- Visualizar conversas em tempo real
- Intervenção manual quando necessário
- Histórico completo de atendimentos
- Métricas e relatórios

### Configuração

**Variáveis de Ambiente:**
```env
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=seu-token-api
CHATWOOT_ACCOUNT_ID=12345
```

**Como configurar:**
1. Acesse seu Chatwoot (self-hosted ou cloud)
2. Vá em Settings > Inboxes
3. Crie um inbox do tipo API
4. Copie o API token
5. Anote o Account ID da URL

### API Utilizada

**Criar Contato:**
```python
POST /api/v1/accounts/{account_id}/contacts
{
    "name": "João Silva",
    "phone_number": "+5511999999999"
}
```

**Criar Conversa:**
```python
POST /api/v1/accounts/{account_id}/conversations
{
    "contact_id": 123,
    "inbox_id": 1
}
```

**Enviar Mensagem:**
```python
POST /api/v1/accounts/{account_id}/conversations/{conversation_id}/messages
{
    "content": "Mensagem aqui",
    "message_type": "incoming"  # ou "outgoing"
}
```

### Sincronização

O sistema sincroniza automaticamente:
- Novas mensagens do cliente → Chatwoot
- Respostas do agente → Chatwoot
- Criação de contatos quando necessário

**Implementação:**
```python
# src/services/chatwoot_sync.py
async def sync_message_to_chatwoot(
    phone: str,
    role: str,
    content: str
) -> bool:
    """Sincroniza mensagem para Chatwoot"""
```

### Configuração Opcional

O Chatwoot é **opcional**. O sistema funciona normalmente sem ele:
- Conversas são salvas no Supabase
- WhatsApp funciona independentemente
- Útil para equipes que querem interface visual

### Troubleshooting Chatwoot

| Problema | Causa | Solução |
|----------|-------|---------|
| Mensagens não aparecem | Token inválido | Verificar CHATWOOT_API_TOKEN |
| Contato duplicado | Cache desatualizado | Limpar cache de contatos |
| Erro 404 | Account ID incorreto | Verificar CHATWOOT_ACCOUNT_ID |

---

## PipeRun (CRM)

> **Para o Cliente:** O PipeRun é o sistema de CRM onde sua equipe gerencia as vendas. Futuramente, leads qualificados pelo robô serão automaticamente criados como oportunidades no PipeRun.

### Status: Planejado

A integração com PipeRun está planejada para fases futuras do projeto.

### Configuração Preparada

**Variáveis de Ambiente:**
```env
PIPERUN_API_URL=https://api.pipe.run/v1
PIPERUN_API_TOKEN=seu-token-api
PIPERUN_PIPELINE_ID=123
PIPERUN_STAGE_ID=456
PIPERUN_ORIGIN_ID=789
```

### Funcionalidades Planejadas

1. **Criação de Oportunidades**
   - Leads "quentes" → Nova oportunidade no pipeline
   - Dados do lead pré-preenchidos

2. **Sincronização de Status**
   - Atualização bidirecional de temperatura
   - Histórico de interações

3. **Notificações**
   - Alertar vendedores sobre leads qualificados
   - Integração com equipe de vendas

### API PipeRun (Referência)

```python
# Criar oportunidade (exemplo futuro)
POST https://api.pipe.run/v1/deals
Headers:
  Authorization: Bearer {TOKEN}
Body:
  {
    "title": "Lead - João Silva",
    "pipeline_id": 123,
    "stage_id": 456,
    "origin_id": 789,
    "contact": {
      "name": "João Silva",
      "phone": "5511999999999"
    }
  }
```

---

## Diagrama de Fluxo de Dados

```
                    ┌─────────────┐
                    │   Cliente   │
                    │  WhatsApp   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Z-API    │
                    │   Webhook   │
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    SDR Agent System    │
              │                        │
              │  ┌──────────────────┐  │
              │  │   Process Msg    │  │
              │  └────────┬─────────┘  │
              │           │            │
              │           ▼            │
              │  ┌──────────────────┐  │
              │  │  Extract Data   │◄─┼──► OpenAI GPT-4o
              │  └────────┬─────────┘  │
              │           │            │
              │           ▼            │
              │  ┌──────────────────┐  │
              │  │  Generate Resp  │◄─┼──► OpenAI GPT-4o
              │  └────────┬─────────┘  │
              │           │            │
              │           ▼            │
              │  ┌──────────────────┐  │
              │  │   Persist Data  │◄─┼──► Supabase
              │  └────────┬─────────┘  │
              │           │            │
              │           ▼            │
              │  ┌──────────────────┐  │
              │  │   Sync Chat     │◄─┼──► Chatwoot
              │  └────────┬─────────┘  │
              │           │            │
              └───────────┼────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │    Z-API    │
                   │    Send     │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Cliente   │
                   │  WhatsApp   │
                   └─────────────┘
```

---

## Checklist de Configuração

### Mínimo para Funcionar

- [x] **OpenAI API Key** - Obrigatório para IA
- [x] **Supabase URL + Service Key** - Obrigatório para persistência

### Para Integração WhatsApp

- [ ] **Z-API Instance ID** - ID da instância
- [ ] **Z-API Instance Token** - Token da instância
- [ ] **Z-API Client Token** - Token do cliente
- [ ] Configurar webhooks no painel Z-API

### Para Interface Visual

- [ ] **Chatwoot API URL** - URL da instalação
- [ ] **Chatwoot API Token** - Token de acesso
- [ ] **Chatwoot Account ID** - ID da conta

### Para CRM (Futuro)

- [ ] **PipeRun API Token** - Token de acesso
- [ ] **PipeRun Pipeline ID** - ID do pipeline
- [ ] **PipeRun Stage ID** - ID do estágio inicial
- [ ] **PipeRun Origin ID** - ID da origem

---

## Monitoramento de Integrações

### Health Check

O endpoint `/api/health` verifica status de todas as integrações:

```json
{
  "status": "healthy",
  "services": {
    "supabase": "connected",
    "openai": "configured",
    "zapi": "configured",
    "chatwoot": "not_configured"
  }
}
```

### Logs de Integração

Todas as chamadas a APIs externas são logadas:

```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "level": "INFO",
  "service": "zapi",
  "action": "send_message",
  "phone": "5511999999999",
  "success": true,
  "response_time_ms": 250
}
```

---

[← Voltar ao Índice](./README.md) | [Anterior: Banco de Dados](./banco-de-dados.md) | [Próximo: Agente SDR →](./agente-sdr.md)
