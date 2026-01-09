"use client"

import { useState } from "react"
import { Settings, Save, RefreshCw, Info } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface AgentParameters {
  max_perguntas: number
  auto_resume: boolean
  pesos_temperatura: {
    peso_urgencia: number
    peso_interesse: number
    peso_budget: number
    peso_autoridade: number
  }
}

export default function ParametersPage() {
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const [parameters, setParameters] = useState<AgentParameters>({
    max_perguntas: 5,
    auto_resume: true,
    pesos_temperatura: {
      peso_urgencia: 0.3,
      peso_interesse: 0.3,
      peso_budget: 0.2,
      peso_autoridade: 0.2,
    },
  })

  const handleMaxPerguntasChange = (value: string) => {
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 1 && num <= 20) {
      setParameters((prev) => ({ ...prev, max_perguntas: num }))
      setHasChanges(true)
    }
  }

  const handleAutoResumeChange = (checked: boolean) => {
    setParameters((prev) => ({ ...prev, auto_resume: checked }))
    setHasChanges(true)
  }

  const handlePesoChange = (key: keyof AgentParameters["pesos_temperatura"], value: number[]) => {
    setParameters((prev) => ({
      ...prev,
      pesos_temperatura: {
        ...prev.pesos_temperatura,
        [key]: value[0],
      },
    }))
    setHasChanges(true)
  }

  const totalPesos = Object.values(parameters.pesos_temperatura).reduce((a, b) => a + b, 0)
  const isPesosValid = Math.abs(totalPesos - 1) < 0.01

  const handleSave = async () => {
    if (!isPesosValid) {
      toast.error("A soma dos pesos deve ser igual a 1.0")
      return
    }

    setIsSaving(true)
    try {
      // TODO: Implement API call to save parameters
      await new Promise((resolve) => setTimeout(resolve, 1000))
      toast.success("Parâmetros salvos com sucesso")
      setHasChanges(false)
    } catch {
      toast.error("Erro ao salvar parâmetros")
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setParameters({
      max_perguntas: 5,
      auto_resume: true,
      pesos_temperatura: {
        peso_urgencia: 0.3,
        peso_interesse: 0.3,
        peso_budget: 0.2,
        peso_autoridade: 0.2,
      },
    })
    setHasChanges(false)
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Parâmetros do Agente</h1>
            <p className="text-muted-foreground">
              Configure o comportamento do agente SDR
            </p>
          </div>
          {hasChanges && (
            <Badge variant="outline" className="text-amber-500 border-amber-500">
              Alterações não salvas
            </Badge>
          )}
        </div>

        {/* Max Perguntas */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Limite de Perguntas
            </CardTitle>
            <CardDescription>
              Número máximo de perguntas antes de classificar o lead
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Label htmlFor="max_perguntas">Máximo de perguntas:</Label>
                <Input
                  id="max_perguntas"
                  type="number"
                  min={1}
                  max={20}
                  value={parameters.max_perguntas}
                  onChange={(e) => handleMaxPerguntasChange(e.target.value)}
                  className="w-20"
                />
              </div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">
                    Após esse número de perguntas, o agente irá classificar o lead
                    automaticamente com base nas informações coletadas.
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </CardContent>
        </Card>

        {/* Auto Resume */}
        <Card>
          <CardHeader>
            <CardTitle>Retomada Automática</CardTitle>
            <CardDescription>
              Retomar automaticamente o agente após o horário comercial
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Switch
                id="auto_resume"
                checked={parameters.auto_resume}
                onCheckedChange={handleAutoResumeChange}
              />
              <Label htmlFor="auto_resume" className="cursor-pointer">
                {parameters.auto_resume ? "Ativado" : "Desativado"}
              </Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">
                    Quando ativado, leads pausados por intervenção do SDR serão
                    automaticamente retomados fora do horário comercial.
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </CardContent>
        </Card>

        {/* Pesos Temperatura */}
        <Card>
          <CardHeader>
            <CardTitle>Pesos de Classificação de Temperatura</CardTitle>
            <CardDescription>
              Configure os pesos usados para calcular a temperatura do lead.
              A soma dos pesos deve ser igual a 1.0.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Urgência */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  Urgência
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        Peso dado à urgência do lead em adquirir o produto.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <span className="text-sm font-mono">
                  {parameters.pesos_temperatura.peso_urgencia.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[parameters.pesos_temperatura.peso_urgencia]}
                onValueChange={(v) => handlePesoChange("peso_urgencia", v)}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            {/* Interesse */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  Interesse
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        Peso dado ao nível de interesse demonstrado pelo lead.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <span className="text-sm font-mono">
                  {parameters.pesos_temperatura.peso_interesse.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[parameters.pesos_temperatura.peso_interesse]}
                onValueChange={(v) => handlePesoChange("peso_interesse", v)}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            {/* Budget */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  Budget
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        Peso dado à capacidade financeira do lead.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <span className="text-sm font-mono">
                  {parameters.pesos_temperatura.peso_budget.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[parameters.pesos_temperatura.peso_budget]}
                onValueChange={(v) => handlePesoChange("peso_budget", v)}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            {/* Autoridade */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  Autoridade
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        Peso dado ao poder de decisão do lead na empresa.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <span className="text-sm font-mono">
                  {parameters.pesos_temperatura.peso_autoridade.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[parameters.pesos_temperatura.peso_autoridade]}
                onValueChange={(v) => handlePesoChange("peso_autoridade", v)}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            {/* Total */}
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="font-medium">Soma dos pesos:</span>
                <Badge
                  variant="outline"
                  className={cn(
                    isPesosValid
                      ? "text-emerald-500 border-emerald-500"
                      : "text-red-500 border-red-500"
                  )}
                >
                  {totalPesos.toFixed(2)}
                </Badge>
              </div>
              {!isPesosValid && (
                <p className="text-sm text-red-500 mt-2">
                  A soma dos pesos deve ser igual a 1.0
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges || isSaving}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Restaurar Padrões
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving || !isPesosValid}
          >
            <Save className={cn("mr-2 h-4 w-4", isSaving && "animate-spin")} />
            {isSaving ? "Salvando..." : "Salvar Alterações"}
          </Button>
        </div>
      </div>
    </TooltipProvider>
  )
}
