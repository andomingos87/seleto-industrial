"use client"

import { use } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  Building2,
  Package,
  Clock,
  Thermometer,
  User,
  Bot,
  Pause,
  Play,
  Copy,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useLead, useLeadConversation, usePauseAgent, useResumeAgent, useAgentStatus } from "@/hooks"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useState } from "react"

function TemperatureBadge({ temperature, size = "default" }: { temperature?: string; size?: "default" | "lg" }) {
  const variants: Record<string, { className: string; label: string; icon: string }> = {
    quente: { className: "bg-red-500/10 text-red-500 border-red-500/20", label: "Quente", icon: "🔥" },
    morno: { className: "bg-amber-500/10 text-amber-500 border-amber-500/20", label: "Morno", icon: "🌡️" },
    frio: { className: "bg-blue-500/10 text-blue-500 border-blue-500/20", label: "Frio", icon: "❄️" },
  }

  const variant = temperature ? variants[temperature] : null

  if (!variant) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Não classificado
      </Badge>
    )
  }

  return (
    <Badge
      variant="outline"
      className={cn(
        variant.className,
        size === "lg" && "text-base px-3 py-1"
      )}
    >
      {variant.icon} {variant.label}
    </Badge>
  )
}

function formatPhone(phone: string) {
  const cleaned = phone.replace(/\D/g, "")
  if (cleaned.length === 13) {
    return `+${cleaned.slice(0, 2)} (${cleaned.slice(2, 4)}) ${cleaned.slice(4, 9)}-${cleaned.slice(9)}`
  }
  if (cleaned.length === 11) {
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`
  }
  return phone
}

function formatDate(dateString?: string) {
  if (!dateString) return "—"
  try {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return dateString
  }
}

function formatMessageTime(dateString: string) {
  try {
    return new Date(dateString).toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return ""
  }
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value?: string | boolean | null
}) {
  const displayValue = typeof value === "boolean" ? (value ? "Sim" : "Não") : value

  return (
    <div className="flex items-start gap-3">
      <Icon className="h-4 w-4 text-muted-foreground mt-0.5" />
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium">
          {displayValue || <span className="text-muted-foreground">—</span>}
        </p>
      </div>
    </div>
  )
}

export default function LeadDetailPage({ params }: { params: Promise<{ phone: string }> }) {
  const { phone } = use(params)
  const router = useRouter()
  const decodedPhone = decodeURIComponent(phone)
  const [copied, setCopied] = useState(false)

  const { data: lead, isLoading: leadLoading, isError: leadError, error: leadErrorMsg } = useLead(decodedPhone)
  const { data: conversation, isLoading: convLoading } = useLeadConversation(decodedPhone)
  const { data: agentStatus } = useAgentStatus()
  const pauseAgent = usePauseAgent()
  const resumeAgent = useResumeAgent()

  const isPaused = agentStatus?.paused_phones?.includes(decodedPhone)

  const handleCopyPhone = async () => {
    try {
      await navigator.clipboard.writeText(decodedPhone)
      setCopied(true)
      toast.success("Telefone copiado!")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error("Erro ao copiar")
    }
  }

  const handlePauseResume = async () => {
    try {
      if (isPaused) {
        const result = await resumeAgent.mutateAsync({ phone: decodedPhone })
        if (result.success) {
          toast.success("Agente retomado para este lead")
        } else {
          toast.error(result.message)
        }
      } else {
        const result = await pauseAgent.mutateAsync({ phone: decodedPhone })
        if (result.success) {
          toast.success("Agente pausado para este lead")
        } else {
          toast.error(result.message)
        }
      }
    } catch {
      toast.error("Erro ao alterar status do agente")
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">
            {leadLoading ? (
              <Skeleton className="h-9 w-48" />
            ) : (
              lead?.name || "Lead sem nome"
            )}
          </h1>
          <p className="text-muted-foreground flex items-center gap-2">
            <Phone className="h-4 w-4" />
            {formatPhone(decodedPhone)}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleCopyPhone}
            >
              {copied ? (
                <CheckCircle2 className="h-3 w-3 text-emerald-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </p>
        </div>
        {lead && (
          <TemperatureBadge temperature={lead.temperature} size="lg" />
        )}
      </div>

      {/* Error State */}
      {leadError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Erro ao carregar lead</p>
                <p className="text-sm text-muted-foreground">
                  {leadErrorMsg instanceof Error ? leadErrorMsg.message : "Lead não encontrado"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Lead Info */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Informações do Lead
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {leadLoading ? (
              <>
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </>
            ) : lead ? (
              <>
                <InfoItem icon={User} label="Nome" value={lead.name} />
                <InfoItem icon={Mail} label="Email" value={lead.email} />
                <InfoItem
                  icon={MapPin}
                  label="Localização"
                  value={lead.city ? `${lead.city}${lead.uf ? `, ${lead.uf}` : ""}` : undefined}
                />
                <InfoItem icon={Building2} label="Conhece Seleto" value={lead.knows_seleto} />
                <Separator />
                <InfoItem icon={Package} label="Produto de Interesse" value={lead.product} />
                <InfoItem icon={Thermometer} label="Volume" value={lead.volume} />
                <InfoItem icon={Clock} label="Urgência" value={lead.urgency} />
                <Separator />
                <InfoItem icon={Clock} label="Criado em" value={formatDate(lead.created_at)} />
                <InfoItem icon={Clock} label="Atualizado em" value={formatDate(lead.updated_at)} />
              </>
            ) : null}
          </CardContent>
        </Card>

        {/* Conversation */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  Histórico de Conversa
                </CardTitle>
                <CardDescription>
                  {conversation?.total || 0} mensagens
                </CardDescription>
              </div>
              <Button
                variant={isPaused ? "default" : "outline"}
                size="sm"
                onClick={handlePauseResume}
                disabled={pauseAgent.isPending || resumeAgent.isPending}
              >
                {isPaused ? (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Retomar Agente
                  </>
                ) : (
                  <>
                    <Pause className="mr-2 h-4 w-4" />
                    Pausar Agente
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px] pr-4">
              {convLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "flex",
                        i % 2 === 0 ? "justify-start" : "justify-end"
                      )}
                    >
                      <Skeleton className="h-16 w-3/4 rounded-lg" />
                    </div>
                  ))}
                </div>
              ) : conversation?.messages && conversation.messages.length > 0 ? (
                <div className="space-y-4">
                  {conversation.messages.map((message) => (
                    <div
                      key={message.id}
                      className={cn(
                        "flex",
                        message.role === "user" ? "justify-start" : "justify-end"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[80%] rounded-lg px-4 py-2",
                          message.role === "user"
                            ? "bg-muted"
                            : "bg-primary text-primary-foreground"
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {message.role === "user" ? (
                            <User className="h-3 w-3" />
                          ) : (
                            <Bot className="h-3 w-3" />
                          )}
                          <span className="text-xs opacity-70">
                            {message.role === "user" ? "Lead" : "Agente"}
                          </span>
                          <span className="text-xs opacity-50">
                            {formatMessageTime(message.timestamp)}
                          </span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Bot className="h-12 w-12 mb-4" />
                  <p>Nenhuma mensagem encontrada</p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
