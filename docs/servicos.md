# Documentação dos Serviços

> **Para o Cliente:** Os serviços são como departamentos especializados dentro do sistema. Cada um cuida de uma tarefa específica: um guarda as conversas, outro envia mensagens, outro classifica clientes. Juntos, eles fazem o sistema funcionar de forma organizada e eficiente.

---

## Visão Geral

O sistema possui serviços organizados em quatro categorias:

1. **Serviços de Dados** - Persistência e recuperação de informações
2. **Serviços de IA** - Processamento inteligente com LLM
3. **Serviços de Integração** - Comunicação com sistemas externos
4. **Serviços de Negócio** - Regras específicas do domínio

**Localização:** `src/services/`

---

## Serviços de Dados

### Lead Persistence

> **Para o Cliente:** Este serviço guarda todas as informações dos potenciais clientes. Quando alguém fala o nome, a cidade, o produto de interesse - tudo é salvo aqui de forma organizada.

**Arquivo:** `src/services/lead_persistence.py`

**Funções Principais:**

```python
upsert_lead(phone: str, data: dict) → dict | None
```
Cria ou atualiza um lead. Se já existe um lead com o mesmo telefone, atualiza os dados. Caso contrário, cria um novo.

**Parâmetros:**
- `phone`: Telefone no formato E.164 (ex: "5511999999999")
- `data`: Dicionário com campos do lead

**Campos Suportados:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome completo |
| `email` | string | E-mail |
| `city` | string | Cidade |
| `uf` | string | Estado (2 letras) |
| `product` | string | Produto de interesse |
| `volume` | string | Volume estimado |
| `urgency` | string | Nível de urgência |
| `knows_seleto` | boolean | Se conhece a Seleto |
| `temperature` | string | Classificação (quente/morno/frio) |

**Exemplo:**
```python
from src.services.lead_persistence import upsert_lead

lead = await upsert_lead(
    phone="5511999999999",
    data={
        "name": "João Silva",
        "city": "São Paulo",
        "product": "FBM100"
    }
)
```

---

```python
get_lead_by_phone(phone: str) → dict | None
```
Busca um lead pelo telefone.

**Retorno:**
- Dicionário com dados do lead, ou `None` se não encontrado

---

```python
get_persisted_lead_data(phone: str) → dict
```
Obtém dados do lead da memória, carregando do Supabase se necessário.

---

```python
persist_lead_data(phone: str, data: dict) → bool
```
Persiste dados no cache de memória (sincroniza com Supabase via conversation_memory).

---

**Características:**
- **Idempotência**: Múltiplas chamadas com mesmo telefone = um único lead
- **Normalização**: Telefone normalizado automaticamente
- **Campos Parciais**: Aceita atualização de campos individuais (null é ignorado)

---

### Orcamento Persistence

> **Para o Cliente:** Aqui guardamos os pedidos de orçamento. Um cliente pode ter vários orçamentos ao longo do tempo, e todos ficam organizados e conectados ao cadastro dele.

**Arquivo:** `src/services/orcamento_persistence.py`

**Funções Principais:**

```python
create_orcamento(lead_id: str, data: dict) → dict | None
```
Cria um novo orçamento vinculado a um lead.

**Campos Suportados:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `resumo` | string | Resumo do orçamento |
| `produto` | string | Produto solicitado |
| `segmento` | string | Segmento de mercado |
| `urgencia_compra` | string | Urgência |
| `volume_diario` | string | Volume diário |
| `oportunidade_pipe_id` | string | ID da oportunidade no PipeRun |

---

```python
get_orcamentos_by_lead(lead_id: str) → list[dict]
```
Lista todos os orçamentos de um lead, ordenados do mais recente ao mais antigo.

---

```python
update_orcamento(orcamento_id: str, data: dict) → dict | None
```
Atualiza um orçamento existente.

---

**Características:**
- **Validação FK**: Verifica se o lead existe antes de criar
- **Ordenação**: Retorna orçamentos ordenados por data de criação (desc)
- **Múltiplos**: Um lead pode ter vários orçamentos

---

### Empresa Persistence

> **Para o Cliente:** Serviço para gerenciar informações de empresas. Se o cliente informa o CNPJ, conseguimos identificar a empresa automaticamente e evitar cadastros duplicados.

**Arquivo:** `src/services/empresa_persistence.py`

**Funções Principais:**

