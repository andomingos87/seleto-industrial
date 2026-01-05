# Segurança

> **Para o Cliente:** A segurança é uma prioridade máxima. Seus dados e os dados de seus clientes são protegidos por múltiplas camadas de segurança. Este documento explica como protegemos o sistema contra ameaças e garantimos a privacidade das informações.

---

## Visão Geral de Segurança

O sistema implementa segurança em múltiplas camadas:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADAS DE SEGURANÇA                         │
├─────────────────────────────────────────────────────────────────┤
│  🔒 Transporte (HTTPS/TLS)                                     │
├─────────────────────────────────────────────────────────────────┤
│  🔑 Autenticação (API Keys, Tokens)                            │
├─────────────────────────────────────────────────────────────────┤
│  🛡️ Autorização (RLS, Permissões)                              │
├─────────────────────────────────────────────────────────────────┤
│  📝 Validação (Input, Sanitização)                             │
├─────────────────────────────────────────────────────────────────┤
│  🔐 Criptografia (Dados em repouso)                            │
├─────────────────────────────────────────────────────────────────┤
│  📊 Auditoria (Logs, Monitoramento)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gestão de Credenciais

> **Para o Cliente:** Todas as senhas e chaves de acesso são tratadas com máximo cuidado. Nunca ficam visíveis no código e são armazenadas de forma segura.

### Princípios

1. **Nunca no código** - Credenciais via variáveis de ambiente
2. **Nunca no git** - `.env` sempre no `.gitignore`
3. **Mínimo privilégio** - Cada serviço tem apenas permissões necessárias
4. **Rotação regular** - Trocar chaves periodicamente

### Variáveis de Ambiente

```bash
# .env (NUNCA commitar este arquivo!)
OPENAI_API_KEY=sk-...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ZAPI_CLIENT_TOKEN=...
```

### .gitignore

```gitignore
# Arquivos de ambiente
.env
.env.local
.env.production

# Credenciais
*.pem
*.key
credentials.json
```

### Validação de Carregamento

```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str  # Obrigatório - erro se não existir
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## Segurança de Transporte

> **Para o Cliente:** Todas as comunicações são criptografadas. Ninguém consegue "interceptar" as mensagens entre o sistema e os serviços externos.

### HTTPS Obrigatório

- **Produção**: Sempre HTTPS
- **Desenvolvimento**: HTTP permitido apenas localmente
- **APIs Externas**: Todas usam HTTPS

### Verificação de Certificado

```python
# Todas as requisições verificam certificado SSL
import httpx

async with httpx.AsyncClient(verify=True) as client:
    response = await client.post(url, json=data)
```

### Headers de Segurança

```python
# Recomendados para produção (via proxy/nginx)
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## Segurança de Dados

### Supabase Row Level Security (RLS)

> **Para o Cliente:** RLS é como ter um segurança em cada tabela do banco de dados, verificando se quem está pedindo os dados tem permissão.

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE orcamentos ENABLE ROW LEVEL SECURITY;

-- Policy para service role (backend)
CREATE POLICY "Service role full access" ON leads
    FOR ALL
    USING (true);

-- Policy mais restritiva para anon (se usado)
CREATE POLICY "Read own data" ON leads
    FOR SELECT
    USING (auth.uid() = user_id);
```

### Criptografia em Repouso

- **Supabase**: Criptografia AES-256 automática
- **Backups**: Criptografados por padrão
- **Logs**: Dados sensíveis mascarados

### Mascaramento em Logs

```python
# src/utils/logging.py
def mask_sensitive_data(data: dict) -> dict:
    """Mascara dados sensíveis antes de logar"""
    sensitive_keys = ['api_key', 'token', 'password', 'secret']

    masked = data.copy()
    for key in sensitive_keys:
        if key in masked:
            masked[key] = '***MASKED***'

    return masked
```

---

## Validação de Input

> **Para o Cliente:** Todo dado que entra no sistema é verificado e "limpo" antes de ser processado. Isso previne ataques e erros.

### Normalização de Telefone

```python
# src/utils/validation.py
import re

