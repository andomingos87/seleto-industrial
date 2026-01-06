# Documentação de Testes — Seleto Industrial SDR Agent

> Documentação completa e estruturada da suíte de testes do projeto  
> Última atualização: 2026-01-06

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Testes](#estrutura-de-testes)
3. [Configuração e Execução](#configuração-e-execução)
4. [Testes por Categoria](#testes-por-categoria)
   - [Testes de API](#testes-de-api)
   - [Testes de Serviços](#testes-de-serviços)
   - [Testes de Agentes](#testes-de-agentes)
   - [Testes de Utilitários](#testes-de-utilitários)
   - [Testes de Integração](#testes-de-integração)
5. [Cobertura e Métricas](#cobertura-e-métricas)
6. [Problemas Conhecidos](#problemas-conhecidos)
7. [Boas Práticas](#boas-práticas)

---

## Visão Geral

O projeto possui uma suíte abrangente de testes automatizados cobrindo:

- **888+ testes passando** (última execução)
- **8-12 testes pulados** (requerem servidor para testes de integração)
- **0 testes falhando** (testes de integração são pulados se servidor não disponível)
- **21 warnings** (deprecations de dependências)

### Estatísticas

- **Total de arquivos de teste**: 35
- **Categorias principais**: API, Serviços, Agentes, Utilitários, Integração
- **Frameworks**: pytest, pytest-asyncio, pytest-cov
- **Cobertura**: Configurada via `pyproject.toml`
- **Markers registrados**: `integration` (para testes que requerem servidor)

---

## Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                    # Configuração e fixtures compartilhadas
├── test_integration_flow.py       # Testes de integração end-to-end
│
├── api/                           # Testes de endpoints da API
│   ├── test_health.py
│   ├── test_chatwoot_webhook.py
│   └── middleware/
│       └── test_security.py
│
├── services/                      # Testes de serviços de negócio
│   ├── test_lead_crud.py
│   ├── test_orcamento_crud.py
│   ├── test_empresa_crud.py
│   ├── test_whatsapp.py
│   ├── test_chatwoot_sync.py
│   ├── test_piperun_client.py
│   ├── test_piperun_sync.py
│   ├── test_conversation_persistence.py
│   ├── test_agent_pause.py
│   ├── test_business_hours.py
│   ├── test_handoff_summary.py
│   ├── test_knowledge_base.py
│   ├── test_temperature_classification.py
│   ├── test_upsell.py
│   ├── test_unavailable_products.py
│   ├── test_prompt_loader.py
│   ├── test_metrics.py
│   ├── test_alerts.py
│   ├── test_audit_trail.py
│   ├── test_audit_trail_integration.py
│   ├── test_lgpd.py
│   └── test_fallback.py
│
├── agents/                        # Testes do SDR Agent
│   ├── test_sdr_agent.py
│   ├── test_sdr_agent_prompt.py
│   ├── test_sdr_agent_history.py
│   ├── test_sdr_agent_knowledge.py
│   ├── test_sdr_agent_temperature.py
│   ├── test_sdr_agent_upsell.py
│   └── test_sdr_agent_unavailable.py
│
└── utils/                         # Testes de utilitários
    ├── test_retry.py
    └── test_validators.py
```

---

## Configuração e Execução

### Pré-requisitos

```bash
# Ativar ambiente virtual
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências de desenvolvimento
pip install -r requirements.txt
```

### Comandos Básicos

```bash
# Executar todos os testes
pytest tests/ -v

# Executar com output detalhado
pytest tests/ -v -s

# Executar com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Executar apenas testes de uma categoria
pytest tests/api/ -v
pytest tests/services/ -v
pytest tests/agents/ -v

# Executar um arquivo específico
pytest tests/api/test_health.py -v

# Executar um teste específico
pytest tests/api/test_health.py::test_health_returns_200 -v

# Executar testes marcados
pytest tests/ -v -m integration
```

### Configuração do pytest

Definida em `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "-v --tb=short"
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
]
```

### Fixtures Compartilhadas

O arquivo `conftest.py` fornece fixtures reutilizáveis:

- `client`: Cliente de teste FastAPI (`TestClient`)

---

## Testes por Categoria

### Testes de API

#### `tests/api/test_health.py`

Testa o endpoint `/api/health`:

- ✅ `test_health_returns_200` — Verifica status HTTP 200
- ✅ `test_health_response_structure` — Valida estrutura JSON da resposta
- ✅ `test_health_content_type` — Verifica Content-Type correto

**Cobertura**: Endpoint de health check básico

#### `tests/api/test_chatwoot_webhook.py`

Testa o webhook do Chatwoot para intervenção de SDR:

- ✅ `TestIsSdrMessage` — Detecta mensagens de SDR
- ✅ `TestExtractPhoneFromPayload` — Extrai telefone do payload
- ✅ `TestChatwootWebhookEndpoint` — Processa webhook do Chatwoot
- ✅ `TestProcessChatwootMessage` — Processa mensagem do SDR
- ✅ `TestPayloadParsing` — Parsing de diferentes formatos de payload

**Cobertura**: Integração com Chatwoot, pausa/resumo do agente

#### `tests/api/middleware/test_security.py`

Testa middleware de segurança:

- ✅ `TestSecurityHeadersMiddleware` — Headers de segurança (CSP, X-Frame-Options, etc.)
- ✅ `TestSecurityHeadersIntegration` — Integração com FastAPI
- ✅ `TestCSPDirectives` — Content Security Policy

**Cobertura**: Segurança HTTP, proteção contra XSS

---

### Testes de Serviços

#### CRUD Operations

##### `tests/services/test_lead_crud.py`

Testa operações CRUD de leads:

- ✅ `TestUpsertLead` — Criação e atualização idempotente por telefone
- ✅ `TestGetLeadByPhone` — Busca por telefone normalizado
- ✅ `TestLeadNormalization` — Normalização de telefone (E.164)
- ✅ `TestLeadErrorHandling` — Tratamento de erros
- ✅ `TestLeadIntegration` — Testes de integração (requer Supabase)

**Cobertura**: Persistência de leads, normalização, idempotência

##### `tests/services/test_orcamento_crud.py`

Testa operações CRUD de orçamentos:

- ✅ `TestCreateOrcamento` — Criação de orçamento com validação de lead FK
- ✅ `TestGetOrcamentosByLead` — Busca de orçamentos por lead
- ✅ `TestUpdateOrcamento` — Atualização de orçamento
- ✅ `TestOrcamentoErrorHandling` — Tratamento de erros
- ✅ `TestOrcamentoIntegration` — Testes de integração

**Cobertura**: Persistência de orçamentos, relacionamento com leads

##### `tests/services/test_empresa_crud.py`

Testa operações CRUD de empresas:

- ✅ `TestCreateEmpresa` — Criação de empresa
- ✅ `TestGetEmpresaByCnpj` — Busca por CNPJ normalizado
- ✅ `TestUpdateEmpresa` — Atualização de empresa
- ✅ `TestEmpresaDeduplication` — Deduplicação por CNPJ
- ✅ `TestEmpresaNormalization` — Normalização de CNPJ (14 dígitos)
- ✅ `TestEmpresaErrorHandling` — Tratamento de erros
- ✅ `TestEmpresaIntegration` — Testes de integração

**Cobertura**: Persistência de empresas, deduplicação, normalização de CNPJ

#### Integrações Externas

##### `tests/services/test_whatsapp.py`

Testa serviço de WhatsApp (Z-API):

- ✅ `TestWhatsAppService` — Envio de mensagens, retry, tratamento de erros

**Cobertura**: Integração com Z-API, envio de mensagens

##### `tests/services/test_chatwoot_sync.py`

Testa sincronização com Chatwoot:

- ✅ `TestCreateChatwootConversation` — Criação de conversa
- ✅ `TestSyncMessageToChatwoot` — Sincronização de mensagens
- ✅ `TestGetChatwootConversationId` — Busca de ID de conversa
- ✅ `TestGetOrCreateChatwootContact` — Criação/busca de contato
- ✅ `TestSendInternalMessage` — Envio de mensagem interna
- ✅ `TestSyncMessageAsync` — Sincronização assíncrona
- ✅ `TestRetryConfiguration` — Configuração de retry

**Cobertura**: Integração bidirecional com Chatwoot

##### `tests/services/test_piperun_client.py`

Testa cliente do Piperun CRM:

- ✅ `TestPiperunClientConfiguration` — Configuração do cliente
- ✅ `TestPiperunClientRequests` — Requisições HTTP
- ✅ `TestGetCityId` — Busca de ID de cidade
- ✅ `TestGetCompanyByCnpj` — Busca de empresa por CNPJ
- ✅ `TestCreateCompany` — Criação de empresa
- ✅ `TestCreatePerson` — Criação de pessoa
- ✅ `TestCreateDeal` — Criação de oportunidade
- ✅ `TestCreateNote` — Criação de nota
- ✅ `TestGenerateNoteTemplate` — Template de nota
- ✅ `TestCacheHelpers` — Helpers de cache
- ✅ `TestErrorClasses` — Classes de erro

**Cobertura**: Cliente HTTP do Piperun, operações CRUD

##### `tests/services/test_piperun_sync.py`

Testa sincronização com Piperun:

- ✅ `TestBuildDealTitle` — Construção de título de oportunidade
- ✅ `TestExtractDddFromPhone` — Extração de DDD
- ✅ `TestGetNextStep` — Próximo passo no pipeline
- ✅ `TestShouldSyncToPiperun` — Decisão de sincronização
- ✅ `TestSyncLeadToPiperun` — Sincronização completa de lead

**Cobertura**: Lógica de sincronização, regras de negócio

#### Persistência e Memória

##### `tests/services/test_conversation_persistence.py`

Testa persistência de conversas no Supabase:

- ✅ `TestGetSupabaseClient` — Cliente Supabase
- ✅ `TestSaveMessageToSupabase` — Salvamento de mensagens
- ✅ `TestGetMessagesFromSupabase` — Recuperação de mensagens
- ✅ `TestSaveContextToSupabase` — Salvamento de contexto
- ✅ `TestGetContextFromSupabase` — Recuperação de contexto

**Cobertura**: Persistência de histórico de conversas

#### Funcionalidades de Negócio

##### `tests/services/test_agent_pause.py`

Testa pausa/resumo do agente:

- ✅ `TestIsAgentPaused` — Verificação de estado pausado
- ✅ `TestPauseAgent` — Pausar agente
- ✅ `TestResumeAgent` — Retomar agente
- ✅ `TestCheckAutoResume` — Verificação de retomada automática
- ✅ `TestTryAutoResume` — Tentativa de retomada
- ✅ `TestIsResumeCommand` — Detecção de comando `/retomar`
- ✅ `TestProcessSdrCommand` — Processamento de comandos SDR
- ✅ `TestClearCache` — Limpeza de cache
- ✅ `TestLoadPauseStatesFromSupabase` — Carregamento de estados
- ✅ `TestGetPauseInfo` — Informações de pausa
- ✅ `TestResumeCommands` — Comandos de retomada

**Cobertura**: Controle de pausa/resumo, sincronização com Supabase

##### `tests/services/test_business_hours.py`

Testa configuração de horário comercial:

- ✅ `TestParseTime` — Parsing de horários
- ✅ `TestGetTimezone` — Timezone (America/Sao_Paulo)
- ✅ `TestGetScheduleForDay` — Horário por dia da semana
- ✅ `TestIsBusinessHours` — Verificação de horário comercial
- ✅ `TestShouldAutoResume` — Decisão de retomada automática
- ✅ `TestGetCurrentScheduleStatus` — Status atual
- ✅ `TestReloadConfig` — Recarregamento de configuração
- ✅ `TestEnvOverrides` — Overrides via variáveis de ambiente
- ✅ `TestDayNames` — Nomes de dias (português)

**Cobertura**: Horário comercial, retomada automática

##### `tests/services/test_handoff_summary.py`

Testa resumo de handoff para leads quentes:

- ✅ `TestGetFieldValue` — Extração de valores de campos
- ✅ `TestGenerateHandoffSummary` — Geração de resumo estruturado
- ✅ `TestIsHandoffSummarySent` — Verificação de envio
- ✅ `TestMarkHandoffSummarySent` — Marcação de envio
- ✅ `TestSendHandoffSummary` — Envio para Chatwoot
- ✅ `TestTriggerHandoffOnHotLead` — Trigger em lead quente
- ✅ `TestClearHandoffSummaryFlag` — Limpeza de flag
- ✅ `TestDuplicatePrevention` — Prevenção de duplicatas
- ✅ `TestErrorHandling` — Tratamento de erros

**Cobertura**: Resumo de handoff, integração com Chatwoot

##### `tests/services/test_knowledge_base.py`

Testa base de conhecimento:

- ✅ `TestKnowledgeBaseLoading` — Carregamento de conhecimento
- ✅ `TestCommercialGuardrails` — Guardrails comerciais
- ✅ `TestTechnicalQueryDetection` — Detecção de perguntas técnicas
- ✅ `TestTechnicalQuestionRegistration` — Registro de perguntas técnicas
- ✅ `TestEquipmentQueryDetection` — Detecção de consultas de equipamentos
- ✅ `TestKnowledgeBaseSearch` — Busca na base de conhecimento
- ✅ `TestGetEquipmentResponse` — Resposta sobre equipamentos
- ✅ `TestConvenienceFunctions` — Funções de conveniência
- ✅ `TestSpecificEquipmentQueries` — Consultas específicas

**Cobertura**: Base de conhecimento, guardrails, escalação técnica

##### `tests/services/test_temperature_classification.py`

Testa classificação de temperatura de leads:

- ✅ `TestLoadTemperaturePrompt` — Carregamento de prompt
- ✅ `TestCalculateEngagementScore` — Cálculo de engajamento
- ✅ `TestCalculateCompletenessScore` — Cálculo de completude
- ✅ `TestParseLLMResponse` — Parsing de resposta do LLM
- ✅ `TestFallbackClassification` — Classificação de fallback
- ✅ `TestShouldClassifyLead` — Decisão de classificação
- ✅ `TestCalculateTemperature` — Cálculo de temperatura
- ✅ `TestUpdateLeadTemperature` — Atualização de temperatura
- ✅ `TestClassifyLead` — Classificação completa
- ✅ `TestConstants` — Constantes de classificação

**Cobertura**: Classificação de leads (quente, morno, frio)

##### `tests/services/test_upsell.py`

Testa detecção e sugestão de upsell:

- ✅ `TestDetectFBM100Interest` — Detecção de interesse em FBM100
- ✅ `TestHasProductionContext` — Verificação de contexto de produção
- ✅ `TestGenerateFB300Suggestion` — Geração de sugestão FB300
- ✅ `TestUpsellSuggestionTracking` — Rastreamento de sugestões
- ✅ `TestShouldSuggestUpsell` — Decisão de sugerir upsell
- ✅ `TestGetUpsellContextForAgent` — Contexto para agente
- ✅ `TestEdgeCases` — Casos extremos

**Cobertura**: Upsell, sugestão de produtos complementares

##### `tests/services/test_unavailable_products.py`

Testa produtos indisponíveis (espeto):

- ✅ `TestDetectEspetoInterest` — Detecção de interesse em espeto
- ✅ `TestShouldSuggestCT200` — Sugestão de CT200 como alternativa
- ✅ `TestGetUnavailableProductMessage` — Mensagem de produto indisponível
- ✅ `TestGetCT200SuggestionMessage` — Mensagem de sugestão CT200
- ✅ `TestProductInterestRegistration` — Registro de interesse
- ✅ `TestGetEspetoContextForAgent` — Contexto para agente
- ✅ `TestEdgeCases` — Casos extremos

**Cobertura**: Produtos indisponíveis, sugestão de alternativas

##### `tests/services/test_prompt_loader.py`

Testa carregamento de prompts do sistema:

- ✅ `TestGetSystemPromptPath` — Caminho do prompt
- ✅ `TestValidatePromptPath` — Validação de caminho
- ✅ `TestLoadSystemPromptFromXml` — Carregamento de XML
- ✅ `TestPromptContentQuality` — Qualidade do conteúdo
- ✅ `TestPromptLoaderCaching` — Cache de prompts

**Cobertura**: Carregamento seguro de prompts, validação de caminhos

#### Observabilidade

##### `tests/services/test_metrics.py`

Testa métricas Prometheus:

- ✅ `TestMetricCreation` — Criação de métricas
- ✅ `TestHTTPRequestMetrics` — Métricas de requisições HTTP
- ✅ `TestIntegrationMetrics` — Métricas de integrações
- ✅ `TestMetricLabels` — Labels de métricas
- ✅ `TestErrorRateCalculation` — Cálculo de taxa de erro
- ✅ `TestPrometheusOutput` — Formato Prometheus
- ✅ `TestMetricsPerformance` — Performance de métricas

**Cobertura**: Métricas Prometheus, observabilidade

##### `tests/services/test_alerts.py`

Testa sistema de alertas:

- ✅ `TestErrorRateDetection` — Detecção de taxa de erro > 10%
- ✅ `TestLatencyDetection` — Detecção de latência P95 > 10s
- ✅ `TestAuthFailureDetection` — Detecção de falhas de autenticação
- ✅ `TestAlertDebounce` — Debounce de alertas
- ✅ `TestNotificationSending` — Envio de notificações (Slack, email, webhook)
- ✅ `TestAlertScheduling` — Agendamento de alertas
- ✅ `TestAlertStateManagement` — Gerenciamento de estado
- ✅ `TestAlertErrorHandling` — Tratamento de erros

**Cobertura**: Sistema de alertas, notificações

#### Segurança e Conformidade

##### `tests/services/test_audit_trail.py`

Testa trilha de auditoria:

- ✅ `TestMaskPhone` — Mascaramento de telefone
- ✅ `TestMaskEmail` — Mascaramento de email
- ✅ `TestMaskCnpj` — Mascaramento de CNPJ
- ✅ `TestMaskSensitiveData` — Mascaramento de dados sensíveis
- ✅ `TestComputeChanges` — Cálculo de diferenças (before/after)
- ✅ `TestLogAuditSync` — Logging de auditoria
- ✅ `TestLogEntityCreateSync` — Log de criação
- ✅ `TestLogEntityUpdateSync` — Log de atualização
- ✅ `TestLogApiCallSync` — Log de chamadas de API
- ✅ `TestAuditActionEnum` — Enum de ações
- ✅ `TestEntityTypeEnum` — Enum de tipos de entidade

**Cobertura**: Trilha de auditoria, mascaramento de PII

##### `tests/services/test_audit_trail_integration.py`

Testa integração de auditoria com Supabase:

- ✅ `TestAuditTrailIntegration` — Integração síncrona
- ✅ `TestAuditTrailAsyncIntegration` — Integração assíncrona

**Cobertura**: Persistência de logs de auditoria

##### `tests/services/test_lgpd.py`

Testa conformidade LGPD:

- ✅ `TestAnonymizeText` — Anonimização de texto
- ✅ `TestAnonymizePhone` — Anonimização de telefone
- ✅ `TestAnonymizeContextData` — Anonimização de contexto
- ✅ `TestRetentionCutoffs` — Cortes de retenção
- ✅ `TestAnonymizeExpiredMessages` — Anonimização de mensagens expiradas
- ✅ `TestAnonymizeExpiredContext` — Anonimização de contexto expirado
- ✅ `TestAnonymizeInactiveLeads` — Anonimização de leads inativos
- ✅ `TestCleanupCompletedOperations` — Limpeza de operações concluídas
- ✅ `TestRunAllRetentionJobs` — Execução de jobs de retenção
- ✅ `TestDataRetentionSettings` — Configurações de retenção
- ✅ `TestAnonymizationIrreversibility` — Irreversibilidade da anonimização

**Cobertura**: LGPD, anonimização, retenção de dados

##### `tests/services/test_fallback.py`

Testa operações pendentes (fallback):

- ✅ `TestPendingOperationsCRUD` — CRUD de operações pendentes
- ✅ `TestGetOperationsCount` — Contagem de operações
- ✅ `TestMarkOperationCompleted` — Marcação de conclusão
- ✅ `TestResetFailedOperation` — Reset de operação falha
- ✅ `TestGetFailedOperations` — Busca de operações falhas
- ✅ `TestDeleteCompletedOperations` — Exclusão de operações concluídas
- ✅ `TestOperationEnums` — Enums de operações

**Cobertura**: Operações pendentes, resiliência

---

### Testes de Agentes

#### `tests/agents/test_sdr_agent.py`

Testa criação do SDR Agent:

- ✅ `TestCreateSdrAgentApiKey` — Validação de API key do OpenAI

**Cobertura**: Inicialização do agente, configuração

#### `tests/agents/test_sdr_agent_prompt.py`

Testa carregamento de prompts:

- ✅ `TestSystemPromptLoading` — Carregamento de prompt do sistema
- ✅ `TestAgentCreation` — Criação do agente com prompt
- ✅ `TestPromptReloadAfterRestart` — Recarregamento após restart
- ✅ `TestPromptLoadingErrors` — Tratamento de erros
- ✅ `TestPromptFileIntegrity` — Integridade do arquivo de prompt

**Cobertura**: Prompts do sistema, validação

#### `tests/agents/test_sdr_agent_history.py`

Testa histórico de conversas:

- ✅ `TestConversationHistoryIntegration` — Integração com histórico do Supabase

**Cobertura**: Carregamento de histórico, contexto de conversa

#### `tests/agents/test_sdr_agent_knowledge.py`

Testa integração com base de conhecimento:

- ✅ `TestSDRAgentCommercialGuardrails` — Guardrails comerciais
- ✅ `TestSDRAgentTechnicalEscalation` — Escalação técnica
- ✅ `TestSDRAgentKnowledgeInjection` — Injeção de conhecimento
- ✅ `TestSDRAgentEquipmentResponses` — Respostas sobre equipamentos
- ✅ `TestGuardrailsPriority` — Prioridade de guardrails
- ✅ `TestMessageHistory` — Histórico de mensagens

**Cobertura**: Base de conhecimento, guardrails, escalação

#### `tests/agents/test_sdr_agent_temperature.py`

Testa classificação de temperatura:

- ✅ `TestTemperatureClassificationIntegration` — Integração com classificação
- ✅ `TestTemperatureClassificationWithConversationHistory` — Classificação com histórico
- ✅ `TestTemperatureClassificationScenarios` — Cenários de classificação
- ✅ `TestTemperaturePersistence` — Persistência de temperatura

**Cobertura**: Classificação de leads, integração com agente

#### `tests/agents/test_sdr_agent_upsell.py`

Testa detecção de upsell:

- ✅ `TestSDRAgentUpsellDetection` — Detecção de oportunidade de upsell
- ✅ `TestSDRAgentUpsellRepetition` — Prevenção de repetição
- ✅ `TestSDRAgentUpsellIntegration` — Integração com agente
- ✅ `TestUpsellContextContent` — Conteúdo do contexto
- ✅ `TestUpsellFlowIntegrity` — Integridade do fluxo
- ✅ `TestUpsellLogging` — Logging de upsell

**Cobertura**: Upsell, sugestão de produtos

#### `tests/agents/test_sdr_agent_unavailable.py`

Testa produtos indisponíveis:

- ✅ `TestSDRAgentEspetoDetection` — Detecção de interesse em espeto
- ✅ `TestSDRAgentCT200Suggestion` — Sugestão de CT200
- ✅ `TestSDRAgentInterestRegistration` — Registro de interesse
- ✅ `TestSDRAgentUnavailableIntegration` — Integração completa
- ✅ `TestSDRAgentUnavailableContextContent` — Conteúdo do contexto
- ✅ `TestSDRAgentUnavailableFlowIntegrity` — Integridade do fluxo
- ✅ `TestSDRAgentUnavailableLogging` — Logging
- ✅ `TestSDRAgentUnavailableWithUpsell` — Integração com upsell

**Cobertura**: Produtos indisponíveis, alternativas

---

### Testes de Utilitários

#### `tests/utils/test_validators.py`

Testa validação e normalização:

- ✅ `TestValidationError` — Erros de validação
- ✅ `TestNormalizePhone` — Normalização de telefone
- ✅ `TestValidatePhone` — Validação de telefone
- ✅ `TestValidatePhoneStrict` — Validação estrita
- ✅ `TestValidatePhoneOrRaise` — Validação com exceção
- ✅ `TestNormalizeCnpj` — Normalização de CNPJ
- ✅ `TestValidateCnpj` — Validação de CNPJ
- ✅ `TestValidateCnpjOrRaise` — Validação com exceção
- ✅ `TestValidateEmail` — Validação de email
- ✅ `TestNormalizeEmail` — Normalização de email
- ✅ `TestValidateEmailOrRaise` — Validação com exceção
- ✅ `TestValidUfs` — UFs válidas
- ✅ `TestValidateUf` — Validação de UF
- ✅ `TestValidateUfStrict` — Validação estrita
- ✅ `TestValidateUfOrRaise` — Validação com exceção
- ✅ `TestNormalizeUf` — Normalização de UF
- ✅ `TestValidDdds` — DDDs válidos
- ✅ `TestValidationIntegration` — Integração de validações
- ✅ `TestEdgeCases` — Casos extremos
- ✅ `TestCnpjCheckDigits` — Dígitos verificadores de CNPJ

**Cobertura**: Validação e normalização de dados

#### `tests/utils/test_retry.py`

Testa lógica de retry:

- ✅ `TestRetryConfig` — Configuração de retry
- ✅ `TestIsRetryableError` — Identificação de erros retryáveis
- ✅ `TestRetryableHTTPError` — Erros HTTP retryáveis
- ✅ `TestCheckResponseForRetry` — Verificação de resposta
- ✅ `TestGetRetryAfterOrBackoff` — Cálculo de backoff
- ✅ `TestSyncRetryDecorator` — Decorator síncrono
- ✅ `TestAsyncRetryDecorator` — Decorator assíncrono
- ✅ `TestRetryLogging` — Logging de retries
- ✅ `TestRateLimitHandling` — Tratamento de rate limit

**Cobertura**: Retry, backoff exponencial, rate limiting

---

### Testes de Integração

#### `tests/test_integration_flow.py`

Testa fluxo completo de integração:

**Testes de Integração (requerem servidor):**
- ✅ `test_server_connectivity` — Verifica conectividade com servidor
- ✅ `test_health_endpoint` — Endpoint de health check
- ✅ `test_webhook_text_message` — Webhook de texto
- ✅ `test_full_conversation_flow` — Fluxo completo de conversa

**Testes Locais (não requerem servidor):**
- ✅ `test_data_extraction_progressive` — Extração progressiva de dados
- ✅ `test_phone_normalization` — Normalização de telefone
- ✅ `test_phone_validation` — Validação de telefone
- ✅ `test_conversation_memory` — Memória de conversa

**Configuração:**

| Variável de Ambiente | Descrição | Padrão |
|---------------------|-----------|--------|
| `INTEGRATION_TEST_URL` | URL base do servidor | `http://localhost:8000` |
| `INTEGRATION_TEST_TIMEOUT` | Timeout em segundos | `30.0` |

**Comportamento:**
- Testes de integração verificam conectividade antes de executar
- Se servidor não acessível, testes são **pulados** (não falham)
- Mensagem de skip inclui instruções de configuração
- Suporte para servidor local ou remoto

**Execução:**

```bash
# Com servidor local (recomendado)
uvicorn src.main:app --reload  # Terminal 1
pytest tests/test_integration_flow.py -v  # Terminal 2

# Com servidor remoto
INTEGRATION_TEST_URL=https://seu-servidor.com pytest tests/test_integration_flow.py -v

# Apenas testes locais (sem servidor)
pytest tests/test_integration_flow.py -v -m "not integration"

# Aumentar timeout
INTEGRATION_TEST_TIMEOUT=60 pytest tests/test_integration_flow.py -v
```

**Cobertura**: Fluxo end-to-end, integração com servidor real

---

## Cobertura e Métricas

### Executar com Cobertura

```bash
# Cobertura completa
pytest tests/ -v --cov=src --cov-report=html

# Cobertura por módulo
pytest tests/ -v --cov=src --cov-report=term-missing

# Cobertura apenas de serviços
pytest tests/services/ -v --cov=src/services --cov-report=html
```

### Configuração de Cobertura

Definida em `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

### Relatório HTML

Após executar com `--cov-report=html`, abra `htmlcov/index.html` no navegador.

---

## Problemas Conhecidos

### ~~1. Testes de Integração com Timeout~~ ✅ RESOLVIDO

**Arquivo**: `tests/test_integration_flow.py`

**Problema anterior**: Testes falhavam com `httpx.ReadTimeout` quando servidor não acessível.

**Solução implementada** (2026-01-06):
- ✅ Timeout configurável via `INTEGRATION_TEST_TIMEOUT` (padrão: 30s)
- ✅ URL padrão alterado para localhost (`http://localhost:8000`)
- ✅ Detecção automática de conectividade antes dos testes
- ✅ Skip automático com mensagem descritiva quando servidor não acessível
- ✅ Tratamento específico para diferentes tipos de erro (conexão, timeout, HTTP)
- ✅ Marker `@pytest.mark.integration` registrado no pyproject.toml
- ✅ Teste de conectividade `test_server_connectivity` adicionado

**Como executar**:
```bash
# Servidor local (recomendado)
uvicorn src.main:app --reload  # Terminal 1
pytest tests/test_integration_flow.py -v  # Terminal 2

# Servidor remoto
INTEGRATION_TEST_URL=https://seleto-industrial.fly.dev pytest tests/test_integration_flow.py -v
```

### 2. Warnings de Deprecation

**Problema**: 21 warnings de deprecation de dependências:
- `pyiceberg`: `enablePackrat`, `escChar`, `unquoteResults`
- `pydantic`: `@model_validator` com `mode='after'` em classmethod
- `supabase`: `timeout` e `verify` parameters

**Impacto**: Baixo — warnings apenas, não afetam funcionalidade.

**Solução**: Aguardar atualizações das dependências.

### ~~3. Pytest Marks Não Registrados~~ ✅ RESOLVIDO

**Problema anterior**: Warnings sobre `pytest.mark.integration` não registrado.

**Solução implementada** (2026-01-06):

Marker registrado em `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
]
```

**Como usar**:
```bash
# Apenas testes de integração
pytest tests/ -v -m integration

# Excluir testes de integração
pytest tests/ -v -m "not integration"
```

### 4. Erro de Formato de Telefone no Chatwoot

**Problema**: Logs mostram erro ao criar contato no Chatwoot:
```
"Phone number should be in e164 format"
```

**Causa**: Telefone sendo enviado sem prefixo `+` (ex: `5511999999999` em vez de `+5511999999999`).

**Arquivo afetado**: `src/services/chatwoot_sync.py`

**Status**: Requer correção no código (não nos testes).

---

## Boas Práticas

### 1. Estrutura de Testes

- ✅ Usar classes `Test*` para agrupar testes relacionados
- ✅ Nomes descritivos: `test_<ação>_<condição>_<resultado>`
- ✅ Um teste por comportamento/requisito
- ✅ Fixtures compartilhadas em `conftest.py`

### 2. Mocks e Fixtures

- ✅ Mockar dependências externas (Supabase, APIs)
- ✅ Usar fixtures para dados de teste reutilizáveis
- ✅ Limpar estado entre testes (setup/teardown)

### 3. Asserções

- ✅ Asserções claras e específicas
- ✅ Mensagens de erro descritivas
- ✅ Validar comportamento, não implementação

### 4. Testes Assíncronos

- ✅ Usar `@pytest.mark.asyncio` para testes async
- ✅ `asyncio_mode = "auto"` no `pyproject.toml`
- ✅ Usar `httpx.AsyncClient` para testes de API async

### 5. Cobertura

- ✅ Almejar >80% de cobertura
- ✅ Focar em lógica de negócio crítica
- ✅ Testar casos de erro e edge cases

### 6. Organização

- ✅ Um arquivo de teste por módulo
- ✅ Espelhar estrutura de `src/` em `tests/`
- ✅ Agrupar testes relacionados em classes

---

## Próximos Passos

### Melhorias Sugeridas

1. ~~**Corrigir testes de integração**~~ ✅ CONCLUÍDO (2026-01-06)

2. ~~**Registrar pytest marks**~~ ✅ CONCLUÍDO (2026-01-06)

3. **Aumentar cobertura**:
   - Testes de edge cases em validações
   - Testes de erro em integrações
   - Testes de performance

4. **Documentação de testes**:
   - Adicionar docstrings em todos os testes
   - Documentar fixtures customizadas
   - Exemplos de execução por categoria

5. **CI/CD**:
   - Executar testes em PRs
   - Relatório de cobertura automático
   - Alertas em falhas de teste

---

*Documento gerado em 2026-01-06*

