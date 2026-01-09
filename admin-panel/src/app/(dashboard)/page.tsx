"use client"

import { Activity, Bot, Clock, Users, CheckCircle2, XCircle, AlertTriangle, Loader2, RefreshCw, Phone, Database, Brain, MessageSquare, Wifi } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useSystemStatus, useAgentStatus } from "@/hooks"
import { cn } from "@/lib/utils"
import Link from "next/link"
import type { IntegrationStatus } from "@/lib/api"

function IntegrationStatusBadge({ status }: { status?: string }) {
  if (!status) {
    return (
      <Badge variant="outline" className="text-gray-500 border-gray-500">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Carregando
      </Badge>
    )
  }

  switch (status) {
    case "ok":
      return (
        <Badge variant="outline" className="text-emerald-500 border-emerald-500">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Operacional
        </Badge>
      )
    case "error":
      return (
        <Badge variant="outline" className="text-red-500 border-red-500">
          <XCircle className="h-3 w-3 mr-1" />
          Erro
        </Badge>
      )
    case "warning":
      return (
        <Badge variant="outline" className="text-amber-500 border-amber-500">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Atenção
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="text-gray-500 border-gray-500">
          Desconhecido
        </Badge>
      )
  }
}

const integrationConfig = {
  whatsapp: { name: "WhatsApp (Z-API)", icon: Phone },
  supabase: { name: "Supabase", icon: Database },
  openai: { name: "OpenAI", icon: Brain },
  piperun: { name: "PipeRun CRM", icon: Wifi },
  chatwoot: { name: "Chatwoot", icon: MessageSquare },
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "ok":
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />
    case "error":
      return <XCircle className="h-5 w-5 text-red-500" />
    case "warning":
      return <AlertTriangle className="h-5 w-5 text-amber-500" />
    default:
      return <AlertTriangle className="h-5 w-5 text-gray-400" />
  }
}

