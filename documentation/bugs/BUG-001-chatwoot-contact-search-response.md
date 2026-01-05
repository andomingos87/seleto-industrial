# BUG-001: Chatwoot Contact Search Response Structure Mismatch

## Status
**Aberto** | Identificado em: 2026-01-05

## Resumo
O serviço `chatwoot_sync.py` assume que a API de busca de contatos do Chatwoot retorna uma lista, mas a API retorna um dicionário com estrutura paginada.

## Erro Observado

```
KeyError: 0
File "/app/src/services/chatwoot_sync.py", line 160, in _get_or_create_chatwoot_contact
    contact_id = contacts[0].get("id")
                 ~~~~~~~~^^^
```

## Análise

### Código Atual (linha 156-160)
```python
if search_response.status_code == 200:
    contacts = search_response.json()
    if contacts and len(contacts) > 0:
        contact_id = contacts[0].get("id")  # <-- Assume que contacts é uma lista
```

### Problema
O código assume que `search_response.json()` retorna uma **lista** de contatos:
```json
[
  {"id": 1, "name": "João", "phone_number": "+5511999999999"},
  {"id": 2, "name": "Maria", "phone_number": "+5511888888888"}
]
```

Porém, a API do Chatwoot (`/api/v1/accounts/{account_id}/contacts/search`) retorna um **dicionário** com estrutura paginada:
```json
{
  "payload": [
    {"id": 1, "name": "João", "phone_number": "+5511999999999"}
  ],
  "meta": {
    "count": 1,
    "current_page": 1
  }
}
```

### Por que `KeyError: 0`?
Quando você tenta acessar `contacts[0]` em um dicionário, Python interpreta `0` como uma **chave** do dicionário, não como um índice de lista. Como não existe a chave `0` no dicionário, ocorre `KeyError: 0`.

## Impacto
- **Severidade**: Baixa (não impede o funcionamento principal do agente)
- **Funcionalidade afetada**: Sincronização de mensagens com Chatwoot
- **Consequência**: Mensagens não são replicadas no Chatwoot para acompanhamento humano

## Solução Proposta

### Opção 1: Extrair lista do payload
```python
if search_response.status_code == 200:
    response_data = search_response.json()
    # Chatwoot retorna {payload: [...], meta: {...}}
    contacts = response_data.get("payload", [])
    if contacts and len(contacts) > 0:
        contact_id = contacts[0].get("id")
```

### Opção 2: Verificar tipo da resposta (mais defensivo)
```python
if search_response.status_code == 200:
    response_data = search_response.json()
    # Suporta ambos: lista direta ou dicionário com payload
    if isinstance(response_data, list):
        contacts = response_data
    elif isinstance(response_data, dict):
        contacts = response_data.get("payload", [])
    else:
        contacts = []

    if contacts and len(contacts) > 0:
        contact_id = contacts[0].get("id")
```

## Arquivos Afetados
- `src/services/chatwoot_sync.py` (linhas 156-165)

## Referências
- [Chatwoot API - Search Contacts](https://www.chatwoot.com/developers/api/#tag/Contacts/operation/contactSearch)
- Log de erro: fly.io logs 2026-01-05T13:17:34Z

## Notas Adicionais
- O mesmo padrão de resposta paginada pode afetar outras chamadas à API do Chatwoot
- Verificar também a chamada de listagem de conversas (linha 76) que pode ter o mesmo problema
- A integração com Chatwoot é secundária - o agente funciona sem ela
