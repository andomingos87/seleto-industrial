/**
 * Seleto Docs - Content Data
 * All documentation content in JavaScript format
 */

const DOCS_CONTENT = {
    // ============================================
    // HOME
    // ============================================
    'home': {
        title: 'Seleto Industrial SDR Agent',
        clientNote: 'Este sistema é um assistente virtual inteligente que atende seus clientes pelo WhatsApp. Ele qualifica leads automaticamente, responde dúvidas sobre produtos e coleta informações importantes para sua equipe de vendas. Pense nele como um vendedor digital que trabalha 24 horas por dia, 7 dias por semana.',
        sections: [
            {
                title: 'Bem-vindo à Documentação',
                content: `
                    <p>O <strong>Seleto Industrial SDR Agent</strong> é um agente de inteligência artificial projetado para automatizar o processo de qualificação de leads via WhatsApp para a Seleto Industrial, fabricante de máquinas para indústria alimentícia.</p>

                    <div class="feature-grid">
                        <div class="feature-card">
                            <div class="feature-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                                </svg>
                            </div>
                            <h4>Atendimento 24/7</h4>
                            <p>Recebe mensagens de texto e áudio, respondendo de forma natural e contextualizada.</p>
                        </div>

                        <div class="feature-card">
                            <div class="feature-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2a10 10 0 1 0 10 10H12V2z"/>
                                    <circle cx="12" cy="12" r="6"/>
                                </svg>
                            </div>
                            <h4>Qualificação Inteligente</h4>
                            <p>Coleta informações progressivamente e classifica leads por temperatura (quente/morno/frio).</p>
                        </div>

                        <div class="feature-card">
                            <div class="feature-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                                </svg>
                            </div>
                            <h4>Base de Conhecimento</h4>
                            <p>Informações sobre produtos, especificações e respostas consistentes.</p>
                        </div>

                        <div class="feature-card">
                            <div class="feature-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="16 18 22 12 16 6"/>
                                    <polyline points="8 6 2 12 8 18"/>
                                </svg>
                            </div>
                            <h4>Integrações</h4>
                            <p>Sincronização com CRM (PipeRun), interface visual (Chatwoot) e Supabase.</p>
                        </div>
                    </div>
                `
            },
            {
                title: 'Fluxo Principal',
                content: `
                    <div class="diagram">Cliente envia mensagem no WhatsApp
        ↓
Z-API recebe e envia para o sistema
        ↓
Sistema processa a mensagem
        ↓
Extrai informações do cliente (nome, cidade, interesse)
        ↓
Consulta base de conhecimento sobre produtos
        ↓
Gera resposta personalizada com IA
        ↓
Envia resposta pelo WhatsApp
        ↓
Salva conversa e dados no banco</div>
                `
            },
            {
                title: 'Tecnologias Utilizadas',
                content: `
                    <table>
                        <thead>
                            <tr>
                                <th>Tecnologia</th>
                                <th>Uso</th>
                                <th>Por que escolhemos</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Python 3.12</strong></td>
                                <td>Linguagem principal</td>
                                <td>Madura, vasta comunidade, ótima para IA</td>
                            </tr>
                            <tr>
                                <td><strong>FastAPI</strong></td>
                                <td>Framework web</td>
                                <td>Rápido, moderno, documentação automática</td>
                            </tr>
                            <tr>
                                <td><strong>Agno Framework</strong></td>
                                <td>Orquestração de IA</td>
                                <td>Especializado em agentes inteligentes</td>
                            </tr>
                            <tr>
                                <td><strong>OpenAI GPT-4o</strong></td>
                                <td>Inteligência Artificial</td>
                                <td>Melhor modelo de linguagem disponível</td>
                            </tr>
                            <tr>
                                <td><strong>Supabase</strong></td>
                                <td>Banco de dados</td>
                                <td>PostgreSQL gerenciado, tempo real, seguro</td>
                            </tr>
                            <tr>
                                <td><strong>Z-API</strong></td>
                                <td>WhatsApp</td>
                                <td>Integração estável e confiável</td>
                            </tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Começando Rapidamente',
                content: `
                    <h4>Pré-requisitos</h4>
                    <ul>
                        <li>Python 3.12+</li>
                        <li>Conta no Supabase</li>
                        <li>Chave de API da OpenAI</li>
                        <li>(Opcional) Conta Z-API para WhatsApp</li>
                    </ul>

                    <h4>Instalação</h4>
                    <pre><code># 1. Clone o repositório
git clone &lt;repo-url&gt;
cd seleto_industrial

# 2. Crie ambiente virtual
python -m venv venv
.\\venv\\Scripts\\activate  # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Execute o servidor
uvicorn src.main:app --reload</code></pre>

                    <h4>Verificando a Instalação</h4>
                    <p>Acesse: <code>http://localhost:8000/docs</code> para ver a documentação interativa da API.</p>
                `
            }
        ]
    },

    // ============================================
    // ARQUITETURA
    // ============================================
    'arquitetura': {
        title: 'Arquitetura do Sistema',
        clientNote: 'Este documento explica como o sistema está organizado "por dentro". Pense como a planta de uma casa: mostra onde fica cada cômodo e como eles se conectam. Entender isso ajuda a saber por que o sistema é confiável e escalável.',
        sections: [
            {
                title: 'Visão Geral da Arquitetura',
                content: `
                    <p>O Seleto Industrial SDR Agent segue uma arquitetura em camadas, onde cada camada tem uma responsabilidade específica.</p>

                    <div class="diagram">┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (WhatsApp)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Z-API (WhatsApp)                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE API (FastAPI)                       │
│     Health Endpoints  │  Webhooks  │  Middleware (Logging)       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE AGENTES (Agno)                      │
│                         SDR Agent                                │
│     • Processamento de mensagens                                 │
│     • Extração de dados                                          │
│     • Classificação de leads                                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE SERVIÇOS                            │
│  Conversation Memory │ Lead Persistence │ WhatsApp Service       │
│  Knowledge Base      │ Upsell Service   │ Chatwoot Sync          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                               │
│         Supabase (PostgreSQL)    │    OpenAI (GPT-4o)            │
└─────────────────────────────────────────────────────────────────┘</div>
                `
            },
            {
                title: 'Componentes Principais',
                content: `
                    <h4>1. Camada de API (FastAPI)</h4>
                    <p>É a "porta de entrada" do sistema. Todo mundo que quer falar com o sistema passa por aqui primeiro.</p>
                    <ul>
                        <li><code>routes/health.py</code> - Endpoint de verificação de saúde</li>
                        <li><code>routes/webhook.py</code> - Endpoints para mensagens de texto e áudio</li>
                        <li><code>middleware/logging.py</code> - Registro de todas as requisições</li>
                    </ul>

                    <h4>2. Camada de Agentes (Agno Framework)</h4>
                    <p>É o "cérebro" do sistema. Aqui acontece toda a inteligência: entender o que o cliente quer, decidir o que responder, classificar o potencial de compra.</p>

                    <h4>3. Camada de Serviços</h4>
                    <p>São os "especialistas" do sistema. Cada serviço sabe fazer uma coisa muito bem.</p>

                    <h4>4. Camada de Dados</h4>
                    <p>É onde todas as informações ficam guardadas de forma segura.</p>
                `
            },
            {
                title: 'Fluxo de Processamento',
                content: `
                    <div class="diagram">1. Recebe mensagem (telefone, texto, nome)
          ↓
2. Normaliza telefone (formato E.164)
          ↓
3. Verifica se é primeira mensagem
          ↓
4. Carrega histórico da conversa
          ↓
5. Extrai dados do lead (LLM)
          ↓
6. Persiste dados extraídos
          ↓
7. Classifica temperatura (se critérios atendidos)
          ↓
8. Aplica guardrails (comercial, técnico)
          ↓
9. Verifica upsell (FBM100 → FB300)
          ↓
10. Verifica produtos indisponíveis (espeto)
          ↓
11. Gera resposta (LLM via Agno)
          ↓
12. Salva resposta no histórico
          ↓
13. Sincroniza com Chatwoot
          ↓
14. Retorna texto da resposta</div>
                `
            },
            {
                title: 'Padrões de Design',
                content: `
                    <table>
                        <thead>
                            <tr>
                                <th>Padrão</th>
                                <th>Onde é usado</th>
                                <th>Por quê</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Singleton</strong></td>
                                <td>Cliente Supabase</td>
                                <td>Garantir uma única conexão</td>
                            </tr>
                            <tr>
                                <td><strong>Repository</strong></td>
                                <td>Serviços de persistência</td>
                                <td>Abstrair acesso a dados</td>
                            </tr>
                            <tr>
                                <td><strong>Factory</strong></td>
                                <td>Criação do agente</td>
                                <td>Instâncias configuradas</td>
                            </tr>
                            <tr>
                                <td><strong>Strategy</strong></td>
                                <td>Guardrails</td>
                                <td>Diferentes estratégias de processamento</td>
                            </tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // API
    // ============================================
    'api': {
        title: 'Documentação da API',
        clientNote: 'A API é como uma lista de "comandos" que outros sistemas podem usar para conversar com o nosso. O WhatsApp usa esses comandos para enviar as mensagens dos clientes, e outros sistemas podem verificar se está tudo funcionando.',
        sections: [
            {
                title: 'Visão Geral',
                content: `
                    <p>O Seleto Industrial SDR Agent expõe uma API RESTful construída com FastAPI.</p>
                    <ul>
                        <li><strong>Base URL (Dev):</strong> <code>http://localhost:8000</code></li>
                        <li><strong>Swagger UI:</strong> <code>/docs</code></li>
                        <li><strong>ReDoc:</strong> <code>/redoc</code></li>
                    </ul>
                `
            },
            {
                title: 'Endpoints',
                content: `
                    <h4>Health Check</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Método</th>
                                <th>Path</th>
                                <th>Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>GET</code></td>
                                <td><code>/health</code></td>
                                <td>Verificação básica de saúde</td>
                            </tr>
                            <tr>
                                <td><code>GET</code></td>
                                <td><code>/api/health</code></td>
                                <td>Status detalhado dos serviços</td>
                            </tr>
                        </tbody>
                    </table>

                    <h4>Webhooks (Z-API)</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Método</th>
                                <th>Path</th>
                                <th>Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>POST</code></td>
                                <td><code>/webhook/text</code></td>
                                <td>Mensagens de texto</td>
                            </tr>
                            <tr>
                                <td><code>POST</code></td>
                                <td><code>/webhook/audio</code></td>
                                <td>Mensagens de áudio</td>
                            </tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Payload do Webhook',
                content: `
                    <pre><code>{
  "phone": "5511999999999",
  "senderName": "João Silva",
  "text": {
    "message": "Olá, gostaria de saber mais sobre a FBM100"
  },
  "messageId": "3EB0123456789",
  "type": "ReceivedCallback",
  "fromMe": false,
  "instanceId": "instance-abc123"
}</code></pre>

                    <table>
                        <thead>
                            <tr>
                                <th>Campo</th>
                                <th>Tipo</th>
                                <th>Obrigatório</th>
                                <th>Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>phone</code></td>
                                <td>string</td>
                                <td>Sim</td>
                                <td>Telefone no formato E.164</td>
                            </tr>
                            <tr>
                                <td><code>senderName</code></td>
                                <td>string</td>
                                <td>Não</td>
                                <td>Nome do remetente</td>
                            </tr>
                            <tr>
                                <td><code>text.message</code></td>
                                <td>string</td>
                                <td>Sim</td>
                                <td>Conteúdo da mensagem</td>
                            </tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Exemplos de Uso',
                content: `
                    <h4>cURL - Enviar Mensagem de Texto</h4>
                    <pre><code>curl -X POST http://localhost:8000/webhook/text \\
  -H "Content-Type: application/json" \\
  -d '{
    "phone": "5511999999999",
    "senderName": "João Silva",
    "text": {
      "message": "Olá, quero saber sobre a FBM100"
    }
  }'</code></pre>

                    <h4>cURL - Verificar Saúde</h4>
                    <pre><code>curl http://localhost:8000/api/health</code></pre>
                `
            }
        ]
    },

    // ============================================
    // SERVIÇOS
    // ============================================
    'servicos': {
        title: 'Documentação dos Serviços',
        clientNote: 'Os serviços são como departamentos especializados dentro do sistema. Cada um cuida de uma tarefa específica: um guarda as conversas, outro envia mensagens, outro classifica clientes. Juntos, eles fazem o sistema funcionar de forma organizada e eficiente.',
        sections: [
            {
                title: 'Visão Geral',
                content: `
                    <p>O sistema possui serviços organizados em quatro categorias:</p>
                    <ul>
                        <li><strong>Serviços de Dados</strong> - Persistência e recuperação de informações</li>
                        <li><strong>Serviços de IA</strong> - Processamento inteligente com LLM</li>
                        <li><strong>Serviços de Integração</strong> - Comunicação com sistemas externos</li>
                        <li><strong>Serviços de Negócio</strong> - Regras específicas do domínio</li>
                    </ul>
                `
            },
            {
                title: 'Serviços de Dados',
                content: `
                    <h4>Lead Persistence</h4>
                    <p>Guarda todas as informações dos potenciais clientes.</p>
                    <pre><code>upsert_lead(phone: str, data: dict) → dict | None
get_lead_by_phone(phone: str) → dict | None
persist_lead_data(phone: str, data: dict) → bool</code></pre>

                    <h4>Orcamento Persistence</h4>
                    <p>Guarda pedidos de orçamento vinculados a leads.</p>
                    <pre><code>create_orcamento(lead_id: str, data: dict) → dict | None
get_orcamentos_by_lead(lead_id: str) → list[dict]
update_orcamento(orcamento_id: str, data: dict) → dict | None</code></pre>

                    <h4>Conversation Memory</h4>
                    <p>Cache em memória com sincronização para Supabase.</p>
                    <pre><code>get_conversation_history(phone: str, max_messages: int) → list
add_message(phone: str, role: str, content: str) → None
get_lead_data(phone: str) → dict</code></pre>
                `
            },
            {
                title: 'Serviços de IA',
                content: `
                    <h4>Data Extraction</h4>
                    <p>Extrai dados estruturados das mensagens usando GPT-4o.</p>

                    <h4>Temperature Classification</h4>
                    <p>Classifica leads em quente/morno/frio.</p>

                    <h4>Knowledge Base</h4>
                    <p>Base de conhecimento sobre produtos + guardrails comerciais.</p>
                `
            },
            {
                title: 'Serviços de Integração',
                content: `
                    <h4>WhatsApp Service</h4>
                    <p>Integração com Z-API para envio de mensagens.</p>

                    <h4>Chatwoot Sync</h4>
                    <p>Sincronização de mensagens com interface visual.</p>

                    <h4>Transcription</h4>
                    <p>Transcrição de áudio usando OpenAI Whisper.</p>
                `
            }
        ]
    },

    // ============================================
    // BANCO DE DADOS
    // ============================================
    'banco-de-dados': {
        title: 'Banco de Dados',
        clientNote: 'O banco de dados é onde todas as informações ficam guardadas de forma segura. Pense nele como um grande arquivo digital que guarda os dados de cada cliente, cada conversa, cada pedido de orçamento. Usamos o Supabase, uma tecnologia moderna e segura baseada na nuvem.',
        sections: [
            {
                title: 'Tabelas',
                content: `
                    <table>
                        <thead>
                            <tr>
                                <th>Tabela</th>
                                <th>Propósito</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>leads</code></td>
                                <td>Dados de potenciais clientes</td>
                            </tr>
                            <tr>
                                <td><code>orcamentos</code></td>
                                <td>Pedidos de orçamento</td>
                            </tr>
                            <tr>
                                <td><code>empresa</code></td>
                                <td>Informações de empresas</td>
                            </tr>
                            <tr>
                                <td><code>conversations</code></td>
                                <td>Histórico de mensagens</td>
                            </tr>
                            <tr>
                                <td><code>conversation_context</code></td>
                                <td>Contexto adicional (chave-valor)</td>
                            </tr>
                            <tr>
                                <td><code>technical_questions</code></td>
                                <td>Perguntas técnicas para engenharia</td>
                            </tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Tabela: leads',
                content: `
                    <table>
                        <thead>
                            <tr>
                                <th>Coluna</th>
                                <th>Tipo</th>
                                <th>Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><code>id</code></td><td>uuid</td><td>Identificador único</td></tr>
                            <tr><td><code>phone</code></td><td>varchar</td><td>Telefone (UNIQUE)</td></tr>
                            <tr><td><code>name</code></td><td>varchar</td><td>Nome completo</td></tr>
                            <tr><td><code>email</code></td><td>varchar</td><td>E-mail</td></tr>
                            <tr><td><code>city</code></td><td>varchar</td><td>Cidade</td></tr>
                            <tr><td><code>uf</code></td><td>varchar(2)</td><td>Estado</td></tr>
                            <tr><td><code>product</code></td><td>varchar</td><td>Produto de interesse</td></tr>
                            <tr><td><code>volume</code></td><td>varchar</td><td>Volume estimado</td></tr>
                            <tr><td><code>urgency</code></td><td>varchar</td><td>Nível de urgência</td></tr>
                            <tr><td><code>temperature</code></td><td>varchar</td><td>Classificação</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Normalização de Dados',
                content: `
                    <h4>Telefone (E.164)</h4>
                    <table>
                        <thead>
                            <tr><th>Input</th><th>Output</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><code>(11) 99999-9999</code></td><td><code>5511999999999</code></td></tr>
                            <tr><td><code>11999999999</code></td><td><code>5511999999999</code></td></tr>
                            <tr><td><code>+55 11 99999-9999</code></td><td><code>5511999999999</code></td></tr>
                        </tbody>
                    </table>

                    <h4>CNPJ</h4>
                    <table>
                        <thead>
                            <tr><th>Input</th><th>Output</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><code>12.345.678/0001-90</code></td><td><code>12345678000190</code></td></tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // INTEGRAÇÕES
    // ============================================
    'integracoes': {
        title: 'Integrações Externas',
        clientNote: 'O sistema não trabalha sozinho - ele se conecta com vários outros serviços para funcionar. É como uma equipe onde cada membro tem uma especialidade: um cuida do WhatsApp, outro da inteligência artificial, outro do banco de dados.',
        sections: [
            {
                title: 'Visão Geral',
                content: `
                    <table>
                        <thead>
                            <tr>
                                <th>Integração</th>
                                <th>Propósito</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><strong>Z-API</strong></td><td>WhatsApp (envio/recebimento)</td><td>✅ Implementado</td></tr>
                            <tr><td><strong>OpenAI</strong></td><td>IA (GPT-4o + Whisper)</td><td>✅ Implementado</td></tr>
                            <tr><td><strong>Supabase</strong></td><td>Banco de dados</td><td>✅ Implementado</td></tr>
                            <tr><td><strong>Chatwoot</strong></td><td>Interface de chat</td><td>✅ Implementado</td></tr>
                            <tr><td><strong>PipeRun</strong></td><td>CRM</td><td>📋 Planejado</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Z-API (WhatsApp)',
                content: `
                    <p>O Z-API é o "carteiro" do sistema. Ele recebe as mensagens do WhatsApp e entrega para nós.</p>

                    <h4>Configuração</h4>
                    <pre><code>ZAPI_INSTANCE_ID=sua-instancia-id
ZAPI_INSTANCE_TOKEN=seu-token-de-instancia
ZAPI_CLIENT_TOKEN=seu-client-token</code></pre>

                    <h4>Webhooks no Painel Z-API</h4>
                    <table>
                        <thead>
                            <tr><th>Webhook</th><th>URL</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Received</td><td><code>https://seu-servidor/webhook/text</code></td></tr>
                            <tr><td>ReceivedAudio</td><td><code>https://seu-servidor/webhook/audio</code></td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'OpenAI',
                content: `
                    <p>A OpenAI é a empresa por trás do ChatGPT. Usamos a mesma tecnologia para que o sistema consiga entender e responder as mensagens.</p>

                    <h4>Serviços Utilizados</h4>
                    <table>
                        <thead>
                            <tr><th>Serviço</th><th>Modelo</th><th>Uso</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Chat Completion</td><td>GPT-4o</td><td>Respostas do agente</td></tr>
                            <tr><td>Whisper</td><td>whisper-1</td><td>Transcrição de áudio</td></tr>
                        </tbody>
                    </table>

                    <h4>Configuração</h4>
                    <pre><code>OPENAI_API_KEY=sk-sua-chave-api
OPENAI_MODEL=gpt-4o</code></pre>
                `
            },
            {
                title: 'Supabase',
                content: `
                    <p>O Supabase é onde todos os dados ficam guardados na nuvem.</p>

                    <h4>Configuração</h4>
                    <pre><code>SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...sua-chave...</code></pre>
                `
            }
        ]
    },

    // ============================================
    // AGENTE SDR
    // ============================================
    'agente-sdr': {
        title: 'Agente SDR',
        clientNote: 'O Agente SDR é o "vendedor virtual" do sistema. Ele conversa com os clientes pelo WhatsApp de forma natural e inteligente, coleta informações importantes, e classifica cada lead pelo potencial de compra. Funciona 24 horas por dia, 7 dias por semana, sem pausa para café!',
        sections: [
            {
                title: 'O que é um SDR?',
                content: `
                    <p><strong>SDR (Sales Development Representative)</strong> é um profissional de vendas responsável por:</p>
                    <ul>
                        <li>Fazer primeiro contato com potenciais clientes</li>
                        <li>Qualificar leads (avaliar potencial de compra)</li>
                        <li>Coletar informações importantes</li>
                        <li>Encaminhar leads qualificados para vendedores</li>
                    </ul>
                    <p>O <strong>Agente SDR</strong> automatiza essas tarefas usando Inteligência Artificial.</p>
                `
            },
            {
                title: 'Classificação de Temperatura',
                content: `
                    <p>A "temperatura" indica o quão próximo de comprar o cliente está.</p>

                    <table>
                        <thead>
                            <tr>
                                <th>Temperatura</th>
                                <th>Significado</th>
                                <th>Ação</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>🔥 <strong>Quente</strong></td>
                                <td>Pronto para comprar</td>
                                <td>Prioridade para vendedor</td>
                            </tr>
                            <tr>
                                <td>🌡️ <strong>Morno</strong></td>
                                <td>Interessado, precisa mais info</td>
                                <td>Continuar qualificando</td>
                            </tr>
                            <tr>
                                <td>❄️ <strong>Frio</strong></td>
                                <td>Apenas pesquisando</td>
                                <td>Nutrir com conteúdo</td>
                            </tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Guardrails (Proteções)',
                content: `
                    <p>Guardrails são "cercas de proteção" que impedem o agente de falar sobre assuntos sensíveis.</p>

                    <h4>Guardrail Comercial</h4>
                    <p>Palavras detectadas: preço, valor, custo, orçamento, desconto, promoção, parcelamento, prazo de entrega, frete, proposta, negociar</p>

                    <h4>Guardrail Técnico</h4>
                    <p>Palavras detectadas: diagrama elétrico, voltagem, amperagem, especificação técnica detalhada, calibração</p>
                `
            },
            {
                title: 'Coleta de Dados',
                content: `
                    <p>O agente coleta informações progressivamente, de forma natural na conversa.</p>

                    <table>
                        <thead>
                            <tr><th>Campo</th><th>Descrição</th><th>Exemplo</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><code>name</code></td><td>Nome completo</td><td>"João Silva"</td></tr>
                            <tr><td><code>company</code></td><td>Nome da empresa</td><td>"ABC Foods"</td></tr>
                            <tr><td><code>city</code></td><td>Cidade</td><td>"São Paulo"</td></tr>
                            <tr><td><code>uf</code></td><td>Estado</td><td>"SP"</td></tr>
                            <tr><td><code>product</code></td><td>Produto de interesse</td><td>"FBM100"</td></tr>
                            <tr><td><code>volume</code></td><td>Volume estimado</td><td>"500kg/dia"</td></tr>
                            <tr><td><code>urgency</code></td><td>Urgência</td><td>"preciso em 15 dias"</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Upsell (FBM100 → FB300)',
                content: `
                    <p>Quando identificamos que o cliente pode se beneficiar de um produto melhor, sugerimos de forma natural.</p>

                    <table>
                        <thead>
                            <tr><th>FBM100 (Manual)</th><th>FB300 (Semi-automática)</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Operação manual</td><td>Semi-automática</td></tr>
                            <tr><td>~200 unid/hora</td><td>~800 unid/hora</td></tr>
                            <tr><td>Menor investimento</td><td>Maior produtividade</td></tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // TESTES
    // ============================================
    'testes': {
        title: 'Testes',
        clientNote: 'Testes são como "inspeções de qualidade" que garantem que o sistema funciona corretamente. Toda vez que fazemos uma mudança, rodamos centenas de testes automáticos para ter certeza de que nada quebrou.',
        sections: [
            {
                title: 'Estrutura de Testes',
                content: `
                    <div class="diagram">tests/
├── conftest.py              # Fixtures compartilhadas
├── test_integration_flow.py # Testes de integração
├── agents/                  # Testes do agente SDR
├── api/                     # Testes de API
└── services/                # Testes de serviços</div>
                `
            },
            {
                title: 'Comandos de Teste',
                content: `
                    <h4>Rodar Todos os Testes</h4>
                    <pre><code># Ativar ambiente virtual
.\\venv\\Scripts\\activate  # Windows

# Rodar todos os testes
pytest tests/ -v</code></pre>

                    <h4>Rodar com Cobertura</h4>
                    <pre><code>pytest tests/ -v --cov=src --cov-report=html</code></pre>

                    <h4>Rodar Testes Específicos</h4>
                    <pre><code># Um arquivo específico
pytest tests/services/test_lead_crud.py -v

# Uma classe específica
pytest tests/services/test_lead_crud.py::TestLeadCRUD -v

# Testes por padrão de nome
pytest tests/ -v -k "lead"</code></pre>
                `
            },
            {
                title: 'Categorias de Testes',
                content: `
                    <table>
                        <thead>
                            <tr><th>Categoria</th><th>Descrição</th><th>Exemplo</th></tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Unitários</strong></td>
                                <td>Testam funções individuais</td>
                                <td>Normalização de telefone</td>
                            </tr>
                            <tr>
                                <td><strong>Serviço</strong></td>
                                <td>Testam serviços completos</td>
                                <td>CRUD de leads</td>
                            </tr>
                            <tr>
                                <td><strong>API</strong></td>
                                <td>Testam endpoints HTTP</td>
                                <td>Webhook de texto</td>
                            </tr>
                            <tr>
                                <td><strong>Integração</strong></td>
                                <td>Testam fluxo completo</td>
                                <td>Mensagem → Resposta</td>
                            </tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // DEPLOY
    // ============================================
    'deploy': {
        title: 'Deploy e Configuração',
        clientNote: 'Este documento explica como colocar o sistema para funcionar em um servidor. É como "ligar" o sistema e deixá-lo disponível 24 horas. Existem diferentes formas de fazer isso, desde a mais simples até a mais robusta.',
        sections: [
            {
                title: 'Opções de Deploy',
                content: `
                    <table>
                        <thead>
                            <tr><th>Método</th><th>Complexidade</th><th>Uso Recomendado</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Local</td><td>Baixa</td><td>Testes e desenvolvimento</td></tr>
                            <tr><td>Docker</td><td>Média</td><td>Staging e produção</td></tr>
                            <tr><td>Cloud (Railway, Render)</td><td>Baixa</td><td>Produção simplificada</td></tr>
                            <tr><td>Kubernetes</td><td>Alta</td><td>Produção escalável</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Deploy Local',
                content: `
                    <pre><code># 1. Clone o repositório
git clone &lt;url-do-repositorio&gt;
cd seleto_industrial

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente
.\\venv\\Scripts\\activate  # Windows

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure variáveis de ambiente
cp .env.example .env

# 6. Execute o servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000</code></pre>
                `
            },
            {
                title: 'Deploy com Docker',
                content: `
                    <pre><code># Construir imagem
docker-compose build

# Iniciar em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down</code></pre>
                `
            },
            {
                title: 'Deploy em Cloud',
                content: `
                    <h4>Railway</h4>
                    <ol>
                        <li>Acesse railway.app</li>
                        <li>Crie conta com GitHub</li>
                        <li>"New Project" → "Deploy from GitHub repo"</li>
                        <li>Configure variáveis de ambiente</li>
                        <li>Deploy automático!</li>
                    </ol>

                    <h4>Render</h4>
                    <ol>
                        <li>Acesse render.com</li>
                        <li>"New" → "Web Service"</li>
                        <li>Conecte repositório GitHub</li>
                        <li>Configure Build e Start commands</li>
                        <li>Adicione variáveis de ambiente</li>
                    </ol>
                `
            }
        ]
    },

    // ============================================
    // SEGURANÇA
    // ============================================
    'seguranca': {
        title: 'Segurança',
        clientNote: 'A segurança é uma prioridade máxima. Seus dados e os dados de seus clientes são protegidos por múltiplas camadas de segurança.',
        sections: [
            {
                title: 'Camadas de Segurança',
                content: `
                    <div class="diagram">┌─────────────────────────────────────────┐
│  🔒 Transporte (HTTPS/TLS)              │
├─────────────────────────────────────────┤
│  🔑 Autenticação (API Keys, Tokens)     │
├─────────────────────────────────────────┤
│  🛡️ Autorização (RLS, Permissões)       │
├─────────────────────────────────────────┤
│  📝 Validação (Input, Sanitização)      │
├─────────────────────────────────────────┤
│  🔐 Criptografia (Dados em repouso)     │
├─────────────────────────────────────────┤
│  📊 Auditoria (Logs, Monitoramento)     │
└─────────────────────────────────────────┘</div>
                `
            },
            {
                title: 'Gestão de Credenciais',
                content: `
                    <ul>
                        <li><strong>Nunca no código</strong> - Credenciais via variáveis de ambiente</li>
                        <li><strong>Nunca no git</strong> - .env sempre no .gitignore</li>
                        <li><strong>Mínimo privilégio</strong> - Cada serviço tem apenas permissões necessárias</li>
                        <li><strong>Rotação regular</strong> - Trocar chaves periodicamente</li>
                    </ul>
                `
            },
            {
                title: 'Segurança de XML',
                content: `
                    <p>Os arquivos de prompt são carregados com medidas de segurança:</p>
                    <ul>
                        <li><strong>Path Traversal Prevention</strong> - Não permite ../ nos caminhos</li>
                        <li><strong>XXE Protection</strong> - Parser XML configurado de forma segura</li>
                        <li><strong>Directory Restriction</strong> - Só carrega de prompts/system_prompt/</li>
                    </ul>
                `
            },
            {
                title: 'Checklist de Segurança',
                content: `
                    <ul>
                        <li>☐ <code>.env</code> não está no git</li>
                        <li>☐ <code>DEBUG=false</code> em produção</li>
                        <li>☐ HTTPS configurado</li>
                        <li>☐ Variáveis de ambiente validadas</li>
                        <li>☐ RLS habilitado no Supabase</li>
                        <li>☐ Logs não expõem dados sensíveis</li>
                    </ul>
                `
            }
        ]
    },

    // ============================================
    // TROUBLESHOOTING
    // ============================================
    'troubleshooting': {
        title: 'Troubleshooting',
        clientNote: 'Este guia ajuda a resolver os problemas mais comuns que podem acontecer com o sistema. Pense nele como um "manual de primeiros socorros" - antes de chamar o suporte, consulte aqui.',
        sections: [
            {
                title: 'Diagnóstico Rápido',
                content: `
                    <pre><code># Verificar se o servidor responde
curl http://localhost:8000/health

# Verificar status detalhado
curl http://localhost:8000/api/health</code></pre>

                    <p>✅ Sistema OK: <code>{"status": "healthy"}</code></p>
                    <p>❌ Sistema com problemas: <code>{"status": "unhealthy"}</code></p>
                `
            },
            {
                title: 'Problemas Comuns',
                content: `
                    <h4>Servidor não inicia</h4>
                    <table>
                        <thead><tr><th>Causa</th><th>Solução</th></tr></thead>
                        <tbody>
                            <tr><td>Ambiente virtual não ativado</td><td><code>.\\venv\\Scripts\\activate</code></td></tr>
                            <tr><td>Dependências não instaladas</td><td><code>pip install -r requirements.txt</code></td></tr>
                            <tr><td>Porta em uso</td><td>Usar outra porta: <code>--port 8001</code></td></tr>
                            <tr><td>Variável de ambiente faltando</td><td>Verificar <code>.env</code></td></tr>
                        </tbody>
                    </table>

                    <h4>Erro de conexão com Supabase</h4>
                    <table>
                        <thead><tr><th>Erro</th><th>Solução</th></tr></thead>
                        <tbody>
                            <tr><td>Invalid URL</td><td>Verificar SUPABASE_URL</td></tr>
                            <tr><td>Invalid API key</td><td>Verificar SUPABASE_SERVICE_ROLE_KEY</td></tr>
                            <tr><td>Connection timeout</td><td>Verificar firewall/proxy</td></tr>
                        </tbody>
                    </table>

                    <h4>Erro de API OpenAI</h4>
                    <table>
                        <thead><tr><th>Erro</th><th>Solução</th></tr></thead>
                        <tbody>
                            <tr><td>401 Unauthorized</td><td>API Key inválida ou expirada</td></tr>
                            <tr><td>429 Too Many Requests</td><td>Rate limit - aguarde</td></tr>
                            <tr><td>500 Internal Error</td><td>Problema na OpenAI - aguarde</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Onde ver os logs',
                content: `
                    <table>
                        <thead><tr><th>Ambiente</th><th>Comando</th></tr></thead>
                        <tbody>
                            <tr><td>Local</td><td>Terminal onde o servidor roda</td></tr>
                            <tr><td>Docker</td><td><code>docker-compose logs -f</code></td></tr>
                            <tr><td>Railway</td><td>Dashboard → Logs</td></tr>
                            <tr><td>Render</td><td>Dashboard → Logs</td></tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // ESTRUTURA DE PASTAS
    // ============================================
    'estrutura-pastas': {
        title: 'Estrutura de Pastas',
        clientNote: 'Esta página mostra como o código está organizado. Pense nas pastas como gavetas de um arquivo - cada uma guarda um tipo específico de documento.',
        sections: [
            {
                title: 'Visão Geral',
                content: `
                    <div class="diagram">seleto_industrial/
│
├── 📁 src/                      # Código fonte principal
│   ├── 📁 agents/               # Agentes de IA
│   ├── 📁 api/                  # Endpoints HTTP
│   ├── 📁 config/               # Configurações
│   ├── 📁 services/             # Lógica de negócio
│   └── 📁 utils/                # Utilitários
│
├── 📁 tests/                    # Testes automatizados
│
├── 📁 prompts/                  # Prompts do agente IA
│
├── 📁 docs/                     # Documentação Markdown
│
├── 📁 docs-web/                 # Esta documentação web
│
├── 📄 requirements.txt          # Dependências Python
├── 📄 Dockerfile               # Configuração Docker
└── 📄 docker-compose.yml       # Orquestração Docker</div>
                `
            },
            {
                title: 'Navegação Rápida',
                content: `
                    <table>
                        <thead><tr><th>Preciso modificar...</th><th>Onde encontrar</th></tr></thead>
                        <tbody>
                            <tr><td>Endpoint de webhook</td><td><code>src/api/routes/webhook.py</code></td></tr>
                            <tr><td>Lógica do agente</td><td><code>src/agents/sdr_agent.py</code></td></tr>
                            <tr><td>Como leads são salvos</td><td><code>src/services/lead_persistence.py</code></td></tr>
                            <tr><td>Prompt do agente</td><td><code>prompts/system_prompt/sp_agente_v1.xml</code></td></tr>
                            <tr><td>Configurações</td><td><code>src/config/settings.py</code></td></tr>
                            <tr><td>Conexão com WhatsApp</td><td><code>src/services/whatsapp.py</code></td></tr>
                        </tbody>
                    </table>
                `
            }
        ]
    },

    // ============================================
    // VARIÁVEIS DE AMBIENTE
    // ============================================
    'variaveis-ambiente': {
        title: 'Variáveis de Ambiente',
        clientNote: 'As variáveis de ambiente são como "configurações secretas" do sistema. Elas guardam senhas, chaves de acesso e outras informações que não podem ficar visíveis no código.',
        sections: [
            {
                title: 'Configuração Inicial',
                content: `
                    <pre><code># Copiar o exemplo
cp .env.example .env

# Editar com suas credenciais
code .env</code></pre>
                `
            },
            {
                title: 'Variáveis Obrigatórias',
                content: `
                    <table>
                        <thead><tr><th>Variável</th><th>Descrição</th></tr></thead>
                        <tbody>
                            <tr><td><code>OPENAI_API_KEY</code></td><td>Chave da API OpenAI</td></tr>
                            <tr><td><code>SUPABASE_URL</code></td><td>URL do projeto Supabase</td></tr>
                            <tr><td><code>SUPABASE_SERVICE_ROLE_KEY</code></td><td>Chave de serviço Supabase</td></tr>
                        </tbody>
                    </table>
                `
            },
            {
                title: 'Variáveis Opcionais',
                content: `
                    <h4>Z-API (WhatsApp)</h4>
                    <pre><code>ZAPI_INSTANCE_ID=sua-instancia
ZAPI_INSTANCE_TOKEN=seu-token
ZAPI_CLIENT_TOKEN=seu-client-token</code></pre>

                    <h4>Chatwoot</h4>
                    <pre><code>CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=seu-token
CHATWOOT_ACCOUNT_ID=12345</code></pre>

                    <h4>Aplicação</h4>
                    <pre><code>APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO</code></pre>
                `
            }
        ]
    },

    // ============================================
    // GLOSSÁRIO
    // ============================================
    'glossario': {
        title: 'Glossário',
        clientNote: 'Este glossário explica os termos técnicos usados na documentação de forma simples. Se você encontrar uma palavra que não entende, provavelmente ela está aqui!',
        sections: [
            {
                title: 'A-C',
                content: `
                    <p><strong>Agente (Agent)</strong> - Um programa de computador que age de forma autônoma para realizar tarefas.</p>
                    <p><strong>API</strong> - "Interface de Programação". É como um "cardápio" que lista o que um sistema pode fazer.</p>
                    <p><strong>API Key</strong> - Uma "senha especial" que identifica quem está usando um serviço.</p>
                    <p><strong>Async</strong> - Forma de programação onde o sistema não precisa esperar uma tarefa terminar para começar outra.</p>
                    <p><strong>Cache</strong> - Armazenamento temporário de dados para acesso rápido.</p>
                    <p><strong>Container</strong> - Uma "caixa" que contém todo o software necessário para rodar uma aplicação.</p>
                    <p><strong>CRM</strong> - Sistema de gestão de relacionamento com cliente.</p>
                    <p><strong>CRUD</strong> - Create, Read, Update, Delete - as quatro operações básicas com dados.</p>
                `
            },
            {
                title: 'D-L',
                content: `
                    <p><strong>Deploy</strong> - O processo de colocar um sistema para funcionar em um servidor.</p>
                    <p><strong>Docker</strong> - Tecnologia para criar e rodar containers.</p>
                    <p><strong>E.164</strong> - Formato padrão internacional para números de telefone.</p>
                    <p><strong>Endpoint</strong> - Um "ponto de acesso" em uma API.</p>
                    <p><strong>Framework</strong> - Conjunto de ferramentas pré-definidas que facilitam criar software.</p>
                    <p><strong>Guardrails</strong> - "Cercas de proteção" - regras que limitam o que o sistema pode fazer.</p>
                    <p><strong>Lead</strong> - Potencial cliente que demonstrou interesse em comprar.</p>
                    <p><strong>LLM</strong> - "Modelo de Linguagem Grande". IA que entende e gera linguagem natural.</p>
                `
            },
            {
                title: 'M-S',
                content: `
                    <p><strong>Mock</strong> - Simulação de algo real para testes.</p>
                    <p><strong>Normalização</strong> - Padronizar dados para um formato consistente.</p>
                    <p><strong>Payload</strong> - Os dados enviados em uma requisição.</p>
                    <p><strong>Prompt</strong> - Instruções dadas para uma IA.</p>
                    <p><strong>Rate Limiting</strong> - Limite de quantas requisições um sistema aceita por período.</p>
                    <p><strong>RLS</strong> - Row Level Security - segurança em nível de linha no banco de dados.</p>
                    <p><strong>SDR</strong> - Sales Development Representative - profissional de qualificação de leads.</p>
                `
            },
            {
                title: 'T-Z',
                content: `
                    <p><strong>Temperatura (de Lead)</strong> - Classificação do potencial de compra: quente, morno ou frio.</p>
                    <p><strong>Token</strong> - Unidade de texto para IA, ou chave de autenticação.</p>
                    <p><strong>Upsell</strong> - Sugerir um produto melhor/mais caro.</p>
                    <p><strong>UUID</strong> - Identificador único universal.</p>
                    <p><strong>Webhook</strong> - Quando um sistema avisa outro que algo aconteceu.</p>
                    <p><strong>Whisper</strong> - Modelo da OpenAI para transcrição de áudio em texto.</p>
                    <p><strong>Z-API</strong> - Serviço brasileiro que conecta sistemas ao WhatsApp.</p>
                `
            }
        ]
    }
};
