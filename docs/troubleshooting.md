# Troubleshooting (Solução de Problemas)

> **Para o Cliente:** Este guia ajuda a resolver os problemas mais comuns que podem acontecer com o sistema. Pense nele como um "manual de primeiros socorros" - antes de chamar o suporte, consulte aqui para ver se é algo simples de resolver.

---

## Diagnóstico Rápido

### O sistema está funcionando?

```bash
# Verificar se o servidor responde
curl http://localhost:8000/health

# Verificar status detalhado
curl http://localhost:8000/api/health
```

**Respostas esperadas:**

✅ Sistema OK:
```json
{"status": "healthy"}
```

❌ Sistema com problemas:
```json
{"status": "unhealthy", "services": {"supabase": "disconnected"}}
```

---

## Problemas Comuns

### 1. Servidor não inicia

> **Para o Cliente:** O sistema não "liga" quando você tenta iniciar.

**Sintoma:** Erro ao executar `uvicorn src.main:app`

**Causas e Soluções:**

| Causa | Solução |
|-------|---------|
| Ambiente virtual não ativado | `.\venv\Scripts\activate` (Windows) |
| Dependências não instaladas | `pip install -r requirements.txt` |
| Porta em uso | Usar outra porta: `--port 8001` |
| Variável de ambiente faltando | Verificar `.env` |

**Verificação passo a passo:**

```bash
# 1. Verificar ambiente virtual
python --version  # Deve ser 3.12+

# 2. Verificar dependências
pip list | grep fastapi

# 3. Verificar porta
netstat -an | grep 8000

# 4. Verificar .env
cat .env | head -5
```

---

### 2. Erro de conexão com Supabase

> **Para o Cliente:** O sistema não consegue se conectar ao banco de dados.

**Sintoma:** `Error: Unable to connect to Supabase`

**Verificações:**

```bash
# Testar conexão
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
result = client.table('leads').select('*').limit(1).execute()
print('Conexão OK!', result)
"
```

**Soluções:**

| Erro | Solução |
|------|---------|
| `Invalid URL` | Verificar `SUPABASE_URL` no `.env` |
| `Invalid API key` | Verificar `SUPABASE_SERVICE_ROLE_KEY` |
| `Connection timeout` | Verificar firewall/proxy |
| `Table not found` | Executar migrations no Supabase |

---

### 3. Erro de API OpenAI

> **Para o Cliente:** A inteligência artificial não está respondendo.

**Sintoma:** `OpenAI API error` ou timeout

**Verificações:**

```bash
# Testar API Key
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Olá'}],
    max_tokens=10
)
print('API OK!', response.choices[0].message.content)
"
```

**Soluções:**

| Erro | Solução |
|------|---------|
| `401 Unauthorized` | API Key inválida ou expirada |
| `429 Too Many Requests` | Rate limit - aguarde ou aumente quota |
| `500 Internal Error` | Problema na OpenAI - aguarde |
| `Timeout` | Aumentar timeout ou reduzir contexto |

---

### 4. Webhook não recebe mensagens

> **Para o Cliente:** As mensagens do WhatsApp não estão chegando no sistema.

**Sintoma:** Mensagens enviadas no WhatsApp não são processadas

**Verificações:**

1. **URL configurada corretamente no Z-API?**
   - Acesse o painel Z-API
   - Verifique se a URL aponta para seu servidor
   - URL deve ser HTTPS em produção

2. **Servidor está acessível externamente?**
   ```bash
   # De outro computador ou celular
   curl https://seu-dominio.com/health
   ```

3. **Logs mostram a requisição?**
   ```bash
   # Ver logs em tempo real
   docker-compose logs -f sdr-agent
   ```

**Soluções:**

| Problema | Solução |
|----------|---------|
| URL HTTP em produção | Usar HTTPS |
| Servidor atrás de firewall | Abrir porta ou usar ngrok |
| URL incorreta no Z-API | Corrigir no painel |
| WhatsApp desconectado | Reconectar no Z-API |

---

### 5. Mensagens não são enviadas

> **Para o Cliente:** O sistema recebe as mensagens mas não responde.

**Sintoma:** Cliente não recebe resposta

**Verificações:**

```bash
# Testar envio manual
python -c "
import asyncio
from src.services.whatsapp import WhatsAppService

async def test():
    service = WhatsAppService()
    if service.is_configured():
        result = await service.send_message('5511999999999', 'Teste')
        print('Envio:', 'OK' if result else 'FALHOU')
    else:
        print('Z-API não configurado')

asyncio.run(test())
"
```

**Soluções:**

| Problema | Solução |
|----------|---------|
| Z-API não configurado | Adicionar variáveis no `.env` |
| Token expirado | Atualizar `ZAPI_CLIENT_TOKEN` |
| Número incorreto | Verificar formato do telefone |
| Sessão desconectada | Reconectar WhatsApp no Z-API |

---

### 6. Dados não estão sendo salvos

> **Para o Cliente:** As informações dos leads não aparecem no banco de dados.

**Sintoma:** Conversas não persistem, leads não são criados

**Verificações:**

```bash
# Verificar se há dados no Supabase
# Via dashboard ou:
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
leads = client.table('leads').select('*').limit(5).execute()
print(f'Leads encontrados: {len(leads.data)}')
"
```

**Soluções:**

| Problema | Solução |
|----------|---------|
| RLS bloqueando | Verificar policies no Supabase |
| Erro silencioso | Verificar logs do servidor |
| Cache não sincronizado | Reiniciar servidor |
| Tabela não existe | Executar migrations |

