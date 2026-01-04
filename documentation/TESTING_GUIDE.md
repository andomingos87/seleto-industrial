# Guia de Testes e Validação — Seleto Industrial SDR Agent

> Baseado nas implementações validadas até 2026-01-04

---

## 📋 Índice

1. [Testes Automatizados](#testes-automatizados)
2. [Testes Manuais de Endpoints](#testes-manuais-de-endpoints)
3. [Testes de Integração (Simulados)](#testes-de-integração-simulados)
4. [Testes de Funcionalidades](#testes-de-funcionalidades)
5. [Validação de Logs](#validação-de-logs)

---

## 🧪 Testes Automatizados

### Executar Testes Existentes

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura de código
pytest tests/ -v --cov=src --cov-report=html

# Executar apenas testes de health
pytest tests/api/test_health.py -v

# Executar com output detalhado
pytest tests/ -v -s
```

### Testes Disponíveis

- ✅ `test_health_returns_200` — Verifica que `/api/health` retorna 200
- ✅ `test_health_response_structure` — Valida estrutura da resposta
- ✅ `test_health_content_type` — Verifica Content-Type JSON

---

## 🔌 Testes Manuais de Endpoints

### 1. Health Check

```bash
# Health check básico (AgentOS)
curl http://localhost:8000/health

# Health check detalhado
curl http://localhost:8000/api/health

# Com formatação JSON
curl http://localhost:8000/api/health | python -m json.tool
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T...",
  "service": "seleto-sdr-agent",
  "version": "0.1.0"
}
```

### 2. Documentação Swagger

```bash
# Abrir no navegador
http://localhost:8000/docs

# Ou ReDoc
http://localhost:8000/redoc
```

### 3. Webhook de WhatsApp (Simulado)

```bash
# Mensagem de texto
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "João Silva",
    "message": "Olá, preciso de uma formadora de hambúrguer",
    "messageId": "test-001",
    "messageType": "text"
  }'

# Mensagem de áudio (simulada)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "Maria Santos",
    "messageType": "audio",
    "audio": {
      "audioUrl": "https://example.com/audio.ogg",
      "mimeType": "audio/ogg",
      "seconds": 10
    },
    "messageId": "test-002"
  }'
```

**Nota:** Para testar com autenticação, adicione o header:
```bash
-H "X-Webhook-Secret: seu_secret_aqui"
# ou
-H "Authorization: Bearer seu_secret_aqui"
```

---

## 🔄 Testes de Integração (Simulados)

### 1. Teste de Fluxo Completo (Primeira Mensagem)

**Cenário:** Lead envia primeira mensagem

```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "Carlos Oliveira",
    "message": "Olá, quero saber sobre formadoras de hambúrguer",
    "messageId": "flow-001",
    "messageType": "text"
  }'
```

**O que validar:**
- ✅ Resposta HTTP 200 em < 2s
- ✅ Logs mostram "Webhook received"
- ✅ Agente processa mensagem
- ✅ Resposta contém saudação da Seleto Industrial
- ✅ Resposta pergunta sobre necessidade (sem exceder 2 perguntas)

### 2. Teste de Coleta Progressiva de Dados

**Cenário:** Lead fornece informações gradualmente

```bash
# Mensagem 1: Nome e produto
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "Ana Costa",
    "message": "Olá, sou a Ana e preciso de uma cortadora de carne",
    "messageId": "flow-002-1",
    "messageType": "text"
  }'

# Mensagem 2: Cidade
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "Ana Costa",
    "message": "Estou em São Paulo, SP",
    "messageId": "flow-002-2",
    "messageType": "text"
  }'

# Mensagem 3: Volume
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "Ana Costa",
    "message": "Preciso processar uns 200kg por dia",
    "messageId": "flow-002-3",
    "messageType": "text"
  }'
```

**O que validar:**
- ✅ Dados extraídos progressivamente (nome, cidade, produto, volume)
- ✅ Agente contextualiza perguntas com base nos dados já coletados
- ✅ Máximo de 2 perguntas diretas por resposta
- ✅ Dados persistidos mesmo que conversa não seja concluída

### 3. Teste de Normalização de Telefone

```bash
# Teste com diferentes formatos
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+55 11 99999-9999",
    "senderName": "Teste",
    "message": "Teste",
    "messageId": "test-phone-1",
    "messageType": "text"
  }'

# Verificar nos logs que telefone foi normalizado para: 5511999999999
```

### 4. Teste de Validação de Webhook

```bash
# Teste sem autenticação (deve funcionar se WHATSAPP_WEBHOOK_SECRET não estiver configurado)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "teste"}'

