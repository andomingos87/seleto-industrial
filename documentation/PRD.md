## PRD — Agente de IA (SDR) para Seleto Industrial

### 1) Metadados

- **Produto**: Agente de IA para atendimento inicial, qualificação e organização de CRM (Seleto Industrial)
- **Canais**: WhatsApp (via provedor; ver “Decisões em aberto”), Chatwoot (painel humano)
- **Orquestração/Runtime**: Agno (Agent Framework + AgentOS Runtime em Python/FastAPI)
- **CRM**: PipeRun / Piperun (API REST)
- **Persistência**: Supabase (Postgres)
- **Artefatos-base usados**: `documentation/requirements_analysis.md`, `documentation/resume.md`, `documentation/MCP - SELETO.json`, `prompts/**`, `webhook_audio_message.json`
- **Versão do PRD**: 1.0
- **Data**: 2026-01-03

---

### 2) Sumário executivo

A Seleto Industrial recebe leads via WhatsApp (campanhas e canais digitais) e precisa:

- **Responder rápido** e com qualidade (primeiro contato humanizado);
- **Qualificar** com base em perguntas progressivas (sem interrogatório);
- **Registrar e estruturar** as informações no CRM (empresa, pessoa, oportunidade, nota);
- **Manter o humano no controle** (SDR acompanha no Chatwoot e pode assumir a conversa);
- **Escalar apenas leads quentes**, reduzindo desperdício de tempo do time comercial.

Este PRD define escopo, fluxos, requisitos, integrações, dados, segurança e critérios de aceite para entregar um MVP robusto e evolutivo.

---

### 3) Problema, contexto e oportunidade

#### 3.1 Contexto do negócio

A Seleto Industrial fabrica equipamentos industriais em aço inox para processos produtivos, com foco em indústria alimentícia (carnes, hambúrgueres, embutidos, etc.). O atendimento inicial frequentemente demanda:

- entendimento da necessidade (tipo de produto/linha),
- volume/capacidade,
- urgência,
- localidade,
- fit com o portfólio.

#### 3.2 Problemas atuais (hipóteses)

- **Tempo de resposta inconsistente** (perda de conversão).
- **Qualificação manual** e repetitiva (custo operacional).
- **CRM incompleto ou desorganizado** (perda de rastreabilidade e follow-up).
- **Leads frios/curiosos** consumindo SDR e vendedores.

#### 3.3 Oportunidade

Automatizar o atendimento inicial e o “SDR 0” com IA + automações, mantendo governança (Chatwoot) e garantindo que o CRM receba dados estruturados e auditáveis.

---

### 4) Objetivos e métricas de sucesso (KPIs)

#### 4.1 Objetivos

- **O1 — Resposta rápida**: reduzir tempo até a primeira resposta e manter ritmo de conversa natural.
- **O2 — Qualificação consistente**: coletar campos essenciais e classificar temperatura do lead.
- **O3 — CRM organizado**: registrar empresa/pessoa/oportunidade e nota padronizada.
- **O4 — Eficiência comercial**: escalar ao humano prioritariamente leads quentes.
- **O5 — Conformidade e segurança**: tratar dados pessoais com controles (LGPD, segredos, logs).

#### 4.2 Métricas sugeridas

- **TTR (Time to Reply)**: P95 < 5s para respostas automáticas (quando IA habilitada).
- **Taxa de coleta mínima**: % de conversas com (nome + produto/necessidade + cidade/UF + urgência) ≥ alvo definido.
- **Taxa de qualificação**: % conversas classificadas (frio/morno/quente) com justificativa mínima em nota.
- **Taxa de criação de oportunidade**: % conversas que geram oportunidade no CRM (quando aplicável).
- **Taxa de intervenção humana**: % conversas assumidas por SDR (espera-se menor em leads frios).
- **Conversão por temperatura**: quente → proposta, morno → follow-up, frio → nurture.
- **Erros de integração**: taxa de falhas por endpoint (PipeRun/Supabase/Chatwoot/WhatsApp).

---