function IntegrationCard({
  name,
  icon: Icon,
  status,
  isLoading,
}: {
  name: string
  icon: React.ComponentType<{ className?: string }>
  status?: IntegrationStatus
  isLoading: boolean
}) {
  return (
    <Card className={cn(
      "transition-all duration-200",
      status?.status === "ok" && "border-emerald-500/20",
      status?.status === "error" && "border-red-500/20",
      status?.status === "warning" && "border-amber-500/20"
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          {name}
        </CardTitle>
        {isLoading ? (
          <Skeleton className="h-5 w-5 rounded-full" />
        ) : (
          <StatusIcon status={status?.status || "unknown"} />
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-2">
          {isLoading ? (
            <Skeleton className="h-5 w-20" />
          ) : (
            <IntegrationStatusBadge status={status?.status} />
          )}
        </div>
        <div className="text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Latência</span>
            {isLoading ? (
              <Skeleton className="h-4 w-16" />
            ) : (
              <span className={cn(
                "font-mono text-xs",
                status?.latency_ms && status.latency_ms > 1000 && "text-amber-500",
                status?.latency_ms && status.latency_ms > 3000 && "text-red-500"
              )}>
                {status?.latency_ms ? `${status.latency_ms}ms` : "—"}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { data: systemStatus, isLoading: isLoadingSystem, isError: isSystemError, refetch, isFetching, dataUpdatedAt } = useSystemStatus()
  const { data: agentStatus, isLoading: isLoadingAgent } = useAgentStatus()

  const integrations = systemStatus?.integrations
  const lastUpdate = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("pt-BR")
    : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Visão geral do SDR Agent da Seleto Industrial
            {lastUpdate && (
              <span className="ml-2 text-xs">
                (Atualizado às {lastUpdate})
              </span>
            )}
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />
          Atualizar
        </Button>
      </div>

      {/* Overall Status Banner */}
      {systemStatus && (
        <Card className={cn(
          "border-2",
          systemStatus.agent_status === "active" && "border-emerald-500/50 bg-emerald-500/5",
          systemStatus.agent_status === "error" && "border-red-500/50 bg-red-500/5",
          systemStatus.agent_status === "paused" && "border-amber-500/50 bg-amber-500/5"
        )}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {systemStatus.agent_status === "active" && <CheckCircle2 className="h-8 w-8 text-emerald-500" />}
                {systemStatus.agent_status === "error" && <XCircle className="h-8 w-8 text-red-500" />}
                {systemStatus.agent_status === "paused" && <AlertTriangle className="h-8 w-8 text-amber-500" />}
                <div>
                  <h2 className="text-lg font-semibold">
                    {systemStatus.agent_status === "active" && "Sistema Operacional"}
                    {systemStatus.agent_status === "error" && "Sistema com Problemas"}
                    {systemStatus.agent_status === "paused" && "Sistema Pausado"}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {systemStatus.agent_status === "active" && "Todas as integrações funcionando normalmente"}
                    {systemStatus.agent_status === "error" && "Uma ou mais integrações com erro"}
                    {systemStatus.agent_status === "paused" && "O agente está pausado"}
                  </p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-lg px-4 py-1",
                  systemStatus.agent_status === "active" && "border-emerald-500 text-emerald-500",
                  systemStatus.agent_status === "error" && "border-red-500 text-red-500",
                  systemStatus.agent_status === "paused" && "border-amber-500 text-amber-500"
                )}
              >
                {systemStatus.agent_status === "active" && "ATIVO"}
                {systemStatus.agent_status === "error" && "ERRO"}
                {systemStatus.agent_status === "paused" && "PAUSADO"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {isSystemError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <XCircle className="h-8 w-8 text-red-500" />
              <div>
                <h2 className="text-lg font-semibold text-red-500">Erro ao carregar status</h2>
                <p className="text-sm text-muted-foreground">
                  Não foi possível conectar ao backend
                </p>
              </div>
            </div>
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-2">
                Verifique se o backend está rodando e a variável de ambiente está configurada:
              </p>
              <pre className="bg-muted p-3 rounded-lg text-sm overflow-x-auto">
                NEXT_PUBLIC_API_URL=http://localhost:8000
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Status do Agente
            </CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {isLoadingAgent ? (
                <Skeleton className="h-6 w-20" />
              ) : (
                <Badge 
                  variant="default" 
                  className={cn(
                    agentStatus?.status === "active" 
                      ? "bg-emerald-500 hover:bg-emerald-600" 
                      : "bg-amber-500 hover:bg-amber-600"
                  )}
                >
                  {agentStatus?.status === "active" ? "Ativo" : "Pausado"}
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {isLoadingAgent ? (
                <Skeleton className="h-3 w-32" />
              ) : agentStatus?.status === "active" ? (
                "Operando normalmente"
              ) : (
                `${agentStatus?.total_paused || 0} telefone(s) pausado(s)`
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leads Hoje</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              <Link href="/leads" className="hover:underline">
                Ver todos os leads →
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Mensagens Processadas
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              Nas últimas 24h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Horário Comercial
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">08:00 - 18:00</div>
            <p className="text-xs text-muted-foreground">
              <Link href="/schedule" className="hover:underline">
                Configurar horários →
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Integration Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Status das Integrações</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {Object.entries(integrationConfig).map(([key, config]) => (
            <IntegrationCard
              key={key}
              name={config.name}
              icon={config.icon}
              status={integrations?.[key as keyof typeof integrations]}
              isLoading={isLoadingSystem}
            />
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <Link href="/agent">
                <Button variant="outline" className="w-full justify-start">
                  <Bot className="mr-2 h-4 w-4" />
                  Controle do Agente
                </Button>
              </Link>
              <Link href="/leads">
                <Button variant="outline" className="w-full justify-start">
                  <Users className="mr-2 h-4 w-4" />
                  Visualizar Leads
                </Button>
              </Link>
              <Link href="/products">
                <Button variant="outline" className="w-full justify-start">
                  <Activity className="mr-2 h-4 w-4" />
                  Gerenciar Produtos
                </Button>
              </Link>
              <Link href="/prompt">
                <Button variant="outline" className="w-full justify-start">
                  <Clock className="mr-2 h-4 w-4" />
                  Editar Prompt
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configurações do Agente</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <Link href="/schedule">
                <Button variant="outline" className="w-full justify-start">
                  <Clock className="mr-2 h-4 w-4" />
                  Horário de Funcionamento
                </Button>
              </Link>
              <Link href="/parameters">
                <Button variant="outline" className="w-full justify-start">
                  <Activity className="mr-2 h-4 w-4" />
                  Parâmetros do Agente
                </Button>
              </Link>
              <Link href="/logs">
                <Button variant="outline" className="w-full justify-start">
                  <Activity className="mr-2 h-4 w-4" />
                  Logs de Auditoria
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Auto-refresh indicator */}
      <div className="text-center text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Auto-refresh a cada 30 segundos
        </span>
      </div>
    </div>
  )
}
