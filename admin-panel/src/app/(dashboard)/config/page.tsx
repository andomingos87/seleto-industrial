"use client"

import { Settings, Save } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function ConfigPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Configuracoes</h1>
        <p className="text-muted-foreground">
          Ajuste as configuracoes gerais do sistema
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametros do Agente
          </CardTitle>
          <CardDescription>
            Configure os limites e comportamentos do agente
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="maxQuestions">Max Perguntas Seguidas</Label>
              <Input
                id="maxQuestions"
                type="number"
                defaultValue="2"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="autoResumeTimeout">
                Auto-Resume Timeout (min)
              </Label>
              <Input
                id="autoResumeTimeout"
                type="number"
                defaultValue="30"
                disabled
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pesos de Temperatura</CardTitle>
          <CardDescription>
            Ajuste os pesos para classificacao de leads
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="engagement">Engajamento</Label>
              <Input
                id="engagement"
                type="number"
                step="0.1"
                defaultValue="0.3"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="completeness">Completude</Label>
              <Input
                id="completeness"
                type="number"
                step="0.1"
                defaultValue="0.4"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="urgency">Urgencia</Label>
              <Input
                id="urgency"
                type="number"
                step="0.1"
                defaultValue="0.3"
                disabled
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button disabled>
          <Save className="mr-2 h-4 w-4" />
          Salvar Alteracoes
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configuracao Necessaria</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Para editar configuracoes, configure a URL do backend:
          </p>
          <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
            NEXT_PUBLIC_API_URL=http://localhost:8000
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
