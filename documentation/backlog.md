# Backlog — Agente de IA (SDR) para Seleto Industrial

> Derivado do PRD v1.0 (2026-01-03)

---

## Resumo do Produto

- **Objetivo**: Automatizar atendimento inicial via WhatsApp, qualificar leads e registrar dados no CRM (PipeRun)
- **Público-alvo**: Leads B2B (indústria alimentícia), SDRs, vendedores
- **Stack**: Agno (Python/FastAPI), Supabase, PipeRun, Chatwoot, WhatsApp (provedor)

---

## Epic 1 — Infraestrutura e Setup Inicial

> Preparar ambiente de desenvolvimento, runtime e integrações base.

### TECH-001: Configurar projeto Agno com FastAPI

- **Tipo**: Technical Story
- **Descrição**: Criar estrutura base do projeto com Agno Agent Framework, FastAPI como runtime HTTP, e configuração de ambiente (variáveis, Docker).
- **Critérios de Aceitação**:
  - [ ] Projeto inicializado com estrutura de diretórios padrão (src/, tests/, config/)
  - [ ] Dockerfile funcional para build e execução local
  - [ ] Arquivo `.env.example` com todas as variáveis necessárias (sem valores reais)
  - [ ] Endpoint `/health` retornando status 200
  - [ ] README com instruções de setup local
- **Dependências**: Nenhuma
- **Prioridade**: Alta
- **Fase**: MVP

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
- **Migrations aplicadas**:
  - `20260103152411_add_missing_fields_to_leads`
  - `20260103152423_add_cnpj_unique_constraint_to_empresa`
  - `20260103152432_enable_rls_on_all_tables`

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
- **Artefatos**:
  - `.env.example` — Template com todas as variáveis documentadas
  - `src/config/settings.py` — Carregamento via Pydantic Settings
  - `README.md` — Documentação das variáveis de ambiente

---

### TECH-004: Configurar logging estruturado ✅

- **Tipo**: Technical Story
- **Descrição**: Implementar logging estruturado (JSON) com contexto por requisição (request_id, phone, etapa do fluxo).
- **Critérios de Aceitação**:
  - [x] Logs em formato JSON com campos: timestamp, level, message, request_id, phone (quando disponível)
  - [x] Níveis de log configuráveis via variável de ambiente
  - [x] Logs de entrada/saída de webhooks
  - [x] Logs de chamadas a APIs externas (PipeRun, Supabase)
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP
- **Concluído em**: 2026-01-03
- **Artefatos**:
  - `src/utils/logging.py` — Módulo de logging estruturado com JSONFormatter e TextFormatter
  - `src/api/middleware/logging.py` — Middleware FastAPI para logging de requests
  - Funções utilitárias: `log_webhook_received()`, `log_webhook_response()`, `log_api_call()`

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
- **Artefatos**:
  - `src/api/routes/webhook.py` — Endpoint POST /webhook/whatsapp com parsing e validação
  - `src/utils/validation.py` — Funções de normalização de telefone (normalize_phone, validate_phone)

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
- **Artefatos**:
  - `src/services/whatsapp.py` — Serviço WhatsAppService com retry e backoff exponencial
  - Função `send_whatsapp_message()` para envio de mensagens

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
- **Dependências**: TECH-005
- **Prioridade**: Média
- **Fase**: Fase 2
- **Concluído em**: 2026-01-03
- **Artefatos**:
  - `src/services/transcription.py` — Serviço TranscriptionService com integração Whisper API
  - Função `transcribe_audio()` para transcrição de áudio
  - Suporte a múltiplos formatos de áudio (ogg, mp3, wav, webm, etc.)

---

## Epic 3 — Agente Conversacional (Core)

> Lógica do agente de IA para atendimento e qualificação.

### US-001: Cumprimentar lead e iniciar coleta de dados

- **Tipo**: User Story
- **Descrição**: Como lead, ao enviar a primeira mensagem, quero receber uma saudação cordial e ser perguntado sobre minha necessidade, para que eu me sinta bem atendido.
- **Critérios de Aceitação**:
  - [ ] Agente responde em até 5s após receber mensagem
  - [ ] Mensagem de boas-vindas menciona a Seleto Industrial
  - [ ] Agente pergunta sobre a necessidade/produto de interesse
  - [ ] Tom cordial, profissional e empático (sem jargões robóticos)
  - [ ] Máximo de 2 perguntas diretas na primeira interação
- **Dependências**: TECH-005, TECH-006
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-002: Coletar dados progressivamente durante a conversa

- **Tipo**: User Story
- **Descrição**: Como agente, quero coletar nome, empresa, cidade/UF, produto, volume e urgência ao longo da conversa, sem enviar um questionário de uma vez.
- **Critérios de Aceitação**:
  - [ ] Dados coletados: nome, empresa (opcional), cidade/UF, produto/necessidade, volume/capacidade, urgência
  - [ ] Máximo de 2 perguntas diretas seguidas (regra de ritmo)
  - [ ] Perguntas contextualizadas com base nas respostas anteriores
  - [ ] Dados parciais são persistidos mesmo que conversa não seja concluída
