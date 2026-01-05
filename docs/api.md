# Documentação da API

> **Para o Cliente:** A API é como uma lista de "comandos" que outros sistemas podem usar para conversar com o nosso. O WhatsApp usa esses comandos para enviar as mensagens dos clientes, e outros sistemas podem verificar se está tudo funcionando.

---

## Visão Geral

O Seleto Industrial SDR Agent expõe uma API RESTful construída com FastAPI. A documentação interativa está disponível automaticamente em `/docs` (Swagger UI) e `/redoc` (ReDoc).

**Base URL:**
- Desenvolvimento: `http://localhost:8000`
- Produção: Conforme configurado no deploy

---

## Autenticação

> **Para o Cliente:** Por enquanto, a segurança é garantida pelo HTTPS e pela validação dos dados recebidos. O Z-API (WhatsApp) só envia para nosso servidor, e outros não conseguem falsificar essas mensagens.

**Status Atual:** Sem autenticação explícita

**Segurança Implementada:**
- HTTPS obrigatório em produção
- Validação de payloads do Z-API
- Rate limiting implícito do Z-API
- Logs de auditoria para todas as requisições

**Roadmap:**
- API Keys para integrações externas
- JWT para endpoints administrativos
- Webhook signatures para validação

---

## Endpoints

### Health Check

#### GET /health

Verificação básica de saúde do servidor (AgentOS).

**Resposta:**
```json
{
  "status": "healthy"
}
```

| Status Code | Descrição |
|-------------|-----------|
| 200 | Servidor funcionando |
| 503 | Servidor com problemas |

---

#### GET /api/health

Verificação detalhada com status dos serviços dependentes.

**Resposta:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "supabase": "connected",
    "openai": "configured",
    "zapi": "configured",
    "chatwoot": "not_configured"
  }
}
```

| Status Code | Descrição |
|-------------|-----------|
| 200 | Todos os serviços essenciais funcionando |
| 503 | Algum serviço essencial indisponível |

---

### Webhooks (Z-API)

> **Para o Cliente:** Esses são os "portões" por onde as mensagens do WhatsApp entram no sistema. Toda vez que um cliente manda uma mensagem, o Z-API bate nesses portões.

#### POST /webhook/text

Recebe mensagens de texto do WhatsApp via Z-API.

**Headers:**
```
Content-Type: application/json
```

**Payload (Z-API format):**
```json
{
  "phone": "5511999999999",
  "senderName": "João Silva",
  "text": {
    "message": "Olá, gostaria de saber mais sobre a FBM100"
  },
  "messageId": "3EB0123456789",
  "type": "ReceivedCallback",
  "fromMe": false,
  "instanceId": "instance-abc123"
}
```

**Campos do Payload:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `phone` | string | Sim | Telefone no formato E.164 (apenas dígitos) |
| `senderName` | string | Não | Nome do remetente no WhatsApp |
| `text.message` | string | Sim | Conteúdo da mensagem de texto |
| `messageId` | string | Não | ID único da mensagem no WhatsApp |
| `type` | string | Não | Tipo de callback (geralmente "ReceivedCallback") |
| `fromMe` | boolean | Não | Se a mensagem foi enviada pelo próprio número |
| `instanceId` | string | Não | ID da instância Z-API |

**Resposta:**
```json
{
  "success": true,
  "message": "Mensagem recebida e processamento iniciado"
}
```

| Status Code | Descrição |
|-------------|-----------|
| 200 | Mensagem aceita para processamento |
| 400 | Payload inválido |
| 500 | Erro interno do servidor |

**Comportamento:**
1. Valida o payload recebido
2. Inicia processamento assíncrono
3. Retorna 200 imediatamente
4. Processa mensagem em background
5. Envia resposta via Z-API

---

#### POST /webhook/audio

Recebe mensagens de áudio do WhatsApp via Z-API.

**Headers:**
```
Content-Type: application/json
```

**Payload (Z-API format):**
```json
{
  "phone": "5511999999999",
  "senderName": "João Silva",
  "audio": {
    "audioUrl": "https://example.com/audio.ogg",
    "mimeType": "audio/ogg; codecs=opus"
  },
  "messageId": "3EB0123456789",
  "type": "ReceivedCallback",
  "fromMe": false,
  "instanceId": "instance-abc123"
}
```

**Campos Adicionais (Audio):**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `audio.audioUrl` | string | Sim | URL para download do áudio |
| `audio.mimeType` | string | Não | Tipo MIME do arquivo de áudio |

**Resposta:**
```json
{
  "success": true,
  "message": "Áudio recebido e processamento iniciado"
}
```

| Status Code | Descrição |
|-------------|-----------|
| 200 | Áudio aceito para processamento |
| 400 | Payload inválido ou URL de áudio ausente |
| 500 | Erro interno do servidor |

**Comportamento:**
1. Valida o payload recebido
2. Baixa o arquivo de áudio
3. Transcreve usando OpenAI Whisper
4. Processa texto transcrito como mensagem normal
5. Envia resposta via Z-API

---

## Modelos de Dados

### WhatsAppWebhookPayload

```python
class WhatsAppWebhookPayload(BaseModel):
    phone: str                      # Telefone E.164
    senderName: Optional[str]       # Nome do remetente
    text: Optional[TextContent]     # Conteúdo de texto
    audio: Optional[AudioContent]   # Conteúdo de áudio
    messageId: Optional[str]        # ID da mensagem
    type: Optional[str]             # Tipo de callback
    fromMe: Optional[bool]          # Se é mensagem própria
    instanceId: Optional[str]       # ID da instância

