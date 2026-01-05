# Testes

> **Para o Cliente:** Testes são como "inspeções de qualidade" que garantem que o sistema funciona corretamente. Toda vez que fazemos uma mudança, rodamos centenas de testes automáticos para ter certeza de que nada quebrou. É assim que garantimos a qualidade do produto.

---

## Visão Geral

O projeto utiliza **pytest** como framework de testes, com cobertura abrangente de:
- Testes unitários (funções individuais)
- Testes de integração (componentes trabalhando juntos)
- Testes de API (endpoints HTTP)
- Testes de agente (comportamento da IA)

**Localização:** `tests/`

---

## Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                      # Fixtures compartilhadas
├── agents/                          # Testes do agente SDR
│   ├── __init__.py
│   ├── test_sdr_agent.py           # Funcionalidade básica
│   ├── test_sdr_agent_history.py   # Histórico de conversa
│   ├── test_sdr_agent_knowledge.py # Base de conhecimento
│   ├── test_sdr_agent_prompt.py    # Carregamento de prompt
│   ├── test_sdr_agent_temperature.py # Classificação
│   ├── test_sdr_agent_unavailable.py # Produtos indisponíveis
│   └── test_sdr_agent_upsell.py    # Sugestões de upsell
├── api/                             # Testes de API
│   ├── __init__.py
│   └── test_health.py              # Health check endpoints
├── services/                        # Testes de serviços
│   ├── __init__.py
│   ├── test_lead_crud.py           # CRUD de leads
│   ├── test_orcamento_crud.py      # CRUD de orçamentos
│   ├── test_empresa_crud.py        # CRUD de empresas
│   ├── test_conversation_persistence.py # Persistência
│   ├── test_chatwoot_sync.py       # Sincronização Chatwoot
│   ├── test_knowledge_base.py      # Base de conhecimento
│   ├── test_prompt_loader.py       # Carregamento de prompts
│   ├── test_temperature_classification.py # Classificação
│   ├── test_unavailable_products.py # Produtos indisponíveis
│   ├── test_upsell.py              # Serviço de upsell
│   └── test_whatsapp.py            # Integração WhatsApp
└── test_integration_flow.py         # Fluxo completo
```

---

## Comandos de Teste

### Rodar Todos os Testes

```bash
# Ativar ambiente virtual primeiro
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Rodar todos os testes
pytest tests/ -v
```

### Rodar com Cobertura

```bash
# Cobertura com relatório no terminal
pytest tests/ -v --cov=src --cov-report=term-missing

# Cobertura com relatório HTML
pytest tests/ -v --cov=src --cov-report=html
# Abrir htmlcov/index.html no navegador
```

### Rodar Testes Específicos

```bash
# Um arquivo específico
pytest tests/services/test_lead_crud.py -v

# Uma classe específica
pytest tests/services/test_lead_crud.py::TestLeadCRUD -v

# Um teste específico
pytest tests/services/test_lead_crud.py::TestLeadCRUD::test_create_lead -v

# Testes por padrão de nome
pytest tests/ -v -k "lead"
pytest tests/ -v -k "not slow"
```

### Rodar Categorias de Testes

```bash
# Apenas testes CRUD
pytest tests/services/test_*_crud.py -v

# Apenas testes do agente
pytest tests/agents/ -v

# Apenas testes de API
pytest tests/api/ -v
```

### Opções Úteis

```bash
# Parar no primeiro erro
pytest tests/ -v -x

# Mostrar prints durante os testes
pytest tests/ -v -s

# Rodar testes em paralelo (requer pytest-xdist)
pytest tests/ -v -n auto

# Verbose com traceback curto
pytest tests/ -v --tb=short

# Verbose com traceback completo
pytest tests/ -v --tb=long
```

---

## Fixtures (conftest.py)

> **Para o Cliente:** Fixtures são "preparações" que os testes usam. Por exemplo, criar um cliente de teste para fazer requisições HTTP, ou preparar dados simulados.

### Fixtures Principais

**Arquivo:** `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    """Cliente HTTP para testar endpoints"""
    return TestClient(app)