### 5) Stakeholders e responsabilidades

- **Marketing**: origem dos leads, campanhas, UTMs/identificação de origem.
- **SDR (humano)**: acompanha conversas no Chatwoot, assume quando necessário, valida qualificação.
- **Vendas (consultores)**: tratam oportunidades qualificadas, orçamento/proposta e negociação.
- **Operação/CS**: regras de atendimento, materiais de apoio, atualização do catálogo.
- **TI/Engenharia**: Agno/Chatwoot/VPS, integrações, segurança, observabilidade.
- **Jurídico/Compliance**: LGPD, retenção e consentimento.

---

### 6) Personas e casos de uso

#### 6.1 Personas

- **Lead (cliente)**: dono/gerente/produção (indústria alimentícia), busca equipamento para aumentar produtividade/qualidade.
- **SDR (humano)**: operador de chat, objetivo é priorizar leads quentes e organizar handoff.
- **Vendedor/consultor**: recebe oportunidade “com contexto”, acelera proposta.
- **Admin técnico**: mantém runtime do Agno (AgentOS)/Chatwoot, credenciais, logs e rotinas.

#### 6.2 Principais jobs-to-be-done

- **Lead**: entender qual equipamento resolve sua dor e como avançar.
- **SDR**: obter dados mínimos, classificar, encaminhar só o que vale.
- **Vendas**: receber oportunidade com nota completa e dados confiáveis.
- **Admin**: garantir disponibilidade 24/7 e integrações estáveis e seguras.

---

### 7) Escopo

#### 7.1 Escopo (in)

- Atendimento automático inicial via WhatsApp (texto e, se disponível, áudio com transcrição).
- Base de conhecimento de produtos para respostas e direcionamento (ex.: formadoras, cortadoras, linhas automáticas).
- Coleta progressiva de dados do lead (sem enviar “questionário”).
- Classificação de temperatura (frio/morno/quente).
- Persistência mínima no banco (lead, empresa, orçamento/conversa quando aplicável).
- Integração com PipeRun:
  - buscar cidade (city_id),
  - criar/buscar empresa (por CNPJ),
  - criar pessoa,
  - criar oportunidade (deal),
  - criar nota vinculada à oportunidade.
- Registro e visibilidade da conversa no Chatwoot.
- Regra de “human-in-the-loop”: agente pausa quando humano intervir.

#### 7.2 Fora de escopo (out)

- **Painel web administrativo próprio** (gestão de prompts, catálogo e configurações).
- **Notificações externas dedicadas** (e-mail/SMS/push) além do que Chatwoot/CRM já provê.
- **Negociação comercial**: prazos, descontos, condições e proposta (salvo exceções formalmente aprovadas; ver “Política de preço”).
- **Precificação dinâmica** e cálculo de frete/instalação.
- **BI/Analytics avançado** (dashboards, atribuição completa) — pode entrar em fases futuras.

---

### 8) Regras de atendimento (conversational design)

#### 8.1 Tom e estilo

- Cordial, profissional, empático.
- Mensagens curtas e claras.
- Evitar jargões e “fala robótica”.
- **Regra de ritmo**: no máximo **duas perguntas diretas seguidas**.

#### 8.2 Política de conteúdo

- Não prometer prazos de entrega.
- Não negociar descontos.
- Não fornecer orçamento/proposta completa.
- **Dúvidas técnicas complexas**: registrar e encaminhar para especialista.

#### 8.3 Política de escalonamento

- **Lead quente**: deve ser preparado para handoff ao SDR/vendas com resumo estruturado.
- **Lead morno**: manter contexto no CRM/Chatwoot, sugerir follow-up (manual ou via processo).
- **Lead frio**: encerrar cordialmente e oferecer material (catálogo/site); registrar no CRM quando aplicável.

#### 8.4 Política de preço (decisão necessária)

Há dois direcionamentos nos artefatos:

- Um conjunto de regras proíbe informar preço/condições.
- Outro documento permite exceção (lead frio) para informar preço de itens específicos.

