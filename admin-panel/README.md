# SDR Agent Admin Panel

Painel administrativo para controle operacional do agente SDR da Seleto Industrial.

## Stack

- **Framework:** Next.js 16 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **Auth:** Supabase Auth
- **State:** TanStack Query (React Query)
- **Forms:** React Hook Form + Zod
- **Deploy:** Fly.io

## Setup Local

### 1. Instalar dependencias

```bash
cd admin-panel
npm install
```

### 2. Configurar variaveis de ambiente

```bash
cp .env.example .env.local
```

Edite `.env.local` com suas credenciais:

```env
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Rodar servidor de desenvolvimento

```bash
npm run dev
```

Acesse [http://localhost:3000](http://localhost:3000).

## Deploy no Fly.io

### 1. Instalar Fly CLI

```bash
# macOS
brew install flyctl

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login no Fly.io

```bash
fly auth login
```

### 3. Criar app (primeira vez)

```bash
fly apps create seleto-admin-panel
```

### 4. Configurar secrets

```bash
fly secrets set NEXT_PUBLIC_SUPABASE_URL="https://seu-projeto.supabase.co"
fly secrets set NEXT_PUBLIC_SUPABASE_ANON_KEY="sua_anon_key"
fly secrets set NEXT_PUBLIC_API_URL="https://seu-backend.fly.dev"
```

### 5. Deploy

```bash
fly deploy --build-arg NEXT_PUBLIC_SUPABASE_URL="https://seu-projeto.supabase.co" \
           --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="sua_anon_key" \
           --build-arg NEXT_PUBLIC_API_URL="https://seu-backend.fly.dev"
```

> **Nota:** As variaveis `NEXT_PUBLIC_*` precisam ser passadas como build args pois sao injetadas no build time pelo Next.js.

### 6. Verificar status

```bash
fly status
fly logs
```

## Estrutura de Pastas

```
admin-panel/
├── src/
│   ├── app/
│   │   ├── (auth)/           # Paginas de autenticacao
│   │   │   └── login/
│   │   ├── (dashboard)/      # Paginas protegidas
│   │   │   ├── agent/        # Controle do agente
│   │   │   ├── config/       # Configuracoes
│   │   │   ├── knowledge/    # Base de conhecimento
│   │   │   ├── leads/        # Lista de leads
│   │   │   ├── logs/         # Audit logs
│   │   │   └── status/       # Status do sistema
│   │   └── auth/callback/    # OAuth callback
│   ├── components/
│   │   ├── layout/           # Sidebar, Header, etc
│   │   ├── providers/        # Context providers
│   │   └── ui/               # shadcn/ui components
│   ├── hooks/                # Custom hooks
│   └── lib/
│       ├── supabase/         # Supabase client/server
│       └── utils.ts          # Utilitarios
├── middleware.ts             # Auth middleware
├── Dockerfile                # Build para producao
└── fly.toml                  # Config Fly.io
```

## Scripts

| Comando | Descricao |
|---------|-----------|
| `npm run dev` | Servidor de desenvolvimento |
| `npm run build` | Build de producao |
| `npm run start` | Rodar build de producao |
| `npm run lint` | Verificar linting |
| `npm run test:e2e` | Rodar testes E2E (headless) |
| `npm run test:e2e:ui` | Rodar testes E2E com UI interativa |
| `npm run test:e2e:headed` | Rodar testes E2E com browser visivel |
| `npm run test:e2e:debug` | Rodar testes E2E em modo debug |
| `npm run test:e2e:report` | Abrir relatorio de testes |

## Testes E2E

Os testes E2E sao implementados com [Playwright](https://playwright.dev/) e cobrem os fluxos criticos do painel administrativo.

### Estrutura de Testes

```
e2e/
├── fixtures/
│   ├── api-mocks.ts      # Mocks para API do backend
│   └── auth.ts           # Helpers de autenticacao
├── auth.spec.ts          # Testes de login e autenticacao
├── status.spec.ts        # Testes do dashboard de status
├── agent-control.spec.ts # Testes de controle do agente
├── business-hours.spec.ts# Testes de configuracao de horarios
└── leads.spec.ts         # Testes de lista e detalhes de leads
```

### Executando Testes

```bash
# Rodar todos os testes (headless)
npm run test:e2e

# Rodar com UI interativa do Playwright
npm run test:e2e:ui

# Rodar um arquivo especifico
npx playwright test e2e/auth.spec.ts

# Rodar em modo debug
npm run test:e2e:debug
```

### Configuracao

Os testes usam mocks para a API do backend, permitindo execucao independente. Para testes com backend real, configure as variaveis de ambiente:

```env
E2E_TEST_EMAIL=seu@email.com
E2E_TEST_PASSWORD=suasenha
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Funcionalidades

### Implementadas (Phase 1)
- [x] Autenticacao com Supabase
- [x] Layout com sidebar responsiva
- [x] Dark/Light mode
- [x] Estrutura de rotas protegidas

### Implementadas (Phase 2)
- [x] Dashboard de status das integracoes (`/status`)
- [x] Controle de pause/resume do agente (`/agent`)
- [x] Editor de horarios comerciais (`/agent/settings`)
- [x] Lista de leads com filtros (`/leads`)
- [x] Visualizacao de conversas (`/leads/[phone]`)
- [x] Testes E2E com Playwright (144 testes)

### Planejadas (Phase 3+)
- [ ] CRUD de produtos (base de conhecimento)
- [ ] Fila de perguntas tecnicas
- [ ] Visualizacao de audit logs
- [ ] Editor de prompts