# Teste com autenticação inválida (deve retornar 401)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: wrong_secret" \
  -d '{"phone": "5511999999999", "message": "teste"}'
```

---

## 🧩 Testes de Funcionalidades

### 1. Teste de Extração de Dados

Crie um script Python para testar a extração:

```python
# test_data_extraction.py
import asyncio
from src.services.data_extraction import extract_lead_data

async def test_extraction():
    # Teste 1: Extrair nome e produto
    message1 = "Olá, sou João Silva e preciso de uma formadora de hambúrguer"
    data1 = await extract_lead_data(message1)
    print("Dados extraídos 1:", data1)
    # Esperado: {"name": "João Silva", "product": "formadora de hambúrguer"}
    
    # Teste 2: Extrair cidade com dados anteriores
    message2 = "Estou em São Paulo, SP"
    data2 = await extract_lead_data(message2, current_data=data1)
    print("Dados extraídos 2:", data2)
    # Esperado: {"city": "São Paulo", "uf": "SP"} (sem repetir name e product)

if __name__ == "__main__":
    asyncio.run(test_extraction())
```

**Executar:**
```bash
python test_data_extraction.py
```

### 2. Teste de Validação de Telefone

```python
# test_validation.py
from src.utils.validation import normalize_phone, validate_phone

# Testes de normalização
test_cases = [
    ("+55 11 99999-9999", "5511999999999"),
    ("(11) 99999-9999", "11999999999"),
    ("5511999999999", "5511999999999"),
]

for input_phone, expected in test_cases:
    result = normalize_phone(input_phone)
    print(f"{input_phone} -> {result} (esperado: {expected})")
    assert result == expected, f"Falhou: {input_phone}"

# Testes de validação
assert validate_phone("5511999999999") == True
assert validate_phone("11999999999") == True
assert validate_phone("123") == False  # Muito curto
```

### 3. Teste de Logging

```bash
# Iniciar servidor com LOG_FORMAT=text para ver logs legíveis
LOG_FORMAT=text uvicorn src.main:app --reload

# Fazer uma requisição e verificar logs
curl http://localhost:8000/api/health

# Verificar se logs contêm:
# - request_id
# - timestamp
# - level
# - message
```

### 4. Teste de Memória de Conversa

```python
# test_conversation_memory.py
from src.services.conversation_memory import conversation_memory

# Teste de primeira mensagem
phone = "5511999999999"
assert conversation_memory.is_first_message(phone) == True

# Adicionar mensagem
conversation_memory.add_message(phone, "user", "Olá")
assert conversation_memory.is_first_message(phone) == False

# Teste de controle de perguntas
conversation_memory.increment_question_count(phone)
assert conversation_memory.get_question_count(phone) == 1

conversation_memory.increment_question_count(phone)
assert conversation_memory.get_question_count(phone) == 2

# Reset quando usuário responde
conversation_memory.reset_question_count(phone)
assert conversation_memory.get_question_count(phone) == 0
```

---

## 📊 Validação de Logs

### 1. Verificar Logs Estruturados (JSON)

```bash
# Iniciar servidor
uvicorn src.main:app --reload

# Fazer requisição
curl http://localhost:8000/api/health

# Verificar logs no console (devem estar em JSON)
# Exemplo de log esperado:
{
  "timestamp": "2026-01-04T...",
  "level": "INFO",
  "message": "Request: GET /api/health",
  "request_id": "uuid-here",
  "method": "GET",
  "path": "/api/health"
}
```

### 2. Verificar Logs de Webhook

```bash
# Enviar webhook
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "message": "Teste",
    "messageType": "text"
  }'

# Verificar logs contêm:
# - log_webhook_received com phone e payload_size
# - log_webhook_response com status_code e duration_ms
# - Logs do processamento do agente
```

### 3. Verificar Logs de API Calls

```bash
# Se WHATSAPP_API_URL estiver configurado, tentar enviar mensagem
# (pode falhar se credenciais não estiverem corretas, mas deve logar)
# Verificar logs contêm:
# - log_api_call com service, method, endpoint, status_code, duration_ms
```

---

## 🐳 Testes com Docker

### 1. Build e Execução

```bash
# Build da imagem
docker build -t seleto-sdr-agent .

# Executar container
docker run -p 8000:8000 --env-file .env seleto-sdr-agent

# Ou com docker-compose
docker-compose up --build
```

### 2. Health Check do Container

```bash
# Verificar health check do container
docker ps
# Verificar status "healthy"