**Requisito do PRD**: definir uma política final, com:

- quais produtos permitem preço,
- em quais condições (temperatura, intenção),
- quais mensagens/limites (ex.: “preço de referência”, “sujeito a alteração”),
- rastreabilidade (nota no CRM).

Até decisão, considerar preço como **fora de escopo** no MVP.

#### 8.5 Regra de oferta (upsell) — formadoras

- Quando o lead demonstrar interesse em **formadora manual (FBM100)**, o agente deve **sugerir também a FB300** como alternativa “acima” (semi automática), sempre em tom consultivo e sem pressão.

#### 8.6 Tratamento de interesse em produto/linha indisponível

- Se o lead perguntar sobre **linha/máquina de espetos** e o produto estiver indisponível, o agente deve:
  - informar que o projeto está em melhoria e que existe uma previsão interna (a confirmar),
  - **registrar o interesse** para contato futuro,
  - oferecer alternativa imediata quando fizer sentido (ex.: **CT200** para corte em cubos, como etapa anterior do processo).

---

### 9) Fluxos principais

#### 9.1 Fluxo A — Novo lead (texto)

1) Lead inicia contato no WhatsApp.
2) Agente cumprimenta, identifica necessidade e coleta nome/empresa.
3) Agente coleta cidade/UF e confirma produto/linha de interesse.
4) Agente pergunta volume/capacidade e urgência.
5) Agente responde dúvidas usando base de conhecimento.
6) Agente classifica temperatura (frio/morno/quente).
7) Sistema registra/atualiza dados (DB) e cria/atualiza registros no CRM (quando aplicável).
8) Se quente, prepara handoff e permite intervenção humana.

#### 9.2 Fluxo B — Novo lead (áudio)

1) Lead envia áudio.
2) Sistema obtém `audioUrl` (via webhook do provedor) e transcreve para texto.
3) Agente responde como no Fluxo A, registrando que houve áudio e a transcrição (se permitido pela política de dados).

#### 9.3 Fluxo C — Intervenção humana (Chatwoot)

1) SDR envia mensagem na conversa.
2) Agente entra em modo “escuta” e **para de responder**.
3) Agente só volta a atuar mediante comando/condição definida (TBD).

#### 9.4 Fluxo D — Criação/Deduplicação de Empresa + Oportunidade no CRM

Objetivo: garantir que a oportunidade exista no CRM e seja vinculada corretamente, evitando duplicidades.

1) Quando o lead responder e houver dados mínimos (nome + intenção/produto), iniciar preparação de CRM.
2) Se houver **cidade/UF**, chamar `get_city_id` para obter `city_id`.
3) Se houver **CNPJ**, buscar empresa no CRM (evitar duplicidade):
   - se existir: reutilizar `company_id`,
   - se não existir: criar empresa (`POST /companies`) e obter `company_id`.
4) Se o lead fornecer e-mail/telefone, criar pessoa no CRM (`POST /persons`) e manter relação conforme padrão do CRM (TBD).
5) Criar oportunidade no CRM (`POST /deals`) com pipeline/stage configurados e título significativo (ex.: “Lead — [Produto] — [Cidade/UF]”).
6) Registrar nota na oportunidade (`POST /notes`) com o template padronizado (ver Apêndice 20.3).
7) Persistir no Supabase o vínculo com o CRM (ex.: salvar `oportunidade_pipe_id` no orçamento/lead).

---

### 10) Requisitos funcionais (RF)

#### 10.1 Conversa e qualificação

- **RF-01 — Atendimento automático via WhatsApp**: iniciar e manter conversa com novos leads.
- **RF-02 — Coleta progressiva de dados**: nome, empresa (se houver), cidade/UF, produto/necessidade, volume/capacidade, urgência, histórico com a Seleto.
- **RF-03 — Respostas com base de conhecimento**: responder dúvidas sobre equipamentos/linhas usando uma base estruturada.
- **RF-04 — Classificação de temperatura**: classificar lead em frio/morno/quente.
- **RF-05 — Registro e auditoria de conversa**: manter histórico acessível no Chatwoot e/ou banco.
- **RF-06 — Escalonamento para humano**: permitir handoff e pausa do agente quando humano intervir.

