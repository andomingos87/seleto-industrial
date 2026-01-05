# Agente SDR (Sales Development Representative)

> **Para o Cliente:** O Agente SDR é o "vendedor virtual" do sistema. Ele conversa com os clientes pelo WhatsApp de forma natural e inteligente, coleta informações importantes, e classifica cada lead pelo potencial de compra. Funciona 24 horas por dia, 7 dias por semana, sem pausa para café!

---

## O que é um SDR?

**SDR (Sales Development Representative)** é um profissional de vendas responsável por:
- Fazer primeiro contato com potenciais clientes
- Qualificar leads (avaliar potencial de compra)
- Coletar informações importantes
- Encaminhar leads qualificados para vendedores

O **Agente SDR** automatiza essas tarefas usando Inteligência Artificial.

---

## Visão Geral

**Arquivo Principal:** `src/agents/sdr_agent.py`

**Framework:** Agno (especializado em agentes de IA)

**LLM:** OpenAI GPT-4o

```python
# Estrutura principal
SDR Agent
├── create_sdr_agent()      # Cria instância do agente
├── process_message()       # Processa uma mensagem
└── reload_system_prompt()  # Recarrega prompt (dev)
```

---

## Fluxo de Processamento

> **Para o Cliente:** Quando um cliente manda mensagem, acontece uma sequência de passos nos bastidores. É tudo muito rápido - geralmente menos de 3 segundos - mas muita coisa acontece nesse tempo.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MENSAGEM DO CLIENTE                          │
│               "Olá, sou João de SP, quero a FBM100"            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. NORMALIZAÇÃO                                                 │
│    • Normaliza telefone (ex: 5511999999999)                    │
│    • Identifica se é primeira mensagem                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CARREGAR CONTEXTO                                           │
│    • Busca histórico da conversa                               │
│    • Carrega dados já coletados do lead                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. EXTRAÇÃO DE DADOS (LLM)                                     │
│    • Analisa mensagem com GPT-4o                               │
│    • Extrai: nome="João", cidade="SP", produto="FBM100"        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PERSISTÊNCIA                                                │
│    • Salva dados extraídos no banco                            │
│    • Atualiza registro do lead                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CLASSIFICAÇÃO DE TEMPERATURA                                │
│    • Avalia engajamento e completude dos dados                 │
│    • Classifica: QUENTE / MORNO / FRIO                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. APLICAR GUARDRAILS                                          │
│    • Verifica se é pergunta comercial (preço)                  │
│    • Verifica se é pergunta técnica avançada                   │
│    • Aplica regras de negócio                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. VERIFICAR OPORTUNIDADES                                     │
│    • Detecta interesse em FBM100 → sugere FB300 (upsell)       │
│    • Detecta interesse em espeto → informa indisponibilidade   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. GERAR RESPOSTA (LLM)                                        │
│    • Envia contexto completo para GPT-4o                       │
│    • Gera resposta personalizada e contextual                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. SALVAR E ENVIAR                                             │
│    • Salva resposta no histórico                               │
│    • Sincroniza com Chatwoot                                   │
│    • Envia via WhatsApp (Z-API)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPOSTA PARA CLIENTE                        │
│    "Olá João! Que bom ter você aqui. A FBM100 é uma            │
│     excelente escolha para produção manual de hambúrgueres..." │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Prompt

> **Para o Cliente:** O System Prompt são as "instruções" que damos para a IA. É como um manual de treinamento que define a personalidade, o conhecimento e as regras do atendente virtual.

**Arquivo:** `prompts/system_prompt/sp_agente_v1.xml`

### Estrutura do Prompt

```xml
<system_prompt>
  <identity>
    <!-- Quem é o agente -->
    Você é um assistente comercial da Seleto Industrial...
  </identity>

  <knowledge>
    <!-- O que o agente sabe -->
    - Produtos: FBM100, FB300, CT200...
    - Especificações técnicas básicas
    - Informações da empresa
  </knowledge>

  <conversation_rules>
    <!-- Como se comportar -->
    - Seja cordial e profissional
    - Colete informações progressivamente
    - Não discuta preços
    - Encaminhe questões técnicas avançadas
  </conversation_rules>

  <data_collection>
    <!-- O que coletar -->
    - Nome
    - Empresa
    - Cidade/UF
    - Produto de interesse
    - Volume estimado
    - Urgência
  </data_collection>
</system_prompt>
```

