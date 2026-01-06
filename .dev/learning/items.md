# Tecnologias, Conceitos e Ferramentas - Seleto Industrial SDR Agent

Este documento lista todas as tecnologias, conceitos, ferramentas e aspectos técnicos utilizados no projeto Seleto Industrial SDR Agent.

---

## 1. Linguagens de Programação

### 1.1 Python 3.12
Linguagem de programação principal do projeto. Versão 3.12 oferece melhorias de performance, type hints avançados e suporte moderno a async/await.

### 1.2 SQL (PostgreSQL)
Linguagem de consulta para interação com o banco de dados PostgreSQL através do Supabase.

### 1.3 YAML
Formato de configuração usado para arquivos de configuração como `business_hours.yaml`.

### 1.4 XML
Formato usado para armazenar system prompts do agente em arquivos estruturados.

---

## 2. Frameworks e Bibliotecas Core

### 2.1 FastAPI
Framework web moderno e assíncrono para Python, usado para criar a API REST do sistema. Oferece documentação automática (Swagger/OpenAPI) e alta performance.

### 2.2 Agno Framework
Framework especializado em orquestração de agentes de IA. Usado para criar e gerenciar o agente SDR conversacional.

### 2.3 AgentOS
Sistema operacional para agentes de IA, integrado com FastAPI para expor endpoints automaticamente.

### 2.4 Uvicorn
Servidor ASGI de alta performance usado para executar a aplicação FastAPI em produção.

### 2.5 Pydantic
Biblioteca para validação de dados e configurações usando type hints do Python. Usado em `settings.py` para gerenciar variáveis de ambiente.

### 2.6 Pydantic Settings
Extensão do Pydantic para gerenciamento de configurações a partir de variáveis de ambiente e arquivos `.env`.

---

## 3. Inteligência Artificial e Processamento de Linguagem

### 3.1 OpenAI GPT-4o
Modelo de linguagem grande (LLM) usado como núcleo do agente conversacional. Processa mensagens e gera respostas contextuais.

### 3.2 OpenAI Whisper
Modelo de transcrição de áudio para converter mensagens de voz em texto.

### 3.3 System Prompt
Prompt de sistema que define o comportamento, personalidade e regras do agente. Carregado de arquivo XML.

### 3.4 Conversational AI
Conceito de IA conversacional onde o agente mantém contexto de conversas anteriores para respostas mais naturais.

### 3.5 Temperature Classification
Classificação de leads em categorias de temperatura (quente, morno, frio) baseada em critérios de negócio.

### 3.6 Data Extraction
Extração estruturada de informações de mensagens não estruturadas usando LLM (nome, cidade, produto de interesse, etc.).

---

## 4. Banco de Dados e Persistência

### 4.1 Supabase
Plataforma Backend-as-a-Service (BaaS) baseada em PostgreSQL. Fornece banco de dados gerenciado, API REST automática e recursos de segurança.

### 4.2 PostgreSQL
Banco de dados relacional open-source que é a base do Supabase. Oferece ACID, transações e suporte a JSON.

### 4.3 Row Level Security (RLS)
Recurso de segurança do PostgreSQL que permite políticas granulares de acesso a nível de linha nas tabelas.

### 4.4 Database Migrations
Sistema de versionamento de schema do banco de dados. Migrações são aplicadas via Supabase MCP tools.

### 4.5 Repository Pattern
Padrão de design que abstrai a lógica de acesso a dados. Implementado em serviços de persistência (`lead_persistence.py`, `orcamento_persistence.py`, etc.).

### 4.6 Upsert Operations
Operações de inserção ou atualização condicional (INSERT ... ON CONFLICT). Usado para garantir idempotência em operações de lead.

### 4.7 Foreign Keys
Relacionamentos entre tabelas garantidos por constraints de chave estrangeira (ex: `orcamentos.lead_id` → `leads.id`).

### 4.8 Unique Constraints
Constraints que garantem unicidade de valores (ex: `leads.phone`, `empresas.cnpj`).

---

## 5. Integrações e APIs Externas

### 5.1 Z-API
Provedor de integração com WhatsApp. Fornece API REST para envio/recebimento de mensagens e webhooks para eventos.