```python
create_empresa(data: dict) → dict | None
```
Cria uma nova empresa. Se já existir uma empresa com o mesmo CNPJ, retorna a existente.

**Campos Suportados:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `nome` | string | Nome da empresa |
| `cidade` | string | Cidade |
| `uf` | string | Estado (2 letras) |
| `cnpj` | string | CNPJ (14 dígitos) |
| `site` | string | Website |
| `email` | string | E-mail |
| `telefone` | string | Telefone |
| `contato` | string | Nome do contato |

---

```python
get_empresa_by_cnpj(cnpj: str) → dict | None
```
Busca empresa pelo CNPJ normalizado.

---

```python
update_empresa(empresa_id: str, data: dict) → dict | None
```
Atualiza dados de uma empresa.

---

**Características:**
- **Deduplicação CNPJ**: Evita empresas duplicadas pelo CNPJ
- **CNPJ Opcional**: Empresa pode ser criada sem CNPJ
- **Normalização**: Remove pontuação do CNPJ automaticamente

---

### Conversation Memory

> **Para o Cliente:** Este é o "memória" do sistema. Ele lembra de tudo que foi conversado com cada cliente, permitindo que o atendimento seja contínuo mesmo se o cliente voltar dias depois.

**Arquivo:** `src/services/conversation_memory.py`

**Classe Principal: `ConversationMemory`**

```python
class ConversationMemory:
    """Cache em memória com sincronização para Supabase"""
```

**Métodos:**

```python
get_conversation_history(phone: str, max_messages: int = None) → list
```
Retorna o histórico de mensagens de uma conversa.

---

```python
get_messages_for_llm(phone: str, max_messages: int = 20) → list[dict]
```
Retorna mensagens formatadas para envio ao LLM (role, content).

---

```python
add_message(phone: str, role: str, content: str) → None
```
Adiciona uma mensagem ao histórico.
- `role`: "user" ou "assistant"
- Sincroniza automaticamente com Chatwoot

---

```python
get_lead_data(phone: str) → dict
```
Retorna dados coletados do lead.

---

```python
update_lead_data(phone: str, data: dict) → None
```
Atualiza dados do lead no cache.

---

**Características:**
- **Lazy Loading**: Carrega do Supabase apenas quando necessário
- **Cache Eficiente**: Evita consultas repetidas ao banco
- **Sync Chatwoot**: Espelha mensagens para interface visual
- **Rate Limiting**: Conta perguntas consecutivas do assistente

---

### Conversation Persistence

> **Para o Cliente:** É a "ponte" entre o sistema e o banco de dados Supabase. Garante que as conversas fiquem salvas de forma segura na nuvem.

**Arquivo:** `src/services/conversation_persistence.py`

**Funções:**

```python
get_supabase_client() → Client | None
```
Retorna cliente singleton do Supabase.

---

```python
save_message_to_supabase(phone: str, role: str, content: str) → bool
```
Salva uma mensagem no banco de dados.

---

```python
get_messages_from_supabase(phone: str, limit: int = 50) → list[dict]
```
Recupera mensagens do histórico.

---

```python
save_context_to_supabase(phone: str, key: str, value: str) → bool
```
Salva contexto adicional da conversa.

---

```python
get_context_from_supabase(phone: str) → dict
```
Recupera contexto salvo.

---

**Características:**
- **Singleton**: Reutiliza conexão com Supabase
- **Graceful Degradation**: Funciona mesmo sem Supabase configurado
- **Normalização**: Telefones normalizados antes de persistir

---

## Serviços de IA

### Data Extraction

> **Para o Cliente:** Este serviço "lê" as mensagens dos clientes e extrai informações importantes automaticamente. Se o cliente escreve "Sou João de São Paulo", o sistema entende que o nome é João e a cidade é São Paulo.

**Arquivo:** `src/services/data_extraction.py`

**Função Principal:**

```python
extract_lead_data(message: str, current_data: dict) → dict | None
```

Usa OpenAI GPT-4o para extrair dados estruturados de uma mensagem.

**Campos Extraídos:**
| Campo | Descrição | Exemplo de Input |
|-------|-----------|------------------|
| `name` | Nome completo | "Me chamo João Silva" |
| `company` | Nome da empresa | "Trabalho na ABC Foods" |
| `city` | Cidade | "Sou de Campinas" |
| `uf` | Estado | "Fico em SP" |
| `product` | Produto de interesse | "Quero saber da FBM100" |
| `volume` | Volume estimado | "Produzimos 500kg por dia" |
| `urgency` | Urgência | "Preciso para ontem!" |
| `knows_seleto` | Conhece a empresa | "Já comprei de vocês" |

