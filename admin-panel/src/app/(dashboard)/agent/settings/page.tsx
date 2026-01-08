"use client"

import { useState, useEffect } from "react"
import { Clock, Save, RefreshCw, CheckCircle2, XCircle, AlertCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useBusinessHours, useUpdateBusinessHours } from "@/hooks"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const weekDays = [
  { key: "monday", label: "Segunda-feira" },
  { key: "tuesday", label: "Terça-feira" },
  { key: "wednesday", label: "Quarta-feira" },
  { key: "thursday", label: "Quinta-feira" },
  { key: "friday", label: "Sexta-feira" },
  { key: "saturday", label: "Sábado" },
  { key: "sunday", label: "Domingo" },
] as const

const timezones = [
  { value: "America/Sao_Paulo", label: "São Paulo (GMT-3)" },
  { value: "America/Manaus", label: "Manaus (GMT-4)" },
  { value: "America/Recife", label: "Recife (GMT-3)" },
  { value: "America/Fortaleza", label: "Fortaleza (GMT-3)" },
  { value: "America/Cuiaba", label: "Cuiabá (GMT-4)" },
  { value: "America/Rio_Branco", label: "Rio Branco (GMT-5)" },
]

type DayKey = typeof weekDays[number]["key"]

interface DaySchedule {
  enabled: boolean
  start: string
  end: string
}

type ScheduleState = Record<DayKey, DaySchedule>