### 5.2 WhatsApp Business API
API oficial do WhatsApp para comunicação empresarial. Acessada via Z-API como intermediário.

### 5.3 PipeRun CRM
Sistema de CRM (Customer Relationship Management) usado para gerenciar oportunidades de negócio e leads qualificados.

### 5.4 Chatwoot
Plataforma de atendimento ao cliente que fornece interface visual para SDRs acompanharem e intervirem em conversas.

### 5.5 REST API
Padrão de arquitetura para comunicação entre sistemas via HTTP. Usado em todas as integrações externas.

### 5.6 Webhooks
Mecanismo de notificação push onde serviços externos enviam eventos HTTP para o sistema (ex: Z-API envia mensagens recebidas).

### 5.7 HTTPX
Biblioteca HTTP assíncrona para Python. Usada para fazer requisições HTTP para APIs externas.

### 5.8 API Authentication
Autenticação via tokens (API keys, bearer tokens) para acesso seguro a APIs externas.

---

## 6. Infraestrutura e DevOps

### 6.1 Docker
Tecnologia de containerização usada para empacotar a aplicação e suas dependências em containers isolados.

### 6.2 Dockerfile
Arquivo de configuração que define como construir a imagem Docker da aplicação. Usa multi-stage build para otimização.

### 6.3 Docker Compose
Ferramenta para orquestrar múltiplos containers Docker. Usado para desenvolvimento local.

### 6.4 Multi-stage Build
Técnica de build Docker que usa múltiplos estágios para reduzir o tamanho final da imagem.

### 6.5 Health Checks
Verificações automáticas de saúde do container para detectar quando a aplicação está pronta ou com problemas.

### 6.6 Environment Variables
Variáveis de ambiente para configuração da aplicação sem hardcoding de valores sensíveis.

### 6.7 .env Files
Arquivos de configuração local para desenvolvimento que contêm variáveis de ambiente (não versionados).

### 6.8 Virtual Environment (venv)
Ambiente Python isolado para gerenciar dependências do projeto sem conflitos com o sistema.

---

## 7. Ferramentas de Desenvolvimento

### 7.1 Ruff
Linter e formatter rápido para Python. Substitui ferramentas como flake8, black e isort em uma única ferramenta.

### 7.2 Pytest
Framework de testes para Python. Usado para testes unitários, de integração e de sistema.

### 7.3 Pytest-asyncio
Plugin do pytest para suporte a testes assíncronos.

### 7.4 Pytest-cov
Plugin do pytest para cobertura de código, medindo quantos percentual do código é testado.

### 7.5 Python-dotenv
Biblioteca para carregar variáveis de ambiente de arquivos `.env`.

### 7.6 PyYAML
Biblioteca para parsing e geração de arquivos YAML.

### 7.7 Git
Sistema de controle de versão usado para gerenciar o código-fonte.

---

## 8. Conceitos e Padrões Arquiteturais

### 8.1 Service Layer Pattern
Padrão onde a lógica de negócio é encapsulada em serviços separados da camada de apresentação (API).

### 8.2 Middleware Pattern
Padrão para interceptar e processar requisições HTTP antes que cheguem aos handlers (ex: logging, segurança).

### 8.3 Singleton Pattern
Padrão de design que garante uma única instância de recursos compartilhados (ex: cliente Supabase).

### 8.4 Factory Pattern
Padrão para criar instâncias configuradas de objetos (ex: `create_sdr_agent()`).

### 8.5 Strategy Pattern
Padrão para aplicar diferentes estratégias de processamento baseado em condições (ex: guardrails do knowledge base).

### 8.6 Decorator Pattern
Padrão implementado via decorators Python para adicionar funcionalidades a funções (ex: retry logic, métricas).

### 8.7 Dependency Injection
Técnica onde dependências são injetadas em vez de criadas diretamente, facilitando testes e manutenção.

### 8.8 Separation of Concerns
Princípio de design que separa responsabilidades em módulos distintos (API, serviços, persistência, etc.).

### 8.9 Async/Await
Paradigma de programação assíncrona em Python para operações I/O não bloqueantes.

### 8.10 Context Managers
Padrão Python para gerenciar recursos com `with` statements (ex: conexões HTTP, métricas).

---

## 9. Segurança e Conformidade