- **Dependências**: US-001, TECH-008
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-003: Responder dúvidas usando base de conhecimento

- **Tipo**: User Story
- **Descrição**: Como lead, quero tirar dúvidas sobre equipamentos da Seleto Industrial, para entender se atendem minha necessidade.
- **Critérios de Aceitação**:
  - [ ] Agente responde perguntas sobre formadoras, cortadoras, linhas automáticas
  - [ ] Respostas baseadas nos arquivos de `prompts/equipamentos/*`
  - [ ] Se dúvida for técnica demais, agente registra e informa que especialista entrará em contato
  - [ ] Agente não promete prazos de entrega, descontos ou orçamento completo
- **Dependências**: TECH-009
- **Prioridade**: Alta
- **Fase**: MVP

---

### US-004: Sugerir upsell de FBM100 para FB300

- **Tipo**: User Story
- **Descrição**: Como agente, quando o lead demonstrar interesse na formadora manual FBM100, quero sugerir também a FB300 (semi-automática) como alternativa.
- **Critérios de Aceitação**:
  - [ ] Quando lead mencionar FBM100, agente apresenta FB300 como opção "acima"
  - [ ] Tom consultivo, sem pressão
  - [ ] Registro da sugestão no contexto da conversa
- **Dependências**: US-003
- **Prioridade**: Média
- **Fase**: MVP

---

### US-005: Tratar interesse em produto indisponível (linha de espetos)

- **Tipo**: User Story
- **Descrição**: Como agente, quando o lead perguntar sobre máquina de espetos (indisponível), quero informar que está em melhoria e oferecer alternativa.
- **Critérios de Aceitação**:
  - [ ] Agente informa que projeto está em melhoria com previsão interna
  - [ ] Agente registra interesse para contato futuro
  - [ ] Agente oferece CT200 (corte em cubos) como alternativa quando fizer sentido
- **Dependências**: US-003
- **Prioridade**: Baixa
- **Fase**: MVP

---

### TECH-008: Implementar memória/histórico de conversa por lead

- **Tipo**: Technical Story
- **Descrição**: Manter histórico de mensagens e contexto coletado por telefone do lead, para continuidade da conversa.
- **Critérios de Aceitação**:
  - [ ] Histórico de mensagens armazenado (Supabase ou memória do Agno)
  - [ ] Contexto coletado (nome, cidade, produto, etc.) persistido e recuperável
  - [ ] Lead identificado por telefone (idempotência)
  - [ ] Histórico disponível para consulta do agente em cada turno
- **Dependências**: TECH-002
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-009: Carregar base de conhecimento de produtos

- **Tipo**: Technical Story
- **Descrição**: Carregar e indexar arquivos de `prompts/equipamentos/*` para uso pelo agente nas respostas.
- **Critérios de Aceitação**:
  - [ ] Arquivos de equipamentos carregados no startup do agente
  - [ ] Busca semântica ou por palavras-chave funcional
  - [ ] Atualização da base requer apenas substituição de arquivos + restart
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-010: Implementar prompt do sistema (sp_agente_v1.xml)

- **Tipo**: Technical Story
- **Descrição**: Configurar o agente com o prompt do sistema definido em `prompts/system_prompt/sp_agente_v1.xml`.
- **Critérios de Aceitação**:
  - [ ] Prompt carregado do arquivo XML
  - [ ] Prompt aplicado em todas as sessões de conversa
  - [ ] Alterações no arquivo refletem após restart
- **Dependências**: TECH-001
- **Prioridade**: Alta
- **Fase**: MVP

---

## Epic 4 — Classificação de Temperatura

> Classificar leads em frio/morno/quente.

### US-006: Classificar lead ao final da qualificação

- **Tipo**: User Story
- **Descrição**: Como SDR, quero que o agente classifique cada lead como frio, morno ou quente, para priorizar meu tempo.
- **Critérios de Aceitação**:
  - [ ] Lead classificado em uma das três temperaturas: frio, morno, quente
  - [ ] Classificação considera: engajamento, completude dos dados, volume, urgência
  - [ ] Classificação persistida no banco (campo `temperature` em `leads`)
  - [ ] Justificativa mínima registrada (ex: "respondeu todas as perguntas, urgência alta")
- **Dependências**: US-002, TECH-011
- **Prioridade**: Alta
- **Fase**: MVP

---

### TECH-011: Implementar lógica de classificação de temperatura

- **Tipo**: Technical Story
- **Descrição**: Criar módulo/função que calcula temperatura do lead com base nos dados coletados, usando prompt `sp_calcula_temperatura.xml`.
- **Critérios de Aceitação**:
  - [ ] Função `calculate_temperature(lead_data) -> (temperature, justification)`
  - [ ] Critérios: engajamento (respondeu perguntas), volume, urgência, fit com portfólio
  - [ ] Prompt de temperatura carregado de `prompts/system_prompt/sp_calcula_temperatura.xml`
  - [ ] Retorno inclui justificativa textual
