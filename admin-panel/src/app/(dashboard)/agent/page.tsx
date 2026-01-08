"use client"

import { useState } from "react"
import { Bot, Pause, Play, RefreshCw, Phone, Trash2, Plus, AlertCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { useAgentStatus, usePauseAgent, useResumeAgent, useReloadPrompt } from "@/hooks"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

export default function AgentPage() {
  const [phoneInput, setPhoneInput] = useState("")
  const { data: agentStatus, isLoading, isError, error } = useAgentStatus()
  const pauseAgent = usePauseAgent()
  const resumeAgent = useResumeAgent()
  const reloadPrompt = useReloadPrompt()

  const handlePausePhone = async () => {
    if (!phoneInput.trim()) {
      toast.error("Digite um número de telefone")
      return
    }

    try {
      const result = await pauseAgent.mutateAsync({ phone: phoneInput.trim() })
      if (result.success) {
        toast.success(result.message)
        setPhoneInput("")
      } else {
        toast.error(result.message)
      }
    } catch {
      toast.error("Erro ao pausar agente")
    }
  }

  const handleResumePhone = async (phone: string) => {
    try {
      const result = await resumeAgent.mutateAsync({ phone })
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
    } catch {
      toast.error("Erro ao retomar agente")
    }
  }

  const handleReloadPrompt = async () => {
    try {
      const result = await reloadPrompt.mutateAsync()
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
    } catch {
      toast.error("Erro ao recarregar prompt")
    }
  }

  const formatPhone = (phone: string) => {
    // Format as +55 (11) 99999-9999
    const cleaned = phone.replace(/\D/g, "")
    if (cleaned.length === 13) {
      return `+${cleaned.slice(0, 2)} (${cleaned.slice(2, 4)}) ${cleaned.slice(4, 9)}-${cleaned.slice(9)}`
    }
    return phone
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Controle do Agente</h1>
        <p className="text-muted-foreground">
          Gerencie o status e operação do agente SDR
        </p>
      </div>

      {/* Error State */}
      {isError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Erro ao carregar status do agente</p>
                <p className="text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Verifique a conexão com o backend"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Global Status Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Status Global
            </CardTitle>
            <CardDescription>
              Controle o funcionamento geral do agente
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status Atual</span>
              {isLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : (
                <Badge
                  variant="outline"
                  className={cn(
                    agentStatus?.status === "active"
                      ? "text-emerald-500 border-emerald-500"
                      : "text-amber-500 border-amber-500"
                  )}
                >
                  {agentStatus?.status === "active" ? "Ativo" : "Pausado"}
                </Badge>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Telefones Pausados</span>
              {isLoading ? (
                <Skeleton className="h-6 w-12" />
              ) : (
                <Badge variant="secondary">
                  {agentStatus?.total_paused || 0}
                </Badge>
              )}
            </div>

            <div className="pt-2 border-t">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full"
                    disabled={reloadPrompt.isPending}
                  >
                    <RefreshCw className={cn(
                      "mr-2 h-4 w-4",
                      reloadPrompt.isPending && "animate-spin"
                    )} />
                    Recarregar Prompt
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Recarregar System Prompt?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Isso irá recarregar o arquivo sp_agente_v1.xml do disco.
                      Novas conversas usarão o prompt atualizado.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={handleReloadPrompt}>
                      Recarregar
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>

        {/* Paused Phones Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5" />
              Telefones Pausados
            </CardTitle>
            <CardDescription>
              Leads pausados individualmente (intervenção SDR)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Add Phone Input */}
            <div className="flex gap-2">
              <Input
                placeholder="5511999999999"
                value={phoneInput}
                onChange={(e) => setPhoneInput(e.target.value)}
                className="font-mono"
              />
              <Button
                onClick={handlePausePhone}
                disabled={pauseAgent.isPending || !phoneInput.trim()}
                size="icon"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* Paused Phones List */}
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {isLoading ? (
                <>
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </>
              ) : agentStatus?.paused_phones && agentStatus.paused_phones.length > 0 ? (
                agentStatus.paused_phones.map((phone) => (
                  <div
                    key={phone}
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                  >
                    <span className="font-mono text-sm">{formatPhone(phone)}</span>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-emerald-500 hover:text-emerald-600 hover:bg-emerald-500/10"
                        onClick={() => handleResumePhone(phone)}
                        disabled={resumeAgent.isPending}
                        title="Retomar agente"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Nenhum telefone pausado
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Ações Rápidas</CardTitle>
          <CardDescription>
            Controles globais do agente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              variant="outline"
              className="flex-1"
              disabled
              title="Pausa global não implementada"
            >
              <Pause className="mr-2 h-4 w-4" />
              Pausar Todos
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              disabled
              title="Resume global não implementado"
            >
              <Play className="mr-2 h-4 w-4" />
              Retomar Todos
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Pausa/resume global será implementado em versão futura
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