**Características:**
- **Incremental**: Só extrai campos novos (não re-extrai conhecidos)
- **Fallback**: Retorna `None` se não conseguir extrair
- **Assíncrono**: Não bloqueia o processamento

**Exemplo:**
```python
from src.services.data_extraction import extract_lead_data

current = {"name": "João"}
new_data = await extract_lead_data(
    "Sou de São Paulo e quero a FBM100",
    current
)
# Retorna: {"city": "São Paulo", "product": "FBM100"}
```

---

### Temperature Classification

> **Para o Cliente:** Este serviço avalia o "calor" do lead - ou seja, a probabilidade de compra. Um lead "quente" está pronto para comprar, um "morno" precisa de mais informações, e um "frio" está apenas pesquisando.

**Arquivo:** `src/services/temperature_classification.py`

**Funções:**

```python
classify_lead(phone: str, lead_data: dict, history: list) → tuple[str, str]
```

Classifica o lead em uma das três temperaturas.

**Retorno:** `(temperatura, justificativa)`
- `temperatura`: "quente", "morno" ou "frio"
- `justificativa`: Explicação da classificação

**Critérios de Classificação:**

| Temperatura | Indicadores |
|-------------|-------------|
| **Quente** | Alta urgência, volume alto, dados completos, engajamento ativo |
| **Morno** | Interesse demonstrado, algumas informações, sem urgência definida |
| **Frio** | Apenas curiosidade, dados mínimos, baixo engajamento |

---

```python
should_classify_lead(lead_data: dict) → bool
```
Verifica se há dados suficientes para classificar.

**Campos Necessários:**
- Nome OU
- Produto de interesse OU
- Volume estimado

---

**Características:**
- **Prompt Especializado**: Usa `sp_calcula_temperatura.xml`
- **Baseado em Contexto**: Considera histórico da conversa
- **Justificativa**: Sempre explica o motivo da classificação

---

### Knowledge Base

> **Para o Cliente:** É a "enciclopédia" do sistema sobre seus produtos. Contém informações das máquinas, especificações, e também "guardrails" - regras sobre o que o sistema pode ou não pode responder.

**Arquivo:** `src/services/knowledge_base.py`

**Classe Principal: `KnowledgeBase`**

```python
knowledge_base = get_knowledge_base()  # Singleton
```

**Métodos:**

```python
search(query: str) → list[EquipmentInfo]
```
Busca informações de equipamentos.

---

```python
is_commercial_query(message: str) → bool
```
Detecta se a mensagem é sobre preço, desconto, condições comerciais.

**Palavras-chave Detectadas:**
- preço, valor, custo, orçamento
- desconto, promoção, parcelamento
- prazo de entrega, frete
- proposta, negociar

---

```python
is_too_technical(message: str) → bool
```
Detecta perguntas técnicas avançadas que devem ir para engenharia.

**Palavras-chave Detectadas:**
- diagrama elétrico, esquema elétrico
- voltagem, amperagem
- especificação técnica detalhada
- calibração

---

```python
get_commercial_response() → str
```
Retorna resposta padrão para questões comerciais.

```
"Para informações sobre preços e condições comerciais,
nossa equipe de vendas entrará em contato com você em breve."
```

---

```python
register_technical_question(phone: str, question: str) → None
```
Registra pergunta técnica para follow-up pela engenharia.

---

**Características:**
- **Guardrails**: Impede discussões de preço/técnicas avançadas
- **Consistência**: Respostas padronizadas sobre produtos
- **Registro**: Perguntas técnicas são logadas para acompanhamento

---

### Prompt Loader

> **Para o Cliente:** Este serviço carrega as "instruções" do agente de IA de forma segura. As instruções ficam em arquivos separados para facilitar ajustes sem mexer no código.

**Arquivo:** `src/services/prompt_loader.py`

**Funções:**

```python
load_system_prompt_from_xml(xml_path: str) → str
```
Carrega e processa um arquivo XML de prompt.

---

```python
get_system_prompt_path(filename: str) → Path
```
Valida e retorna o caminho seguro para um arquivo de prompt.

---

