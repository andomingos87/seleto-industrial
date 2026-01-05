# Arquitetura do Sistema

> **Para o Cliente:** Este documento explica como o sistema está organizado "por dentro". Pense como a planta de uma casa: mostra onde fica cada cômodo e como eles se conectam. Entender isso ajuda a saber por que o sistema é confiável e escalável.

---

## Visão Geral da Arquitetura

O Seleto Industrial SDR Agent segue uma arquitetura em camadas, onde cada camada tem uma responsabilidade específica. Isso torna o sistema mais fácil de manter e evoluir.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (WhatsApp)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Z-API (WhatsApp)                         │
│              Serviço de integração com WhatsApp                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE API (FastAPI)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Health    │  │  Webhooks   │  │      Middleware         │  │
│  │  Endpoints  │  │  (text/audio)│  │  (Logging, Context)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE AGENTES (Agno)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      SDR Agent                             │  │
│  │  • Processamento de mensagens                              │  │
│  │  • Extração de dados                                       │  │
│  │  • Classificação de leads                                  │  │
│  │  • Geração de respostas                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE SERVIÇOS                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Conversation│  │   Lead      │  │     WhatsApp            │  │
│  │   Memory    │  │ Persistence │  │     Service             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Knowledge  │  │   Upsell    │  │     Chatwoot            │  │
│  │    Base     │  │   Service   │  │      Sync               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │Temperature  │  │ Unavailable │  │     Data                │  │
│  │Classification│ │  Products   │  │    Extraction           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                               │
│  ┌─────────────────────────────┐  ┌───────────────────────────┐ │
│  │         Supabase            │  │         OpenAI            │ │
│  │  • PostgreSQL               │  │  • GPT-4o (LLM)           │ │
│  │  • Row Level Security       │  │  • Whisper (Audio)        │ │
│  │  • Real-time subscriptions  │  │  • Embeddings             │ │
│  └─────────────────────────────┘  └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes Principais

### 1. Camada de API (FastAPI)

> **Para o Cliente:** É a "porta de entrada" do sistema. Todo mundo que quer falar com o sistema passa por aqui primeiro.

**Localização:** `src/api/`

**Responsabilidades:**
- Receber requisições HTTP (webhooks do WhatsApp)
- Validar dados de entrada
- Rotear para os serviços apropriados
- Retornar respostas padronizadas

**Componentes:**

| Arquivo | Função |
|---------|--------|
| `routes/health.py` | Endpoint de verificação de saúde |
| `routes/webhook.py` | Endpoints para mensagens de texto e áudio |
| `middleware/logging.py` | Registro de todas as requisições |

**Padrões Utilizados:**
- RESTful API design
- Async/await para operações não-bloqueantes
- Middleware para concerns transversais (logging, contexto)

---

### 2. Camada de Agentes (Agno Framework)

> **Para o Cliente:** É o "cérebro" do sistema. Aqui acontece toda a inteligência: entender o que o cliente quer, decidir o que responder, classificar o potencial de compra.

**Localização:** `src/agents/`

**Responsabilidades:**
- Orquestrar o fluxo de processamento de mensagens
- Coordenar chamadas aos serviços
- Gerenciar contexto da conversa
- Gerar respostas usando IA

**Componente Principal:**

```python
# src/agents/sdr_agent.py
SDR Agent
├── create_sdr_agent()      # Cria instância do agente
├── process_message()       # Processa uma mensagem
└── reload_system_prompt()  # Recarrega prompt (dev)
```

**Fluxo de Processamento:**

```
1. Recebe mensagem (telefone, texto, nome)
          ↓
2. Normaliza telefone (formato E.164)
          ↓
3. Verifica se é primeira mensagem
          ↓
4. Carrega histórico da conversa
          ↓
5. Extrai dados do lead (LLM)
          ↓
6. Persiste dados extraídos
          ↓
7. Classifica temperatura (se critérios atendidos)
          ↓
8. Aplica guardrails (comercial, técnico)
          ↓
9. Verifica upsell (FBM100 → FB300)
          ↓
10. Verifica produtos indisponíveis (espeto)
          ↓
11. Gera resposta (LLM via Agno)
          ↓
12. Salva resposta no histórico
          ↓
13. Sincroniza com Chatwoot
          ↓
14. Retorna texto da resposta
```

---

### 3. Camada de Serviços

> **Para o Cliente:** São os "especialistas" do sistema. Cada serviço sabe fazer uma coisa muito bem: um guarda as conversas, outro envia mensagens, outro classifica clientes, e assim por diante.

**Localização:** `src/services/`

#### Serviços de Dados

| Serviço | Arquivo | Função |
|---------|---------|--------|
| **Lead Persistence** | `lead_persistence.py` | CRUD de leads com idempotência |
| **Orcamento Persistence** | `orcamento_persistence.py` | CRUD de orçamentos |
| **Empresa Persistence** | `empresa_persistence.py` | CRUD de empresas |
| **Conversation Memory** | `conversation_memory.py` | Cache + sync com Supabase |
| **Conversation Persistence** | `conversation_persistence.py` | Camada de acesso ao Supabase |

#### Serviços de IA

| Serviço | Arquivo | Função |
|---------|---------|--------|
| **Data Extraction** | `data_extraction.py` | Extração estruturada via LLM |
| **Temperature Classification** | `temperature_classification.py` | Qualificação de leads |
| **Knowledge Base** | `knowledge_base.py` | Base de conhecimento + guardrails |
| **Prompt Loader** | `prompt_loader.py` | Carregamento seguro de prompts |