@pytest.fixture
def sample_lead_data():
    """Dados de exemplo para testes de lead"""
    return {
        "phone": "5511999999999",
        "name": "João Teste",
        "email": "joao@teste.com",
        "city": "São Paulo",
        "uf": "SP",
        "product": "FBM100"
    }

@pytest.fixture
def mock_openai(mocker):
    """Mock da API OpenAI para testes offline"""
    return mocker.patch("openai.OpenAI")
```

### Usando Fixtures

```python
def test_create_lead(client, sample_lead_data):
    """Usa fixture de client e sample_lead_data"""
    response = client.post("/leads", json=sample_lead_data)
    assert response.status_code == 200
```

---

## Categorias de Testes

### 1. Testes Unitários

> **Para o Cliente:** Testam partes pequenas e isoladas do código. Como testar se cada peça de um relógio funciona antes de montar o relógio todo.

**Exemplo - Normalização de Telefone:**

```python
# tests/services/test_validation.py
from src.utils.validation import normalize_phone

class TestPhoneNormalization:
    def test_normalize_with_country_code(self):
        assert normalize_phone("+55 11 99999-9999") == "5511999999999"

    def test_normalize_without_country_code(self):
        assert normalize_phone("11999999999") == "5511999999999"

    def test_normalize_with_ddd(self):
        assert normalize_phone("(11) 99999-9999") == "5511999999999"

    def test_normalize_already_normalized(self):
        assert normalize_phone("5511999999999") == "5511999999999"
```

### 2. Testes de Serviço

> **Para o Cliente:** Testam os serviços completos, como salvar um lead no banco de dados ou enviar uma mensagem.

**Exemplo - Lead CRUD:**

```python
# tests/services/test_lead_crud.py
import pytest
from src.services.lead_persistence import upsert_lead, get_lead_by_phone

class TestLeadCRUD:
    @pytest.mark.asyncio
    async def test_create_lead(self, mock_supabase):
        """Deve criar um novo lead"""
        lead = await upsert_lead("5511999999999", {
            "name": "João Silva",
            "city": "São Paulo"
        })

        assert lead is not None
        assert lead["name"] == "João Silva"
        assert lead["city"] == "São Paulo"

    @pytest.mark.asyncio
    async def test_update_existing_lead(self, mock_supabase):
        """Deve atualizar lead existente"""
        # Criar lead
        await upsert_lead("5511999999999", {"name": "João"})

        # Atualizar
        lead = await upsert_lead("5511999999999", {"city": "SP"})

        assert lead["name"] == "João"
        assert lead["city"] == "SP"

    @pytest.mark.asyncio
    async def test_idempotent_upsert(self, mock_supabase):
        """Múltiplos upserts não criam duplicatas"""
        await upsert_lead("5511999999999", {"name": "João"})
        await upsert_lead("5511999999999", {"name": "João"})

        # Deve haver apenas um lead
        lead = await get_lead_by_phone("5511999999999")
        assert lead is not None
