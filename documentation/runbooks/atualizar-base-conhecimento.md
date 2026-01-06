# Runbook: Atualizar Base de Conhecimento

## Objetivo

Este runbook descreve como atualizar a base de conhecimento do agente SDR, incluindo informações de equipamentos, FAQs e respostas padrão. A base de conhecimento é usada para responder dúvidas técnicas sobre os produtos da Seleto Industrial.

## Pré-requisitos

- Acesso ao repositório Git
- Conhecimento de XML (para prompts) e TXT (para equipamentos)
- Revisão do conteúdo por especialista de produto
- Ambiente de desenvolvimento para testes

## Estrutura da Base de Conhecimento

```
prompts/
├── sp_agente_v1.xml          # System prompt principal do agente
└── equipamentos/
    ├── prompt_manus.txt      # Descrições detalhadas de equipamentos
    └── resumo_maquinas.txt   # Resumo das máquinas disponíveis
```

## Arquivos e Propósito

| Arquivo | Propósito | Formato |
|---------|-----------|---------|
| `sp_agente_v1.xml` | Comportamento e personalidade do agente | XML |
| `prompt_manus.txt` | Especificações técnicas dos equipamentos | TXT |
| `resumo_maquinas.txt` | Visão geral e produtividade | TXT |

## Passos

### 1. Preparar Alterações

