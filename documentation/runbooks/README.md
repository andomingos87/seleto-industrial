# Runbooks de Operação

Este diretório contém procedimentos operacionais documentados para cenários comuns de operação e manutenção do Seleto Industrial SDR Agent.

## Índice de Runbooks

| Runbook | Descrição | Urgência |
|---------|-----------|----------|
| [Pausar/Retomar Agente](./pausar-retomar-agente.md) | Controlar manualmente o estado do agente SDR | Alta |
| [Rotacionar Credenciais](./rotacionar-credenciais.md) | Atualizar chaves de API e tokens de acesso | Média |
| [Reprocessar Mensagens](./reprocessar-mensagens.md) | Reprocessar mensagens que falharam no processamento | Média |
| [Atualizar Base de Conhecimento](./atualizar-base-conhecimento.md) | Atualizar informações de produtos e FAQs | Baixa |
| [Verificar Saúde do Sistema](./verificar-saude-sistema.md) | Diagnosticar e verificar estado do sistema | Alta |

## Estrutura de Runbook

Cada runbook segue um formato padrão com as seguintes seções:

1. **Objetivo** - O que o procedimento realiza
2. **Pré-requisitos** - Acessos e ferramentas necessárias
3. **Passos** - Instruções passo a passo
4. **Verificação** - Como confirmar que o procedimento foi bem-sucedido
5. **Rollback** - Como reverter em caso de problemas
6. **Troubleshooting** - Problemas comuns e soluções

## Uso

1. Identifique o cenário que você precisa resolver
2. Leia o runbook correspondente **completamente** antes de executar
3. Siga os passos na ordem indicada
4. Execute a verificação para confirmar sucesso
5. Se houver problemas, consulte a seção de Rollback ou Troubleshooting

## Manutenção

- Runbooks devem ser revisados a cada mudança significativa no sistema
- Ao modificar um runbook, atualize a data de "Última atualização"
- Documente qualquer problema encontrado na seção de Troubleshooting

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-06
**Responsável:** Equipe de Operações
