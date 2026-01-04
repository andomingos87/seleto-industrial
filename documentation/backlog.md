# Backlog — Agente de IA (SDR) para Seleto Industrial

> Derivado do PRD v1.0 (2026-01-03)

---

## Resumo do Produto

- **Objetivo**: Automatizar atendimento inicial via WhatsApp, qualificar leads e registrar dados no CRM (Piperun)
- **Público-alvo**: Leads B2B (indústria alimentícia), SDRs, vendedores
- **Stack**: Agno (Python/FastAPI), Supabase, Piperun, Chatwoot, WhatsApp (Z-API)

**Nota:** As stories TECH-005, TECH-006 e TECH-007 requerem as seguintes variáveis de ambiente para integração com a Z-API:
- `ZAPI_INSTANCE_ID`: Identificador da instância Z-API.
- `ZAPI_INSTANCE_TOKEN`: Token da instância.
- `ZAPI_CLIENT_TOKEN`: Token de conta (usado no header `Client-Token`).
- `ZAPI_WEBHOOK_SECRET`: Secret para validar webhooks recebidos (opcional).

---

## Epic 1 — Infraestrutura e Setup Inicial

> Preparar ambiente de desenvolvimento, runtime e integrações base.

### TECH-001: Configurar projeto Agno com FastAPI ✅

- **Tipo**: Technical Story
- **Descrição**: Criar estrutura base do projeto com Agno Agent Framework, FastAPI como runtime HTTP, e configuração de ambiente (variáveis, Docker).
- **Critérios de Aceitação**:
  - [x] Projeto inicializado com estrutura de diretórios padrão (src/, tests/, config/)
  - [x] Dockerfile funcional para build e execução local
  - [x] Arquivo `.env.example` com todas as variáveis necessárias (sem valores reais)
  - [x] Endpoint `/health` retornando status 200
  - [x] README com instruções de setup local
- **Dependências**: Nenhuma
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-04
- **Artefatos**:
  - Estrutura de diretórios: `src/`, `tests/`, `config/`
  - `Dockerfile` — Build multi-stage com healthcheck
  - `.env.example` — Template com todas as variáveis de ambiente (incluindo Z-API)
  - `src/api/routes/health.py` — Endpoint `/api/health` retornando status 200
  - `README.md` — Instruções completas de setup local e Docker

---

### TECH-002: Configurar Supabase — Schema de Banco de Dados ✅

- **Tipo**: Technical Story
- **Descrição**: Criar tabelas `leads`, `orcamentos` e `empresa` no Supabase conforme dicionário de dados do PRD.
- **Critérios de Aceitação**:
  - [x] Tabela `leads` com campos: id (uuid PK), phone (unique), name, temperature, city, uf, produto_interesse, volume_estimado, urgencia_compra, updated_at
  - [x] Tabela `orcamentos` com campos: id (uuid PK), lead (FK), resumo, produto, segmento, urgencia_compra, volume_diario, oportunidade_pipe_id, created_at
  - [x] Tabela `empresa` com campos: id (uuid PK), nome, cidade, uf, cnpj (unique quando presente), site, email, telefone, contato (FK), created_at
  - [x] RLS ativado em todas as tabelas
  - [x] Migration scripts versionados
- **Dependências**: Nenhuma
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Migrations aplicadas**:
  - `20260103152411_add_missing_fields_to_leads`
  - `20260103152423_add_cnpj_unique_constraint_to_empresa`
  - `20260103152432_enable_rls_on_all_tables`
- **Validação**:
  - ✅ Tabelas verificadas no Supabase: `leads`, `orcamentos`, `empresa`
  - ✅ Todos os campos especificados estão presentes
  - ✅ RLS ativado em todas as tabelas (verificado via MCP Supabase)
  - ✅ Foreign keys configuradas corretamente
  - ✅ Constraint unique no campo `cnpj` da tabela `empresa` aplicada
  - ✅ Migrações versionadas e aplicadas no banco

---

### TECH-003: Configurar gestão de segredos ✅

- **Tipo**: Technical Story
- **Descrição**: Implementar gestão segura de credenciais (API keys, tokens) usando variáveis de ambiente no runtime, sem hardcode no repositório.
- **Critérios de Aceitação**:
  - [x] Todas as credenciais carregadas via variáveis de ambiente
  - [x] Nenhum token/chave presente em arquivos versionados (validar com grep)
  - [x] Documentação de quais variáveis são necessárias
  - [x] Suporte a rotação de credenciais sem redeploy (quando aplicável)
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `.env.example` — Template com todas as variáveis documentadas
  - `src/config/settings.py` — Carregamento via Pydantic Settings
  - `README.md` — Documentação das variáveis de ambiente
- **Validação**:
  - ✅ Todas as credenciais carregadas via variáveis de ambiente (Pydantic BaseSettings)
  - ✅ Nenhum token/chave hardcoded encontrado no código (grep validado)
  - ✅ Arquivo `.env` protegido no `.gitignore` (não versionado)
  - ✅ `.env.example` existe e documenta todas as variáveis necessárias
  - ✅ README contém seção completa sobre variáveis de ambiente e rotação de credenciais
  - ✅ Suporte a rotação documentado (algumas integrações podem precisar restart, conforme documentado)

---

### TECH-004: Configurar logging estruturado ✅

