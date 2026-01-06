# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Seleto Industrial SDR Agent - AI agent for WhatsApp lead qualification. Built with Python 3.12, FastAPI, and Agno Framework. Integrates with Supabase (database), OpenAI GPT-4o (LLM), Z-API (WhatsApp), PipeRun (CRM), and Chatwoot.

## Commands

### Development
```bash
# Setup
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env

# Run server
uvicorn src.main:app --reload
```

### Testing
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html

# Single test file
pytest tests/services/test_lead_crud.py -v

# CRUD tests only
pytest tests/services/test_*_crud.py -v
```

### Code Quality
```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Docker
```bash
docker-compose up --build
```

## Architecture

### Core Components

1. **FastAPI App** (`src/main.py`) - AgentOS-based web server with auto-generated API docs
2. **SDR Agent** (`src/agents/sdr_agent.py`) - Agno Framework agent using OpenAI, processes WhatsApp messages
3. **Webhook Handlers** (`src/api/routes/webhook.py`) - Z-API webhook endpoints for text/audio messages

### Data Flow
```
WhatsApp → Z-API Webhook → Message Processing → SDR Agent → Response → Z-API → WhatsApp
                              ↓                    ↓
                        Supabase (persistence)  Knowledge Base
```

### Key Services

- **Lead Persistence** (`lead_persistence.py`) - CRUD with phone normalization, idempotent upserts
- **Orcamento Persistence** (`orcamento_persistence.py`) - Budget CRUD with lead FK validation
- **Empresa Persistence** (`empresa_persistence.py`) - Company CRUD with CNPJ deduplication
- **Conversation Memory** (`conversation_memory.py`) - In-memory cache + Supabase sync
- **WhatsApp** (`whatsapp.py`) - Z-API integration with retry logic
- **Knowledge Base** (`knowledge_base.py`) - Product info and FAQs
- **Chatwoot Sync** (`chatwoot_sync.py`) - Bidirectional message sync with Chatwoot
- **Agent Pause** (`agent_pause.py`) - Pause/resume agent on SDR intervention
- **Business Hours** (`business_hours.py`) - Business hours configuration and verification
- **Handoff Summary** (`handoff_summary.py`) - Generate and send hot lead summaries

### System Prompt

Located at `prompts/sp_agente_v1.xml`. Loaded securely with path validation and XML parsing protection.

## Database

**Always use Supabase MCP tools for database operations.**

Tables: `conversations`, `conversation_context`, `leads`, `orcamentos`, `empresas`, `technical_questions`

### Data Normalization
- **Phone**: E.164 format, digits only (e.g., `5511999999999`)
- **CNPJ**: 14 digits only (e.g., `12345678000190`)

## Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase admin key

For full integration (MVP):
- `ZAPI_INSTANCE_ID`, `ZAPI_INSTANCE_TOKEN`, `ZAPI_CLIENT_TOKEN` - Z-API WhatsApp
- `PIPERUN_API_TOKEN`, `PIPERUN_PIPELINE_ID`, `PIPERUN_STAGE_ID`, `PIPERUN_ORIGIN_ID` - CRM
- `CHATWOOT_API_URL`, `CHATWOOT_API_TOKEN`, `CHATWOOT_ACCOUNT_ID` - Chat platform

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Basic health check |
| `GET /api/health` | Detailed health status |
| `POST /webhook/text` | Text message webhook (Z-API) |
| `POST /webhook/audio` | Audio message webhook (Z-API) |
| `POST /webhook/chatwoot` | Chatwoot webhook (SDR intervention) |
| `GET /metrics` | Prometheus metrics (TECH-023) |
| `GET /docs` | Swagger UI |

## Key Implementation Notes

1. **Z-API** does not support custom webhook headers. Security via HTTPS + payload validation.
2. **Lead operations** are idempotent - multiple upserts with same phone = one lead.
3. **Async operations** - Agent processing and message sending are async.
4. **No hardcoded credentials** - All secrets via environment variables.
5. **Agent Pause/Resume** - Agent pauses when SDR sends message in Chatwoot; resumes via `/retomar` command or automatically outside business hours.
6. **Handoff Summary** - Structured summary sent to Chatwoot as internal note when lead is classified as "quente" (hot).
7. **Business Hours** - Configured in `config/business_hours.yaml` (default: Mon-Fri 08:00-18:00 America/Sao_Paulo).

## Observability (Epic 8)

### Metrics (TECH-023)
- **Endpoint**: `GET /metrics` - Prometheus format
- **Module**: `src/services/metrics.py`
- **Metrics**:
  - `http_requests_total` - HTTP requests by endpoint/method/status
  - `http_request_duration_seconds` - Latency histogram (P50, P95, P99)
  - `integration_requests_total` - Integration calls by service/status
  - `integration_request_duration_seconds` - Integration latency

### Alerts (TECH-024)
- **Module**: `src/services/alerts.py`
- **Alert Types**:
  - Error rate > 10% (5-minute window)
  - Latency P95 > 10s
  - Auth failures (401/403)
- **Notifications**: Slack webhook, email, generic webhook
- **Config**: `ALERT_*` environment variables

### Runbooks (TECH-025)
- **Location**: `documentation/runbooks/`
- Pausar/Retomar Agente
- Rotacionar Credenciais
- Reprocessar Mensagens
- Atualizar Base de Conhecimento
- Verificar Saúde do Sistema

## Security & Compliance (Epic 9)

### Audit Trail (TECH-028)
- **Module**: `src/services/audit_trail.py`
- **Table**: `audit_logs` (requires migration: `migrations/001_create_audit_logs_table.sql`)
- **Features**:
  - Logs CRUD operations on leads, orcamentos, empresas
  - Logs API calls to external services (Piperun CRM)
  - Sensitive data masking (phone, email, CNPJ, tokens)
  - Configurable retention (`AUDIT_RETENTION_DAYS`, default 90 days)
  - Before/after diff for UPDATE operations
- **Functions**:
  - `log_entity_create_sync()` - Log CREATE operations
  - `log_entity_update_sync()` - Log UPDATE with diff
  - `log_api_call_sync()` - Log external API calls
  - `mask_sensitive_data()` - Mask PII before logging
  - `get_audit_logs()` - Query audit logs with filters
  - `cleanup_old_audit_logs()` - Retention cleanup

## Documentation

- `.context/docs/` - Architecture, workflows, security docs
- `documentation/` - Project planning and requirements
- `documentation/runbooks/` - Operational runbooks
- `prompts/` - Agent prompts and product info