#### Serviços de Integração

| Serviço | Arquivo | Função |
|---------|---------|--------|
| **WhatsApp** | `whatsapp.py` | Envio de mensagens via Z-API |
| **Chatwoot Sync** | `chatwoot_sync.py` | Sincronização de mensagens |
| **Transcription** | `transcription.py` | Transcrição de áudio (Whisper) |

#### Serviços de Negócio

| Serviço | Arquivo | Função |
|---------|---------|--------|
| **Upsell** | `upsell.py` | Detecção de oportunidades FBM100→FB300 |
| **Unavailable Products** | `unavailable_products.py` | Gestão de produtos indisponíveis |

---

### 4. Camada de Dados

> **Para o Cliente:** É onde todas as informações ficam guardadas de forma segura. Usamos o Supabase, que é como um cofre digital super seguro na nuvem, e a OpenAI para a inteligência artificial.

**Supabase (PostgreSQL)**
- Banco de dados principal
- Row Level Security (RLS) para segurança
- Backups automáticos
- API REST automática

**OpenAI**
- GPT-4o para geração de texto
- Whisper para transcrição de áudio
- API REST com retry logic

---

## Padrões de Design Utilizados

### 1. Singleton Pattern

Usado para garantir uma única instância de recursos compartilhados:

```python
# Exemplo: Cliente Supabase
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(url, key)
    return _supabase_client
```

### 2. Repository Pattern

Usado para abstrair o acesso a dados:

```python
# Serviços de persistência encapsulam toda lógica de banco
lead_persistence.upsert_lead(phone, data)
lead_persistence.get_lead_by_phone(phone)
```

### 3. Factory Pattern

Usado para criar instâncias configuradas:

```python
# Criação do agente com configurações
agent = create_sdr_agent()
```

### 4. Strategy Pattern

Usado para diferentes estratégias de processamento:

```python
# Guardrails aplicam diferentes estratégias
if knowledge_base.is_commercial_query(message):
    return knowledge_base.get_commercial_response()
elif knowledge_base.is_too_technical(message):
    knowledge_base.register_technical_question(...)
```

### 5. Decorator Pattern

Usado via middleware para adicionar funcionalidades:

```python
# Middleware adiciona logging a todas as requisições
app.add_middleware(LoggingMiddleware)
```

---

## Fluxo de Dados

### Mensagem de Texto

```
Z-API Webhook → POST /webhook/text
                      ↓
              Validação do payload
                      ↓
              Extração: phone, message, sender_name
                      ↓
              process_message() [async]
                      ↓
              ┌───────┴───────┐
              ↓               ↓
      Processa           Retorna 200 OK
      mensagem           (imediato)
         ↓
   Gera resposta
         ↓
   Envia via Z-API
```

### Mensagem de Áudio

```
Z-API Webhook → POST /webhook/audio
                      ↓
              Extração da URL do áudio
                      ↓
              Download do arquivo
                      ↓
              Transcrição (Whisper)
                      ↓
              process_message() com texto transcrito
                      ↓
              [mesmo fluxo de texto]
```

---

## Decisões de Arquitetura

### 1. Processamento Assíncrono

**Decisão:** Processar mensagens de forma assíncrona
**Motivo:** Z-API tem timeout curto; processamento com IA pode demorar
**Implementação:** `asyncio.create_task()` após retornar 200 OK

### 2. Cache em Memória + Persistência

**Decisão:** Usar cache in-memory com sync para Supabase
**Motivo:** Performance para leituras frequentes; durabilidade para dados importantes
**Implementação:** `ConversationMemory` com lazy loading do Supabase

### 3. Idempotência por Telefone

**Decisão:** Usar telefone como chave única para leads
**Motivo:** Evitar duplicatas; permitir retomada de conversas
**Implementação:** `UNIQUE` constraint + `upsert` com `on_conflict`

### 4. Separação de Prompts

**Decisão:** Manter prompts em arquivos XML separados
**Motivo:** Facilitar iteração; permitir versionamento; hot-reload
**Implementação:** `prompts/system_prompt/*.xml`

### 5. Guardrails de Negócio

**Decisão:** Implementar guardrails em código, não apenas no prompt
**Motivo:** Garantia de cumprimento; controle programático
**Implementação:** `KnowledgeBase.is_commercial_query()`, etc.

---

## Escalabilidade

### Horizontal

```
              Load Balancer
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
Instance 1     Instance 2     Instance 3
    ↓               ↓               ↓
    └───────────────┼───────────────┘
                    ↓
              Supabase (shared)
```

- Instâncias stateless (estado no Supabase)
- Docker para deploy consistente
- Load balancing via container orchestration

### Vertical

- Aumento de recursos da instância
- Ajuste de pool de conexões
- Otimização de queries

---

## Monitoramento e Observabilidade

### Logging

- JSON estruturado para análise
- Request ID para rastreamento
- Context variables (phone, flow_step)

### Health Checks

- `/health` - Verificação básica
- `/api/health` - Status detalhado dos serviços

### Métricas Futuras

- Tempo de resposta
- Taxa de sucesso/erro
- Leads qualificados por período
- Distribuição de temperatura

---

## Próximos Passos de Evolução

1. **Rate Limiting** - Limitar requisições por IP/telefone
2. **Circuit Breaker** - Fallback para serviços externos
3. **Message Queue** - Desacoplar processamento pesado
4. **Caching Redis** - Cache distribuído para escala
5. **Observability Stack** - Prometheus + Grafana

---

[← Voltar ao Índice](./README.md) | [Próximo: API →](./api.md)
