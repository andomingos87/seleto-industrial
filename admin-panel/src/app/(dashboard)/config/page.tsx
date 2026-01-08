"use client"

import Link from "next/link"
import { Settings, Save, Code, Clock } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function ConfigPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Configurações</h1>
        <p className="text-muted-foreground">
          Ajuste as configurações gerais do sistema
        </p>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/config/prompts">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Editor de Prompts
              </CardTitle>
              <CardDescription>
                Edite os prompts do sistema (apenas desenvolvedores)
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/agent/settings">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Horário de Funcionamento
              </CardTitle>
              <CardDescription>
                Configure os horários de atendimento do agente
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parâmetros do Agente
          </CardTitle>
          <CardDescription>
            Configure os limites e comportamentos do agente
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="maxQuestions">Máx Perguntas Seguidas</Label>
              <Input
                id="maxQuestions"
                type="number"
                defaultValue="2"
                disabled
              />
              <p className="text-xs text-muted-foreground">
                Número máximo de perguntas que o agente faz antes de aguardar resposta
              </p>
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
              <p className="text-xs text-muted-foreground">
                Tempo para retomar automaticamente após pausa
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pesos de Temperatura</CardTitle>
          <CardDescription>
            Ajuste os pesos para classificação de leads
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
              <Label htmlFor="urgency">Urgência</Label>
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
          Salvar Alterações
        </Button>
      </div>

      <Card className="border-muted">
        <CardHeader>
          <CardTitle className="text-muted-foreground">Em Desenvolvimento</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            A edição de parâmetros do agente está em desenvolvimento.
            Por enquanto, utilize o Editor de Prompts para ajustar o comportamento do agente.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