**Segurança:**
- **Path Traversal Prevention**: Não permite `../` nos caminhos
- **XXE Protection**: Parser XML configurado de forma segura
- **Directory Restriction**: Só carrega de `prompts/system_prompt/`

---

## Serviços de Integração

### WhatsApp Service

> **Para o Cliente:** Este serviço envia as mensagens de volta para o WhatsApp. Quando o sistema gera uma resposta, é este serviço que a entrega para o cliente.

**Arquivo:** `src/services/whatsapp.py`

**Classe Principal: `WhatsAppService`**

```python
class WhatsAppService:
    """Integração com Z-API para WhatsApp"""
```

**Métodos:**

```python
is_configured() → bool
```
Verifica se todas as credenciais Z-API estão configuradas.

---

```python
async send_message(
    phone: str,
    text: str,
    max_retries: int = 3,
    initial_backoff: float = 1.0
) → bool
```

Envia mensagem de texto para um número.

**Parâmetros:**
- `phone`: Número de destino (será normalizado)
- `text`: Texto da mensagem
- `max_retries`: Tentativas em caso de falha (padrão: 3)
- `initial_backoff`: Tempo inicial entre tentativas (segundos)

**Retorno:** `True` se enviou com sucesso

---

**Características:**
- **Retry Logic**: Exponential backoff (1s, 2s, 4s...)
- **Normalização**: Telefone formatado antes do envio
- **Header Correto**: Usa `Client-Token` (não Bearer)

**Configuração Z-API:**
```
Endpoint: https://api.z-api.io/instances/{ID}/token/{TOKEN}/send-text
Header: Client-Token: {CLIENT_TOKEN}
```

---

### Chatwoot Sync

> **Para o Cliente:** O Chatwoot é uma interface visual onde sua equipe pode ver as conversas. Este serviço sincroniza automaticamente todas as mensagens do WhatsApp para lá.

**Arquivo:** `src/services/chatwoot_sync.py`

**Funções:**

```python
create_chatwoot_conversation(phone: str, sender_name: str) → str | None
```
Cria uma nova conversa no Chatwoot para um contato.

---

```python
sync_message_to_chatwoot(phone: str, role: str, content: str) → bool
```
Sincroniza uma mensagem para o Chatwoot.
- `role`: "customer" ou "agent"

---

**Características:**
- **Cache de Contatos**: Evita criar contatos duplicados
- **Cache de Conversas**: Reutiliza conversas existentes
- **Opcional**: Funciona mesmo sem Chatwoot configurado
- **Defensive Parsing**: Trata diferentes formatos de resposta da API

---

### Transcription Service

> **Para o Cliente:** Quando um cliente envia áudio no WhatsApp, este serviço transforma em texto usando a mesma tecnologia do ChatGPT. Assim o sistema consegue entender mensagens de voz.

**Arquivo:** `src/services/transcription.py`

**Função:**

```python
async transcribe_audio(audio_url: str, audio_mime_type: str = None) → str | None
```

Transcreve áudio para texto usando OpenAI Whisper.

**Parâmetros:**
- `audio_url`: URL para download do áudio
- `audio_mime_type`: Tipo MIME (opcional)

**Retorno:** Texto transcrito ou `None` em caso de erro

---

**Características:**
- **OpenAI Whisper**: Modelo state-of-the-art para transcrição
- **Download Automático**: Baixa áudio da URL fornecida
- **Múltiplos Formatos**: Suporta OGG, MP3, WAV, etc.

---

## Serviços de Negócio

### Upsell Service

> **Para o Cliente:** Este serviço identifica oportunidades de venda de produtos melhores. Por exemplo, se um cliente pergunta sobre a máquina manual (FBM100), o sistema pode sugerir a semi-automática (FB300) que produz mais.

**Arquivo:** `src/services/upsell.py`

**Função:**

```python
get_upsell_context_for_agent(
    phone: str,
    lead_data: dict,
    message: str
) → str | None
```

Verifica se há oportunidade de upsell e retorna contexto para o agente.

**Retorno:**
- Contexto sobre FB300 se detectar interesse em FBM100
- `None` se não houver oportunidade

---

**Detecção FBM100:**
```python
FBM100_KEYWORDS = [
    "fbm100", "fbm 100", "formadora manual",
    "hambúrguer manual", "máquina manual",
    "produção manual", "fazer hambúrguer manual"
]
```

**Contexto de Produção (quando mencionar):**
```python
PRODUCTION_CONTEXT_KEYWORDS = [
    "produção", "produtividade", "capacidade", "volume"
]
```