### Carregamento Seguro

O prompt é carregado com medidas de segurança:

```python
# src/services/prompt_loader.py
def load_system_prompt_from_xml(xml_path: str) -> str:
    # Valida que o caminho está dentro de prompts/
    # Previne path traversal (../../../)
    # Parser XML seguro contra XXE attacks
```

---

## Classificação de Temperatura

> **Para o Cliente:** A "temperatura" indica o quão próximo de comprar o cliente está. É como um termômetro de vendas: quanto mais quente, mais pronto para fechar negócio.

### Temperaturas

| Temperatura | Significado | Ação |
|-------------|-------------|------|
| 🔥 **Quente** | Pronto para comprar | Prioridade para vendedor |
| 🌡️ **Morno** | Interessado, precisa mais info | Continuar qualificando |
| ❄️ **Frio** | Apenas pesquisando | Nutrir com conteúdo |

### Critérios de Classificação

**Lead Quente:**
- Urgência alta (precisa para ontem, esta semana)
- Volume significativo (alta produção)
- Dados completos (nome, empresa, cidade)
- Engajamento ativo (várias mensagens, perguntas específicas)

**Lead Morno:**
- Interesse demonstrado em produto específico
- Algumas informações coletadas
- Urgência média ou não definida
- Fazendo pesquisa de mercado

**Lead Frio:**
- Apenas curiosidade inicial
- Poucos dados fornecidos
- Sem urgência
- Respostas curtas ou evasivas

### Prompt de Classificação

**Arquivo:** `prompts/system_prompt/sp_calcula_temperatura.xml`

```xml
<classification_prompt>
  <context>
    Analise o lead com base em:
    - Histórico da conversa
    - Dados coletados
    - Nível de engajamento
  </context>

  <criteria>
    <hot>Alta urgência + alto volume + dados completos</hot>
    <warm>Interesse + alguns dados + sem pressa</warm>
    <cold>Apenas curiosidade + dados mínimos</cold>
  </criteria>

  <output>
    Retorne: temperatura, justificativa
  </output>
</classification_prompt>
```

### Quando Classificar

```python
def should_classify_lead(lead_data: dict) -> bool:
    """Verifica se há dados suficientes para classificar"""
    return any([
        lead_data.get("name"),
        lead_data.get("product"),
        lead_data.get("volume")
    ])
```

---

## Guardrails (Regras de Proteção)

> **Para o Cliente:** Guardrails são "cercas de proteção" que impedem o agente de falar sobre assuntos sensíveis. Por exemplo, ele nunca discute preços pelo WhatsApp - isso garante que a negociação seja feita pela equipe de vendas.

### Guardrail Comercial

**Palavras-chave detectadas:**
```python
COMMERCIAL_KEYWORDS = [
    "preço", "valor", "custo", "orçamento",
    "desconto", "promoção", "parcelamento",
    "prazo de entrega", "frete",
    "proposta", "negociar"
]
```

**Comportamento:**
```
Cliente: "Qual o preço da FBM100?"
         ↓
Sistema: Detecta pergunta comercial
         ↓
Resposta: "Para informações sobre preços e condições
          comerciais, nossa equipe de vendas entrará
          em contato com você em breve. Enquanto isso,
          posso tirar outras dúvidas sobre o produto!"
```

### Guardrail Técnico

**Palavras-chave detectadas:**
```python
TECHNICAL_KEYWORDS = [
    "diagrama elétrico", "esquema elétrico",
    "voltagem", "amperagem",
    "especificação técnica detalhada",
    "calibração"
]
```

**Comportamento:**
```
Cliente: "Preciso do diagrama elétrico da máquina"
         ↓
Sistema: Detecta pergunta técnica avançada
         ↓
Sistema: Registra pergunta para engenharia
         ↓
Resposta: "Esta é uma questão técnica específica
          que vou encaminhar para nossa equipe de
          engenharia. Eles entrarão em contato!"
```

