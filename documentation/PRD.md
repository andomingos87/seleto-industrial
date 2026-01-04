## PRD — Agente de IA (SDR) para Seleto Industrial

### 1) Metadados

- **Produto**: Agente de IA para atendimento inicial, qualificação e organização de CRM (Seleto Industrial)
- **Canais**: WhatsApp (via provedor; ver “Decisões em aberto”), Chatwoot (painel humano)
- **Orquestração/Runtime**: Agno (Agent Framework + AgentOS Runtime em Python/FastAPI)
- **CRM**: Piperun (API REST)
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
- **Erros de integração**: taxa de falhas por endpoint (Piperun/Supabase/Chatwoot/WhatsApp).

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
- Integração com Piperun:
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
- **Negociação comercial**: prazos, descontos, condições e proposta (ver "Política de preço" na seção 8.4).
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

#### 8.4 Política de preço

**Decisão final (D2)**: Política de preço não permitida, sem exceções.

O agente **não deve informar preços, condições comerciais ou descontos em nenhuma circunstância**, independentemente da temperatura do lead (frio/morno/quente) ou do produto de interesse.

Quando o lead solicitar informações sobre preço, o agente deve:
- Explicar cordialmente que valores e condições são personalizados conforme necessidade específica;
- Oferecer encaminhamento para um consultor comercial que poderá fornecer orçamento detalhado;
- Coletar informações adicionais que ajudem na preparação do orçamento (volume, urgência, especificações técnicas).

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
2) Agente entra em modo "escuta" e **para de responder**.
3) **Retomada do agente**:
   - **Dentro do horário de atendimento**: agente só retoma mediante comando explícito do SDR (ex.: `/retomar`, `/continuar`).
   - **Fora do horário de atendimento**: agente retoma automaticamente quando o lead enviar nova mensagem (SDR não está presente).
4) Horário de atendimento configurável em arquivo de configuração (fuso horário, dias da semana, horários de início/fim).

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
- **RF-05 — Registro e auditoria de conversa**: manter histórico completo persistido no Supabase (DB) para auditoria, análise e backup, e acessível no Chatwoot para acompanhamento humano em tempo real.
- **RF-06 — Escalonamento para humano**: permitir handoff e pausa do agente quando humano intervir, com retomada baseada em horário de atendimento (comando explícito dentro do horário, automática fora do horário).

#### 10.2 Persistência (Supabase)

- **RF-07 — Atualizar dados do lead**: persistir/atualizar nome e atributos do lead por telefone (E.164 sem símbolos).
- **RF-08 — Orçamentos no banco**: criar registro de orçamento com resumo/produto/segmento/urgência/volume e vincular ao lead.
- **RF-09 — Empresas no banco**: criar empresa local com nome/cidade/UF/CNPJ/site/email/telefone e vínculo com lead.
- **RF-10 — Obter oportunidade vinculada ao lead**: recuperar `oportunidade_pipe_id` do orçamento do lead quando necessário.

#### 10.3 Integração CRM (Piperun)

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
- **RN-06 — Campos obrigatórios mínimos para "qualificado"** (MVP):
  - nome (ou "não informado"),
  - cidade/UF (ou "não informado"),
  - produto/necessidade (ou "não informado"),
  - urgência (ou "não informado").
- **RN-07 — Retomada do agente após intervenção humana**:
  - Dentro do horário de atendimento: agente só retoma mediante comando explícito do SDR (ex.: `/retomar`, `/continuar`).
  - Fora do horário de atendimento: agente retoma automaticamente quando o lead enviar nova mensagem.
  - Horário de atendimento configurável em arquivo de configuração (fuso horário, dias da semana, horários de início/fim por dia).

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

#### 13.1 WhatsApp (Z-API)