### 9.1 HTTPS/TLS
Protocolo de comunicação segura via criptografia TLS. Obrigatório para todos os endpoints expostos.

### 9.2 Security Headers
Headers HTTP de segurança (ex: X-Content-Type-Options, X-Frame-Options) para proteção contra ataques comuns.

### 9.3 Data Masking
Técnica de mascaramento de dados sensíveis em logs e auditoria (ex: telefones, emails parcialmente ocultos).

### 9.4 LGPD (Lei Geral de Proteção de Dados)
Conformidade com a legislação brasileira de proteção de dados pessoais. Inclui retenção, anonimização e direitos do titular.

### 9.5 Audit Trail
Registro de auditoria de operações sensíveis para rastreabilidade e investigação.

### 9.6 Data Retention Policies
Políticas de retenção de dados que definem por quanto tempo dados são mantidos antes de anonimização/exclusão.

### 9.7 Data Anonymization
Processo de remoção ou mascaramento de identificadores pessoais em dados para conformidade com LGPD.

### 9.8 Input Validation
Validação de dados de entrada para prevenir injeção de dados maliciosos ou inválidos.

### 9.9 Path Traversal Protection
Proteção contra ataques de path traversal ao carregar arquivos (ex: system prompts).

### 9.10 API Key Management
Gerenciamento seguro de chaves de API via variáveis de ambiente, sem hardcoding.

---

## 10. Observabilidade e Monitoramento

### 10.1 Prometheus
Sistema de monitoramento e métricas de código aberto. O projeto expõe métricas no formato Prometheus.

### 10.2 Metrics Collection
Coleta de métricas de performance e comportamento do sistema (latência, taxa de erro, contadores).

### 10.3 Histograms
Tipo de métrica Prometheus para medir distribuições de valores (ex: latência P50, P95, P99).

### 10.4 Counters
Tipo de métrica Prometheus para contar eventos (ex: total de requisições HTTP, total de mensagens processadas).

### 10.5 Alerting
Sistema de alertas para notificar sobre condições críticas (alta taxa de erro, latência elevada, falhas de autenticação).

### 10.6 Alert Debouncing
Técnica para evitar spam de alertas repetindo o mesmo problema em intervalos curtos.

### 10.7 Structured Logging
Logging estruturado em formato JSON para facilitar parsing e análise por ferramentas de log.

### 10.8 Log Levels
Níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) para filtrar informações por importância.

### 10.9 Health Checks
Endpoints HTTP para verificar a saúde do sistema e suas dependências.

### 10.10 Runbooks
Documentação operacional com procedimentos para tarefas comuns (pausar agente, verificar saúde, etc.).

---

## 11. Resiliência e Tratamento de Erros

### 11.1 Retry Logic
Lógica de retry para tentar novamente operações que falharam devido a erros temporários.

### 11.2 Exponential Backoff
Estratégia de retry onde o tempo de espera aumenta exponencialmente entre tentativas.

### 11.3 Jitter
Adição de aleatoriedade ao backoff para evitar "thundering herd" quando múltiplos clientes retentam simultaneamente.

### 11.4 Circuit Breaker Pattern
Padrão para interromper chamadas a serviços que estão falhando repetidamente (não implementado, mas conceito relevante).

### 11.5 Fallback Mechanisms
Mecanismos de fallback para continuar operação mesmo quando integrações externas falham (ex: salvar localmente se CRM falhar).

### 11.6 Error Classification
Classificação de erros em retryable (temporários) vs non-retryable (permanentes) para decidir se deve retentar.

### 11.7 Graceful Degradation
Capacidade do sistema de continuar funcionando com funcionalidades reduzidas quando componentes falham.

### 11.8 Timeout Handling
Tratamento de timeouts em requisições HTTP para evitar espera indefinida.

---

## 12. Processamento de Dados

### 12.1 Data Normalization
Normalização de dados para formatos padrão (ex: telefone para E.164, CNPJ para 14 dígitos).

### 12.2 E.164 Format
Formato internacional padrão para números de telefone (ex: `5511999999999`).

### 12.3 CNPJ Validation
Validação e normalização de CNPJ (Cadastro Nacional de Pessoa Jurídica) brasileiro.

### 12.4 Email Validation
Validação de formato de endereços de email.

