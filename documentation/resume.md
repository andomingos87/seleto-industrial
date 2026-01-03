## **1. Visão Geral do Sistema**

O objetivo é desenvolver um **agente de IA** integrado à **API Oficial do WhatsApp** e ao **CRM Pipedrive/Piperun**.

Esse agente realizará o **atendimento inicial**, **qualificação de leads** e **criação automática de oportunidades** no CRM.

---

## **2. Componentes Principais**

| Componente | Função |
| --- | --- |
| **Agente de IA** | Atua via API oficial do WhatsApp, conduz o atendimento com o lead, faz perguntas de qualificação e coleta dados. |
| **Agno (AgentOS Runtime)** | Hospeda o agente como serviço (FastAPI), gerencia sessões e executa integrações (CRM/DB/Chatwoot). |
| **CRM Piperun** | Recebe os dados do lead via requisição POST e cria automaticamente um registro de Lead e uma Oportunidade. |
| **Chatwoot (ou outro painel de atendimento)** | Permite ao SDR monitorar o atendimento em tempo real e intervir quando necessário. |
| **Base de Conhecimento / Cadastro de Produtos** | Fornece informações para o agente responder dúvidas e sugerir produtos. |

---

## **3. Fluxo de Atendimento**

1. **Entrada do Lead**
    - O lead inicia contato via WhatsApp.
    - O agente de IA faz perguntas para entender o perfil e coletar informações.
2. **Coleta de Dados**
    - Campos coletados: (Exemplo mutável)
        
        `Nome`, `Email`, `WhatsApp`, `Resumo`, `Produto`, `Segmento`, `Urgência de Compra`, `Volume Diário`, etc.
        
3. **Envio ao CRM**
    - O agente envia os dados via **POST** para o **Piperun**, criando **Lead** e **Oportunidade**.
4. **Qualificação**
    - O lead é classificado como **Quente**, **Morno** ou **Frio** conforme critérios exemplo:
        - Volume de Produção
        - Tipo de Produto
        - Segmento
        - Urgência de Compra
        - Nível de Engajamento
5. **Distribuição e Acompanhamento**
    - Leads são direcionados automaticamente para times (Alpha, Bravo etc.) com base na categoria do produto.
    - SDR monitora o atendimento via painel (Chatwoot) e interfere quando necessário.
    - Leads descartados ou pós-venda seguem fluxos distintos.

---

## **4. Critérios de Qualificação (Score)**

Está sendo desenvolvido e será enviado pela empresa solicitante

---

## **5. Integrações e Automação**

- **Entrada:** WhatsApp Business API (oficial)
- **Saída:** CRM Piperun (via POST JSON)
- **Monitoramento:** Chatwoot
- **Base de dados:** Catálogo de produtos + FAQ para IA + Banco de dados (Atual ou Sugerido pelo desenvolvedor)
- **Ações Automáticas:**
    - Criar Lead e Oportunidade.
    - Preencher campos no CRM (nome, telefone, interesse, urgência, etc.).
    - Atribuir lead à equipe correspondente.
    - Notificar SDRs conforme a classificação (Quente/Morno/Frio).

---

## **6. Responsabilidades Operacionais**

| Papel | Responsabilidade |
| --- | --- |
| **Agente de IA** | Conduz diálogo, coleta dados e envia ao CRM. |
| **SDR** | Monitora o atendimento e intervém quando necessário. |
| **Equipe Comercial (Alpha/Bravo)** | Recebe leads qualificados e faz follow-up. |

---