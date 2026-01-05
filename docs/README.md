# Seleto Industrial SDR Agent - Documentação

> **Para o Cliente:** Este sistema é um assistente virtual inteligente que atende seus clientes pelo WhatsApp. Ele qualifica leads automaticamente, responde dúvidas sobre produtos e coleta informações importantes para sua equipe de vendas. Pense nele como um vendedor digital que trabalha 24 horas por dia, 7 dias por semana.

---

## 📋 Índice

### Visão Geral
- [Introdução](#introdução)
- [O que o sistema faz](#o-que-o-sistema-faz)
- [Tecnologias utilizadas](#tecnologias-utilizadas)

### Documentação Técnica
| Documento | Descrição |
|-----------|-----------|
| [Arquitetura](./arquitetura.md) | Estrutura geral do sistema e componentes |
| [API](./api.md) | Endpoints disponíveis e como utilizá-los |
| [Serviços](./servicos.md) | Detalhamento de cada serviço do sistema |
| [Banco de Dados](./banco-de-dados.md) | Estrutura das tabelas e relacionamentos |
| [Integrações](./integracoes.md) | WhatsApp, CRM, Chatwoot e outras |
| [Agente SDR](./agente-sdr.md) | Como funciona a inteligência artificial |
| [Testes](./testes.md) | Como executar e criar testes |
| [Deploy](./deploy.md) | Como colocar em produção |
| [Segurança](./seguranca.md) | Medidas de proteção implementadas |
| [Troubleshooting](./troubleshooting.md) | Solução de problemas comuns |

### Guias Rápidos
| Guia | Descrição |
|------|-----------|
| [Estrutura de Pastas](./estrutura-pastas.md) | Organização do código |
| [Variáveis de Ambiente](./variaveis-ambiente.md) | Configurações necessárias |
| [Glossário](./glossario.md) | Termos técnicos explicados |

---

## Introdução

> **Para o Cliente:** O Seleto Industrial SDR Agent é como ter um funcionário dedicado que nunca dorme. Ele conversa com seus potenciais clientes pelo WhatsApp, entende o que eles precisam, e organiza tudo para sua equipe de vendas entrar em ação no momento certo.

O **Seleto Industrial SDR Agent** é um agente de inteligência artificial projetado para automatizar o processo de qualificação de leads via WhatsApp para a Seleto Industrial, fabricante de máquinas para indústria alimentícia.

### Principais Funcionalidades

1. **Atendimento Automatizado pelo WhatsApp**
   - Recebe mensagens de texto e áudio
   - Responde de forma natural e contextualizada
   - Disponível 24/7

2. **Qualificação Inteligente de Leads**
   - Coleta informações importantes progressivamente
   - Classifica leads por "temperatura" (quente, morno, frio)
   - Identifica oportunidades de venda

3. **Gestão do Conhecimento**
   - Base de informações sobre produtos
   - Respostas consistentes sobre especificações
   - Encaminha questões técnicas avançadas

4. **Integrações Empresariais**
   - Sincronização com CRM (PipeRun)
   - Interface visual (Chatwoot)
   - Persistência de dados (Supabase)

---

## O que o sistema faz

> **Para o Cliente:** Imagine o seguinte cenário: um cliente manda uma mensagem às 22h perguntando sobre a máquina de hambúrguer. O sistema responde imediatamente, pergunta sobre o volume de produção dele, a cidade onde fica, e vai coletando informações. Quando sua equipe chegar pela manhã, já tem um lead qualificado esperando no sistema com todas as informações organizadas.

### Fluxo Principal

```
Cliente envia mensagem no WhatsApp
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
    Salva conversa e dados no banco
```

### Funcionalidades Específicas

| Funcionalidade | O que faz | Exemplo |
|---------------|-----------|---------|
| **Coleta de Dados** | Extrai informações das mensagens | "Sou de São Paulo" → salva cidade=SP |
| **Classificação de Leads** | Avalia potencial de compra | Cliente com urgência alta = lead "quente" |
| **Upsell** | Sugere produtos melhores | Interesse em FBM100 → sugere FB300 |
| **Guardrails** | Evita discussões sensíveis | Não discute preços, encaminha para vendas |
| **Produtos Indisponíveis** | Gerencia expectativas | Espetos → informa previsão de disponibilidade |

---

## Tecnologias Utilizadas

> **Para o Cliente:** O sistema usa as tecnologias mais modernas do mercado para garantir velocidade, segurança e inteligência. A IA é a mesma tecnologia usada pelo ChatGPT, e os dados ficam protegidos em servidores seguros na nuvem.

### Stack Principal

| Tecnologia | Uso | Por que escolhemos |
|------------|-----|-------------------|
| **Python 3.12** | Linguagem principal | Madura, vasta comunidade, ótima para IA |
| **FastAPI** | Framework web | Rápido, moderno, documentação automática |
| **Agno Framework** | Orquestração de IA | Especializado em agentes inteligentes |
| **OpenAI GPT-4o** | Inteligência Artificial | Melhor modelo de linguagem disponível |
| **Supabase** | Banco de dados | PostgreSQL gerenciado, tempo real, seguro |
| **Z-API** | WhatsApp | Integração estável e confiável |
| **Docker** | Containerização | Deploy consistente em qualquer ambiente |

### Integrações

| Sistema | Propósito |
|---------|-----------|
| **WhatsApp (Z-API)** | Receber e enviar mensagens |
| **Supabase** | Armazenar conversas e dados de leads |
| **Chatwoot** | Interface visual para atendentes |
| **PipeRun** | CRM para gestão de oportunidades |
| **OpenAI** | Processamento de linguagem natural |

---

## Começando Rapidamente

### Pré-requisitos

- Python 3.12+
- Conta no Supabase
- Chave de API da OpenAI
- (Opcional) Conta Z-API para WhatsApp

### Instalação

```bash
# 1. Clone o repositório
git clone <repo-url>
cd seleto_industrial

# 2. Crie ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Execute o servidor
uvicorn src.main:app --reload
```

### Verificando a Instalação

Acesse: `http://localhost:8000/docs` para ver a documentação interativa da API.

---

## Estrutura do Projeto

```
seleto_industrial/
├── src/                    # Código fonte principal
│   ├── agents/            # Agente de IA
│   ├── api/               # Endpoints da API
│   ├── config/            # Configurações
│   ├── services/          # Lógica de negócio
│   └── utils/             # Utilitários
├── tests/                  # Testes automatizados
├── prompts/               # Prompts do agente IA
├── docs/                  # Esta documentação
└── documentation/         # Documentação do produto
```

Para mais detalhes, consulte [Estrutura de Pastas](./estrutura-pastas.md).

---

## Suporte e Contato

Para questões técnicas ou suporte:
- Consulte o [Troubleshooting](./troubleshooting.md)
- Abra uma issue no repositório
- Entre em contato com a equipe de desenvolvimento

---

## Próximos Passos

1. **Desenvolvedores**: Comece pela [Arquitetura](./arquitetura.md)
2. **DevOps**: Veja o guia de [Deploy](./deploy.md)
3. **QA**: Consulte a documentação de [Testes](./testes.md)
4. **Gestores**: Leia sobre as [Integrações](./integracoes.md)

---

*Documentação gerada em Janeiro de 2026*
