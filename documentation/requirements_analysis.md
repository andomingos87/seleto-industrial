## **1. Visão Geral**

O sistema consiste em um **agente de inteligência artificial** conectado ao **WhatsApp Business API** e ao **CRM Piperun**, executado como um serviço em **Agno (Agent Framework + AgentOS Runtime em Python/FastAPI)** e interface de atendimento via **Chatwoot** (ambos em VPS própria).

O objetivo é automatizar o **atendimento inicial e a qualificação de leads**, mantendo o SDR como operador humano via Chatwoot.

---

## **2. Escopo do Projeto**

- Desenvolvimento de um **agente de IA** capaz de:
    - Atender leads via WhatsApp (API oficial).
    - Coletar informações específicas do lead.
    - Responder dúvidas sobre produtos e serviços.
    - Classificar o lead (quente, morno, frio) com base em regras fixas.
    - Enviar automaticamente os dados coletados ao CRM Piperun via API REST.
- O sistema **não incluirá painel web administrativo nem envio de notificações.**

---

## **3. Requisitos Funcionais**

| Código | Requisito | Descrição |
| --- | --- | --- |
| RF-01 | Atendimento automático via WhatsApp | O agente inicia e mantém conversas com novos leads através da API oficial. |
| RF-02 | Coleta de dados | O agente deve capturar informações: nome, e-mail, telefone, produto de interesse, volume diário, urgência e segmento. |
| RF-03 | Consulta à base de conhecimento | O agente responde dúvidas sobre produtos com base em uma base de dados local ou planilha estruturada. |
| RF-04 | Classificação de leads | O sistema deve classificar leads conforme regras fixas de volume e urgência. |
| RF-05 | Envio ao CRM Piperun | Após coletar dados, o agente envia um POST JSON para a API Piperun criando Lead e Oportunidade. |
| RF-06 | Registro de conversas | Todas as interações são armazenadas e visualizadas no Chatwoot. |
| RF-07 | Intervenção manual | O SDR pode assumir o atendimento no Chatwoot quando necessário. |

---

## **4. Requisitos Não Funcionais**

| Código | Requisito | Descrição |
| --- | --- | --- |
| RNF-01 | Desempenho | As respostas do agente devem ocorrer em até 5 segundos. |
| RNF-02 | Disponibilidade | O sistema deve operar 24/7, com reinício automático em caso de falha da VPS. |
| RNF-03 | Segurança | Dados sensíveis (nome, telefone, e-mail) devem trafegar via HTTPS. |
| RNF-04 | Escalabilidade | A arquitetura deve suportar múltiplas instâncias de Chatwoot e múltiplas rotas/workflows no runtime (Agno/AgentOS). |
| RNF-05 | Confiabilidade | O agente deve registrar logs de erros e requisições no runtime (Agno/AgentOS) para auditoria. |

---

## **5. Integrações**

| Sistema | Tipo | Descrição |
| --- | --- | --- |
| **WhatsApp Business API (Oficial)** | Entrada | Canal de comunicação com o usuário. |
| **Chatwoot (Self-Hosted)** | Interface | Painel onde o SDR acompanha e interage. |
| **Agno (AgentOS Runtime)** | Orquestração/Runtime | Hospeda o agente (FastAPI), gerencia sessões, executa tools e integrações (CRM/DB/Chatwoot). |
| **CRM Piperun** | Saída | Recebe dados via POST JSON (Lead + Oportunidade). |

---

## **6. Regras de Negócio**

| Código | Regra | Critério |
| --- | --- | --- |
| RN-01 | Lead Quente |  |
| RN-02 | Lead Morno |  |
| RN-03 | Lead Frio |  |
| RN-04 | Persistência de Dados |  |
| RN-05 | Atendimento humano |  |

---

## **7. Perfis de Usuário**

| Perfil | Descrição | Permissões |
| --- | --- | --- |
| **Lead** | Usuário final que interage via WhatsApp. | Envia mensagens e fornece dados. |
| **Agente de IA** | Sistema automatizado que conduz o diálogo. | Coleta e envia informações. |
| **SDR** | Operador humano que acompanha e intervém via Chatwoot. | Visualiza conversas e assume atendimentos. |
| **Administrador Técnico** | Responsável pela VPS e manutenção do runtime do Agno (AgentOS) e integrações. | Gerencia ambiente e logs. |

---

## **8. Ambiente e Tecnologias**

- **Servidor:** VPS Linux (Dockerized)
- **Runtime/Orquestração:** Agno (Agent Framework + AgentOS Runtime em Python/FastAPI)
- **Atendimento:** Chatwoot Self-Hosted
- **CRM:** Piperun API
- **IA:** Modelo de linguagem (OpenAI ou alternativo)
- **Banco de conhecimento:** Base local estruturada (CSV, planilha ou banco SQL leve)

---