# Ou manualmente
docker exec <container_id> python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
```

---

## 🔍 Checklist de Validação

### Infraestrutura (TECH-001, TECH-003, TECH-004)
- [ ] Servidor inicia sem erros
- [ ] Endpoint `/health` retorna 200
- [ ] Endpoint `/api/health` retorna JSON válido
- [ ] Logs aparecem em formato JSON (ou text conforme config)
- [ ] Variáveis de ambiente carregadas corretamente
- [ ] Nenhum token hardcoded no código

### Webhook (TECH-005)
- [ ] Webhook recebe mensagem de texto
- [ ] Webhook recebe mensagem de áudio
- [ ] Telefone normalizado corretamente
- [ ] Resposta HTTP 200 em < 2s
- [ ] Logs de entrada/saída funcionando
- [ ] Validação de autenticação funciona (se configurado)

### Agente (US-001, US-002)
- [ ] Primeira mensagem recebe saudação
- [ ] Saudação menciona "Seleto Industrial"
- [ ] Agente pergunta sobre necessidade
- [ ] Máximo de 2 perguntas diretas por resposta
- [ ] Dados extraídos progressivamente
- [ ] Dados parciais persistidos
- [ ] Perguntas contextualizadas com dados anteriores

### Serviços
- [ ] Extração de dados funciona (nome, cidade, produto, etc.)
- [ ] Normalização de telefone funciona
- [ ] Memória de conversa mantém histórico
- [ ] Controle de ritmo de perguntas funciona

---

## 🚨 Limitações Conhecidas

### O que NÃO pode ser testado sem configuração:

1. **Envio real de WhatsApp** — Requer:
   - `WHATSAPP_API_URL` configurado
   - `WHATSAPP_API_TOKEN` válido
   - Ou variáveis Z-API configuradas

2. **Transcrição de áudio real** — Requer:
   - `OPENAI_API_KEY` válida
   - URL de áudio acessível

3. **Persistência no Supabase** — Requer:
   - `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` configurados
   - Tabelas criadas (TECH-002 já validado)

4. **Integração com Piperun** — Não implementado ainda (TECH-015+)

5. **Integração com Chatwoot** — Não implementado ainda (TECH-022)

---

## 📝 Exemplos de Scripts de Teste

### Script Completo de Teste de Fluxo

```python
# test_full_flow.py
import asyncio
import httpx
import json

async def test_full_conversation_flow():
    """Testa fluxo completo de conversa."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Health check
        health = await client.get(f"{base_url}/api/health")
        assert health.status_code == 200
        print("✅ Health check OK")
        
        # 2. Primeira mensagem
        payload1 = {
            "phone": "5511999999999",
            "senderName": "Teste Lead",
            "message": "Olá, preciso de uma formadora de hambúrguer",
            "messageId": "test-001",
            "messageType": "text"
        }
        response1 = await client.post(
            f"{base_url}/webhook/whatsapp",
            json=payload1
        )
        assert response1.status_code == 200
        print("✅ Primeira mensagem processada")
        
        # 3. Segunda mensagem (fornecendo mais dados)
        payload2 = {
            "phone": "5511999999999",
            "senderName": "Teste Lead",
            "message": "Sou João Silva, de São Paulo, SP",
            "messageId": "test-002",
            "messageType": "text"
        }
        response2 = await client.post(
            f"{base_url}/webhook/whatsapp",
            json=payload2
        )
        assert response2.status_code == 200
        print("✅ Segunda mensagem processada")
        
        print("\n✅ Fluxo completo testado com sucesso!")

if __name__ == "__main__":
    asyncio.run(test_full_conversation_flow())
```

**Executar:**
```bash
python test_full_flow.py
```

---

## 🎯 Próximos Passos para Testes

Para expandir a cobertura de testes, considere criar:

1. **Testes unitários para:**
   - `data_extraction.py` — Extração de dados
   - `validation.py` — Normalização e validação
   - `conversation_memory.py` — Memória de conversa
   - `whatsapp.py` — Envio de mensagens (com mocks)

2. **Testes de integração para:**
   - Fluxo completo de webhook → agente → resposta
   - Persistência de dados (quando Supabase estiver configurado)
   - Transcrição de áudio (com mock de URL)

3. **Testes E2E (quando integrações estiverem prontas):**
   - Webhook real do WhatsApp
   - Envio real de mensagens
   - Persistência no Supabase
   - Criação de oportunidades no Piperun

---

*Última atualização: 2026-01-04*