class TextContent(BaseModel):
    message: str                    # Texto da mensagem

class AudioContent(BaseModel):
    audioUrl: str                   # URL do áudio
    mimeType: Optional[str]         # Tipo MIME
```

### HealthResponse

```python
class HealthResponse(BaseModel):
    status: str                     # "healthy" ou "unhealthy"
    version: Optional[str]          # Versão da aplicação
    services: Optional[Dict]        # Status dos serviços
```

---

## Códigos de Erro

| Código | Descrição | Ação Recomendada |
|--------|-----------|------------------|
| 400 | Payload inválido | Verificar formato do JSON |
| 404 | Endpoint não encontrado | Verificar URL |
| 422 | Erro de validação | Verificar campos obrigatórios |
| 500 | Erro interno | Verificar logs do servidor |
| 503 | Serviço indisponível | Aguardar e tentar novamente |

---

## Exemplos de Uso

### cURL - Enviar Mensagem de Texto

```bash
curl -X POST http://localhost:8000/webhook/text \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "senderName": "João Silva",
    "text": {
      "message": "Olá, quero saber sobre a FBM100"
    }
  }'
```

### cURL - Verificar Saúde

```bash
curl http://localhost:8000/api/health
```

### Python - Enviar Mensagem

```python
import httpx

async def send_test_message():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhook/text",
            json={
                "phone": "5511999999999",
                "senderName": "Teste",
                "text": {"message": "Olá!"}
            }
        )
        return response.json()
```

### JavaScript - Fetch API

```javascript
fetch('http://localhost:8000/webhook/text', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    phone: '5511999999999',
    senderName: 'João',
    text: { message: 'Olá!' }
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Rate Limiting

> **Para o Cliente:** Isso é uma proteção contra sobrecarga. Se alguém tentar "bombardear" o sistema, ele se protege automaticamente.

**Status Atual:** Sem rate limiting explícito

**Proteções Existentes:**
- Z-API já limita requisições na origem
- Processamento assíncrono evita bloqueios
- Timeout em operações externas

**Roadmap:**
- 100 req/min por IP
- 30 req/min por telefone
- Burst de 10 requisições

---

## Documentação Interativa

### Swagger UI

Acesse: `http://localhost:8000/docs`

Funcionalidades:
- Testar endpoints diretamente no navegador
- Ver schemas de request/response
- Gerar código de exemplo

### ReDoc

Acesse: `http://localhost:8000/redoc`

Funcionalidades:
- Documentação formatada
- Navegação lateral
- Busca integrada

---

## Configuração do Z-API

> **Para o Cliente:** O Z-API é o serviço que conecta o WhatsApp ao nosso sistema. Você configura ele uma vez, aponta para nosso servidor, e pronto - as mensagens começam a fluir.

### Configuração do Webhook no Z-API

1. Acesse o painel do Z-API
2. Selecione sua instância
3. Configure os webhooks:

| Evento | URL | Método |
|--------|-----|--------|
| Received | `https://seu-servidor.com/webhook/text` | POST |
| ReceivedAudio | `https://seu-servidor.com/webhook/audio` | POST |

### Variáveis de Ambiente Necessárias

```env
ZAPI_INSTANCE_ID=sua-instancia
ZAPI_INSTANCE_TOKEN=seu-token
ZAPI_CLIENT_TOKEN=seu-client-token
```

---

## Tratamento de Erros

### Erros do Payload

```json
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Erros do Servidor

```json
{
  "success": false,
  "error": "Descrição do erro"
}
```

### Logs de Erro

Todos os erros são logados em formato JSON:

```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "ERROR",
  "message": "Erro ao processar mensagem",
  "request_id": "uuid-aqui",
  "phone": "5511999999999",
  "error": "Detalhes do erro"
}
```

---

## Boas Práticas

### Para Integradores

1. **Sempre trate erros** - Implemente retry com backoff exponencial
2. **Valide respostas** - Verifique o status code antes de processar
3. **Use HTTPS** - Nunca envie dados sensíveis em HTTP
4. **Log tudo** - Mantenha registros das requisições para debug

### Para Desenvolvedores

1. **Teste localmente primeiro** - Use `/docs` para testar
2. **Simule payloads do Z-API** - Copie exemplos reais
3. **Monitore logs** - Verifique erros em tempo real
4. **Use async** - Aproveite a natureza assíncrona da API

---

[← Voltar ao Índice](./README.md) | [Anterior: Arquitetura](./arquitetura.md) | [Próximo: Serviços →](./servicos.md)
