# Seleto Industrial SDR Agent

Agente de IA para qualificação de leads via WhatsApp para a Seleto Industrial.

## Stack

- **Runtime**: Python 3.12 + FastAPI + Agno Framework
- **Banco de Dados**: Supabase (PostgreSQL)
- **CRM**: PipeRun
- **Chat**: Chatwoot
- **Canal**: WhatsApp

## Requisitos

- Python 3.12+
- Docker e Docker Compose (opcional)
- Chave de API OpenAI

## Setup Local

### 1. Clonar repositório

```bash
git clone <repo-url>
cd seleto_industrial
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

### 5. Executar servidor

```bash
uvicorn src.main:app --reload
```

O servidor estará disponível em `http://localhost:8000`.

## Setup com Docker

```bash
# Build e execução
docker-compose up --build

# Apenas execução (após build)
docker-compose up -d
```

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check básico do AgentOS |
| GET | `/api/health` | Health check detalhado do serviço |
| GET | `/docs` | Documentação Swagger UI |
| GET | `/redoc` | Documentação ReDoc |

## Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ -v --cov=src --cov-report=html
```

## Estrutura do Projeto

```
src/
├── main.py           # Entry point
├── config/           # Configurações (settings.py)
├── api/routes/       # Endpoints da API
├── agents/           # Agentes Agno
├── services/         # Serviços de negócio
└── utils/            # Utilitários
tests/                # Testes automatizados
prompts/              # Prompts do agente
```

## Desenvolvimento

### Linting e Formatação

```bash
# Verificar código
ruff check src/ tests/

# Formatar código
ruff format src/ tests/
```

### Variáveis de Ambiente

Consulte o arquivo `.env.example` para todas as variáveis disponíveis.

#### Variáveis Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-...` |
| `SUPABASE_URL` | URL do projeto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Chave service_role do Supabase | `eyJ...` |

#### Variáveis de Integração

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `PIPERUN_API_TOKEN` | Token da API PipeRun | MVP |
| `PIPERUN_PIPELINE_ID` | ID do pipeline de vendas | MVP |
| `PIPERUN_STAGE_ID` | ID do estágio inicial | MVP |
| `PIPERUN_ORIGIN_ID` | ID da origem do lead | MVP |
| `WHATSAPP_API_URL` | URL da API do provedor WhatsApp | MVP |
| `WHATSAPP_API_TOKEN` | Token de autenticação WhatsApp | MVP |
| `WHATSAPP_WEBHOOK_SECRET` | Secret para validar webhooks | MVP |
| `CHATWOOT_API_URL` | URL da instância Chatwoot | MVP |
| `CHATWOOT_API_TOKEN` | Token da API Chatwoot | MVP |
| `CHATWOOT_ACCOUNT_ID` | ID da conta no Chatwoot | MVP |

#### Variáveis de Configuração

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `APP_ENV` | Ambiente de execução | `development` |
| `DEBUG` | Modo debug | `false` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `LOG_FORMAT` | Formato do log (`json` ou `text`) | `json` |
| `HOST` | Host do servidor | `0.0.0.0` |
| `PORT` | Porta do servidor | `8000` |
| `OPENAI_MODEL` | Modelo OpenAI | `gpt-4o` |

#### Rotação de Credenciais

Para rotacionar credenciais sem redeploy:
1. Atualize a variável de ambiente no ambiente de execução
2. O serviço carregará automaticamente no próximo request (para integrações que suportam)
3. Para credenciais críticas (Supabase, OpenAI), um restart pode ser necessário

## Licença

Proprietário - Seleto Industrial

# seleto-industrial
# seleto-industrial
