"use client"

import { RefreshCw, CheckCircle2, XCircle, AlertTriangle, Wifi, Database, Brain, Phone, MessageSquare } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useSystemStatus } from "@/hooks"
import { IntegrationStatus } from "@/lib/api"
import { cn } from "@/lib/utils"

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

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { className: string; label: string }> = {
    ok: { className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", label: "Operacional" },
    error: { className: "bg-red-500/10 text-red-500 border-red-500/20", label: "Erro" },
    warning: { className: "bg-amber-500/10 text-amber-500 border-amber-500/20", label: "Atenção" },
  }

  const variant = variants[status] || variants.warning

  return (
    <Badge variant="outline" className={variant.className}>
      {variant.label}
    </Badge>
  )
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
        <div className="flex items-center gap-2 mb-4">
          {isLoading ? (
            <Skeleton className="h-5 w-20" />
          ) : (
            <StatusBadge status={status?.status || "unknown"} />
          )}
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Latência</span>
            {isLoading ? (
              <Skeleton className="h-4 w-16" />
            ) : (
              <span className={cn(
                "font-mono",
                status?.latency_ms && status.latency_ms > 1000 && "text-amber-500",
                status?.latency_ms && status.latency_ms > 3000 && "text-red-500"
              )}>
                {status?.latency_ms ? `${status.latency_ms}ms` : "—"}
              </span>
            )}
          </div>
          {status?.error && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Erro</span>
              <span className="text-red-500 text-xs truncate max-w-[150px]" title={status.error}>
                {status.error}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default function StatusPage() {
  const { data, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } = useSystemStatus()

  const lastUpdate = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("pt-BR")
    : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Status do Sistema
          </h1>
          <p className="text-muted-foreground">
            Monitoramento em tempo real das integrações
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
      {data && (
        <Card className={cn(
          "border-2",
          data.agent_status === "active" && "border-emerald-500/50 bg-emerald-500/5",
          data.agent_status === "error" && "border-red-500/50 bg-red-500/5",
          data.agent_status === "paused" && "border-amber-500/50 bg-amber-500/5"
        )}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {data.agent_status === "active" && <CheckCircle2 className="h-8 w-8 text-emerald-500" />}
                {data.agent_status === "error" && <XCircle className="h-8 w-8 text-red-500" />}
                {data.agent_status === "paused" && <AlertTriangle className="h-8 w-8 text-amber-500" />}
                <div>
                  <h2 className="text-lg font-semibold">
                    {data.agent_status === "active" && "Sistema Operacional"}
                    {data.agent_status === "error" && "Sistema com Problemas"}
                    {data.agent_status === "paused" && "Sistema Pausado"}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {data.agent_status === "active" && "Todas as integrações funcionando normalmente"}
                    {data.agent_status === "error" && "Uma ou mais integrações com erro"}
                    {data.agent_status === "paused" && "O agente está pausado"}
                  </p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-lg px-4 py-1",
                  data.agent_status === "active" && "border-emerald-500 text-emerald-500",
                  data.agent_status === "error" && "border-red-500 text-red-500",
                  data.agent_status === "paused" && "border-amber-500 text-amber-500"
                )}
              >
                {data.agent_status === "active" && "ATIVO"}
                {data.agent_status === "error" && "ERRO"}
                {data.agent_status === "paused" && "PAUSADO"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {isError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <XCircle className="h-8 w-8 text-red-500" />
              <div>
                <h2 className="text-lg font-semibold text-red-500">Erro ao carregar status</h2>
                <p className="text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Não foi possível conectar ao backend"}
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

      {/* Integration Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(integrationConfig).map(([key, config]) => (
          <IntegrationCard
            key={key}
            name={config.name}
            icon={config.icon}
            status={data?.integrations?.[key as keyof typeof data.integrations]}
            isLoading={isLoading}
          />
        ))}
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