### 12.5 State (UF) Validation
Validação de códigos de estado brasileiro (2 letras, uppercase).

### 12.6 In-Memory Caching
Cache em memória para melhorar performance de acesso a dados frequentemente consultados.

### 12.7 Lazy Loading
Carregamento sob demanda de dados apenas quando necessário (ex: carregar histórico de conversa do Supabase apenas na primeira mensagem).

---

## 13. Funcionalidades de Negócio

### 13.1 Lead Qualification
Processo de qualificação de leads através de conversa para identificar potencial de compra.

### 13.2 Progressive Data Collection
Coleta progressiva de dados do lead ao longo da conversa, sem pressionar com muitas perguntas.

### 13.3 Knowledge Base
Base de conhecimento sobre produtos e equipamentos usada pelo agente para responder perguntas técnicas.

### 13.4 Guardrails
Regras e restrições que o agente deve seguir (ex: não discutir preços, não dar prazos de entrega).

### 13.5 Upsell
Sugestão de produtos superiores quando o lead demonstra interesse em produtos de menor valor.

### 13.6 Unavailable Products Handling
Tratamento de interesse em produtos indisponíveis, informando previsão de disponibilidade.

### 13.7 Technical Escalation
Encaminhamento de perguntas muito técnicas para especialistas humanos.

### 13.8 Handoff Summary
Resumo estruturado enviado ao Chatwoot quando um lead é classificado como "quente" para facilitar transição para SDR humano.

### 13.9 Agent Pause/Resume
Mecanismo para pausar o agente quando SDR humano intervém e retomar automaticamente ou via comando.

### 13.10 Business Hours
Configuração de horários comerciais para determinar quando o agente deve operar ou permitir intervenção humana.

---

## 14. Testes e Qualidade

### 14.1 Unit Tests
Testes unitários que testam funções e classes isoladamente, sem dependências externas.

### 14.2 Integration Tests
Testes de integração que verificam a interação entre múltiplos componentes do sistema.

### 14.3 Test Fixtures
Dados e configurações reutilizáveis para testes (definidos em `conftest.py`).

### 14.4 Mocking
Técnica de simular dependências externas em testes para isolamento e controle.

### 14.5 Test Coverage
Métrica que mede a porcentagem do código coberta por testes.

### 14.6 Test Assertions
Afirmações em testes que verificam se o comportamento esperado ocorreu.

### 14.7 Async Testing
Testes de código assíncrono usando `pytest-asyncio` e `async/await`.

---

## 15. Configuração e Deployment

### 15.1 Configuration Management
Gerenciamento de configurações via Pydantic Settings a partir de variáveis de ambiente.

### 15.2 Settings Validation
Validação automática de configurações na inicialização da aplicação.

### 15.3 Environment-based Configuration
Configurações diferentes para desenvolvimento, staging e produção baseadas em variável `APP_ENV`.

### 15.4 Health Check Endpoints
Endpoints HTTP para verificar status da aplicação e dependências.

### 15.5 Graceful Shutdown
Encerramento gracioso da aplicação que permite finalizar requisições em andamento antes de parar.

---

## 16. Comunicação e Sincronização

### 16.1 Bidirectional Sync
Sincronização bidirecional de mensagens entre o sistema e Chatwoot para manter consistência.

### 16.2 Message Queue (Conceptual)
Conceito de fila de mensagens para processamento assíncrono (não implementado, mas relevante para escalabilidade).

### 16.3 Event-driven Architecture
Arquitetura baseada em eventos onde ações são disparadas por eventos (ex: webhook recebe mensagem → processa).

### 16.4 Non-blocking Operations
Operações assíncronas que não bloqueiam a thread principal, permitindo processamento paralelo.

---

## 17. Documentação e Metadados

### 17.1 OpenAPI/Swagger
Especificação de API REST gerada automaticamente pelo FastAPI para documentação interativa.

### 17.2 API Documentation
Documentação automática de endpoints via Swagger UI em `/docs`.

### 17.3 Type Hints
Anotações de tipo em Python para melhor documentação e verificação estática de tipos.

### 17.4 Docstrings
Documentação inline em funções e classes usando docstrings Python.

### 17.5 Conventional Commits
Padrão de mensagens de commit para melhor rastreabilidade e geração automática de changelogs.

---