#### 10.2 Persistência (Supabase)

- **RF-07 — Atualizar dados do lead**: persistir/atualizar nome e atributos do lead por telefone (E.164 sem símbolos).
- **RF-08 — Orçamentos no banco**: criar registro de orçamento com resumo/produto/segmento/urgência/volume e vincular ao lead.
- **RF-09 — Empresas no banco**: criar empresa local com nome/cidade/UF/CNPJ/site/email/telefone e vínculo com lead.
- **RF-10 — Obter oportunidade vinculada ao lead**: recuperar `oportunidade_pipe_id` do orçamento do lead quando necessário.

#### 10.3 Integração CRM (PipeRun)

- **RF-11 — Obter `city_id`**: buscar código de cidade por nome + UF.
- **RF-12 — Criar empresa no CRM**: criar empresa com name, city_id, cnpj, website, email_nf.
- **RF-13 — Buscar empresa no CRM por CNPJ**: evitar duplicidade.
- **RF-14 — Atualizar empresa no CRM**: atualizar campos quando necessário (endpoint deve aceitar ID dinâmico).
- **RF-15 — Criar pessoa no CRM**: criar pessoa com nome, telefones, e-mails e city_id.
- **RF-16 — Criar oportunidade (deal)**: criar oportunidade em pipeline/stage configuráveis.
- **RF-17 — Criar nota na oportunidade**: registrar nota padronizada com resumo + dados coletados + classificação.

---

### 11) Regras de negócio (RN)

- **RN-01 — Temperatura por engajamento**: classificação deve considerar respostas e completude (critérios detalhados ainda precisam de definição mais rica).
- **RN-02 — Escalonar somente quente**: apenas leads quentes devem ser encaminhados ao SDR humano (regra atual do agente).
- **RN-03 — Limite de perguntas**: máximo duas perguntas diretas seguidas.
- **RN-04 — Idempotência por telefone**: o lead deve ser identificado pelo telefone (evitar duplicatas).
- **RN-05 — Empresa por CNPJ**: se CNPJ informado e empresa existir no CRM, usar registro existente.
- **RN-06 — Campos obrigatórios mínimos para “qualificado”** (MVP):
  - nome (ou “não informado”),
  - cidade/UF (ou “não informado”),
  - produto/necessidade (ou “não informado”),
  - urgência (ou “não informado”).

---

### 12) Requisitos não-funcionais (RNF)

- **RNF-01 — Latência**: resposta do agente em até 5s (P95) quando integrações não estiverem degradadas.
- **RNF-02 — Disponibilidade**: operação 24/7 com reinício automático e monitoramento.
- **RNF-03 — Segurança em trânsito**: todo tráfego via HTTPS/TLS.
- **RNF-04 — Segurança de segredos**: tokens/chaves nunca hardcoded em repositório; usar variáveis de ambiente/secret manager do runtime (Agno) e credenciais seguras nos provedores.
- **RNF-05 — Confiabilidade**: retries com backoff em integrações externas e trilha de logs para auditoria.
- **RNF-06 — Escalabilidade**: suportar múltiplos fluxos e evolução de catálogo sem reescrever arquitetura.

---

### 13) Integrações (contratos e responsabilidades)

#### 13.1 WhatsApp (provedor)

O projeto deve suportar recebimento de mensagens via webhook do provedor (existe exemplo de payload contendo áudio). Campos típicos:

- **Identificação do lead**: `phone`
- **Nome exibido**: `senderName`/`chatName`
- **Mensagem**: texto ou objeto `audio` com `audioUrl`

**Decisão em aberto**: usar WhatsApp Business API oficial vs provedor terceiro (ex.: Z-API). O PRD assume apenas “provedor com webhook + envio de mensagens”.

#### 13.2 Chatwoot

