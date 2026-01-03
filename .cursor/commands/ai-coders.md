# AI Coders Context CLI

Estou usando uma ferramenta de CLI chamada **ai-coders/context** para criar planos estruturados.

---

## Comando: `plan`

Cria um plano de colaboração que vincula guias de documentação e playbooks de agentes, ou preenche um plano existente com assistência de LLM.

### Uso

```bash
npx @ai-coders/context plan <plan-name>
```

### Opções

#### Configuração de Saída

| Opção | Descrição |
|-------|-----------|
| `-o, --output <dir>` | Diretório scaffold contendo `docs/` e `agents/` (padrão: `./.context`) |
| `--title <title>` | Título customizado para o documento do plano |
| `--summary <text>` | Inicializa o plano com um resumo ou declaração de objetivo |

#### Modo de Operação

| Opção | Descrição |
|-------|-----------|
| `-f, --force` | Sobrescreve o plano se já existir (modo scaffold) |
| `--fill` | Usa uma LLM para preencher ou atualizar o plano ao invés de criar scaffold |
| `--dry-run` | Visualiza as mudanças sem escrever arquivos |

#### Configuração da LLM (modo fill)

| Opção | Descrição |
|-------|-----------|
| `-k, --api-key <key>` | Chave de API para o provedor de LLM selecionado |
| `-m, --model <model>` | Modelo LLM a ser usado (padrão: `x-ai/grok-4-fast`) |
| `-p, --provider <name>` | Provedor (apenas `openrouter`) |
| `--base-url <url>` | URL base customizada para OpenRouter |
| `--prompt <file>` | Prompt de instrução a seguir (opcional; usa instruções padrão quando omitido) |

#### Análise de Repositório

| Opção | Descrição |
|-------|-----------|
| `-r, --repo <path>` | Raiz do repositório para sumarizar e adicionar contexto (modo fill) |
| `--include <patterns...>` | Padrões glob para incluir durante análise do repositório |
| `--exclude <patterns...>` | Padrões glob para excluir da análise do repositório |

#### Ajuda

| Opção | Descrição |
|-------|-----------|
| `-h, --help` | Exibe ajuda do comando |

---

## Exemplos de Uso

### Criar um novo plano (scaffold)

```bash
ai-context plan meu-plano --title "Plano de Desenvolvimento" --summary "Objetivo do projeto"
```

### Preencher um plano existente com LLM

```bash
ai-context plan meu-plano --fill -k $API_KEY -r ./
```

### Preview sem modificar arquivos

```bash
ai-context plan meu-plano --fill --dry-run
```