## 18. Processamento de Áudio

### 18.1 Audio Transcription
Transcrição de mensagens de áudio do WhatsApp para texto usando OpenAI Whisper.

### 18.2 Audio File Handling
Processamento de arquivos de áudio recebidos via webhook do Z-API.

### 18.3 Media Storage
Armazenamento temporário de arquivos de mídia antes do processamento.

---

## 19. Gerenciamento de Estado

### 19.1 Conversation State
Estado de conversas mantido em memória e persistido no Supabase.

### 19.2 Session Management
Gerenciamento de sessões de conversa identificadas por número de telefone normalizado.

### 19.3 Context Preservation
Preservação de contexto de conversas anteriores para respostas mais naturais do agente.

### 19.4 Thread ID
Identificador de thread usado pelo Agno Framework para manter contexto de conversa.

---

## 20. Otimizações e Performance

### 20.1 Connection Pooling
Reutilização de conexões HTTP para reduzir overhead de estabelecimento de conexão.

### 20.2 Lazy Initialization
Inicialização sob demanda de recursos pesados apenas quando necessário.

### 20.3 Caching Strategies
Estratégias de cache para reduzir chamadas a APIs externas e banco de dados.

### 20.4 Response Time Optimization
Otimização de tempo de resposta para manter latência abaixo de 5 segundos conforme requisitos.

### 20.5 Batch Operations
Operações em lote para reduzir número de chamadas a APIs externas (conceito, não implementado).

---

## 21. Metodologias e Processos

### 21.1 Agile Development
Metodologia ágil de desenvolvimento com sprints e histórias de usuário.

### 21.2 Technical Stories
Histórias técnicas que descrevem tarefas de infraestrutura e arquitetura (ex: TECH-001, TECH-002).

### 21.3 User Stories
Histórias de usuário que descrevem funcionalidades do ponto de vista do usuário (ex: US-001, US-002).

### 21.4 Acceptance Criteria
Critérios de aceitação que definem quando uma história está completa.

### 21.5 Epic Organization
Organização de trabalho em épicos temáticos (ex: Epic 8 - Observabilidade, Epic 9 - Segurança).

### 21.6 Test-Driven Development (TDD)
Metodologia de desenvolvimento onde testes são escritos antes do código (aplicado parcialmente).

### 21.7 Code Review
Processo de revisão de código por pares antes de merge.

### 21.8 Continuous Integration (CI)
Integração contínua de código com execução automática de testes (conceito, configuração não mostrada).

---

## 22. Estrutura de Projeto

### 22.1 Modular Architecture
Arquitetura modular com separação clara de responsabilidades em módulos (`agents/`, `services/`, `api/`, etc.).

### 22.2 Package Structure
Estrutura de pacotes Python com `__init__.py` para organização de código.

### 22.3 Configuration Files
Arquivos de configuração separados (`config/`, `prompts/`, `.env`) para facilitar manutenção.

### 22.4 Test Organization
Organização de testes espelhando estrutura do código fonte (`tests/` com mesma hierarquia de `src/`).

### 22.5 Documentation Structure
Estrutura de documentação organizada em `docs/`, `documentation/`, `.context/` para diferentes propósitos.

---

## 23. Ferramentas de Build e Dependências

### 23.1 pip
Gerenciador de pacotes Python usado para instalar dependências do projeto.

### 23.2 requirements.txt
Arquivo que lista todas as dependências Python do projeto com versões específicas.

### 23.3 pyproject.toml
Arquivo de configuração moderno do Python para metadados do projeto, ferramentas de build e configurações de ferramentas.

### 23.4 setuptools
Ferramenta de build e distribuição de pacotes Python.

### 23.5 Wheel Format
Formato de distribuição de pacotes Python pré-compilados para instalação rápida.

---

## 24. Conceitos de IA e Machine Learning

### 24.1 Large Language Models (LLM)
Modelos de linguagem grandes como GPT-4o que processam e geram texto natural.

### 24.2 Prompt Engineering
Técnica de construção de prompts eficazes para obter melhores respostas de LLMs.

### 24.3 Few-shot Learning
Aprendizado com poucos exemplos através de prompts que incluem exemplos de comportamento desejado.