- Fonte de verdade para atendimento humano e histórico visual.
- Deve permitir:
  - monitoramento em tempo real,
  - intervenção humana,
  - evento/condição para pausar o agente.

#### 13.3 Agno (Agent Framework + AgentOS Runtime)

- Hospeda o **runtime** do agente como um serviço **containerizado** em Python, com app **FastAPI** (AgentOS Runtime).
- Recebe webhooks do provedor (WhatsApp) e/ou eventos do Chatwoot e inicia sessões de atendimento.
- Executa o agente com:
  - prompt do sistema (`sp_agente_v1.xml`),
  - memória/histórico de conversa,
  - ferramentas (tools) para Supabase e PipeRun,
  - guardrails e Human-in-the-Loop (pausa/retomada sob regras).
- Publica endpoints para ingestão e operações (ex.: webhook mensagem, webhook status, webhook áudio) conforme o provedor utilizado.
- Observabilidade: logs estruturados, tracing e métricas (com ou sem uso do Control Plane/UI do Agno, se adotado).

#### 13.4 Supabase (persistência)

Tabelas mínimas já observadas nos fluxos:

- `leads` (ex.: `phone`, `name`, `orcamentos`, etc.)
- `orcamentos` (ex.: `lead`, `resumo`, `produto`, `segmento`, `urgencia_compra`, `volume_diario`, `oportunidade_pipe_id`)
- `empresa` (ex.: `nome`, `cidade`, `uf`, `cnpj`, `site`, `email`, `telefone`, `contato`)

**Boa prática (Context7 / Supabase docs)**:

- Ativar **Row Level Security (RLS)** nas tabelas e usar **Service Key** (somente servidor) para automações administrativas, evitando exposição em clientes.
- Alternativa: criar role Postgres com `BYPASSRLS` apenas para rotinas internas, com auditoria e rotação.

#### 13.5 PipeRun / Piperun (CRM)

Endpoints observados nos artefatos (sem segredos):

- `GET /v1/cities` (query: name, uf) → obter `city_id`
- `POST /v1/companies` → criar empresa
- `GET /v1/companies` (query: cnpj) → buscar empresa
- `PUT /v1/companies/{id}` → atualizar empresa (**requer ID dinâmico**)
- `POST /v1/persons` → criar pessoa
- `POST /v1/deals` → criar oportunidade
- `POST /v1/notes` → criar nota na oportunidade

Configurações do CRM devem ser parametrizadas:

- pipeline/funil,
- estágio (stage),
- origem (IDs por canal),
- dono (owner) se aplicável.

##### 13.5.1 Parâmetros atuais observados nos artefatos (para validação)

- **Pipeline/Funil**: há evidência de uso de `pipeline_id = 100848` (validar no CRM).
- **Stage/Etapa**: há evidência de `stage_id = 647558` em um fluxo, e referência a uma etapa “LEAD NOVO SDR” em outro material; **confirmar IDs corretos** e parametrizar.
- **Origens (IDs)**: existe uma tabela de mapeamento de origem → ID (ver Apêndice 20.2).
- **Owner/dono**: há referência operacional a um e-mail de responsável (validar regra de ownership no CRM e parametrizar).

---

### 14) Dados: modelo, validações e retenção

#### 14.1 Identificadores e normalização

- **Telefone**: armazenar em formato apenas dígitos (ex.: `5511999999999`), validando DDI/DDD quando possível.
- **CNPJ**: normalizar para 14 dígitos (remover pontuação).
- **E-mail**: validar formato e armazenar lowercased.
- **Cidade/UF**: UF com 2 letras; cidade como texto livre + mapeamento para `city_id`.

#### 14.2 Retenção e LGPD (recomendação)

- Definir prazo de retenção para:
  - mensagens/transcrições,
  - dados de lead,
  - logs técnicos.
- Implementar processo de:
  - anonimização/remoção sob solicitação,
  - minimização de dados (coletar apenas o necessário),
  - controle de acesso e trilhas de auditoria.

#### 14.3 Dicionário de dados sugerido (MVP)