def normalize_phone(phone: str) -> str:
    """Remove caracteres não-numéricos"""
    # Previne injeção via telefone
    digits = re.sub(r'\D', '', phone)

    # Validação de formato
    if len(digits) < 10:
        return ''

    # Adiciona código do país se necessário
    if len(digits) == 11:
        return f'55{digits}'

    return digits
```

### Validação de CNPJ

```python
def normalize_cnpj(cnpj: str) -> str:
    """Normaliza e valida CNPJ"""
    digits = re.sub(r'\D', '', cnpj)

    if len(digits) != 14:
        return ''

    return digits
```

### Validação de Payload (Pydantic)

```python
from pydantic import BaseModel, validator

class WebhookPayload(BaseModel):
    phone: str
    text: Optional[dict]

    @validator('phone')
    def validate_phone(cls, v):
        normalized = normalize_phone(v)
        if not normalized:
            raise ValueError('Telefone inválido')
        return normalized
```

---

## Segurança de XML (Prompts)

> **Para o Cliente:** Os arquivos de instrução do agente (prompts) são carregados de forma segura, prevenindo ataques que tentam acessar arquivos do servidor.

### Prevenção de Path Traversal

```python
# src/services/prompt_loader.py
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "system_prompt"

def get_system_prompt_path(filename: str) -> Path:
    """Valida que o arquivo está dentro do diretório permitido"""

    # Resolve o caminho completo
    requested_path = (PROMPTS_DIR / filename).resolve()

    # Verifica se está dentro do diretório permitido
    if not str(requested_path).startswith(str(PROMPTS_DIR.resolve())):
        raise ValueError(f"Path traversal detectado: {filename}")

    return requested_path
```

### Parser XML Seguro

```python
import xml.etree.ElementTree as ET

def load_system_prompt_from_xml(xml_path: str) -> str:
    """Carrega XML de forma segura contra XXE"""

    # Parser sem resolução de entidades externas
    parser = ET.XMLParser()

    # Desabilita DTD e entidades externas
    # (ElementTree já é seguro por padrão, mas explicitamos)

    tree = ET.parse(xml_path, parser=parser)
    return extract_prompt_content(tree)
```

### Ataques Prevenidos

| Ataque | Prevenção |
|--------|-----------|
| Path Traversal (`../../../etc/passwd`) | Validação de diretório |
| XXE (XML External Entity) | Parser seguro |
| XML Bomb | Limite de tamanho |

---

## Segurança de API

### Rate Limiting (Recomendado)

```python
# Exemplo com slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/webhook/text")
@limiter.limit("60/minute")
async def webhook_text(request: Request):
    ...
```

### Validação de Origem

```python
# Verificar que requisição vem do Z-API
ALLOWED_IPS = ['ip1.zapi.io', 'ip2.zapi.io']

def verify_origin(request: Request) -> bool:
    client_ip = request.client.host
    return client_ip in ALLOWED_IPS
```

### Timeout em Requisições

```python
# Timeout para evitar DoS
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, json=data)
```

---

## Proteção contra Ataques Comuns

### SQL Injection

**Prevenção:** Uso de ORM/Query Builder (Supabase Client)

```python
# ✅ SEGURO - Supabase client usa prepared statements
supabase.table("leads").select("*").eq("phone", phone).execute()