- **Tipo**: Technical Story
- **Descrição**: Implementar logging estruturado (JSON) com contexto por requisição (request_id, phone, etapa do fluxo).
- **Critérios de Aceitação**:
  - [x] Logs em formato JSON com campos: timestamp, level, message, request_id, phone (quando disponível)
  - [x] Níveis de log configuráveis via variável de ambiente
  - [x] Logs de entrada/saída de webhooks
  - [x] Logs de chamadas a APIs externas (Piperun, Supabase)
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/utils/logging.py` — Módulo de logging estruturado com JSONFormatter e TextFormatter
  - `src/api/middleware/logging.py` — Middleware FastAPI para logging de requests
  - Funções utilitárias: `log_webhook_received()`, `log_webhook_response()`, `log_api_call()`
- **Validação**:
  - ✅ Logs em formato JSON com campos: timestamp, level, message, request_id, phone (quando disponível) — JSONFormatter implementado
  - ✅ Níveis de log configuráveis via variável de ambiente (`LOG_LEVEL` e `LOG_FORMAT` em settings.py)
  - ✅ Logs de entrada/saída de webhooks — `log_webhook_received()` e `log_webhook_response()` usados no middleware e rotas
  - ✅ Logs de chamadas a APIs externas — `log_api_call()` implementado e usado (ex: WhatsApp), preparado para Piperun e Supabase
  - ✅ Contexto por requisição usando ContextVar (request_id, phone, flow_step)
  - ✅ Middleware FastAPI integrado para logging automático de todas as requisições

---

## Epic 2 — Ingestão de Mensagens (WhatsApp)

> Receber e processar mensagens do provedor WhatsApp.

### TECH-005: Implementar webhook de recebimento de mensagens (texto) ✅

- **Tipo**: Technical Story
- **Descrição**: Criar endpoint POST para receber webhooks do provedor WhatsApp com mensagens de texto.
- **Critérios de Aceitação**:
  - [x] Endpoint `POST /webhook/whatsapp` funcional
  - [x] Parsing correto de payload com campos: phone, senderName, message (texto)
  - [x] Validação de token/header de autenticação do provedor
  - [x] Normalização do telefone para formato E.164 (apenas dígitos)
  - [x] Resposta 200 em até 2s (processamento assíncrono se necessário)
  - [x] Logs de entrada com phone e tipo de mensagem
- **Dependências**: TECH-001, TECH-004
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/api/routes/webhook.py` — Endpoint POST /webhook/whatsapp com parsing e validação
  - `src/utils/validation.py` — Funções de normalização de telefone (normalize_phone, validate_phone)
- **Validação**:
  - ✅ Endpoint `POST /webhook/whatsapp` funcional e registrado no main.py
  - ✅ Parsing correto de payload com campos: phone, senderName, message (texto) — WhatsAppWebhookPayload implementado
  - ✅ Validação de token/header de autenticação — `validate_webhook_auth()` suporta Authorization Bearer e X-Webhook-Secret
  - ✅ Normalização do telefone para formato E.164 (apenas dígitos) — `normalize_phone()` implementada e usada
  - ✅ Resposta 200 em até 2s — Processamento assíncrono com `asyncio.create_task()` e resposta imediata
  - ✅ Logs de entrada com phone e tipo de mensagem — `log_webhook_received()` usado com phone e message_type
- **Especificações Z-API**:
  - Endpoint de webhook configurado via: `PUT /instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/update-webhook-received`
  - Payload recebido: `phone`, `senderName`, `message`, `messageId`, `messageType`, `audio` (opcional)
  - Autenticação: Header `Client-Token` (Account Security Token) para configuração do webhook
  - URL do webhook: `https://seu-dominio.com/webhook/whatsapp` (deve ser HTTPS válido)
  - Formato: JSON direto no body da requisição POST (sem wrapper de headers)

---

### TECH-006: Implementar envio de mensagens via WhatsApp ✅

- **Tipo**: Technical Story
- **Descrição**: Criar serviço para enviar mensagens de texto via API do provedor WhatsApp.
- **Critérios de Aceitação**:
  - [x] Função `send_whatsapp_message(phone, text)` implementada
  - [x] Retry com backoff exponencial em caso de falha (até 3 tentativas)
  - [x] Logs de sucesso/falha com phone e status
  - [x] Tratamento de rate limit do provedor
- **Dependências**: TECH-001, TECH-003
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/services/whatsapp.py` — Serviço WhatsAppService com retry e backoff exponencial
  - Função `send_whatsapp_message()` para envio de mensagens
- **Validação**:
  - ✅ Função `send_whatsapp_message(phone, text)` implementada (linha 221-232)
  - ✅ Retry com backoff exponencial em caso de falha (até 3 tentativas) — `max_retries=3` por padrão, backoff exponencial: `initial_backoff * (2**attempt)`
  - ✅ Logs de sucesso/falha com phone e status — Logs detalhados em sucesso (linhas 114-121), falha (linhas 133-140), e tentativas esgotadas (linhas 206-213)
  - ✅ Tratamento de rate limit do provedor — Tratamento específico de 429 com `Retry-After` header (linhas 86-100)
  - ✅ Tratamento de erros HTTP — 4xx (não retry exceto 429), 5xx (retry), timeout e connection errors (retry)
  - ✅ Normalização de telefone antes do envio — Usa `normalize_phone()` para formato E.164
- **Especificações Z-API**:
  - Endpoint: `POST https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/send-text`
  - Autenticação: Header `Client-Token: {ZAPI_CLIENT_TOKEN}`
  - Payload: `{"phone": "5511999999999", "message": "texto"}`
  - Variáveis de ambiente: `ZAPI_INSTANCE_ID`, `ZAPI_INSTANCE_TOKEN`, `ZAPI_CLIENT_TOKEN`
  - Retry: Implementado com backoff exponencial (até 3 tentativas)
  - Rate limit: Tratamento de 429 com `Retry-After` header
  - Erros tratados: 401 (Unauthorized), 404 (Not Found), 405 (Method Not Allowed), 415 (Unsupported Media Type), 429 (Rate Limit), 5xx (Server Error)

---

### TECH-007: Implementar recebimento e transcrição de áudio ✅

- **Tipo**: Technical Story
- **Descrição**: Processar mensagens de áudio recebidas via webhook, baixar arquivo e transcrever para texto.
- **Critérios de Aceitação**:
  - [x] Parsing de payload com objeto `audio` (audioUrl, mimeType, seconds)
  - [x] Download do arquivo de áudio via URL
  - [x] Integração com serviço de transcrição (ex: Whisper API)
  - [x] Texto transcrito disponível para processamento pelo agente
  - [x] Log indicando que mensagem era áudio + duração
  - [x] Fallback/erro tratado se transcrição falhar
  - [ ] Remoção automática de arquivos de áudio após 90 dias (conforme política LGPD - D6)
  - [ ] Anonimização de transcrições após 90 dias (remover identificadores diretos como nome, telefone, CNPJ)
- **Dependências**: TECH-005
- **Prioridade**: Média
- **Fase**: Fase 2
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/services/transcription.py` — Serviço TranscriptionService com integração Whisper API
  - Função `transcribe_audio()` para transcrição de áudio
  - Suporte a múltiplos formatos de áudio (ogg, mp3, wav, webm, etc.)