Observação: o schema real pode variar, mas os dados abaixo precisam existir para suportar os fluxos e integrações.

- **Tabela `leads`**
  - `id` (uuid)
  - `phone` (text, **único**, normalizado)
  - `name` (text)
  - `temperature` (text: frio|morno|quente)
  - `city` (text)
  - `uf` (text, 2 chars)
  - `produto_interesse` (text)
  - `volume_estimado` (integer, opcional)
  - `urgencia_compra` (text, opcional)
  - `orcamentos` (json/text/array — decisão de modelagem)
  - `updated_at` (timestamptz)

- **Tabela `orcamentos`**
  - `id` (uuid)
  - `lead` (uuid, FK → `leads.id`)
  - `resumo` (text)
  - `produto` (text)
  - `segmento` (text)
  - `urgencia_compra` (text)
  - `volume_diario` (integer)
  - `oportunidade_pipe_id` (text)
  - `created_at` (timestamptz)

- **Tabela `empresa`**
  - `id` (uuid)
  - `nome` (text)
  - `cidade` (text)
  - `uf` (text, 2 chars)
  - `cnpj` (text, normalizado; idealmente único quando presente)
  - `site` (text)
  - `email` (text)
  - `telefone` (text)
  - `contato` (uuid, referência ao lead em atendimento)
  - `created_at` (timestamptz)

---

### 15) Observabilidade e operações

- **Logs estruturados** por etapa: entrada webhook → decisão IA → chamadas externas → persistência.
- **Métricas**: latência, falhas por endpoint, taxa de sucesso de criação de registros, taxa de escalonamento.
- **Alertas**: falha contínua em CRM/WhatsApp, degradação de tempo de resposta, erros de autenticação.
- **Runbooks**: como pausar agente, como rotacionar credenciais, como reprocessar mensagens.

---

### 16) Riscos e mitigação

- **R1 — Segredos expostos**: tokens hardcoded em workflows/arquivos.
  - Mitigação: mover para credenciais/variáveis; varredura e rotação.
- **R2 — Duplicidade no CRM** (empresa/pessoa/oportunidade).
  - Mitigação: chaves idempotentes (CNPJ/telefone), busca antes de criar, dedupe.
- **R3 — Classificação frágil** (temperatura baseada só em “respondeu perguntas”).
  - Mitigação: enriquecer critérios com volume/urgência/fit e registrar justificativa.
- **R4 — Provedor WhatsApp**: mudanças ou limitações (áudio, rate limit).
  - Mitigação: adaptar camada de ingestão; desacoplar via serviço Agno (AgentOS Runtime).
- **R5 — Intervenção humana**: conflito agente vs SDR.
  - Mitigação: regra rígida de pausa e comandos de retomada.

---

### 17) Fases e entregáveis (roadmap)

#### 17.1 MVP (fase 1)

- Atendimento texto + coleta progressiva.
- Classificação frio/morno/quente.
- Registro mínimo (lead + nota + oportunidade) quando aplicável.
- Handoff/pausa por intervenção humana.
- Segurança mínima: segredos fora do repo, HTTPS, logs.

#### 17.2 Fase 2

- Suporte completo a áudio (transcrição + registro).
- Busca/criação de empresa e pessoa com dedupe.
- Nota padronizada e enriquecida (com campos “não informado”).
- Tratamento de erros e retries robustos.

#### 17.3 Fase 3

- Governança de catálogo (processo de atualização).
- Métricas e relatórios operacionais.
- Evolução de score (fit + intenção + timing + capacidade).

---

### 18) Critérios de aceite (alto nível)

- **CA-01**: Ao receber mensagem (texto), o agente responde e conduz coleta com no máximo duas perguntas seguidas.
- **CA-02**: O sistema registra nome/telefone (quando fornecidos) e mantém histórico acessível no Chatwoot.
- **CA-03**: O lead é classificado (frio/morno/quente) e a classificação é persistida/registrada conforme arquitetura definida.
- **CA-04**: Para leads qualificados para CRM, o sistema cria oportunidade no PipeRun e adiciona nota com template padronizado.
- **CA-05**: Se o SDR humano enviar mensagem, o agente pausa e não envia novas mensagens automaticamente.
- **CA-06**: Em falhas temporárias de CRM, há retry/backoff e logs suficientes para auditoria.
- **CA-07**: Nenhum segredo (token/chave) fica hardcoded em arquivos versionados.

