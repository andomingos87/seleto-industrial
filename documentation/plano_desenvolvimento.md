## Plano de Desenvolvimento — Seleto Industrial (Agno / AgentOS Runtime)

### 0) Premissas, qualidade e Definition of Done (DoD)

- **Stack**: Python + Agno (Agent Framework + AgentOS Runtime/FastAPI) + Supabase + PipeRun + Chatwoot + provedor WhatsApp.
- **Branches/PRs**: mudanças entram via PR com revisão (mín. 1 reviewer), descrição, risco, e checklist.
- **Padrões de código**:
  - Formatação e lint automatizados (ex.: Ruff + format).
  - Tipagem estática (ex.: MyPy/Pyright).
  - Testes automatizados (pytest) com cobertura mínima definida por fase.
  - Logs estruturados e correlation-id em todas as requisições.
- **DoD mínimo por tarefa**:
  - Código + testes + documentação curta + observabilidade básica.
  - Sem segredos hardcoded e sem PII em arquivos versionados.
  - Reprocessamento seguro (idempotência) para entradas de webhook.

---

### 1) Fase 1 — Alinhamentos técnicos e decisões críticas (curto, mas obrigatório)

**Objetivo**: eliminar ambiguidade que bloqueia implementação e garantir requisitos “não-funcionais” desde o início.

- **1.1 Decisões de produto/integração (TBDs do PRD)**
  - **1.1.1 Provedor WhatsApp**: oficial vs terceiro (ex.: Z-API).
    - Subtarefas:
      - Levantar requisitos: áudio, templates, rate limit, custos, LGPD/contrato.
      - Definir payloads oficiais (webhook) e autenticação/assinatura.
  - **1.1.2 CRM alvo**: confirmar PipeRun/Piperun vs Pipedrive.
    - Subtarefas:
      - Validar endpoints e autenticação.
      - Confirmar entidades necessárias (empresa/pessoa/deal/nota) e relacionamentos.
  - **1.1.3 Pipeline/Stage/Origens**: validar IDs no CRM.
    - Subtarefas:
      - Confirmar `pipeline_id`, `stage_id` e tabela de origens.
      - Documentar em `documentation/PRD.md` e em variáveis de ambiente.
  - **1.1.4 Política de preço**: proibido vs exceções (lead frio).
    - Subtarefas:
      - Definir regra final + mensagens + rastreabilidade (nota no CRM).

- **1.2 Critérios de aceite da fase**
  - Documento curto de decisões (ou update no PRD) com: provedor WhatsApp, CRM final, IDs do CRM, política de preço.

---

### 2) Fase 2 — Fundação do repositório e runtime (sustentação do projeto)

**Objetivo**: criar base de código segura, testável e deployável, antes de implementar lógica de negócio.

- **2.1 Estrutura do projeto (Python)**
  - Subtarefas:
    - Criar pacote (ex.: `src/seleto_agent/`).
    - Separar módulos: `api/`, `agents/`, `integrations/`, `domain/`, `services/`, `db/`, `observability/`.
    - Definir camada de configuração (Settings) via env vars.

- **2.2 Dependências e tooling**
  - Subtarefas:
    - Definir `pyproject.toml` (ou `requirements.txt`) com versões fixadas.
    - Adicionar Agno, FastAPI (via AgentOS), HTTP client, Supabase client, etc.
    - Adicionar lint/format/typecheck/test no pipeline local.

- **2.3 CI/CD e qualidade**
  - Subtarefas:
    - Pipeline de CI: lint + typecheck + tests.
    - Secret scanning (ex.: gitleaks) e bloqueio de segredos.
    - Convention para commits e PR template.

- **2.4 Containerização e execução**
  - Subtarefas:
    - `Dockerfile` (imagem pequena, sem segredos).
    - `docker-compose.yml` para dev (opcional): app + mocks.
    - Guia de execução local (README).

- **2.5 Observabilidade mínima (desde o dia 1)**
  - Subtarefas:
    - Logging estruturado (json) + correlation id.
    - Healthcheck endpoint (`/healthz`) e readiness (`/readyz`).

- **2.6 Critérios de aceite da fase**
  - Serviço sobe localmente, CI passa, endpoints de health respondem, e há logs estruturados.

---

### 3) Fase 3 — Ingestão de mensagens (webhooks) + sessões

**Objetivo**: receber eventos do WhatsApp (texto/áudio) de forma segura e idempotente e roteá-los para uma sessão do agente.

- **3.1 Contratos de entrada (webhook)**
  - Subtarefas:
    - Definir schemas (Pydantic) para payload de texto e áudio.
    - Validar headers, timestamp, assinatura (se existir).
    - Normalizar telefone (apenas dígitos) e extrair `messageId`.