export default function AgentSettingsPage() {
  const { data, isLoading, isError, error, refetch } = useBusinessHours()
  const updateBusinessHours = useUpdateBusinessHours()

  const [schedule, setSchedule] = useState<ScheduleState>({
    monday: { enabled: true, start: "08:00", end: "18:00" },
    tuesday: { enabled: true, start: "08:00", end: "18:00" },
    wednesday: { enabled: true, start: "08:00", end: "18:00" },
    thursday: { enabled: true, start: "08:00", end: "18:00" },
    friday: { enabled: true, start: "08:00", end: "18:00" },
    saturday: { enabled: false, start: "08:00", end: "12:00" },
    sunday: { enabled: false, start: "08:00", end: "12:00" },
  })

  const [timezone, setTimezone] = useState("America/Sao_Paulo")
  const [hasChanges, setHasChanges] = useState(false)

  // Load data from API
  useEffect(() => {
    if (data) {
      setTimezone(data.timezone || "America/Sao_Paulo")
      
      const newSchedule: ScheduleState = { ...schedule }
      weekDays.forEach(({ key }) => {
        const dayData = data.schedule?.[key]
        if (dayData === null) {
          newSchedule[key] = { enabled: false, start: "08:00", end: "18:00" }
        } else if (dayData) {
          newSchedule[key] = {
            enabled: true,
            start: dayData.start || "08:00",
            end: dayData.end || "18:00",
          }
        }
      })
      setSchedule(newSchedule)
      setHasChanges(false)
    }
  }, [data])

  const handleDayToggle = (day: DayKey, enabled: boolean) => {
    setSchedule((prev) => ({
      ...prev,
      [day]: { ...prev[day], enabled },
    }))
    setHasChanges(true)
  }

  const handleTimeChange = (day: DayKey, field: "start" | "end", value: string) => {
    setSchedule((prev) => ({
      ...prev,
      [day]: { ...prev[day], [field]: value },
    }))
    setHasChanges(true)
  }

  const handleTimezoneChange = (value: string) => {
    setTimezone(value)
    setHasChanges(true)
  }

  const handleSave = async () => {
    try {
      // Convert schedule to API format
      const apiSchedule: Record<string, { start: string; end: string } | null> = {}
      weekDays.forEach(({ key }) => {
        const day = schedule[key]
        apiSchedule[key] = day.enabled ? { start: day.start, end: day.end } : null
      })

      await updateBusinessHours.mutateAsync({
        timezone,
        schedule: apiSchedule,
      })

      toast.success("Horários salvos com sucesso")
      setHasChanges(false)
    } catch {
      toast.error("Erro ao salvar horários")
    }
  }

  const handleReset = () => {
    refetch()
    setHasChanges(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Horários Comerciais</h1>
          <p className="text-muted-foreground">
            Configure os horários de funcionamento do agente
          </p>
        </div>
        {hasChanges && (
          <Badge variant="outline" className="text-amber-500 border-amber-500">
            Alterações não salvas
          </Badge>
        )}
      </div>

      {/* Error State */}
      {isError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Erro ao carregar configurações</p>
                <p className="text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Verifique a conexão com o backend"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Current Status */}
      {data?.current_status && (
        <Card className={cn(
          "border-2",
          data.current_status.is_business_hours
            ? "border-emerald-500/50 bg-emerald-500/5"
            : "border-amber-500/50 bg-amber-500/5"
        )}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {data.current_status.is_business_hours ? (
                  <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                ) : (
                  <XCircle className="h-6 w-6 text-amber-500" />
                )}
                <div>
                  <p className="font-medium">
                    {data.current_status.is_business_hours
                      ? "Dentro do Horário Comercial"
                      : "Fora do Horário Comercial"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Horário atual: {data.current_status.current_time} ({data.current_status.timezone})
                  </p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  data.current_status.is_business_hours
                    ? "border-emerald-500 text-emerald-500"
                    : "border-amber-500 text-amber-500"
                )}
              >
                {data.current_status.is_business_hours ? "ABERTO" : "FECHADO"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schedule Editor */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Horários por Dia
          </CardTitle>
          <CardDescription>
            Defina os horários de início e fim para cada dia da semana.
            Dias desabilitados são considerados fechados.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {weekDays.map(({ key, label }) => (
            <div
              key={key}
              className={cn(
                "flex items-center gap-4 py-3 px-4 rounded-lg transition-colors",
                schedule[key].enabled ? "bg-muted/30" : "bg-muted/10 opacity-60"
              )}
            >
              <div className="w-32">
                <Label className="font-medium">{label}</Label>
              </div>
              
              {isLoading ? (
                <>
                  <Skeleton className="h-6 w-10" />
                  <Skeleton className="h-9 w-24" />
                  <Skeleton className="h-9 w-24" />
                </>
              ) : (
                <>
                  <Switch
                    checked={schedule[key].enabled}
                    onCheckedChange={(checked) => handleDayToggle(key, checked)}
                  />
                  
                  <div className="flex items-center gap-2 flex-1">
                    <Input
                      type="time"
                      value={schedule[key].start}
                      onChange={(e) => handleTimeChange(key, "start", e.target.value)}
                      className="w-28"
                      disabled={!schedule[key].enabled}
                    />
                    <span className="text-muted-foreground text-sm">até</span>
                    <Input
                      type="time"
                      value={schedule[key].end}
                      onChange={(e) => handleTimeChange(key, "end", e.target.value)}
                      className="w-28"
                      disabled={!schedule[key].enabled}
                    />
                  </div>

                  <Badge
                    variant="outline"
                    className={cn(
                      "w-20 justify-center",
                      schedule[key].enabled
                        ? "text-emerald-500 border-emerald-500/50"
                        : "text-muted-foreground border-muted"
                    )}
                  >
                    {schedule[key].enabled ? "Aberto" : "Fechado"}
                  </Badge>
                </>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Timezone */}
      <Card>
        <CardHeader>
          <CardTitle>Fuso Horário</CardTitle>
          <CardDescription>
            Fuso horário usado para calcular os horários comerciais
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-10 w-64" />
          ) : (
            <Select value={timezone} onValueChange={handleTimezoneChange}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Selecione o fuso horário" />
              </SelectTrigger>
              <SelectContent>
                {timezones.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={!hasChanges || updateBusinessHours.isPending}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Descartar
        </Button>
        <Button
          onClick={handleSave}
          disabled={!hasChanges || updateBusinessHours.isPending}
        >
          <Save className={cn(
            "mr-2 h-4 w-4",
            updateBusinessHours.isPending && "animate-spin"
          )} />
          {updateBusinessHours.isPending ? "Salvando..." : "Salvar Alterações"}
        </Button>
      </div>
    </div>
  )
}