---

**Características:**
- **Anti-Repetição**: Não sugere duas vezes para o mesmo telefone
- **Timing Inteligente**: Sugere quando falar de produção
- **Contexto Rico**: Fornece informações da FB300 ao agente

---

### Unavailable Products Service

> **Para o Cliente:** Gerencia produtos que estão temporariamente indisponíveis. Se um cliente perguntar sobre a linha de espetos (que está em melhoria), o sistema informa a previsão e sugere alternativas.

**Arquivo:** `src/services/unavailable_products.py`

**Função:**

```python
get_espeto_context_for_agent(
    phone: str,
    lead_data: dict,
    message: str
) → str | None
```

Verifica interesse em espetos e retorna contexto apropriado.

---

**Detecção Espeto:**
```python
ESPETO_KEYWORDS = [
    "espeto", "espetos", "espetinho",
    "máquina de espeto", "produção de espeto",
    "linha automática para espeto"
]
```

**Informações:**
- **Status**: Em melhoria, previsão março/2026
- **Alternativa**: CT200 (máquina de corte em cubos)

---

**Características:**
- **Registro de Interesse**: Salva interesse para contato futuro
- **Alternativas**: Sugere produtos disponíveis
- **Expectativas**: Informa prazo realista

---

## Utilitários

### Logging

> **Para o Cliente:** O sistema registra tudo que acontece em "logs" - são como um diário detalhado. Se algo der errado, conseguimos voltar e ver exatamente o que aconteceu.

**Arquivo:** `src/utils/logging.py`

**Funções:**

```python
get_logger(name: str) → Logger
```
Cria logger configurado para o módulo.

---

```python
set_request_id(request_id: str = None) → str
```
Define ID único da requisição (gera automaticamente se não informado).

---

```python
set_phone(phone: str) → None
```
Define telefone no contexto do log.

---

```python
set_flow_step(step: str) → None
```
Define etapa atual do fluxo.

---

```python
clear_context() → None
```
Limpa todas as variáveis de contexto.

---

**Formato de Log:**
```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "INFO",
  "message": "Mensagem processada",
  "logger": "src.agents.sdr_agent",
  "request_id": "uuid-aqui",
  "phone": "5511999999999",
  "flow_step": "process_message"
}
```

---

### Validation

> **Para o Cliente:** Funções que garantem que os dados estejam no formato correto. Por exemplo, telefones são padronizados para sempre ter o mesmo formato, facilitando encontrar clientes no sistema.

**Arquivo:** `src/utils/validation.py`

**Funções:**

```python
normalize_phone(phone: str) → str
```
Normaliza telefone para formato E.164 (apenas dígitos).
- Input: "(11) 99999-9999" → Output: "5511999999999"

---

```python
validate_phone(phone: str) → bool
```
Valida se telefone tem pelo menos 10 dígitos.

---

```python
normalize_cnpj(cnpj: str) → str
```
Remove pontuação do CNPJ.
- Input: "12.345.678/0001-90" → Output: "12345678000190"

---

```python
validate_cnpj(cnpj: str) → bool
```
Valida se CNPJ tem exatamente 14 dígitos.

---

```python
normalize_email(email: str) → str
```
Normaliza e-mail (lowercase, trim).

---

```python
validate_email(email: str) → bool
```
Valida formato básico de e-mail.

---

```python
normalize_uf(uf: str) → str
```
Normaliza UF para uppercase (2 caracteres).

---

```python
validate_uf(uf: str) → bool
```
Valida se UF tem exatamente 2 letras.

---

## Diagrama de Dependências

```
                    ┌──────────────┐
                    │  SDR Agent   │
                    └──────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Conversation│   │  Data    │    │Knowledge │
    │  Memory   │    │Extraction│    │   Base   │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Conversation│  │  OpenAI  │    │Temperature│
    │Persistence│   │   API    │    │Classification│
    └──────────┘    └──────────┘    └──────────┘
           │                               │
           │                               │
           ▼                               ▼
    ┌──────────┐                    ┌──────────┐
    │ Supabase │                    │  Lead    │
    │          │◄───────────────────│Persistence│
    └──────────┘                    └──────────┘
```

---

[← Voltar ao Índice](./README.md) | [Anterior: API](./api.md) | [Próximo: Banco de Dados →](./banco-de-dados.md)
