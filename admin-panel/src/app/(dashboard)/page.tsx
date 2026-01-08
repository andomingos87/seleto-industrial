import { Activity, Bot, Clock, Users } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visao geral do SDR Agent da Seleto Industrial
        </p>
      </div>

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
              <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                Ativo
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Operando normalmente
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
              Conecte ao backend para ver
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
              Nas ultimas 24h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Horario Comercial
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">08:00 - 18:00</div>
            <p className="text-xs text-muted-foreground">
              Segunda a Sexta
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Integrações</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">WhatsApp (Z-API)</span>
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                Verificar
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Supabase</span>
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                Verificar
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">OpenAI</span>
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                Verificar
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">PipeRun</span>
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                Verificar
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Chatwoot</span>
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                Verificar
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Acoes Rapidas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Conecte o backend para habilitar acoes como:
            </p>
            <ul className="text-sm space-y-2 list-disc list-inside text-muted-foreground">
              <li>Pausar/Retomar agente</li>
              <li>Recarregar prompt do sistema</li>
              <li>Visualizar leads em tempo real</li>
              <li>Editar horarios comerciais</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