```

### 3. Testes de API

> **Para o Cliente:** Testam os endpoints HTTP - as "portas de entrada" do sistema. Simulam requisições como se fossem feitas pelo Z-API.

**Exemplo - Health Check:**

```python
# tests/api/test_health.py
def test_health_endpoint(client):
    """GET /health deve retornar status healthy"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_health_endpoint(client):
    """GET /api/health deve retornar status dos serviços"""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "supabase" in data["services"]
```

**Exemplo - Webhook:**

```python
# tests/api/test_webhook.py
def test_text_webhook(client, mock_agent):
    """POST /webhook/text deve processar mensagem"""
    payload = {
        "phone": "5511999999999",
        "senderName": "João",
        "text": {"message": "Olá"}
    }

    response = client.post("/webhook/text", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] == True
```

### 4. Testes do Agente

> **Para o Cliente:** Testam o comportamento da inteligência artificial. Verificam se o agente responde corretamente, extrai dados, classifica leads, etc.

**Exemplo - Extração de Dados:**

```python
# tests/agents/test_sdr_agent.py
import pytest
from unittest.mock import patch, AsyncMock

class TestSDRAgent:
    @pytest.mark.asyncio
    async def test_extract_name_from_message(self):
        """Deve extrair nome da mensagem"""
        message = "Olá, meu nome é João Silva"

        with patch("src.services.data_extraction.extract_lead_data") as mock:
            mock.return_value = {"name": "João Silva"}

            data = await extract_lead_data(message, {})

            assert data["name"] == "João Silva"

    @pytest.mark.asyncio
    async def test_detect_commercial_query(self):
        """Deve detectar pergunta comercial"""
        from src.services.knowledge_base import KnowledgeBase

        kb = KnowledgeBase()

        assert kb.is_commercial_query("Qual o preço?") == True
        assert kb.is_commercial_query("Como funciona?") == False
```

**Exemplo - Classificação de Temperatura:**

```python
# tests/agents/test_sdr_agent_temperature.py
class TestTemperatureClassification:
    @pytest.mark.asyncio
    async def test_hot_lead(self):
        """Lead com urgência alta deve ser quente"""
        lead_data = {
            "name": "João",
            "product": "FBM100",
            "volume": "500kg/dia",
            "urgency": "preciso urgente"
        }

        temp, _ = await classify_lead("5511999999999", lead_data, [])

        assert temp == "quente"

    @pytest.mark.asyncio
    async def test_cold_lead(self):
        """Lead com poucos dados deve ser frio"""
        lead_data = {"name": "Maria"}

        temp, _ = await classify_lead("5511888888888", lead_data, [])

        assert temp == "frio"
```

### 5. Testes de Integração

> **Para o Cliente:** Testam o fluxo completo, do início ao fim. Como uma mensagem entra no sistema, é processada, e a resposta é gerada.

```python
# tests/test_integration_flow.py
import pytest
from unittest.mock import patch, AsyncMock

class TestIntegrationFlow:
    @pytest.mark.asyncio
    async def test_complete_message_flow(self):
        """Fluxo completo: webhook → agent → response"""

        with patch("src.services.whatsapp.WhatsAppService.send_message") as mock_send:
            mock_send.return_value = True

            # Simula webhook
            response = client.post("/webhook/text", json={
                "phone": "5511999999999",
                "senderName": "João",
                "text": {"message": "Olá, quero saber da FBM100"}
            })

            assert response.status_code == 200

            # Verifica que mensagem foi enviada
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_lead_persistence_flow(self):
        """Lead deve ser salvo durante conversa"""
        # Primeira mensagem
        client.post("/webhook/text", json={
            "phone": "5511999999999",
            "text": {"message": "Sou João de São Paulo"}
        })

        # Verificar persistência
        lead = await get_lead_by_phone("5511999999999")
        assert lead["name"] == "João"
        assert lead["city"] == "São Paulo"
```

---

## Mocking

> **Para o Cliente:** "Mocking" é simular partes do sistema que não queremos testar diretamente. Por exemplo, simulamos a OpenAI para não gastar dinheiro com chamadas de API durante os testes.

### Mock de API Externa

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_send_message_success():
    """Deve enviar mensagem com sucesso"""

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"success": True}
        )

        service = WhatsAppService()
        result = await service.send_message("5511999999999", "Olá")

        assert result == True
```

### Mock do Supabase

```python
@pytest.fixture
def mock_supabase(mocker):
    """Mock do cliente Supabase"""
    mock_client = mocker.MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value.data = []
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "123", "phone": "5511999999999"}
    ]

    mocker.patch(
        "src.services.conversation_persistence.get_supabase_client",
        return_value=mock_client
    )

    return mock_client
```

### Mock da OpenAI

```python
@pytest.fixture
def mock_openai(mocker):
    """Mock da API OpenAI"""
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(message=mocker.MagicMock(content="Resposta mock"))
    ]

    mock_client = mocker.MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    mocker.patch("openai.OpenAI", return_value=mock_client)

    return mock_client
```

---

## Cobertura de Código

### Relatório de Cobertura

```bash
# Gerar relatório
pytest tests/ --cov=src --cov-report=html

# Resultado no terminal
---------- coverage: platform win32, python 3.12.0 ----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
src/agents/sdr_agent.py                   150     12    92%
src/services/lead_persistence.py           45      3    93%
src/services/whatsapp.py                   38      5    87%
src/utils/validation.py                    25      0   100%
-----------------------------------------------------------
TOTAL                                     500     45    91%
```

### Meta de Cobertura

| Componente | Meta | Atual |
|------------|------|-------|
| Utils | 95%+ | ✅ |
| Services | 85%+ | ✅ |
| Agents | 80%+ | ✅ |
| API | 90%+ | ✅ |
| **Total** | **85%+** | ✅ |

### Ignorar Arquivos

```ini
# pytest.ini ou setup.cfg
[coverage:run]
omit =
    tests/*
    venv/*
    */__init__.py
```

---

## Boas Práticas

### Nomenclatura

```python
# ✅ BOM - Descritivo
def test_create_lead_with_valid_phone_should_succeed():
    pass

def test_create_lead_with_invalid_phone_should_fail():
    pass

# ❌ RUIM - Genérico
def test_create_lead():
    pass

def test_create_lead_2():
    pass
```

### Organização (AAA Pattern)

```python
def test_upsert_lead_updates_existing():
    # Arrange (Preparar)
    existing_lead = {"phone": "5511999999999", "name": "João"}

    # Act (Agir)
    result = await upsert_lead("5511999999999", {"city": "SP"})

    # Assert (Verificar)
    assert result["name"] == "João"
    assert result["city"] == "SP"
```

### Testes Independentes

```python
# ✅ BOM - Cada teste é independente
class TestLeadCRUD:
    def test_create_lead(self):
        # Cria e verifica
        pass

    def test_update_lead(self):
        # Cria, atualiza e verifica (não depende do anterior)
        pass

# ❌ RUIM - Testes dependentes
class TestLeadCRUD:
    lead_id = None

    def test_create_lead(self):
        self.lead_id = create_lead()  # Modifica estado compartilhado

    def test_update_lead(self):
        update_lead(self.lead_id)  # Depende do teste anterior
```

### Dados de Teste

```python
# ✅ BOM - Fixtures para dados comuns
@pytest.fixture
def sample_lead():
    return {
        "phone": "5511999999999",
        "name": "João Teste"
    }

def test_something(sample_lead):
    # Usa fixture
    pass

# ❌ RUIM - Dados hardcoded repetidos
def test_something():
    lead = {"phone": "5511999999999", "name": "João Teste"}
    pass

def test_another():
    lead = {"phone": "5511999999999", "name": "João Teste"}  # Repetição
    pass
```

---

## CI/CD Integration

### GitHub Actions (Exemplo)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Troubleshooting de Testes

### Teste falha com timeout

```bash
# Aumentar timeout
pytest tests/ -v --timeout=30
```

### Testes assíncronos falham

```python
# Certifique-se de usar o decorator
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Mock não funcionando

```python
# Verifique o caminho do patch
# ✅ Correto - onde é usado
@patch("src.agents.sdr_agent.OpenAI")

# ❌ Errado - onde é definido
@patch("openai.OpenAI")
```

### Fixture não encontrada

```python
# Fixtures devem estar em conftest.py ou no mesmo arquivo
# Ou importadas explicitamente
from tests.conftest import sample_lead_data
```

---

[← Voltar ao Índice](./README.md) | [Anterior: Agente SDR](./agente-sdr.md) | [Próximo: Deploy →](./deploy.md)