- **Dependências**: TECH-010
- **Prioridade**: Alta
- **Fase**: MVP

---

## Epic 5 — Persistência Local (Supabase)

> Salvar e recuperar dados de leads, orçamentos e empresas.

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

## Epic 6 — Integração CRM (PipeRun)

> Sincronizar dados com o CRM PipeRun.

### TECH-015: Implementar cliente HTTP para PipeRun

- **Tipo**: Technical Story
- **Descrição**: Criar cliente HTTP reutilizável para chamadas à API do PipeRun, com autenticação e retry.
- **Critérios de Aceitação**:
  - [ ] Classe/módulo `PipeRunClient` com métodos para cada endpoint
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
- **Descrição**: Buscar código da cidade no PipeRun por nome + UF.
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
- **Descrição**: Buscar empresa existente no PipeRun por CNPJ para evitar duplicidade.
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
- **Descrição**: Criar empresa no PipeRun com dados coletados.
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
- **Descrição**: Criar pessoa (contato) no PipeRun.
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
- **Descrição**: Criar oportunidade no PipeRun em pipeline/stage configurados.
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
- **Descrição**: Registrar nota padronizada na oportunidade do PipeRun.
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
- **Descrição**: Enviar mensagens do agente e do lead para o Chatwoot, mantendo histórico visível para SDRs.
- **Critérios de Aceitação**:
  - [ ] Mensagens do lead replicadas no Chatwoot
  - [ ] Mensagens do agente replicadas no Chatwoot
  - [ ] Conversa identificada por telefone do lead
  - [ ] Histórico acessível em tempo real pelo SDR
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
  - [ ] Status de "agente pausado" registrado no contexto da conversa
  - [ ] Log indicando intervenção humana
- **Dependências**: TECH-022
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
  - [ ] Taxa de sucesso/falha por integração (WhatsApp, PipeRun, Supabase)
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

---

## Resumo por Fase

### MVP (Fase 1) — 22 stories

| Epic | Stories |
|------|---------|
| Epic 1 — Infraestrutura | TECH-001, TECH-002, TECH-003, TECH-004 |
| Epic 2 — Ingestão WhatsApp | TECH-005, TECH-006 |
| Epic 3 — Agente Conversacional | US-001, US-002, US-003, US-004, US-005, TECH-008, TECH-009, TECH-010 |
| Epic 4 — Classificação | US-006, TECH-011 |
| Epic 5 — Persistência | TECH-012, TECH-013 |
| Epic 6 — CRM | TECH-015, TECH-016, TECH-020, TECH-021, US-007 |
| Epic 7 — Chatwoot | TECH-022, US-008, US-009 |
| Epic 9 — Segurança | TECH-026, TECH-027 |
| Epic 10 — Resiliência | TECH-029 |

### Fase 2 — 11 stories

| Epic | Stories |
|------|---------|
| Epic 2 — Ingestão WhatsApp | TECH-007 |
| Epic 5 — Persistência | TECH-014 |
| Epic 6 — CRM | TECH-017, TECH-018, TECH-019 |
| Epic 8 — Observabilidade | TECH-023, TECH-024, TECH-025 |
| Epic 9 — Segurança | TECH-028 |
| Epic 10 — Resiliência | TECH-030 |

---

## Matriz de Dependências (simplificada)

```
TECH-001 (setup)
    ├── TECH-002 (schema)
    │       └── TECH-012, TECH-013, TECH-014, TECH-008
    ├── TECH-003 (segredos)
    │       └── TECH-015 (PipeRun client)
    │               └── TECH-016, TECH-017, TECH-018, TECH-019, TECH-020, TECH-021
    ├── TECH-004 (logs)
    │       └── TECH-005 (webhook)
    │               └── TECH-006, TECH-007
    ├── TECH-009 (knowledge base)
    ├── TECH-010 (prompt)
    │       └── TECH-011 (temperatura)
    └── TECH-022 (Chatwoot)
            └── US-008, US-009

US-001 → US-002 → US-003 → US-004, US-005
US-002 + TECH-011 → US-006
TECH-020 + TECH-021 + TECH-013 → US-007
```

---

## Decisões Pendentes (do PRD)

As stories a seguir podem precisar de refinamento após decisões:

| Decisão | Stories Impactadas |
|---------|-------------------|
| D1 — Provedor WhatsApp | TECH-005, TECH-006, TECH-007 |
| D3 — Regras de score | TECH-011, US-006 |
| D4 — Pipeline/Stage IDs | TECH-020, US-007 |
| D7 — Comandos de retomada | US-008 (adicionar story futura) |

---

*Backlog gerado em 2026-01-03 com base no PRD v1.0*