- **3.2 Idempotência e reprocessamento**
  - Subtarefas:
    - Implementar dedupe por `(provider, instanceId, messageId)` (ou equivalente).
    - Registrar evento bruto (audit) e status de processamento.
    - Criar estratégia de retry/backoff para falhas temporárias.

- **3.3 Adaptador do provedor WhatsApp (saída)**
  - Subtarefas:
    - Criar interface `WhatsAppProvider` (send text, send media, mark read).
    - Implementar `ZApiProvider` (se for o caso) e um `MockProvider` para testes.

- **3.4 Gestão de sessão**
  - Subtarefas:
    - Chave de sessão por telefone + janela de tempo.
    - Persistir contexto mínimo por sessão (ex.: no Supabase ou store do Agno).

- **3.5 Critérios de aceite da fase**
  - Webhook recebe mensagem, valida, não duplica, cria/recupera sessão e consegue responder “eco” via provedor (em sandbox).

---

### 4) Fase 4 — Implementação do agente (Agno) + guardrails

**Objetivo**: colocar o agente rodando com prompt, memória e regras de conversa; sem ainda depender de CRM completo.

- **4.1 Prompting e comportamento**
  - Subtarefas:
    - Importar e versionar prompt base (`sp_agente_v1.xml`) como fonte de instrução.
    - Implementar guardrails:
      - no máximo 2 perguntas seguidas,
      - proibir preço/prazo/desconto (até decisão),
      - encerrar cordialmente leads frios.

- **4.2 Base de conhecimento**
  - Subtarefas:
    - Modelar conhecimento inicial (texto estruturado) a partir de `prompts/equipamentos/*`.
    - Definir estratégia: lookup simples (MVP) → RAG/Vector DB (fase futura).

- **4.3 Tools internas (stubs)**
  - Subtarefas:
    - Definir tools com contratos estáveis (inputs/outputs), espelhando o legado do n8n:
      - atualizar lead (nome/temperatura),
      - criar orçamento,
      - criar empresa no DB,
      - integrar CRM (stubs inicialmente).

- **4.4 Human-in-the-loop (HITL) — comportamento**
  - Subtarefas:
    - Implementar “modo escuta” por conversa quando houver intervenção humana (evento do Chatwoot; integração completa na fase 6).
    - Definir comando de retomada (TBD).

- **4.5 Critérios de aceite da fase**
  - Dado um texto de lead, o agente conduz coleta progressiva respeitando guardrails e gera um resumo estruturado.

---

### 5) Fase 5 — Persistência (Supabase) e modelo de dados

**Objetivo**: persistir leads/conversas/orçamentos com segurança e permitir auditoria e retomada.

- **5.1 Schema e migrações**
  - Subtarefas:
    - Definir tabelas mínimas (conforme PRD): `leads`, `orcamentos`, `empresa` (+ `events/messages` recomendado).
    - Criar migrações SQL versionadas.

- **5.2 Segurança no banco (RLS e roles)**
  - Subtarefas:
    - Ativar RLS onde aplicável.
    - Definir política de acesso:
      - automação server-side com service role (nunca no cliente),
      - auditoria de operações sensíveis.

- **5.3 Repositórios e validações**
  - Subtarefas:
    - Camada `repositories` (CRUD) com validação e normalização (telefone/CNPJ/email).
    - Testes de integração (com DB local ou Supabase test).

- **5.4 Critérios de aceite da fase**
  - Conversa gera/atualiza lead, registra eventos essenciais, e permite reprocessamento idempotente.

---

### 6) Fase 6 — Integração PipeRun (CRM): empresa, pessoa, oportunidade e nota

**Objetivo**: automatizar a criação/atualização no CRM com deduplicação e parâmetros configuráveis.

- **6.1 Cliente do CRM (HTTP)**
  - Subtarefas:
    - Implementar `PipeRunClient` (timeouts, retries, backoff, rate-limit).
    - Tipar requests/responses e mapear erros comuns.

- **6.2 Cidade (`city_id`)**
  - Subtarefas:
    - Implementar busca `city_id` por cidade + UF com caching.

- **6.3 Empresa (dedupe por CNPJ)**
  - Subtarefas:
    - Buscar empresa por CNPJ antes de criar.
    - Criar empresa quando não existir.
    - Atualizar empresa quando campos mudarem (ID dinâmico).

- **6.4 Pessoa**
  - Subtarefas:
    - Criar pessoa com e-mail/telefone e `city_id` quando disponível.
    - Definir relacionamento pessoa↔empresa (conforme CRM).