---

## Coleta de Dados

> **Para o Cliente:** O agente vai coletando informações aos poucos, de forma natural na conversa. Não é um formulário - é como uma conversa onde a pessoa vai contando sobre sua necessidade.

### Campos Coletados

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `name` | Nome completo | "João Silva" |
| `company` | Nome da empresa | "ABC Foods" |
| `city` | Cidade | "São Paulo" |
| `uf` | Estado | "SP" |
| `product` | Produto de interesse | "FBM100" |
| `volume` | Volume estimado | "500kg/dia" |
| `urgency` | Urgência | "preciso em 15 dias" |
| `knows_seleto` | Conhece a empresa | true/false |

### Extração Automática

```
Mensagem: "Sou o João da ABC Foods em Campinas-SP,
           produzimos cerca de 300kg de hambúrguer por dia"
                    ↓
           Extração via GPT-4o
                    ↓
Dados extraídos: {
    "name": "João",
    "company": "ABC Foods",
    "city": "Campinas",
    "uf": "SP",
    "volume": "300kg/dia",
    "product": "hambúrguer" (inferido)
}
```

### Coleta Progressiva

O agente não pede todas as informações de uma vez:

```
[Mensagem 1] Cliente: "Olá"
[Resposta 1] Agente: "Olá! Bem-vindo à Seleto Industrial!
                      Como posso ajudá-lo hoje?"

[Mensagem 2] Cliente: "Quero saber da máquina de hambúrguer"
[Resposta 2] Agente: "Temos ótimas opções! Para entender
                      melhor sua necessidade, qual seria
                      seu volume de produção diário?"

[Mensagem 3] Cliente: "Uns 200kg por dia"
→ Sistema extrai: product="hambúrguer", volume="200kg/dia"

[Resposta 3] Agente: "200kg é uma boa produção! Você já
                      conhece a Seleto Industrial?"
```

---

## Upsell (Venda de Upgrade)

> **Para o Cliente:** Quando identificamos que o cliente pode se beneficiar de um produto melhor, sugerimos de forma natural. Por exemplo, se ele quer a máquina manual, mostramos a semi-automática que produz mais.

### FBM100 → FB300

| FBM100 (Manual) | FB300 (Semi-automática) |
|-----------------|------------------------|
| Operação manual | Semi-automática |
| ~200 unid/hora | ~800 unid/hora |
| Menor investimento | Maior produtividade |
| Ideal para pequeno volume | Ideal para médio/alto volume |

**Detecção de Oportunidade:**
```python
FBM100_KEYWORDS = [
    "fbm100", "fbm 100", "formadora manual",
    "hambúrguer manual", "máquina manual"
]

PRODUCTION_KEYWORDS = [
    "produção", "produtividade", "capacidade", "volume"
]
```

**Comportamento:**
```
Cliente: "Estou interessado na FBM100 para aumentar
          minha produção"
         ↓
Sistema: Detecta FBM100 + contexto de produção
         ↓
Contexto para agente: "O cliente mencionou FBM100 e
                       produção. Considere mencionar
                       a FB300 como alternativa para
                       maior produtividade."
         ↓
Resposta: "A FBM100 é excelente! Se seu foco é
           aumentar produtividade, a FB300 pode
           ser interessante - ela produz até 4x
           mais. Posso contar mais sobre ela?"
```

---

## Produtos Indisponíveis

> **Para o Cliente:** Quando um produto está temporariamente indisponível, o agente informa de forma transparente e sugere alternativas, evitando frustração do cliente.

### Linha de Espetos

**Status:** Em melhoria, previsão março/2026

**Detecção:**
```python
ESPETO_KEYWORDS = [
    "espeto", "espetos", "espetinho",
    "máquina de espeto", "produção de espeto"
]
```

**Comportamento:**
```
Cliente: "Vocês têm máquina de espeto?"
         ↓
Sistema: Detecta interesse em espeto
         ↓
Sistema: Registra interesse para contato futuro
         ↓
Resposta: "Nossa linha de espetos está em fase de
           melhorias e deve voltar em março de 2026.
           Posso registrar seu interesse para avisá-lo
           quando disponível! Enquanto isso, nossa
           CT200 é ótima para corte em cubos."
```