**Provedor selecionado**: Z-API (https://api.z-api.io)

O projeto utiliza a Z-API como provedor para integração com WhatsApp, fornecendo:
- Envio de mensagens de texto, áudio, mídia
- Recebimento de mensagens via webhooks
- Gerenciamento de instâncias e tokens

##### 13.1.1 Autenticação e Configuração

- **Base URL**: `https://api.z-api.io`
- **Autenticação**: Header `Client-Token` com Account Security Token
- **Instância**: Cada instância WhatsApp possui um `INSTANCE_ID` único
- **Token**: Token de autenticação específico da instância (`INSTANCE_TOKEN`)

**Variáveis de ambiente necessárias:**
- `ZAPI_INSTANCE_ID`: ID da instância Z-API
- `ZAPI_INSTANCE_TOKEN`: Token da instância
- `ZAPI_CLIENT_TOKEN`: Account Security Token (Client-Token header)
- `ZAPI_WEBHOOK_SECRET`: Secret para validação de webhooks (opcional)

##### 13.1.2 Endpoints de Envio

**Envio de texto:**
```
POST https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/send-text
Headers:
  Client-Token: {ZAPI_CLIENT_TOKEN}
  Content-Type: application/json
Body:
  {
    "phone": "5511999999999",
    "message": "Texto da mensagem"
  }
```

**Envio de áudio:**
```
POST https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/send-message-audio
```

**Outros tipos de mídia:**
- Imagem: `/send-message-image`
- Vídeo: `/send-message-video`
- Documento: `/send-message-document`
- Localização: `/send-message-location`

##### 13.1.3 Webhooks de Recebimento

**Configuração do webhook:**
```
PUT https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/update-webhook-received
Headers:
  Client-Token: {ZAPI_CLIENT_TOKEN}
  Content-Type: application/json
Body:
  {
    "value": "https://seu-dominio.com/webhook/whatsapp"
  }
```

**Formato do webhook recebido:**
```json
{
  "phone": "5511999999999",
  "senderName": "Nome do Contato",
  "message": "Texto da mensagem",
  "messageId": "unique_message_id",
  "messageType": "text",
  "audio": {
    "audioUrl": "https://...",
    "mimeType": "audio/ogg",
    "seconds": 5
  }
}
```

##### 13.1.4 Formato de Payloads

**Envio (texto):**
- `phone`: Número em formato E.164 (apenas dígitos)
- `message`: Texto da mensagem (suporta `\n` para quebras de linha)

**Recebimento (webhook):**
- `phone`: Número do remetente
- `senderName`: Nome exibido do contato
- `message`: Texto (se mensagem de texto)
- `audio`: Objeto com `audioUrl`, `mimeType`, `seconds` (se mensagem de áudio)
- `messageId`: ID único da mensagem
- `messageType`: Tipo da mensagem (`text`, `audio`, `image`, etc.)

##### 13.1.5 Tratamento de Erros

- **200 (OK)**: Requisição bem-sucedida
- **401 (Unauthorized)**: Verificar Client-Token e credenciais
- **404 (Not Found)**: Verificar INSTANCE_ID e INSTANCE_TOKEN
- **405 (Method Not Allowed)**: Verificar método HTTP correto (POST/PUT)
- **415 (Unsupported Media Type)**: Verificar header `Content-Type: application/json`
- **429 (Rate Limit)**: Retry com backoff exponencial, respeitando header `Retry-After`
- **5xx (Server Error)**: Retry com backoff exponencial

**Limitações conhecidas:**
- Rate limit: Consultar documentação Z-API para limites específicos por plano
- Tamanho máximo de mensagem: 4096 caracteres
- Formatos de áudio suportados: OGG (Opus), MP3, WAV, WEBM
- Webhook deve ser HTTPS válido

#### 13.2 Chatwoot

- Fonte de verdade para atendimento humano e histórico visual.
- Deve permitir:
  - monitoramento em tempo real,
  - intervenção humana,
  - evento/condição para pausar o agente.
- **Comandos do SDR para retomada do agente** (dentro do horário de atendimento):
  - `/retomar` ou `/continuar`: reativa o agente para continuar atendendo automaticamente.
  - Comandos devem ser processados pelo sistema e não aparecer como mensagem visível ao lead.
  - Fora do horário de atendimento, o agente retoma automaticamente quando o lead enviar nova mensagem (não requer comando).

#### 13.3 Agno (Agent Framework + AgentOS Runtime)

- Hospeda o **runtime** do agente como um serviço **containerizado** em Python, com app **FastAPI** (AgentOS Runtime).
- Recebe webhooks do provedor (WhatsApp) e/ou eventos do Chatwoot e inicia sessões de atendimento.
- Executa o agente com:
  - prompt do sistema (`sp_agente_v1.xml`),
  - memória/histórico de conversa,
  - ferramentas (tools) para Supabase e Piperun,
  - guardrails e Human-in-the-Loop (pausa/retomada sob regras baseadas em horário de atendimento).
- **Configuração de horário de atendimento**: arquivo de configuração (ex.: `config/horario_atendimento.yaml` ou `.env`) contendo:
  - fuso horário (ex.: `America/Sao_Paulo`),
  - dias da semana com atendimento (ex.: segunda a sexta),
  - horários de início/fim por dia (ex.: 08:00-18:00),
  - permitindo fácil alteração sem recompilação.
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

#### 13.5 Piperun (CRM)

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

#### 14.2 Retenção e LGPD (política adotada — D6)

**Política de retenção:**

- **Áudio/transcrição**: retenção de **90 dias**, após os quais:
  - arquivos de áudio serão removidos permanentemente;
  - transcrições serão anonimizadas (mantendo apenas texto sem identificadores diretos como nome, telefone, CNPJ).
- **Dados de lead**: retenção de **2 anos**, com anonimização após período de inatividade de **1 ano**.
- **Logs técnicos**: retenção de **30 dias** para logs de aplicação, **90 dias** para logs de auditoria de integrações.

**Consentimento:**
- Consentimento **implícito** no uso do serviço via WhatsApp (cliente inicia contato voluntariamente).
- Informar ao lead, quando apropriado, que a conversa será registrada para melhor atendimento.

**Minimização de dados:**
- Coletar apenas dados necessários para qualificação e atendimento.
- Não armazenar dados sensíveis além do necessário (ex.: não armazenar CPF a menos que seja estritamente necessário).

**Direitos do titular (LGPD):**
- Implementar processo para atendimento de solicitações de:
  - **Acesso**: fornecer cópia dos dados pessoais em formato estruturado.
  - **Correção**: atualizar dados incorretos ou incompletos.
  - **Exclusão**: remover dados pessoais quando solicitado (respeitando obrigações legais de retenção).
  - **Portabilidade**: exportar dados em formato interoperável quando aplicável.
- Manter trilha de auditoria de todas as solicitações e ações realizadas.

**Controles de acesso:**
- Implementar controle de acesso baseado em roles para dados pessoais.
- Logs de acesso e modificação de dados pessoais.
- Criptografia de dados sensíveis em repouso e em trânsito.

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
  - Mitigação: regra rígida de pausa e retomada baseada em horário de atendimento (comando explícito dentro do horário, automática fora do horário).

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
- **CA-02**: O sistema registra nome/telefone (quando fornecidos) e mantém histórico completo persistido no Supabase e acessível no Chatwoot.
- **CA-03**: O lead é classificado (frio/morno/quente) e a classificação é persistida/registrada conforme arquitetura definida.
- **CA-04**: Para leads qualificados para CRM, o sistema cria oportunidade no Piperun e adiciona nota com template padronizado.
- **CA-05**: Se o SDR humano enviar mensagem, o agente pausa. Dentro do horário de atendimento, o agente só retoma mediante comando explícito do SDR. Fora do horário de atendimento, o agente retoma automaticamente quando o lead enviar nova mensagem.
- **CA-06**: Em falhas temporárias de CRM, há retry/backoff e logs suficientes para auditoria.
- **CA-07**: Nenhum segredo (token/chave) fica hardcoded em arquivos versionados.

---

### 19) Decisões em aberto (TBD)

- **D1**: ~~Provedor WhatsApp: API oficial vs terceiro (ex.: Z-API). Requisitos de conformidade e limitações.~~ **RESOLVIDO**: Z-API selecionado como provedor. Ver seção 13.1 para especificações técnicas completas.
- **D2**: ~~Política final de preço: não permitido, sem exceções.~~ **RESOLVIDO**: Política de preço não permitida, sem exceções. O agente não deve informar preços, condições comerciais ou descontos em nenhuma circunstância.
- **D3**: Regras completas de score (temperatura) incorporando fit/volume/urgência (não apenas engajamento).
- **D4**: Quais etapas do funil e IDs corretos (pipeline/stage) no Piperun.
- **D5**: ~~Estratégia de persistência do histórico (Chatwoot apenas vs DB + Chatwoot).~~ **RESOLVIDO**: DB + Chatwoot. O histórico completo será persistido no Supabase (DB) para auditoria, análise e backup, enquanto o Chatwoot mantém a interface visual para acompanhamento humano em tempo real.
- **D6**: ~~Retenção de áudio/transcrição e política LGPD (prazo, consentimento, minimização).~~ **RESOLVIDO**: Recomendação adotada: (a) **Áudio/transcrição**: retenção de 90 dias, após os quais arquivos de áudio serão removidos e transcrições anonimizadas (mantendo apenas texto sem identificadores diretos); (b) **Dados de lead**: retenção de 2 anos, com anonimização após período de inatividade de 1 ano; (c) **Consentimento**: implícito no uso do serviço via WhatsApp (cliente inicia contato voluntariamente); (d) **Minimização**: coletar apenas dados necessários para qualificação e atendimento; (e) **Direitos do titular**: implementar processo para atendimento de solicitações de acesso, correção, exclusão e portabilidade conforme LGPD.
- **D7**: ~~Comandos de retomada do agente após intervenção humana.~~ **RESOLVIDO**: Retomada baseada em horário de atendimento. **Dentro do horário de atendimento**: agente só retoma mediante comando explícito do SDR (ex.: `/retomar`, `/continuar`). **Fora do horário de atendimento**: agente retoma automaticamente quando o lead enviar nova mensagem (SDR não está presente). O horário de atendimento deve ser configurável em arquivo de configuração (fuso horário, dias da semana, horários de início/fim por dia) para fácil alteração.
- **D8**: ~~CRM alvo final (PipeRun/Piperun vs Pipedrive) — materiais citam ambos, mas integrações atuais estão em PipeRun.~~ **RESOLVIDO**: Piperun confirmado como CRM alvo final. Todas as integrações devem utilizar a API do Piperun.

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

#### 20.5 Exemplo (redigido) de payload de webhook com áudio (Z-API)

O formato abaixo é apenas ilustrativo e não deve conter tokens/segredos em documentação pública.

**Formato do webhook recebido pela Z-API:**

```json
{
  "phone": "5511999999999",
  "senderName": "Nome do Contato",
  "message": null,
  "messageId": "unique_message_id_12345",
  "messageType": "audio",
  "audio": {
    "audioUrl": "https://api.z-api.io/storage/audio/arquivo.ogg",
    "mimeType": "audio/ogg; codecs=opus",
    "seconds": 5
  }
}
```

**Formato do webhook recebido para mensagem de texto:**

```json
{
  "phone": "5511999999999",
  "senderName": "Nome do Contato",
  "message": "Olá, gostaria de informações sobre formadoras",
  "messageId": "unique_message_id_67890",
  "messageType": "text",
  "audio": null
}
```

**Nota**: A Z-API envia o payload diretamente no body da requisição POST, sem wrapper de headers. O webhook deve ser configurado via API (ver seção 13.1.3).