---

### 19) Decisões em aberto (TBD)

- **D1**: Provedor WhatsApp: API oficial vs terceiro (ex.: Z-API). Requisitos de conformidade e limitações.
- **D2**: Política final de preço (permitido ou não; exceções).
- **D3**: Regras completas de score (temperatura) incorporando fit/volume/urgência (não apenas engajamento).
- **D4**: Quais etapas do funil e IDs corretos (pipeline/stage) no PipeRun.
- **D5**: Estratégia de persistência do histórico (Chatwoot apenas vs DB + Chatwoot).
- **D6**: Retenção de áudio/transcrição e política LGPD (prazo, consentimento, minimização).
- **D7**: Comandos de retomada do agente após intervenção humana.
- **D8**: CRM alvo final (PipeRun/Piperun vs Pipedrive) — materiais citam ambos, mas integrações atuais estão em PipeRun.

---

### 20) Apêndices

#### 20.1 Ativos existentes no repositório

- Prompt do agente: `prompts/system_prompt/sp_agente_v1.xml`
- Prompt de temperatura: `prompts/system_prompt/sp_calcula_temperatura.xml`
- Workflow legado (n8n) usado como referência de contratos/inputs de tools: `documentation/MCP - SELETO.json`
- Base de conhecimento (equipamentos): `prompts/equipamentos/*`
- Frases prontas: `prompts/frases_prontas/frases_prontas.txt`
- Exemplo webhook áudio: `webhook_audio_message.json`

#### 20.2 Tabela de origens (CRM) — IDs por canal (para validação)

Valores observados em material operacional (confirmar no CRM):

- **Ação Marketing**: 638648
- **Contato do Site**: 629282
- **Site**: 556694
- **Neurologic**: 545920
- **WhatsApp**: 556735
- **Instagram**: 535713
- **Facebook**: 535712

#### 20.3 Template de nota no CRM (padrão sugerido)

Se um campo não for informado, preencher com “Não informado”.

- **Resumo do Atendimento**:
  - [Breve resumo da conversa e do que foi solicitado.]
- **Dados do Cliente**:
  - Empresa: [Nome da Empresa]
  - Contato: [Nome do Contato]
  - Cidade / DDD: [Cidade / (XX)]
  - Segmento: [Ex: Frigorífico, Laticínios, etc.]
- **Necessidade Identificada**:
  - [Descrição clara da dor/objetivo do cliente.]
- **Equipamento de Interesse**:
  - [Modelo ou tipo de máquina citado.]
- **Classificação do Lead**:
  - [Quente / Morno / Frio]
- **Próximo Passo**:
  - [Ex: “Encaminhado para consultor para envio de orçamento.” / “Agendado follow-up em X dias.”]

#### 20.4 Template de handoff para lead quente (Chatwoot/SDR)

- Novo Lead Quente — via [Canal]
  - Nome:
  - Empresa:
  - Localização:
  - Produto de Interesse:
  - Capacidade / Volume:
  - Urgência:
  - Já conhece a Seleto Industrial?:
  - Observações adicionais:

#### 20.5 Exemplo (redigido) de payload de webhook com áudio

O formato abaixo é apenas ilustrativo e não deve conter tokens/segredos em documentação pública.

```json
{
  "headers": {
    "origin": "https://api.<provedor>",
    "content-type": "application/json",
    "token": "<redacted>"
  },
  "body": {
    "phone": "5511XXXXXXXXX",
    "senderName": "Nome",
    "type": "ReceivedCallback",
    "audio": {
      "audioUrl": "https://.../arquivo.ogg",
      "mimeType": "audio/ogg; codecs=opus",
      "seconds": 2
    }
  }
}
```


