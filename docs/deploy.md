# Deploy e Configuração

> **Para o Cliente:** Este documento explica como colocar o sistema para funcionar em um servidor. É como "ligar" o sistema e deixá-lo disponível 24 horas. Existem diferentes formas de fazer isso, desde a mais simples (para testes) até a mais robusta (para produção).

---

## Visão Geral

O sistema pode ser implantado de várias formas:

| Método | Complexidade | Uso Recomendado |
|--------|--------------|-----------------|
| Local (desenvolvimento) | Baixa | Testes e desenvolvimento |
| Docker | Média | Staging e produção |
| Cloud (Railway, Render) | Baixa | Produção simplificada |
| Kubernetes | Alta | Produção escalável |

---

## Pré-requisitos

### Software Necessário

- **Python 3.12+** - Linguagem principal
- **pip** - Gerenciador de pacotes Python
- **Git** - Controle de versão
- **Docker** (opcional) - Containerização

### Contas e Serviços

- **Supabase** - Banco de dados (obrigatório)
- **OpenAI** - API de IA (obrigatório)
- **Z-API** - WhatsApp (para integração completa)
- **Chatwoot** - Interface visual (opcional)

---

## Configuração de Ambiente

### 1. Variáveis de Ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

**Arquivo `.env`:**

```env
# ============================================
# APLICAÇÃO
# ============================================
APP_NAME="Seleto Industrial SDR Agent"
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
LOG_FORMAT=json

# ============================================
# OPENAI (OBRIGATÓRIO)
# ============================================
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_MODEL=gpt-4o

# ============================================
# SUPABASE (OBRIGATÓRIO)
# ============================================
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...sua-chave...

# ============================================
# Z-API - WHATSAPP (OPCIONAL)
# ============================================
ZAPI_INSTANCE_ID=sua-instancia
ZAPI_INSTANCE_TOKEN=seu-token
ZAPI_CLIENT_TOKEN=seu-client-token

# ============================================
# CHATWOOT (OPCIONAL)
# ============================================
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=seu-token
CHATWOOT_ACCOUNT_ID=12345

# ============================================
# PIPERUN CRM (OPCIONAL)
# ============================================
PIPERUN_API_URL=https://api.pipe.run/v1
PIPERUN_API_TOKEN=seu-token
PIPERUN_PIPELINE_ID=123
PIPERUN_STAGE_ID=456
PIPERUN_ORIGIN_ID=789
```

### 2. Validação de Configuração

Após configurar, valide:

```bash
# Ativar ambiente virtual
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Verificar se carrega sem erros
python -c "from src.config.settings import settings; print(settings.APP_NAME)"
```

---

## Deploy Local (Desenvolvimento)

> **Para o Cliente:** Ideal para testar o sistema antes de colocar em produção.

### Passo a Passo

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd seleto_industrial

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 6. Execute o servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Verificação

- Acesse: `http://localhost:8000/health`
- Documentação: `http://localhost:8000/docs`

---

## Deploy com Docker

> **Para o Cliente:** Docker empacota todo o sistema em um "container" - como uma caixa que contém tudo que o sistema precisa para funcionar. Isso garante que funcione igual em qualquer servidor.

### Arquivos Docker

**Dockerfile:**
```dockerfile
# Imagem base Python
FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Copiar dependências primeiro (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY src/ ./src/
COPY prompts/ ./prompts/

# Variáveis de ambiente padrão
ENV HOST=0.0.0.0
ENV PORT=8000

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  sdr-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DEBUG=false
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Comandos Docker

```bash
# Construir imagem
docker-compose build

# Iniciar em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down

# Reconstruir após mudanças
docker-compose up -d --build
```

### Verificação Docker

```bash
# Status do container
docker-compose ps

# Logs do container
docker-compose logs sdr-agent

# Acessar shell do container
docker-compose exec sdr-agent /bin/bash
```

---

## Deploy em Cloud

### Railway

> **Para o Cliente:** Railway é uma plataforma que cuida de toda a infraestrutura. Você só precisa conectar o código e ele faz o resto.

**Passo a Passo:**

1. Acesse [railway.app](https://railway.app)
2. Crie conta com GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Selecione o repositório
5. Configure variáveis de ambiente
6. Deploy automático!

**railway.json (opcional):**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn src.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Render

> **Para o Cliente:** Render é similar ao Railway - simples de usar e gerencia a infraestrutura automaticamente.

**Passo a Passo:**

1. Acesse [render.com](https://render.com)
2. "New" → "Web Service"
3. Conecte repositório GitHub
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
5. Adicione variáveis de ambiente
6. Deploy!

**render.yaml (opcional):**
```yaml
services:
  - type: web
    name: seleto-sdr-agent
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
```

### Heroku

```bash
# Criar Procfile
echo "web: uvicorn src.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create seleto-sdr-agent
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set SUPABASE_URL=https://...
git push heroku main
```

---

## Configuração de Produção

### Checklist de Produção

- [ ] `APP_ENV=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=INFO` (ou WARNING)
- [ ] `LOG_FORMAT=json`
- [ ] Todas as credenciais configuradas
- [ ] HTTPS habilitado
- [ ] Backup do banco configurado
- [ ] Monitoramento ativo

### Variáveis de Produção

```env
# Produção
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Timeouts ajustados
OPENAI_TIMEOUT=30
ZAPI_TIMEOUT=10