### 24.4 Context Window
Limite de tokens que um LLM pode processar em uma única requisição. Importante para gerenciar histórico de conversa.

### 24.5 Token Management
Gerenciamento de tokens para otimizar uso de API e custos, mantendo contexto relevante dentro dos limites.

### 24.6 Temperature Parameter
Parâmetro que controla a aleatoriedade/creativeidade das respostas do LLM (não usado explicitamente, mas conceito relevante).

---

## 25. Integração e Sincronização de Dados

### 25.1 Data Synchronization
Sincronização de dados entre sistemas (Supabase ↔ Chatwoot ↔ PipeRun) para manter consistência.

### 25.2 Idempotent Operations
Operações que podem ser executadas múltiplas vezes sem efeitos colaterais (ex: upsert de leads).

### 25.3 Data Deduplication
Prevenção de duplicação de dados através de constraints únicas e lógica de upsert.

### 25.4 Conflict Resolution
Resolução de conflitos quando dados são modificados em múltiplos sistemas simultaneamente.

### 25.5 Event Sourcing (Conceptual)
Conceito de armazenar eventos em vez de estado final (não implementado, mas relevante para auditoria).

---

## 26. Timezone e Localização

### 26.1 Timezone Handling
Tratamento de fusos horários para garantir que horários comerciais sejam calculados corretamente.

### 26.2 pytz / tzdata
Bibliotecas para gerenciamento de timezones (tzdata incluída no requirements.txt).

### 26.3 UTC Timestamps
Armazenamento de timestamps em UTC para consistência, convertendo para timezone local quando necessário.

### 26.4 Business Hours Configuration
Configuração de horários comerciais por dia da semana e timezone específico.

---

## 27. Validação e Sanitização

### 27.1 Input Sanitization
Limpeza e sanitização de dados de entrada para prevenir injeção e garantir formato correto.

### 27.2 Phone Number Validation
Validação de números de telefone para garantir formato válido antes de processamento.

### 27.3 CNPJ Validation
Validação de CNPJ incluindo verificação de dígitos verificadores.

### 27.4 Email Format Validation
Validação de formato de email usando regex ou bibliotecas especializadas.

### 27.5 Data Type Validation
Validação de tipos de dados usando Pydantic para garantir tipos corretos em runtime.

---

## 28. Logging e Debugging

### 28.1 Structured Logging
Logging estruturado em formato JSON para facilitar análise e parsing por ferramentas de log.

### 28.2 Log Context
Contexto adicional em logs (ex: número de telefone, IDs de transação) para rastreabilidade.

### 28.3 Debug Instrumentation
Instrumentação de código para debug com logs detalhados em pontos específicos.

### 28.4 Error Tracking
Rastreamento de erros com stack traces completos para facilitar debugging.

### 28.5 Log Aggregation (Conceptual)
Conceito de agregar logs de múltiplas fontes em uma plataforma central (não implementado, mas relevante).

---

## 29. Versionamento e Controle

### 29.1 Semantic Versioning
Versionamento semântico de releases (MAJOR.MINOR.PATCH) para comunicar impacto de mudanças.

### 29.2 Git Branching
Estratégias de branching Git para desenvolvimento de features, hotfixes e releases.

### 29.3 Migration Versioning
Versionamento de migrações de banco de dados para rastreabilidade e rollback.

### 29.4 Code Versioning
Controle de versão de código-fonte via Git para histórico e colaboração.

---

## 30. Conceitos de Arquitetura de Software

### 30.1 Layered Architecture
Arquitetura em camadas separando API, serviços de negócio e persistência de dados.

### 30.2 Clean Architecture
Princípios de arquitetura limpa com separação de responsabilidades e independência de frameworks.

### 30.3 Domain-Driven Design (DDD) Concepts
Conceitos de DDD como entidades de domínio (Lead, Orcamento, Empresa) e serviços de domínio.

### 30.4 API Gateway Pattern
Padrão de gateway de API para centralizar roteamento, autenticação e rate limiting (conceito, FastAPI atua como gateway).

### 30.5 Microservices Concepts
Conceitos de microsserviços com serviços independentes e comunicação via APIs (aplicado parcialmente).

---

Este documento serve como referência completa de todas as tecnologias, conceitos e ferramentas utilizadas no projeto Seleto Industrial SDR Agent.