- **Validação**:
  - ✅ Parsing de payload com objeto `audio` (audioUrl, mimeType, seconds) — Extração em `process_audio_message()` (linhas 213-215)
  - ✅ Download do arquivo de áudio via URL — Implementado com httpx.AsyncClient (linhas 61-75)
  - ✅ Integração com serviço de transcrição (Whisper API) — OpenAI Whisper-1 model (linhas 79-84)
  - ✅ Texto transcrito disponível para processamento pelo agente — Passado para `process_message()` (linhas 270-276)
  - ✅ Log indicando que mensagem era áudio + duração — Logs detalhados em múltiplos pontos (webhook.py linhas 228-238, transcription.py linhas 51-58, 88-95)
  - ✅ Fallback/erro tratado se transcrição falhar — Mensagem de fallback enviada quando transcrição falha (linhas 247-259, 292-306)
  - ⚠️ Remoção automática de arquivos de áudio após 90 dias — Pendente (TECH-031)
  - ⚠️ Anonimização de transcrições após 90 dias — Pendente (TECH-031)
- **Especificações Z-API**:
  - Webhook de áudio: Payload contém objeto `audio` com `audioUrl`, `mimeType`, `seconds`
  - Formatos suportados: OGG (Opus), MP3, WAV, WEBM, AAC, M4A
  - Download: Arquivo disponível via `audioUrl` (HTTPS)
  - Transcrição: Integração com Whisper API (OpenAI) para converter áudio em texto
  - Fallback: Se transcrição falhar, agente solicita que lead repita por texto
  - Campo `messageType`: `"audio"` quando mensagem é de áudio
  - Limpeza: Arquivos temporários removidos automaticamente após transcrição

---

## Epic 3 — Agente Conversacional (Core)

> Lógica do agente de IA para atendimento e qualificação.

### US-001: Cumprimentar lead e iniciar coleta de dados ✅

- **Tipo**: User Story
- **Descrição**: Como lead, ao enviar a primeira mensagem, quero receber uma saudação cordial e ser perguntado sobre minha necessidade, para que eu me sinta bem atendido.
- **Critérios de Aceitação**:
  - [x] Agente responde em até 5s após receber mensagem
  - [x] Mensagem de boas-vindas menciona a Seleto Industrial
  - [x] Agente pergunta sobre a necessidade/produto de interesse
  - [x] Tom cordial, profissional e empático (sem jargões robóticos)
  - [x] Máximo de 2 perguntas diretas na primeira interação