# Retry configurado
MAX_RETRIES=3
INITIAL_BACKOFF=1.0
```

### HTTPS/SSL

Para produção, HTTPS é obrigatório:

- **Railway/Render**: HTTPS automático
- **Docker + Nginx**: Configure certificado SSL
- **Load Balancer**: Termine SSL no LB

---

## Webhooks Z-API

### Configuração no Painel Z-API

Após deploy, configure os webhooks no Z-API:

| Webhook | URL |
|---------|-----|
| Received | `https://seu-dominio.com/webhook/text` |
| ReceivedAudio | `https://seu-dominio.com/webhook/audio` |

### Teste de Webhook

```bash
# Testar localmente com ngrok
ngrok http 8000

# Copie a URL gerada e configure no Z-API
# Ex: https://abc123.ngrok.io/webhook/text
```

---

## Monitoramento

### Health Checks

Configure health checks em seu provedor:

```
URL: /health
Método: GET
Intervalo: 30s
Timeout: 10s
```

### Logs

**Formato JSON (produção):**
```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "level": "INFO",
  "message": "Mensagem processada",
  "request_id": "uuid",
  "phone": "5511999999999"
}
```

**Visualização:**
- Railway: Dashboard → Logs
- Render: Dashboard → Logs
- Docker: `docker-compose logs -f`

### Alertas Recomendados

| Métrica | Threshold | Ação |
|---------|-----------|------|
| Health check fail | 3 consecutivos | Alerta crítico |
| Response time | >5s | Alerta warning |
| Error rate | >5% | Alerta crítico |
| Memory usage | >80% | Alerta warning |

---

## Scaling

### Horizontal (Múltiplas Instâncias)

```yaml
# docker-compose.yml com scale
services:
  sdr-agent:
    deploy:
      replicas: 3
```

### Vertical (Mais Recursos)

- Railway/Render: Upgrade do plano
- Docker: Ajustar limits
```yaml
services:
  sdr-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Considerações

O sistema é **stateless** (estado no Supabase), então:
- ✅ Pode escalar horizontalmente
- ✅ Load balancing funciona
- ✅ Sem sticky sessions necessário

---

## Rollback

### Com Docker

```bash
# Listar imagens anteriores
docker images

# Rollback para versão anterior
docker-compose down
docker tag seleto-sdr-agent:previous seleto-sdr-agent:latest
docker-compose up -d
```

### Com Git

```bash
# Voltar para commit anterior
git revert HEAD
git push

# Ou resetar (cuidado em produção)
git reset --hard HEAD~1
git push -f
```

### Em Cloud

- Railway: Rollback via dashboard
- Render: Rollback via dashboard
- Heroku: `heroku rollback`

---

## Troubleshooting de Deploy

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs --tail=100 sdr-agent

# Verificar se .env existe
cat .env

# Testar build localmente
docker-compose build --no-cache
```

### Erro de conexão com Supabase

```bash
# Testar conectividade
python -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
print(client.table('leads').select('*').limit(1).execute())
"
```

### Webhook não recebido

1. Verificar URL no painel Z-API
2. Testar endpoint manualmente:
```bash
curl -X POST https://seu-dominio.com/webhook/text \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "text": {"message": "teste"}}'
```
3. Verificar logs do servidor

### OpenAI timeout

```env
# Aumentar timeout
OPENAI_TIMEOUT=60
```

---

## Backup e Recuperação

### Banco de Dados (Supabase)

- Backups automáticos diários
- Point-in-time recovery (planos pagos)
- Export manual via dashboard

### Código

```bash
# Backup do repositório
git bundle create backup.bundle --all
```

### Configurações

```bash
# Backup de .env (guarde em local seguro!)
cp .env .env.backup
# NUNCA commite .env no git!
```

---

## Custos Estimados

### Serviços Externos

| Serviço | Plano | Custo Mensal |
|---------|-------|--------------|
| OpenAI | Pay-as-you-go | ~$20-50 |
| Supabase | Free / Pro | $0 / $25 |
| Z-API | Básico | ~R$100 |
| Chatwoot | Self-hosted | $0 |

### Infraestrutura

| Provedor | Plano | Custo Mensal |
|----------|-------|--------------|
| Railway | Hobby | ~$5-20 |
| Render | Starter | ~$7 |
| Heroku | Basic | ~$7 |
| VPS (Digital Ocean) | Basic | ~$12 |

---

[← Voltar ao Índice](./README.md) | [Anterior: Testes](./testes.md) | [Próximo: Segurança →](./seguranca.md)