1. **Criar branch de trabalho:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b update/knowledge-base-YYYY-MM-DD
   ```

2. **Fazer backup dos arquivos atuais:**
   ```bash
   cp prompts/equipamentos/*.txt prompts/equipamentos/backup/
   ```

### 2. Atualizar Informações de Equipamentos

#### Editar `prompt_manus.txt`

```bash
# Abrir arquivo para edição
code prompts/equipamentos/prompt_manus.txt
```

**Formato esperado:**
```text
=== FORMADORAS DE HAMBÚRGUER ===

- Formadora Manual FBM100
  Capacidade: 500-600 hambúrgueres/dia
  Cuba: 1,5kg
  Peso médio: 80-200g
  Indicação: Pequenos restaurantes, food trucks

- Formadora Semi Automática FB300
  Capacidade: 300-350 hambúrgueres/hora
  Reservatório: 5kg
  Peso médio: 80-200g
  Indicação: Restaurantes de médio porte
```

**Diretrizes de conteúdo:**
- Use linguagem clara e objetiva
- Inclua especificações técnicas mensuráveis
- Mantenha consistência de formato
- NÃO inclua preços ou condições comerciais

#### Editar `resumo_maquinas.txt`

```bash
code prompts/equipamentos/resumo_maquinas.txt
```

**Formato esperado:**
```text
Linha de Formadoras:
- FBM100: Manual, ideal para iniciantes
- FB300: Semi-automática, médio volume
- FB700: Automática, alto volume
- SE SmartPro: Elétrica, industrial
- SE3000: Industrial, 3.000/hora
- SE6000: Industrial, 6.000/hora
```

### 3. Atualizar System Prompt (se necessário)

O system prompt (`sp_agente_v1.xml`) define o comportamento do agente:

```bash
code prompts/sp_agente_v1.xml
```

**Seções do system prompt:**
- `<persona>` - Identidade e tom de voz
- `<knowledge>` - Referência à base de conhecimento
- `<guardrails>` - Regras de segurança comercial
- `<escalation>` - Quando escalar para humano

**CUIDADO:** Alterações no system prompt afetam todo o comportamento do agente. Teste extensivamente.

### 4. Validar Formato

```python
# scripts/validate_knowledge_base.py
from pathlib import Path
import xml.etree.ElementTree as ET

def validate_system_prompt():
    """Validar XML do system prompt."""
    try:
        path = Path("prompts/sp_agente_v1.xml")
        ET.parse(path)
        print("✅ System prompt XML válido")
        return True
    except ET.ParseError as e:
        print(f"❌ Erro de XML: {e}")
        return False

def validate_equipment_files():
    """Validar arquivos de equipamentos."""
    equipment_dir = Path("prompts/equipamentos")
    valid = True

    for txt_file in equipment_dir.glob("*.txt"):
        content = txt_file.read_text(encoding="utf-8")
        if len(content) < 100:
            print(f"⚠️  Arquivo {txt_file.name} parece muito curto")
            valid = False
        else:
            print(f"✅ {txt_file.name}: {len(content)} caracteres")

    return valid

if __name__ == "__main__":
    validate_system_prompt()
    validate_equipment_files()
```

### 5. Testar Localmente

```bash
# Iniciar servidor local
uvicorn src.main:app --reload

# Testar busca de conhecimento
python -c "
from src.services.knowledge_base import get_knowledge_base

kb = get_knowledge_base()
kb.load_equipment_files()

# Testar busca
result = kb.search_knowledge_base('formadora hamburguer')
print(result)
"
```

### 6. Executar Testes

```bash
# Testes da base de conhecimento
pytest tests/services/test_knowledge_base.py -v

# Testes do agente
pytest tests/agents/test_sdr_agent.py -v
```

### 7. Commit e Deploy

```bash
# Adicionar alterações
git add prompts/

# Commit com mensagem descritiva
git commit -m "Update knowledge base: [descrição das alterações]

- Atualizado [equipamento X]
- Adicionado [novo equipamento Y]
- Corrigido [informação Z]"

# Push e criar PR
git push origin update/knowledge-base-YYYY-MM-DD
```

### 8. Deploy em Produção

Após aprovação do PR:

```bash
# Merge e deploy
git checkout main
git pull origin main

# O deploy automático deve aplicar as alterações
# Ou fazer deploy manual:
docker compose pull
docker compose up -d
```

## Verificação

1. **Verificar carregamento:**
   ```bash
   # Nos logs, procurar por
   grep "Knowledge base loaded" /var/log/seleto/app.log
   ```

2. **Testar perguntas:**
   - Enviar mensagem via WhatsApp: "Qual formadora vocês recomendam?"
   - Verificar se a resposta usa as novas informações

3. **Verificar no Chatwoot:**
   - As respostas do agente devem refletir o novo conteúdo

## Rollback

Se o novo conteúdo causar problemas:

1. **Reverter para versão anterior:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Restaurar backup:**
   ```bash
   cp prompts/equipamentos/backup/*.txt prompts/equipamentos/
   ```

3. **Reiniciar serviço:**
   ```bash
   docker compose restart app
   ```

4. **Forçar reload da base de conhecimento:**
   ```python
   # O reload acontece automaticamente no restart
   # Para forçar em runtime:
   from src.services.knowledge_base import get_knowledge_base
   kb = get_knowledge_base()
   kb._loaded = False
   kb.load_equipment_files()
   ```

## Troubleshooting

### Erro: "Equipment directory not found"
1. Verifique se o diretório `prompts/equipamentos/` existe
2. Verifique permissões de leitura

### Erro: "Failed to load equipment file"
1. Verifique encoding do arquivo (deve ser UTF-8)
2. Verifique se não há caracteres inválidos

### Agente responde com informações antigas
1. O cache pode estar ativo - reinicie o serviço
2. Verifique se os arquivos foram salvos corretamente
3. Verifique se o deploy foi executado

### Respostas do agente incorretas
1. Verifique o conteúdo do arquivo
2. Teste a busca localmente
3. Revise o system prompt

### Guardrails não funcionando
1. Verifique a lista de `COMMERCIAL_KEYWORDS` em `knowledge_base.py`
2. Verifique a lista de `TECHNICAL_KEYWORDS`
3. Adicione novas palavras-chave se necessário

## Boas Práticas

1. **Revisão de conteúdo:**
   - Sempre tenha revisão por especialista de produto
   - Verifique consistência de informações

2. **Versionamento:**
   - Use branches para alterações
   - Mantenha histórico de mudanças

3. **Testes:**
   - Teste com perguntas variadas
   - Verifique guardrails (perguntas comerciais)

4. **Documentação:**
   - Documente o que foi alterado no commit
   - Mantenha changelog se necessário

5. **Backup:**
   - Mantenha backup antes de grandes alterações
   - Use Git para histórico completo

## Categorias de Equipamentos

Referência para adicionar novos equipamentos:

| Categoria | Palavras-chave de busca |
|-----------|-------------------------|
| formadora | formadora, hambúrguer, fbm, fb300, fb700, smartpro, se3000, se6000 |
| cortadora | cortadora, corte, bife, cubo, tira, ct200, filetadora, fs150 |
| ensacadeira | ensacadeira, linguiça, embutido |
| misturador | misturador, homogeneizador, mistura |
| linha_automatica | linha automática, epe1200, espeto |

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Arquivos relacionados:** `src/services/knowledge_base.py`, `prompts/equipamentos/*`
