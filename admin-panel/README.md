# Seleto Industrial - Admin Panel

Painel administrativo para gerenciamento do SDR Agent.

## Stack

- **Framework:** Next.js 16 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **Auth:** Supabase Auth
- **State:** TanStack Query (React Query)
- **Forms:** React Hook Form + Zod
- **Testing:** Playwright (E2E)
- **Deploy:** Fly.io

## Features

- 📊 **Dashboard de Status** - Visão geral do sistema e integrações
- 🤖 **Controle do Agente** - Pausar/retomar, recarregar prompt
- ⏰ **Horário Comercial** - Configurar dias e horários de operação
- 👥 **Gestão de Leads** - Lista e detalhes de conversas
- 📦 **Base de Conhecimento** - CRUD de produtos
- ❓ **Perguntas Técnicas** - Fila para especialistas
- 📝 **Audit Logs** - Histórico de operações com diff viewer
- ⚙️ **Editor de Prompts** - Edição do system prompt com backup

## Desenvolvimento

### Requisitos

- Node.js 20+
- npm ou pnpm

### Setup

```bash
cd admin-panel
npm install
cp .env.example .env.local
# Editar .env.local com suas credenciais
npm run dev
```

Acesse [http://localhost:3000](http://localhost:3000).

### Variáveis de Ambiente

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testes

### E2E (Playwright)

```bash
npm run test:e2e        # Headless
npm run test:e2e:ui     # Com UI interativa
npm run test:e2e:headed # Com browser visível
npm run test:e2e:debug  # Modo debug
npm run test:e2e:report # Ver relatório
```

### Cobertura

- **66 testes E2E** passando
- Fluxos: Auth, Agent Control, Business Hours, Leads

### Estrutura de Testes

```
e2e/
├── fixtures/
│   ├── api-mocks.ts      # Mocks para API do backend
│   └── auth.ts           # Helpers de autenticação
├── auth.spec.ts          # Testes de login/logout
├── status.spec.ts        # Testes do dashboard
├── agent-control.spec.ts # Testes de controle do agente
├── business-hours.spec.ts# Testes de horários
└── leads.spec.ts         # Testes de leads
```

## Deploy

### Fly.io

#### Primeiro Deploy

```bash
# Instalar Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Criar app (primeira vez)
flyctl apps create seleto-admin-panel
```

#### Deploy com Script

```bash
# Configurar credenciais
cp .env.production.example .env.production
# Editar .env.production

# Deploy
./scripts/deploy.sh
```

#### Deploy Manual

```bash
flyctl deploy \
  --build-arg NEXT_PUBLIC_SUPABASE_URL="https://xxx.supabase.co" \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJ..." \
  --build-arg NEXT_PUBLIC_API_URL="https://seleto-industrial.fly.dev"
```

> **Nota:** As variáveis `NEXT_PUBLIC_*` precisam ser passadas como build args pois são injetadas no build time pelo Next.js.

### URLs

- **Produção:** https://seleto-admin-panel.fly.dev
- **API Backend:** https://seleto-industrial.fly.dev
- **Health Check:** https://seleto-admin-panel.fly.dev/api/health

### Comandos Úteis

```bash
flyctl status -a seleto-admin-panel  # Ver status
flyctl logs -a seleto-admin-panel    # Ver logs
flyctl dashboard -a seleto-admin-panel # Abrir dashboard
```

## Estrutura

```
admin-panel/
├── src/
│   ├── app/                    # Rotas e páginas (App Router)
│   │   ├── (auth)/             # Páginas de autenticação
│   │   │   └── login/
│   │   ├── (dashboard)/        # Páginas protegidas
│   │   │   ├── agent/          # Controle do agente
│   │   │   ├── config/         # Configurações e prompts
│   │   │   ├── knowledge/      # Base de conhecimento
│   │   │   ├── leads/          # Lista de leads
│   │   │   ├── logs/           # Audit logs
│   │   │   └── status/         # Status do sistema
│   │   └── api/                # API routes
│   │       └── health/         # Health check endpoint
│   ├── components/
│   │   ├── layout/             # Sidebar, Header
│   │   ├── providers/          # Context providers
│   │   └── ui/                 # shadcn/ui components
│   ├── hooks/                  # React Query hooks
│   └── lib/
│       ├── api/                # API client
│       └── supabase/           # Supabase client/server
├── e2e/                        # Testes Playwright
├── scripts/
│   └── deploy.sh               # Script de deploy
├── Dockerfile                  # Build para produção
└── fly.toml                    # Config Fly.io
```

## Scripts

| Comando | Descrição |
|---------|-----------|
| `npm run dev` | Servidor de desenvolvimento |
| `npm run build` | Build de produção |
| `npm run start` | Rodar build de produção |
| `npm run lint` | Verificar linting |
| `npm run test:e2e` | Rodar testes E2E (headless) |
| `npm run test:e2e:ui` | Rodar testes E2E com UI |
| `npm run test:e2e:headed` | Rodar testes E2E com browser |
| `npm run test:e2e:debug` | Rodar testes E2E em debug |
| `npm run test:e2e:report` | Abrir relatório de testes |

## Troubleshooting

### Erro de conexão com backend

1. Verifique se `NEXT_PUBLIC_API_URL` está configurado
2. Verifique se o backend está rodando
3. Verifique CORS no backend

### Erro de autenticação

1. Verifique as credenciais do Supabase
2. Limpe cookies e localStorage
3. Verifique se o email está confirmado

### Build falha no Fly.io

1. Verifique se os build args estão corretos
2. Verifique logs: `flyctl logs -a seleto-admin-panel`
3. Teste build local: `docker build -t test .`

## Licença

Proprietary - Seleto Industrial