---

### 7. Classificação de temperatura incorreta

> **Para o Cliente:** Leads estão sendo classificados de forma errada (quente quando deveria ser frio, etc).

**Sintoma:** Temperatura não reflete engajamento real

**Verificações:**

1. **Dados do lead estão completos?**
   - Verificar se nome, produto, volume foram extraídos

2. **Prompt de classificação está correto?**
   - Verificar `prompts/system_prompt/sp_calcula_temperatura.xml`

**Soluções:**

| Problema | Solução |
|----------|---------|
| Poucos dados | Aguardar mais mensagens antes de classificar |
| Prompt inadequado | Ajustar critérios no XML |
| Erro na extração | Verificar logs de data_extraction |

---

### 8. Resposta do agente genérica/incorreta

> **Para o Cliente:** O robô não está respondendo de forma adequada às perguntas.

**Sintoma:** Respostas não contextuais ou irrelevantes

**Verificações:**

1. **System prompt está carregando?**
   ```python
   from src.services.prompt_loader import load_system_prompt_from_xml
   prompt = load_system_prompt_from_xml('prompts/system_prompt/sp_agente_v1.xml')
   print(f'Prompt carregado: {len(prompt)} caracteres')
   ```

2. **Histórico está sendo passado?**
   - Verificar logs para "messages_for_llm"

**Soluções:**

| Problema | Solução |
|----------|---------|
| Prompt não carrega | Verificar caminho do arquivo |
| Histórico vazio | Verificar conversation_memory |
| Token limit | Reduzir max_messages |

---

## Logs e Diagnóstico

### Onde ver os logs

| Ambiente | Comando |
|----------|---------|
| Local | Terminal onde o servidor roda |
| Docker | `docker-compose logs -f` |
| Railway | Dashboard → Logs |
| Render | Dashboard → Logs |

### Entendendo os logs

```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "ERROR",
  "message": "Erro ao processar mensagem",
  "request_id": "abc-123",
  "phone": "5511999999999",
  "error": "Connection refused"
}
```

| Campo | Significado |
|-------|-------------|
| `level` | Severidade (ERROR, WARNING, INFO) |
| `message` | Descrição do evento |
| `request_id` | ID único para rastrear requisição |
| `phone` | Telefone relacionado |
| `error` | Detalhes do erro |

### Aumentar verbosidade

```env
# No .env
LOG_LEVEL=DEBUG
```

---

## Comandos Úteis

### Reiniciar o sistema

```bash
# Local
Ctrl+C  # Parar
uvicorn src.main:app --reload  # Reiniciar

# Docker
docker-compose restart

# Com rebuild
docker-compose up -d --build
```

### Limpar cache

```bash
# Python
find . -type d -name __pycache__ -exec rm -rf {} +

# Docker
docker system prune -f
```

### Verificar recursos

```bash
# Memória e CPU
docker stats

# Espaço em disco
df -h
```

---

## Problemas de Performance

### Sistema lento

**Possíveis causas:**

1. **OpenAI lento** - Horário de pico
2. **Muitas mensagens** - Rate limiting
3. **Banco sobrecarregado** - Muitas queries

**Soluções:**

```bash
# Verificar tempo de resposta da OpenAI
time python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Olá'}],
    max_tokens=10
)
"
```

### Uso excessivo de memória

```bash
# Verificar memória do processo
ps aux | grep python

# Reiniciar para liberar
docker-compose restart
```

---

## Quando Escalar para Suporte

Se após seguir este guia o problema persistir:

1. **Colete informações:**
   - Logs dos últimos 30 minutos
   - Passos para reproduzir
   - Versão do sistema

2. **Documente:**
   - O que estava funcionando antes
   - O que mudou recentemente
   - Frequência do problema

3. **Entre em contato:**
   - Abra uma issue no repositório
   - Envie email com os detalhes
   - Inclua logs relevantes (sem credenciais!)

---

## FAQ (Perguntas Frequentes)

### O sistema funciona offline?

Não. Ele precisa de conexão com:
- OpenAI (IA)
- Supabase (banco)
- Z-API (WhatsApp)

### Quantas mensagens aguenta por minuto?

Depende dos limites da OpenAI e Z-API. Em média, ~60 mensagens/minuto.

### Posso usar outro modelo de IA?

Sim, mas precisaria de ajustes no código. O sistema foi otimizado para GPT-4o.

### Como faço backup dos dados?

Os dados estão no Supabase, que faz backup automático. Para export manual, use o dashboard.

### O sistema aprende com as conversas?

Não automaticamente. O modelo é fixo (GPT-4o). Melhorias vêm de ajustes no prompt.

---

## Glossário de Erros

| Erro | Significado | Ação |
|------|-------------|------|
| `ConnectionRefused` | Servidor não acessível | Verificar se está rodando |
| `Timeout` | Operação demorou demais | Aumentar timeout |
| `401 Unauthorized` | Credencial inválida | Verificar API keys |
| `429 Too Many Requests` | Rate limit | Aguardar |
| `500 Internal Server Error` | Erro no servidor | Ver logs detalhados |
| `502 Bad Gateway` | Proxy com problema | Verificar nginx/load balancer |
| `503 Service Unavailable` | Serviço indisponível | Serviço externo fora |

---

[← Voltar ao Índice](./README.md) | [Anterior: Segurança](./seguranca.md)