---

## Memória de Conversa

> **Para o Cliente:** O agente lembra de tudo que foi conversado. Se o cliente voltar dias depois, não precisa repetir as informações - o sistema já sabe quem ele é e o que ele precisa.

### Estrutura

```python
ConversationMemory:
    # Cache em memória para acesso rápido
    _conversations: Dict[phone → List[Message]]
    _lead_data: Dict[phone → Dict]

    # Sincronização com Supabase para persistência
    # Carregamento lazy (só quando necessário)
```

### Contexto para o LLM

```python
def get_messages_for_llm(phone: str, max_messages: int = 20):
    """Retorna últimas 20 mensagens formatadas para LLM"""
    return [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
```

### Limite de Perguntas Consecutivas

Para evitar que o agente faça muitas perguntas seguidas:

```python
MAX_CONSECUTIVE_QUESTIONS = 2

# Se o agente fez 2 perguntas sem resposta do cliente,
# a próxima mensagem deve ser mais informativa/educativa
```

---

## Configuração do Agente

### Criação

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_sdr_agent() -> Agent:
    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        system_prompt=load_system_prompt(),
        description="Agente SDR da Seleto Industrial"
    )
```

### Parâmetros do Modelo

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| `model` | gpt-4o | Melhor capacidade de raciocínio |
| `temperature` | 0.7 | Equilíbrio criatividade/consistência |
| `max_tokens` | 500 | Respostas concisas |

### Hot Reload (Desenvolvimento)

```python
def reload_system_prompt():
    """Recarrega prompt sem reiniciar servidor"""
    global _system_prompt
    _system_prompt = load_system_prompt_from_xml(PROMPT_PATH)
```

---

## Métricas e Monitoramento

### Logs Gerados

```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "phone": "5511999999999",
  "flow_step": "process_message",
  "extracted_data": {"name": "João", "city": "SP"},
  "temperature": "morno",
  "response_time_ms": 2500
}
```

### Métricas Importantes

| Métrica | O que mede |
|---------|------------|
| Tempo de resposta | Performance do sistema |
| Taxa de extração | Qualidade da coleta de dados |
| Distribuição de temperatura | Eficácia da qualificação |
| Taxa de upsell | Oportunidades identificadas |

---

## Boas Práticas

### Para o Prompt

1. **Seja específico** - Instruções claras geram melhores respostas
2. **Use exemplos** - Few-shot learning melhora precisão
3. **Defina limites** - O que NÃO fazer é tão importante quanto o que fazer
4. **Teste iterativamente** - Ajuste baseado em conversas reais

### Para o Código

1. **Logs detalhados** - Facilita debug e análise
2. **Graceful degradation** - Sistema funciona mesmo com falhas parciais
3. **Timeout adequado** - Evita travamentos em chamadas à API
4. **Cache inteligente** - Reduz latência e custos

### Para a Experiência

1. **Respostas rápidas** - <3 segundos ideal
2. **Tom natural** - Evitar parecer robótico
3. **Transparência** - Informar quando não sabe
4. **Handoff suave** - Transição clara para humanos

---

## Troubleshooting

### Agente não responde

1. Verificar `OPENAI_API_KEY`
2. Verificar conectividade com OpenAI
3. Checar logs de erro
4. Verificar timeout

### Respostas genéricas

1. Verificar se prompt está carregando
2. Checar se histórico está sendo passado
3. Ajustar temperatura do modelo
4. Revisar system prompt

### Dados não extraídos

1. Verificar formato da mensagem
2. Checar resposta do extraction prompt
3. Verificar se campos já estão preenchidos
4. Testar com mensagens mais explícitas

### Classificação incorreta

1. Revisar critérios no prompt
2. Verificar dados do lead
3. Checar histórico da conversa
4. Ajustar pesos dos critérios

---

[← Voltar ao Índice](./README.md) | [Anterior: Integrações](./integracoes.md) | [Próximo: Testes →](./testes.md)
