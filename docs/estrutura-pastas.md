# Estrutura de Pastas

> **Para o Cliente:** Esta página mostra como o código está organizado. Pense nas pastas como gavetas de um arquivo - cada uma guarda um tipo específico de documento. Essa organização facilita encontrar e modificar qualquer parte do sistema.

---

## Visão Geral

```
seleto_industrial/
│
├── 📁 src/                      # Código fonte principal
│   ├── 📁 agents/               # Agentes de IA
│   ├── 📁 api/                  # Endpoints HTTP
│   ├── 📁 config/               # Configurações
│   ├── 📁 services/             # Lógica de negócio
│   └── 📁 utils/                # Utilitários
│
├── 📁 tests/                    # Testes automatizados
│   ├── 📁 agents/               # Testes de agentes
│   ├── 📁 api/                  # Testes de API
│   └── 📁 services/             # Testes de serviços
│
├── 📁 prompts/                  # Prompts do agente IA
│   ├── 📁 system_prompt/        # Prompts de sistema
│   ├── 📁 equipamentos/         # Info de produtos
│   └── 📁 frases_prontas/       # Frases pré-definidas
│
├── 📁 docs/                     # Esta documentação
│
├── 📁 documentation/            # Documentação do produto
│
├── 📄 requirements.txt          # Dependências Python
├── 📄 Dockerfile               # Configuração Docker
├── 📄 docker-compose.yml       # Orquestração Docker
├── 📄 .env.example             # Exemplo de variáveis
└── 📄 README.md                # Leia-me principal
```

---

## Detalhamento por Pasta

### 📁 src/ (Código Fonte)

O coração do sistema. Todo o código Python que faz a aplicação funcionar.

```
src/
├── __init__.py                 # Marca como pacote Python
├── main.py                     # Ponto de entrada (FastAPI app)
│
├── 📁 agents/                  # AGENTES DE IA
│   ├── __init__.py
│   └── sdr_agent.py           # Agente SDR principal
│
├── 📁 api/                     # CAMADA DE API
│   ├── __init__.py
│   ├── 📁 routes/             # Endpoints
│   │   ├── __init__.py
│   │   ├── health.py          # GET /api/health
│   │   └── webhook.py         # POST /webhook/*
│   └── 📁 middleware/         # Middlewares
│       ├── __init__.py
│       └── logging.py         # Logging de requisições
│
├── 📁 config/                  # CONFIGURAÇÕES
│   ├── __init__.py
│   └── settings.py            # Pydantic Settings
│
├── 📁 services/                # LÓGICA DE NEGÓCIO
│   ├── __init__.py
│   ├── lead_persistence.py    # CRUD de leads
│   ├── orcamento_persistence.py # CRUD de orçamentos
│   ├── empresa_persistence.py # CRUD de empresas
│   ├── conversation_memory.py # Cache de conversas
│   ├── conversation_persistence.py # Supabase
│   ├── whatsapp.py           # Integração Z-API
│   ├── chatwoot_sync.py      # Integração Chatwoot
│   ├── knowledge_base.py     # Base de conhecimento
│   ├── data_extraction.py    # Extração de dados
│   ├── temperature_classification.py # Classificação
│   ├── prompt_loader.py      # Carregamento de prompts
│   ├── upsell.py            # Lógica de upsell
│   ├── unavailable_products.py # Produtos indisponíveis
│   └── transcription.py     # Transcrição de áudio
│
└── 📁 utils/                  # UTILITÁRIOS
    ├── __init__.py
    ├── logging.py            # Logging estruturado
    └── validation.py         # Validação de dados
```

---

### 📁 tests/ (Testes)

Todos os testes automatizados organizados por área.

```
tests/
├── __init__.py
├── conftest.py                # Fixtures compartilhadas
├── test_integration_flow.py   # Testes de integração
│
├── 📁 agents/                 # TESTES DE AGENTES
│   ├── __init__.py
│   ├── test_sdr_agent.py
│   ├── test_sdr_agent_history.py
│   ├── test_sdr_agent_knowledge.py
│   ├── test_sdr_agent_prompt.py
│   ├── test_sdr_agent_temperature.py
│   ├── test_sdr_agent_unavailable.py
│   └── test_sdr_agent_upsell.py
│
├── 📁 api/                    # TESTES DE API
│   ├── __init__.py
│   └── test_health.py
│
└── 📁 services/               # TESTES DE SERVIÇOS
    ├── __init__.py
    ├── test_lead_crud.py
    ├── test_orcamento_crud.py
    ├── test_empresa_crud.py
    ├── test_conversation_persistence.py
    ├── test_chatwoot_sync.py
    ├── test_knowledge_base.py
    ├── test_prompt_loader.py
    ├── test_temperature_classification.py
    ├── test_unavailable_products.py
    ├── test_upsell.py
    └── test_whatsapp.py
```

---

### 📁 prompts/ (Prompts de IA)