- **6.5 Oportunidade e Nota**
  - Subtarefas:
    - Criar deal com pipeline/stage/origem/dono parametrizados.
    - Criar nota usando template padronizado (com “Não informado”).
    - Persistir `oportunidade_pipe_id` no Supabase.

- **6.6 Critérios de aceite da fase**
  - Lead qualificado cria/atualiza empresa/pessoa/deal e adiciona nota no CRM sem duplicar registros.

---

### 7) Fase 7 — Chatwoot (painel) e handoff (HITL completo)

**Objetivo**: garantir governança humana e integração do fluxo agente↔humano.

- **7.1 Integração Chatwoot (API/Webhooks)**
  - Subtarefas:
    - Mapear eventos: mensagem do agente, mensagem humana, status da conversa.
    - Implementar webhook do Chatwoot para detectar intervenção humana.

- **7.2 Pausa/retomada do agente**
  - Subtarefas:
    - Ao detectar humano: setar flag de pausa por conversa/sessão.
    - Definir comando de retomada (ex.: “/bot on”) e auditoria.

- **7.3 Handoff para lead quente**
  - Subtarefas:
    - Enviar resumo estruturado para o SDR (no Chatwoot e/ou nota no CRM).
    - Garantir que o agente pare de responder após handoff.

- **7.4 Critérios de aceite da fase**
  - Quando humano escreve, o agente não responde mais; quando retoma, volta com contexto correto.

---

### 8) Fase 8 — Áudio (transcrição) e multimodal (se necessário)

**Objetivo**: suportar fluxo real de áudio com privacidade e retenção controladas.

- **8.1 Download e validação do áudio**
  - Subtarefas:
    - Baixar `audioUrl` com segurança (timeouts, tamanho máximo).
    - Validar MIME/type e duração.

- **8.2 Transcrição**
  - Subtarefas:
    - Definir provedor de transcrição (modelo/serviço).
    - Persistir transcrição (ou resumo) conforme política LGPD.

- **8.3 Critérios de aceite da fase**
  - Áudio vira texto; agente responde corretamente; falhas geram fallback (“pode repetir em texto?”).

---

### 9) Fase 9 — Hardening: segurança, confiabilidade, observabilidade e performance

**Objetivo**: preparar para produção com resiliência e compliance.

- **9.1 Segurança**
  - Subtarefas:
    - Secret management (env/secret store) + rotação.
    - Redação de logs (não logar PII desnecessária).
    - Rate limiting e proteção de endpoints públicos.

- **9.2 Confiabilidade**
  - Subtarefas:
    - Circuit breaker para CRM/provedor.
    - Dead-letter para mensagens não processáveis.
    - Reprocessamento manual controlado (admin).

- **9.3 Observabilidade**
  - Subtarefas:
    - Métricas (latência, falhas por integração, throughput).
    - Tracing distribuído (opcional).
    - Dashboards e alertas.

- **9.4 Performance e custos**
  - Subtarefas:
    - Medir P95/P99 e otimizar contexto.
    - Cache de cidade, dedupe agressivo, compressão de contexto.

- **9.5 Critérios de aceite da fase**
  - SLOs definidos e monitorados; alertas funcionando; incidentes simulados com runbook.

---

### 10) Fase 10 — Deploy, homologação e Go-Live

**Objetivo**: colocar em produção com segurança, rollback e acompanhamento.

- **10.1 Ambientes**
  - Subtarefas:
    - `dev` / `staging` / `prod` com variáveis separadas.
    - Chaves e endpoints segregados por ambiente.

- **10.2 Deploy**
  - Subtarefas:
    - Deploy container (VPS/K8s/Render/etc.).
    - Configurar domínio/HTTPS.
    - Configurar webhooks do provedor (staging → prod).

- **10.3 Homologação (UAT)**
  - Subtarefas:
    - Roteiro de testes com casos reais (quente/morno/frio, CNPJ, áudio, interrupção humana).
    - Checklist de aceite do time comercial/SDR.

- **10.4 Go-live e acompanhamento**
  - Subtarefas:
    - Feature flags (habilitar por canal/origem).
    - Monitoramento intensivo nas primeiras 72h.
    - Plano de rollback (desligar agente, manter Chatwoot).

- **10.5 Critérios de aceite da fase**
  - Produção estável, sem duplicidade grave no CRM, e com governança humana funcionando.

---

### 11) Backlog pós-MVP (evoluções recomendadas)

- **Score avançado** (fit + volume + urgência + intenção).
- **RAG com vector store** para catálogo/FAQ (quando a base crescer).
- **Evals contínuos** (qualidade das respostas, compliance com política).
- **Painel interno** para atualização de base de conhecimento e regras (se necessário).