# ❌ INSEGURO - Nunca faça isso
query = f"SELECT * FROM leads WHERE phone = '{phone}'"
```

### XSS (Cross-Site Scripting)

**Prevenção:** API não retorna HTML, apenas JSON

```python
# Todas as respostas são JSON
return JSONResponse({"success": True, "data": data})
```

### CSRF (Cross-Site Request Forgery)

**Prevenção:** API stateless, não usa cookies de sessão

### Command Injection

**Prevenção:** Não executamos comandos shell com input do usuário

---

## Auditoria e Logging

> **Para o Cliente:** Todas as ações são registradas. Se algo der errado, conseguimos ver exatamente o que aconteceu e quando.

### O que é Logado

| Evento | Dados Registrados |
|--------|-------------------|
| Requisição HTTP | Timestamp, método, path, IP, status |
| Processamento de mensagem | Phone (hash), flow_step, duração |
| Erros | Stack trace, contexto, severity |
| Acesso a dados | Tabela, operação, timestamp |

### Formato de Log Seguro

```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "INFO",
  "message": "Mensagem processada",
  "request_id": "uuid-aqui",
  "phone_hash": "sha256(5511999999999)",  // Hash, não telefone real
  "flow_step": "process_message",
  "duration_ms": 2500
}
```

### Dados NÃO Logados

- Conteúdo completo das mensagens (privacidade)
- API keys e tokens
- Dados pessoais identificáveis (quando possível)

---

## Checklist de Segurança

### Antes do Deploy

- [ ] `.env` não está no git
- [ ] `DEBUG=false` em produção
- [ ] HTTPS configurado
- [ ] Variáveis de ambiente validadas
- [ ] RLS habilitado no Supabase
- [ ] Logs não expõem dados sensíveis

### Monitoramento Contínuo

- [ ] Alertas de erro configurados
- [ ] Rate limiting ativo
- [ ] Logs centralizados
- [ ] Backup funcionando

### Revisão Periódica

- [ ] Rotação de API keys (trimestral)
- [ ] Revisão de permissões (mensal)
- [ ] Atualização de dependências (semanal)
- [ ] Teste de penetração (anual)

---

## Resposta a Incidentes

### Em caso de vazamento de credencial

1. **Revogar imediatamente** a credencial comprometida
2. **Gerar nova** credencial
3. **Atualizar** em todos os ambientes
4. **Investigar** logs para identificar uso indevido
5. **Documentar** o incidente

### Contatos de Emergência

| Serviço | Ação |
|---------|------|
| OpenAI | Revogar API Key no dashboard |
| Supabase | Regenerar Service Role Key |
| Z-API | Contatar suporte para desconectar instância |

---

## Conformidade e Privacidade

### LGPD (Lei Geral de Proteção de Dados)

O sistema coleta e processa dados pessoais. Para conformidade:

1. **Base legal**: Consentimento ou interesse legítimo
2. **Minimização**: Coletar apenas dados necessários
3. **Transparência**: Informar sobre uso dos dados
4. **Direitos do titular**: Permitir acesso e exclusão

### Dados Coletados

| Dado | Finalidade | Base Legal |
|------|------------|------------|
| Telefone | Identificação e contato | Interesse legítimo |
| Nome | Personalização | Consentimento |
| Cidade/UF | Logística | Interesse legítimo |
| Mensagens | Atendimento | Execução de contrato |

### Retenção de Dados

| Tipo | Período |
|------|---------|
| Conversas | 2 anos |
| Leads | Enquanto cliente potencial |
| Logs | 90 dias |

---

## Boas Práticas

### Para Desenvolvedores

1. **Nunca hardcode credenciais** - Use sempre variáveis de ambiente
2. **Valide todo input** - Especialmente de fontes externas
3. **Use bibliotecas atualizadas** - Mantenha dependências em dia
4. **Revise código sensível** - Peer review em mudanças de segurança
5. **Teste cenários de ataque** - Inclua testes de segurança

### Para Operações

1. **Monitore acessos** - Alertas para padrões anormais
2. **Mantenha backups** - Testados e criptografados
3. **Documente incidentes** - Para aprendizado contínuo
4. **Treine a equipe** - Conscientização de segurança

---

## Atualizações de Segurança

### Dependências

```bash
# Verificar vulnerabilidades conhecidas
pip install safety
safety check -r requirements.txt

# Atualizar dependências
pip install --upgrade -r requirements.txt
```

### Monitoramento de CVEs

Acompanhe vulnerabilidades em:
- [OpenAI Security](https://openai.com/security)
- [Supabase Security](https://supabase.com/docs/guides/security)
- [Python CVEs](https://www.cvedetails.com/vendor/10210/Python.html)

---

[← Voltar ao Índice](./README.md) | [Anterior: Deploy](./deploy.md) | [Próximo: Troubleshooting →](./troubleshooting.md)