- **Dependências**: TECH-005, TECH-006
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/services/prompt_loader.py` — Serviço para carregar prompt do sistema do XML (TECH-010)
  - `src/services/conversation_memory.py` — Memória básica de conversa por telefone (TECH-008 básico)
  - `src/agents/sdr_agent.py` — Agente SDR com prompt do sistema e lógica de processamento
  - Integração com webhook para processar mensagens e enviar respostas automaticamente
- **Validação**:
  - ✅ Agente responde em até 5s após receber mensagem — Tempo medido e logado (linhas 99, 227), warning se exceder 5s (linhas 241-248). Processamento assíncrono no webhook garante resposta HTTP rápida
  - ✅ Mensagem de boas-vindas menciona a Seleto Industrial — Prompt XML (linha 111) e fallback (linhas 191-195, 264-267) incluem "Seleto Industrial"
  - ✅ Agente pergunta sobre a necessidade/produto de interesse — Prompt XML (linha 114) e objetivos (linha 87) direcionam para entender o que o lead busca
  - ✅ Tom cordial, profissional e empático (sem jargões robóticos) — Diretrizes claras no prompt XML (linhas 24-26): "Sempre cordial, profissional e empático", "Evite jargões técnicos, gírias ou mensagens robotizadas"
  - ✅ Máximo de 2 perguntas diretas na primeira interação — Controle implementado via `question_count` (linhas 122-123, 136-141, 199-218) e reforçado no prompt XML (linha 33): "Faça no máximo duas perguntas diretas seguidas"
  - ✅ Detecção de primeira mensagem — `is_first_message()` verifica se é primeira interação (linha 102)
  - ✅ Fallback para primeira mensagem — Mensagem de boas-vindas padrão se agente falhar (linhas 190-195, 263-268)

---

### US-002: Coletar dados progressivamente durante a conversa ✅

- **Tipo**: User Story
- **Descrição**: Como agente, quero coletar nome, empresa, cidade/UF, produto, volume e urgência ao longo da conversa, sem enviar um questionário de uma vez.
- **Critérios de Aceitação**:
  - [x] Dados coletados: nome, empresa (opcional), cidade/UF, produto/necessidade, volume/capacidade, urgência
  - [x] Máximo de 2 perguntas diretas seguidas (regra de ritmo)
  - [x] Perguntas contextualizadas com base nas respostas anteriores
  - [x] Dados parciais são persistidos mesmo que conversa não seja concluída
- **Dependências**: US-001, TECH-008
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Revisado em**: 2026-01-04
- **Artefatos**:
  - `src/services/data_extraction.py` — Serviço de extração de dados estruturados usando LLM
  - `src/services/lead_persistence.py` — Serviço de persistência de dados parciais (preparado para Supabase)
  - `src/services/conversation_memory.py` — Controle de ritmo de perguntas (question_count)
  - `src/agents/sdr_agent.py` — Integração de extração e persistência no fluxo de processamento
  - `prompts/system_prompt/sp_agente_v1.xml` — Atualizado com diretrizes de coleta progressiva
- **Validação**:
  - ✅ Dados coletados: nome, empresa (opcional), cidade/UF, produto/necessidade, volume/capacidade, urgência — `LEAD_DATA_FIELDS` inclui todos os campos (linhas 20-29): name, company, city, uf, product, volume, urgency, knows_seleto
  - ✅ Máximo de 2 perguntas diretas seguidas (regra de ritmo) — Controle via `question_count` (linhas 122-123, 136-141, 199-218), reset quando usuário responde (linha 117), diretriz no prompt XML (linha 33)
  - ✅ Perguntas contextualizadas com base nas respostas anteriores — Dados coletados passados como contexto ao agente (linhas 129-133), prompt XML (linhas 36, 62) instrui a contextualizar perguntas
  - ✅ Dados parciais são persistidos mesmo que conversa não seja concluída — `persist_lead_data()` chamado imediatamente após extração (linha 112), comentário explícito "even if partial - US-002 requirement" (linha 110), atualização imediata na memória (linha 41)
  - ✅ Extração incremental — `extract_lead_data()` recebe `current_data` e extrai apenas informações novas (linhas 45-46, 74-76)
  - ✅ Normalização de dados — UF normalizado para 2 letras maiúsculas (linhas 190-192), urgência normalizada (linhas 193-205), knows_seleto normalizado (linhas 206-214)

---

### US-003: Responder dúvidas usando base de conhecimento

- **Tipo**: User Story
- **Descrição**: Como lead, quero tirar dúvidas sobre equipamentos da Seleto Industrial, para entender se atendem minha necessidade.
- **Critérios de Aceitação**:
  - [x] Agente responde perguntas sobre formadoras, cortadoras, linhas automáticas
  - [x] Respostas baseadas nos arquivos de `prompts/equipamentos/*`
  - [x] Se dúvida for técnica demais, agente registra e informa que especialista entrará em contato
  - [x] Agente não promete prazos de entrega, descontos ou orçamento completo
  - [x] Agente não informa preços, condições comerciais ou descontos em nenhuma circunstância
- **Dependências**: TECH-009
- **Prioridade**: Alta
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/knowledge_base.py` - Serviço de base de conhecimento com guardrails
  - `tests/services/test_knowledge_base.py` - 77 testes do serviço
  - `tests/agents/test_sdr_agent_knowledge.py` - 11 testes de integração

---

### US-004: Sugerir upsell de FBM100 para FB300 ✅

- **Tipo**: User Story
- **Descrição**: Como agente, quando o lead demonstrar interesse na formadora manual FBM100, quero sugerir também a FB300 (semi-automática) como alternativa.
- **Critérios de Aceitação**:
  - [x] Quando lead mencionar FBM100, agente apresenta FB300 como opção "acima"
  - [x] Tom consultivo, sem pressão
  - [x] Registro da sugestão no contexto da conversa
- **Dependências**: US-003
- **Prioridade**: Média
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/upsell.py` - Serviço de detecção de interesse e sugestão de upsell
  - `src/agents/sdr_agent.py` - Integração do upsell no fluxo de processamento (linhas 205-212)
  - `tests/services/test_upsell.py` - 40 testes unitários do serviço
  - `tests/agents/test_sdr_agent_upsell.py` - 11 testes de integração
- **Validação**:
  - ✅ Detecção de interesse em FBM100 via múltiplas keywords (FBM100, formadora manual, hambúrguer manual, etc.)
  - ✅ Sugestão de FB300 injetada no contexto do agente com tom consultivo
  - ✅ Comparativo de produtividade: FBM100 (500-600/dia) vs FB300 (300-350/hora)
  - ✅ Controle para evitar sugestões repetidas (mesmo lead não recebe duas vezes)
  - ✅ Registro de sugestões no contexto com timestamp e mensagem que disparou
  - ✅ 51 testes passando (40 unitários + 11 integração)

---

### US-005: Tratar interesse em produto indisponível (linha de espetos) ✅

- **Tipo**: User Story
- **Descrição**: Como agente, quando o lead perguntar sobre máquina de espetos (indisponível), quero informar que está em melhoria e oferecer alternativa.
- **Critérios de Aceitação**:
  - [x] Agente informa que projeto está em melhoria com previsão interna
  - [x] Agente registra interesse para contato futuro
  - [x] Agente oferece CT200 (corte em cubos) como alternativa quando fizer sentido
- **Dependências**: US-003
- **Prioridade**: Baixa
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/unavailable_products.py` - Serviço de detecção de interesse e tratamento de produtos indisponíveis
  - `src/agents/sdr_agent.py` - Integração do tratamento de produtos indisponíveis no fluxo de processamento (linhas 215-222)
  - `tests/services/test_unavailable_products.py` - 47 testes unitários do serviço
  - `tests/agents/test_sdr_agent_unavailable.py` - 15 testes de integração
- **Validação**:
  - ✅ Detecção de interesse em linha de espetos via múltiplas keywords (espeto, espetos, espetinho, espetar, máquina de espeto, etc.)
  - ✅ Mensagem sobre indisponibilidade injetada no contexto do agente com tom profissional e empático
  - ✅ Registro de interesse para contato futuro (ProductInterest dataclass com phone, product, timestamp, context)
  - ✅ Sugestão condicional de CT200 quando lead menciona contexto de corte (cubo, tira, cortar, preparar carne)
  - ✅ Instrução para agente NÃO mencionar data de previsão (março/2026) - informação apenas interna
  - ✅ 62 testes passando (47 unitários + 15 integração)
  - ✅ Integração com base de conhecimento e guardrails existentes funcional

---

### TECH-008: Implementar memória/histórico de conversa por lead ✅

- **Tipo**: Technical Story
- **Descrição**: Manter histórico de mensagens e contexto coletado por telefone do lead, para continuidade da conversa.
- **Critérios de Aceitação**:
  - [x] Histórico completo de mensagens persistido no Supabase (DB) para auditoria, análise e backup
  - [x] Histórico também replicado no Chatwoot para interface visual e acompanhamento humano em tempo real
  - [x] Contexto coletado (nome, cidade, produto, etc.) persistido e recuperável
  - [x] Lead identificado por telefone (idempotência)
  - [x] Histórico disponível para consulta do agente em cada turno
- **Dependências**: TECH-002
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-XX
- **Artefatos**:
  - `src/services/conversation_persistence.py` - Serviço de persistência no Supabase
  - `src/services/chatwoot_sync.py` - Serviço de sincronização com Chatwoot
  - Modificações em `src/services/conversation_memory.py` - Integração com persistência Supabase e Chatwoot
  - Modificações em `src/services/lead_persistence.py` - Integração com contexto persistido
  - Migrations SQL para Supabase: `create_conversation_messages_table`, `create_conversation_context_table`
  - Testes: `tests/services/test_conversation_persistence.py`, `tests/services/test_chatwoot_sync.py`, `tests/agents/test_sdr_agent_history.py`
- **Validação**:
  - ✅ Tabelas `conversation_messages` e `conversation_context` criadas no Supabase com RLS ativado
  - ✅ Mensagens são persistidas automaticamente no Supabase quando adicionadas ao histórico
  - ✅ Mensagens são sincronizadas com Chatwoot de forma assíncrona (não bloqueia resposta)
  - ✅ Contexto coletado é persistido e recuperado do Supabase
  - ✅ Histórico é carregado automaticamente do Supabase quando necessário (cache em memória)
  - ✅ Lead identificado por telefone normalizado (idempotência garantida)
  - ✅ Histórico disponível para o agente em cada turno através de `conversation_memory.get_messages_for_llm()`

---

### TECH-009: Carregar base de conhecimento de produtos

- **Tipo**: Technical Story
- **Descrição**: Carregar e indexar arquivos de `prompts/equipamentos/*` para uso pelo agente nas respostas.
- **Critérios de Aceitação**:
  - [x] Arquivos de equipamentos carregados no startup do agente
  - [x] Busca semântica ou por palavras-chave funcional
  - [x] Atualização da base requer apenas substituição de arquivos + restart
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/knowledge_base.py` - Classe `KnowledgeBase` com métodos `load_equipment_files()` e `search_knowledge_base()`
  - Cache em memória implementado (singleton pattern)
  - Busca por palavras-chave funcional para formadoras, cortadoras, ensacadeiras, misturadores e linhas automáticas

---

### TECH-010: Implementar prompt do sistema (sp_agente_v1.xml)

- **Tipo**: Technical Story
- **Descrição**: Configurar o agente com o prompt do sistema definido em `prompts/system_prompt/sp_agente_v1.xml`.
- **Critérios de Aceitação**:
  - [x] Prompt carregado do arquivo XML
  - [x] Prompt aplicado em todas as sessões de conversa
  - [x] Alterações no arquivo refletem após restart
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP
- **Status**: ✅ Concluído
- **Data de Conclusão**: 2026-01-27
- **Data de Revisão**: 2026-01-27

---

## Epic 4 — Classificação de Temperatura

> Classificar leads em frio/morno/quente.

### US-006: Classificar lead ao final da qualificação ✅

- **Tipo**: User Story
- **Descrição**: Como SDR, quero que o agente classifique cada lead como frio, morno ou quente, para priorizar meu tempo.
- **Critérios de Aceitação**:
  - [x] Lead classificado em uma das três temperaturas: frio, morno, quente
  - [x] Classificação considera: engajamento, completude dos dados, volume, urgência
  - [x] Classificação persistida no banco (campo `temperature` no contexto do lead via Supabase)
  - [x] Justificativa mínima registrada (ex: "respondeu todas as perguntas, urgência alta")
- **Dependências**: US-002, TECH-011
- **Prioridade**: Alta
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/temperature_classification.py` - Serviço de classificação de temperatura
  - `src/agents/sdr_agent.py` - Integração da classificação no fluxo de processamento (linhas 177-206)
  - `prompts/system_prompt/sp_calcula_temperatura.xml` - Prompt XML com critérios de classificação
  - `tests/services/test_temperature_classification.py` - 37 testes unitários
  - `tests/agents/test_sdr_agent_temperature.py` - 10 testes de integração
- **Validação**:
  - ✅ Função `calculate_temperature()` classifica leads como frio, morno ou quente
  - ✅ Score de engajamento calculado a partir do histórico de conversa (respostas, tamanho das mensagens)
  - ✅ Score de completude calculado a partir dos dados coletados (campos preenchidos)
  - ✅ Volume e urgência considerados na classificação via LLM
  - ✅ Temperatura persistida no campo `temperature` do contexto do lead no Supabase
  - ✅ Justificativa persistida no campo `temperature_justification`
  - ✅ Fallback para classificação por regras quando LLM indisponível
  - ✅ 47 testes passando (37 unitários + 10 integração)

---

### TECH-011: Implementar lógica de classificação de temperatura ✅

- **Tipo**: Technical Story
- **Descrição**: Criar módulo/função que calcula temperatura do lead com base nos dados coletados, usando prompt `sp_calcula_temperatura.xml`.
- **Critérios de Aceitação**:
  - [x] Função `calculate_temperature(lead_data) -> (temperature, justification)`
  - [x] Critérios: engajamento (respondeu perguntas), volume, urgência, fit com portfólio
  - [x] Prompt de temperatura carregado de `prompts/system_prompt/sp_calcula_temperatura.xml`
  - [x] Retorno inclui justificativa textual
- **Dependências**: TECH-010
- **Prioridade**: Alta
- **Fase**: MVP
- **Status**: ✅ Concluído (2026-01-04)
- **Artefatos**:
  - `src/services/temperature_classification.py` - Módulo com funções:
    - `calculate_temperature(lead_data, conversation_summary, conversation_history, phone)` - Função principal
    - `calculate_engagement_score(phone, conversation_history)` - Cálculo de engajamento
    - `calculate_completeness_score(lead_data)` - Cálculo de completude
    - `load_temperature_prompt()` - Carregamento do prompt XML
    - `update_lead_temperature(phone, temperature, justification)` - Persistência
    - `should_classify_lead(lead_data)` - Verificação de critérios para classificar
    - `classify_lead(phone, lead_data, conversation_history)` - Função de alto nível
  - `prompts/system_prompt/sp_calcula_temperatura.xml` - Prompt com critérios detalhados:
    - Critérios para frio: baixo engajamento, dados incompletos, sem urgência
    - Critérios para morno: engajamento moderado, dados parciais, urgência baixa/média
    - Critérios para quente: alto engajamento, dados completos, urgência alta, volume significativo
    - Exemplos de classificação para cada temperatura
    - Pesos: engajamento (25%), completude (25%), volume (25%), urgência (25%)
- **Validação**:
  - ✅ Função `calculate_temperature()` retorna tupla (temperatura, justificativa)
  - ✅ Critérios de engajamento calculados: taxa de resposta, tamanho médio das mensagens, número de mensagens
  - ✅ Critérios de completude calculados: campos obrigatórios (60%) e opcionais (40%)
  - ✅ Urgência e volume incluídos no contexto enviado ao LLM
  - ✅ Prompt XML carregado e formatado corretamente
  - ✅ Justificativa textual retornada em todas as classificações
  - ✅ Fallback baseado em regras quando LLM falha

---

## Epic 5 — Persistência Local (Supabase)

> Salvar e recuperar dados de leads, orçamentos e empresas.

**Status do Epic:** 🟡 Em Progresso (Stage 1 concluído)

**Progresso:**
- ✅ Stage 1: Discovery & Setup (2026-01-XX)
  - ✅ Schema Supabase validado (leads, orcamentos, empresa)
  - ✅ Código existente revisado (conversation_persistence, validation, lead_persistence)
  - ✅ Estrutura de testes criada (test_lead_crud, test_orcamento_crud, test_empresa_crud)
- ⏳ Stage 2: TECH-012 - CRUD de Leads (próximo)
- ⏳ Stage 3: TECH-013 - CRUD de Orçamentos
- ⏳ Stage 4: TECH-014 - CRUD de Empresas
- ⏳ Stage 5: Validação, Testes e Documentação

**Notas do Stage 1:**
- Schema validado: `leads.phone` tem constraint UNIQUE ✅
- Schema validado: `empresa.cnpj` NÃO tem constraint UNIQUE ⚠️ (dedupe via lógica de aplicação)
- Código reutilizável identificado: `get_supabase_client()`, `normalize_phone()`, `normalize_cnpj()`
- Estrutura de testes criada seguindo padrão de `test_conversation_persistence.py`
- Ver plan detalhado: `.context/plans/epic-5-persistencia-local-supabase.md`

### TECH-012: Implementar CRUD de leads

- **Tipo**: Technical Story
- **Descrição**: Criar funções para criar, buscar e atualizar leads no Supabase, com idempotência por telefone.
- **Critérios de Aceitação**:
  - [ ] `upsert_lead(phone, data)` — cria ou atualiza lead
  - [ ] `get_lead_by_phone(phone)` — retorna lead ou None
  - [ ] Telefone normalizado (E.164, apenas dígitos) antes de operações
  - [ ] Atualização parcial (não sobrescreve campos com null)
  - [ ] Logs de operações
- **Dependências**: TECH-002
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-013: Implementar CRUD de orçamentos

- **Tipo**: Technical Story
- **Descrição**: Criar funções para criar e recuperar orçamentos vinculados a leads.
- **Critérios de Aceitação**:
  - [ ] `create_orcamento(lead_id, data)` — cria orçamento
  - [ ] `get_orcamentos_by_lead(lead_id)` — lista orçamentos do lead
  - [ ] `update_orcamento(id, data)` — atualiza campos (ex: oportunidade_pipe_id)
  - [ ] Campos: resumo, produto, segmento, urgencia_compra, volume_diario
- **Dependências**: TECH-002
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-014: Implementar CRUD de empresas

- **Tipo**: Technical Story
- **Descrição**: Criar funções para criar e buscar empresas no Supabase, com dedupe por CNPJ.
- **Critérios de Aceitação**:
  - [ ] `create_empresa(data)` — cria empresa
  - [ ] `get_empresa_by_cnpj(cnpj)` — busca por CNPJ normalizado
  - [ ] `update_empresa(id, data)` — atualiza campos
  - [ ] CNPJ normalizado para 14 dígitos antes de operações
- **Dependências**: TECH-002
- **Prioridade**: Média
- **Fase**: Fase 2

---

## Epic 6 — Integração CRM (Piperun)

> Sincronizar dados com o CRM Piperun.

### TECH-015: Implementar cliente HTTP para Piperun

- **Tipo**: Technical Story
- **Descrição**: Criar cliente HTTP reutilizável para chamadas à API do Piperun, com autenticação e retry.
- **Critérios de Aceitação**:
  - [ ] Classe/módulo `PiperunClient` com métodos para cada endpoint
  - [ ] Autenticação via token em header
  - [ ] Retry com backoff exponencial (até 3 tentativas)
  - [ ] Timeout configurável (default 10s)
  - [ ] Logs de request/response (sem expor tokens)
- **Dependências**: TECH-003
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-016: Implementar busca de city_id

- **Tipo**: Technical Story
- **Descrição**: Buscar código da cidade no Piperun por nome + UF.
- **Critérios de Aceitação**:
  - [ ] Função `get_city_id(city_name, uf) -> city_id`
  - [ ] Chamada a `GET /v1/cities?name={name}&uf={uf}`
  - [ ] Retorna None se cidade não encontrada
  - [ ] Cache opcional para evitar chamadas repetidas
- **Dependências**: TECH-015
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-017: Implementar busca de empresa por CNPJ

- **Tipo**: Technical Story
- **Descrição**: Buscar empresa existente no Piperun por CNPJ para evitar duplicidade.
- **Critérios de Aceitação**:
  - [ ] Função `get_company_by_cnpj(cnpj) -> company_id | None`
  - [ ] Chamada a `GET /v1/companies?cnpj={cnpj}`
  - [ ] CNPJ normalizado antes da busca
- **Dependências**: TECH-015
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-018: Implementar criação de empresa no CRM

- **Tipo**: Technical Story
- **Descrição**: Criar empresa no Piperun com dados coletados.
- **Critérios de Aceitação**:
  - [ ] Função `create_company(name, city_id, cnpj, website, email_nf) -> company_id`
  - [ ] Chamada a `POST /v1/companies`
  - [ ] Retorna ID da empresa criada
- **Dependências**: TECH-015, TECH-016
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-019: Implementar criação de pessoa no CRM

- **Tipo**: Technical Story
- **Descrição**: Criar pessoa (contato) no Piperun.
- **Critérios de Aceitação**:
  - [ ] Função `create_person(name, phones, emails, city_id) -> person_id`
  - [ ] Chamada a `POST /v1/persons`
  - [ ] Telefones e e-mails como arrays
- **Dependências**: TECH-015, TECH-016
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-020: Implementar criação de oportunidade (deal)

- **Tipo**: Technical Story
- **Descrição**: Criar oportunidade no Piperun em pipeline/stage configurados.
- **Critérios de Aceitação**:
  - [ ] Função `create_deal(title, pipeline_id, stage_id, origin_id, person_id, company_id) -> deal_id`
  - [ ] Chamada a `POST /v1/deals`
  - [ ] Pipeline, stage e origin parametrizados via config/env
  - [ ] Título no formato: "Lead — [Produto] — [Cidade/UF]"
- **Dependências**: TECH-015
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-021: Implementar criação de nota na oportunidade

- **Tipo**: Technical Story
- **Descrição**: Registrar nota padronizada na oportunidade do Piperun.
- **Critérios de Aceitação**:
  - [ ] Função `create_note(deal_id, content) -> note_id`
  - [ ] Chamada a `POST /v1/notes`
  - [ ] Conteúdo segue template do PRD (Apêndice 20.3)
  - [ ] Campos não informados preenchidos com "Não informado"
- **Dependências**: TECH-015, TECH-020
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-007: Criar oportunidade no CRM para lead qualificado

- **Tipo**: User Story
- **Descrição**: Como SDR, quero que leads qualificados tenham oportunidade criada automaticamente no CRM, para que eu possa acompanhar o funil.
- **Critérios de Aceitação**:
  - [ ] Oportunidade criada quando lead tem dados mínimos (nome + produto + cidade)
  - [ ] Oportunidade vinculada ao pipeline e stage corretos
  - [ ] Nota com resumo do atendimento anexada à oportunidade
  - [ ] ID da oportunidade salvo no campo `oportunidade_pipe_id` do orçamento
- **Dependências**: TECH-020, TECH-021, TECH-013
- **Prioridade**: Alta
- **Fase**: MVP

---

## Epic 7 — Integração Chatwoot

> Sincronizar conversas e permitir intervenção humana.

### TECH-022: Integrar com Chatwoot para registro de conversas

- **Tipo**: Technical Story
- **Descrição**: Enviar mensagens do agente e do lead para o Chatwoot, mantendo histórico visível para SDRs. Histórico completo também persistido no Supabase (DB) conforme decisão D5.
- **Critérios de Aceitação**:
  - [ ] Mensagens do lead replicadas no Chatwoot
  - [ ] Mensagens do agente replicadas no Chatwoot
  - [ ] Histórico completo também persistido no Supabase (DB) para auditoria, análise e backup
  - [ ] Conversa identificada por telefone do lead
  - [ ] Histórico acessível em tempo real pelo SDR no Chatwoot
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-008: Pausar agente quando SDR intervir

- **Tipo**: User Story
- **Descrição**: Como SDR, quando eu enviar uma mensagem na conversa pelo Chatwoot, quero que o agente pare de responder automaticamente, para que eu assuma o atendimento.
- **Critérios de Aceitação**:
  - [ ] Ao detectar mensagem de SDR no Chatwoot, agente entra em modo "escuta"
  - [ ] Agente não envia novas mensagens automáticas após intervenção
  - [ ] **Dentro do horário de atendimento**: agente só retoma mediante comando explícito do SDR (`/retomar` ou `/continuar`)
  - [ ] **Fora do horário de atendimento**: agente retoma automaticamente quando o lead enviar nova mensagem (SDR não está presente)
  - [ ] Status de "agente pausado" registrado no contexto da conversa
  - [ ] Log indicando intervenção humana e horário de atendimento atual
- **Dependências**: TECH-022, TECH-032
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-009: Gerar resumo de handoff para lead quente

- **Tipo**: User Story
- **Descrição**: Como SDR, quando um lead quente for identificado, quero receber um resumo estruturado no Chatwoot, para assumir o atendimento com contexto.
- **Critérios de Aceitação**:
  - [ ] Resumo gerado no formato do template (Apêndice 20.4)
  - [ ] Campos: Nome, Empresa, Localização, Produto, Capacidade, Urgência, Conhece Seleto, Observações
  - [ ] Resumo enviado como mensagem interna no Chatwoot
  - [ ] Enviado automaticamente quando temperatura = quente
- **Dependências**: US-006, TECH-022
- **Prioridade**: Alta
- **Fase**: MVP

---

## Epic 8 — Observabilidade e Operações

> Monitoramento, métricas e alertas.

### TECH-023: Implementar métricas de latência e taxa de sucesso

- **Tipo**: Technical Story
- **Descrição**: Coletar métricas de tempo de resposta e taxa de sucesso/falha por operação.
- **Critérios de Aceitação**:
  - [ ] Métrica de latência por endpoint (P50, P95, P99)
  - [ ] Taxa de sucesso/falha por integração (WhatsApp, Piperun, Supabase)
  - [ ] Métricas expostas em formato Prometheus ou equivalente
- **Dependências**: TECH-004
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-024: Implementar alertas para falhas críticas

- **Tipo**: Technical Story
- **Descrição**: Configurar alertas para falhas contínuas em integrações e degradação de performance.
- **Critérios de Aceitação**:
  - [ ] Alerta quando taxa de erro > 10% em janela de 5 minutos
  - [ ] Alerta quando latência P95 > 10s
  - [ ] Alerta quando autenticação falhar em qualquer integração
  - [ ] Notificação via canal configurado (Slack, email, etc.)
- **Dependências**: TECH-023
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-025: Criar runbook de operações

- **Tipo**: Technical Story
- **Descrição**: Documentar procedimentos operacionais para cenários comuns.
- **Critérios de Aceitação**:
  - [ ] Runbook: Como pausar/retomar o agente manualmente
  - [ ] Runbook: Como rotacionar credenciais
  - [ ] Runbook: Como reprocessar mensagens com falha
  - [ ] Runbook: Como atualizar base de conhecimento
- **Dependências**: Nenhuma
- **Prioridade**: Baixa
- **Fase**: Fase 2

---

## Epic 9 — Segurança e Conformidade

> Garantir segurança de dados e conformidade com LGPD.

### TECH-026: Implementar validação e normalização de dados

- **Tipo**: Technical Story
- **Descrição**: Validar e normalizar dados de entrada (telefone, CNPJ, e-mail, UF).
- **Critérios de Aceitação**:
  - [ ] Telefone: validar formato, normalizar para E.164 (apenas dígitos)
  - [ ] CNPJ: normalizar para 14 dígitos, remover pontuação
  - [ ] E-mail: validar formato, armazenar lowercase
  - [ ] UF: validar 2 letras, uppercase
  - [ ] Funções utilitárias reutilizáveis
- **Dependências**: Nenhuma
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-027: Garantir HTTPS em todas as comunicações

- **Tipo**: Technical Story
- **Descrição**: Configurar TLS/HTTPS para todos os endpoints expostos.
- **Critérios de Aceitação**:
  - [ ] Endpoint de webhook acessível apenas via HTTPS
  - [ ] Certificado válido configurado
  - [ ] Redirecionamento HTTP → HTTPS
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-028: Implementar audit trail para operações sensíveis

- **Tipo**: Technical Story
- **Descrição**: Registrar log de auditoria para criação/atualização de dados e chamadas a APIs externas.
- **Critérios de Aceitação**:
  - [ ] Log de criação/atualização de leads, orçamentos, empresas
  - [ ] Log de chamadas ao CRM (sem expor payloads sensíveis)
  - [ ] Logs retidos por período configurável
  - [ ] Logs consultáveis para investigação
- **Dependências**: TECH-004
- **Prioridade**: Média
- **Fase**: Fase 2

---

## Epic 10 — Tratamento de Erros e Resiliência

> Garantir robustez em cenários de falha.

### TECH-029: Implementar retry com backoff para integrações

- **Tipo**: Technical Story
- **Descrição**: Aplicar retry com backoff exponencial em chamadas a APIs externas.
- **Critérios de Aceitação**:
  - [ ] Retry em falhas temporárias (5xx, timeout, connection error)
  - [ ] Máximo de 3 tentativas com backoff exponencial
  - [ ] Não retry em erros de cliente (4xx exceto 429)
  - [ ] Log de cada tentativa
- **Dependências**: TECH-015
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-030: Implementar fallback para falhas de CRM

- **Tipo**: Technical Story
- **Descrição**: Continuar atendimento mesmo se CRM estiver indisponível, persistindo dados localmente para sincronização posterior.
- **Critérios de Aceitação**:
  - [ ] Se criação de oportunidade falhar após retries, dados salvos localmente
  - [ ] Flag indicando "pendente de sincronização"
  - [ ] Job/processo para reprocessar pendências
  - [ ] Alerta gerado para operação
- **Dependências**: TECH-029, TECH-013
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-031: Implementar política de retenção de dados e LGPD

- **Tipo**: Technical Story
- **Descrição**: Implementar política de retenção de dados conforme decisão D6 do PRD, incluindo remoção de áudio, anonimização de transcrições e atendimento a direitos do titular (LGPD).
- **Critérios de Aceitação**:
  - [ ] Job agendado para remover arquivos de áudio após 90 dias
  - [ ] Job agendado para anonimizar transcrições após 90 dias (remover identificadores diretos)
  - [ ] Job agendado para anonimizar dados de lead após 1 ano de inatividade
  - [ ] Processo para atender solicitações de acesso (fornecer cópia dos dados pessoais)
  - [ ] Processo para atender solicitações de correção (atualizar dados incorretos)
  - [ ] Processo para atender solicitações de exclusão (remover dados quando solicitado, respeitando obrigações legais)
  - [ ] Processo para atender solicitações de portabilidade (exportar dados em formato interoperável)
  - [ ] Trilha de auditoria de todas as solicitações e ações realizadas
  - [ ] Logs de acesso e modificação de dados pessoais
- **Dependências**: TECH-002, TECH-007, TECH-012
- **Prioridade**: Média
- **Fase**: Fase 2

---

### TECH-032: Implementar configuração de horário de atendimento e lógica de retomada

- **Tipo**: Technical Story
- **Descrição**: Implementar sistema de configuração de horário de atendimento e lógica de retomada do agente após intervenção humana, conforme decisão D7 do PRD.
- **Critérios de Aceitação**:
  - [ ] Arquivo de configuração de horário de atendimento (ex.: `config/horario_atendimento.yaml` ou `.env`) com:
    - Fuso horário configurável (ex.: `America/Sao_Paulo`)
    - Dias da semana com atendimento (ex.: segunda a sexta)
    - Horários de início/fim por dia (ex.: 08:00-18:00)
  - [ ] Função para verificar se está dentro do horário de atendimento
  - [ ] Processamento de comandos do SDR (`/retomar`, `/continuar`) dentro do horário
  - [ ] Retomada automática quando fora do horário e lead enviar nova mensagem
  - [ ] Comandos processados pelo sistema e não aparecem como mensagem visível ao lead
  - [ ] Logs de pausa/retomada com indicação de horário de atendimento
- **Dependências**: TECH-001, TECH-022
- **Prioridade**: Alta
- **Fase**: MVP

---

---

## Resumo por Fase

### MVP (Fase 1) — 24 stories

| Epic | Stories |
|------|---------|
| Epic 1 — Infraestrutura | TECH-001, TECH-002, TECH-003, TECH-004 |
| Epic 2 — Ingestão WhatsApp | TECH-005, TECH-006 |
| Epic 3 — Agente Conversacional | US-001, US-002, US-003, US-004, US-005, TECH-008, TECH-009, TECH-010 |
| Epic 4 — Classificação | US-006, TECH-011 |
| Epic 5 — Persistência | TECH-012, TECH-013 |
| Epic 6 — CRM | TECH-015, TECH-016, TECH-020, TECH-021, US-007 |
| Epic 7 — Chatwoot | TECH-022, US-008, US-009, TECH-032 |
| Epic 9 — Segurança | TECH-026, TECH-027 |
| Epic 10 — Resiliência | TECH-029 |

### Fase 2 — 12 stories

| Epic | Stories |
|------|---------|
| Epic 2 — Ingestão WhatsApp | TECH-007 |
| Epic 5 — Persistência | TECH-014 |
| Epic 6 — CRM | TECH-017, TECH-018, TECH-019 |
| Epic 8 — Observabilidade | TECH-023, TECH-024, TECH-025 |
| Epic 9 — Segurança | TECH-028, TECH-031 |
| Epic 10 — Resiliência | TECH-030 |

---

## Matriz de Dependências (simplificada)

```
TECH-001 (setup)
    ├── TECH-002 (schema)
    │       └── TECH-012, TECH-013, TECH-014, TECH-008
    ├── TECH-003 (segredos)
    │       └── TECH-015 (Piperun client)
    │               └── TECH-016, TECH-017, TECH-018, TECH-019, TECH-020, TECH-021
    ├── TECH-004 (logs)
    │       └── TECH-005 (webhook)
    │               └── TECH-006, TECH-007
    ├── TECH-009 (knowledge base)
    ├── TECH-010 (prompt)
    │       └── TECH-011 (temperatura)
    └── TECH-022 (Chatwoot)
            └── US-008, US-009, TECH-032
                    └── (US-008 também depende de TECH-032 para retomada)

US-001 → US-002 → US-003 → US-004, US-005
US-002 + TECH-011 → US-006
TECH-020 + TECH-021 + TECH-013 → US-007
```

---

## Decisões Pendentes (do PRD)

As stories a seguir podem precisar de refinamento após decisões:

| Decisão | Stories Impactadas |
|---------|-------------------|
| D3 — Regras de score | TECH-011, US-006 |
| D4 — Pipeline/Stage IDs | TECH-020, US-007 |

---

*Backlog gerado em 2026-01-03 com base no PRD v1.0*