Arquivos de configuração da inteligência artificial.

```
prompts/
├── 📁 system_prompt/          # PROMPTS DE SISTEMA
│   ├── sp_agente_v1.xml      # Prompt principal do SDR
│   └── sp_calcula_temperatura.xml # Prompt de classificação
│
├── 📁 equipamentos/           # INFORMAÇÕES DE PRODUTOS
│   └── resumo_maquinas.txt   # Especificações
│
└── 📁 frases_prontas/         # FRASES PRÉ-DEFINIDAS
    └── frases_prontas.txt    # Respostas padrão
```

---

### 📁 docs/ (Documentação Técnica)

Esta documentação que você está lendo.

```
docs/
├── README.md                  # Índice principal
├── arquitetura.md            # Arquitetura do sistema
├── api.md                    # Documentação da API
├── servicos.md              # Detalhes dos serviços
├── banco-de-dados.md        # Schema do banco
├── integracoes.md           # Integrações externas
├── agente-sdr.md            # Funcionamento do agente
├── testes.md                # Guia de testes
├── deploy.md                # Deploy e configuração
├── seguranca.md             # Medidas de segurança
├── troubleshooting.md       # Solução de problemas
├── estrutura-pastas.md      # Este arquivo
├── variaveis-ambiente.md    # Configuração
└── glossario.md             # Termos técnicos
```

---

### 📁 documentation/ (Documentação do Produto)

Documentação de produto e planejamento.

```
documentation/
├── backlog.md               # Product backlog
├── PRD.md                   # Requisitos do produto
├── requirements_analysis.md # Análise de requisitos
├── TESTING_GUIDE.md        # Guia de testes
└── 📁 bugs/                 # Registro de bugs
```

---

### Arquivos na Raiz

| Arquivo | Propósito |
|---------|-----------|
| `requirements.txt` | Lista de dependências Python |
| `Dockerfile` | Configuração para build Docker |
| `docker-compose.yml` | Orquestração de containers |
| `.env.example` | Template de variáveis de ambiente |
| `.gitignore` | Arquivos ignorados pelo Git |
| `README.md` | Leia-me principal do projeto |
| `CLAUDE.md` | Instruções para IA (Claude Code) |
| `AGENTS.md` | Definição de agentes de desenvolvimento |
| `pytest.ini` | Configuração do pytest |

---

## Convenções de Nomenclatura

### Arquivos Python

| Convenção | Exemplo |
|-----------|---------|
| Classes | `PascalCase` → `LeadPersistence` |
| Funções | `snake_case` → `get_lead_by_phone` |
| Arquivos | `snake_case` → `lead_persistence.py` |
| Constantes | `UPPER_SNAKE` → `MAX_RETRIES` |

### Arquivos de Teste

```
test_<modulo>.py
test_<modulo>_<funcionalidade>.py

Exemplos:
- test_lead_crud.py
- test_sdr_agent_temperature.py
```

### Diretórios

- Sempre `snake_case` em minúsculas
- Nomes descritivos e concisos
- Plural quando contém múltiplos itens (`routes`, `services`)

---

## Navegação Rápida

### Preciso modificar...

| Tarefa | Onde encontrar |
|--------|----------------|
| Endpoint de webhook | `src/api/routes/webhook.py` |
| Lógica do agente | `src/agents/sdr_agent.py` |
| Como leads são salvos | `src/services/lead_persistence.py` |
| Prompt do agente | `prompts/system_prompt/sp_agente_v1.xml` |
| Configurações | `src/config/settings.py` |
| Conexão com WhatsApp | `src/services/whatsapp.py` |
| Classificação de temperatura | `src/services/temperature_classification.py` |
| Testes de um serviço | `tests/services/test_<serviço>.py` |

---

## Onde Adicionar Código Novo

### Nova Funcionalidade

```
1. Serviço em src/services/<nome>.py
2. Testes em tests/services/test_<nome>.py
3. Integração no agente (se necessário)
```

### Novo Endpoint

```
1. Route em src/api/routes/<nome>.py
2. Importar em src/api/routes/__init__.py
3. Testes em tests/api/test_<nome>.py
```

### Novo Prompt

```
1. Arquivo em prompts/system_prompt/<nome>.xml
2. Loader em src/services/prompt_loader.py
3. Uso no agente
```

---

## Arquivos Importantes

### Ponto de Entrada

**`src/main.py`**
```python
# FastAPI app é criado aqui
# Rotas são registradas
# Middlewares são configurados
```

### Configuração Central

**`src/config/settings.py`**
```python
# Todas as variáveis de ambiente
# Validação de configuração
# Valores padrão
```

### Agente Principal

**`src/agents/sdr_agent.py`**
```python
# Orquestração de processamento
# Integração com serviços
# Geração de respostas
```

---

[← Voltar ao Índice](./README.md) | [Próximo: Variáveis de Ambiente →](./variaveis-ambiente.md)
