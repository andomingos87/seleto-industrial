"use client"

import { useState, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Search, Users, ChevronLeft, ChevronRight, ArrowUpDown, AlertCircle, Phone, MapPin, Thermometer } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useLeads } from "@/hooks"
import { LeadsListParams, Lead } from "@/lib/api"
import { cn } from "@/lib/utils"
import { useDebounce } from "@/hooks/use-debounce"

function TemperatureBadge({ temperature }: { temperature?: string }) {
  const variants: Record<string, { className: string; label: string }> = {
    quente: { className: "bg-red-500/10 text-red-500 border-red-500/20", label: "Quente" },
    morno: { className: "bg-amber-500/10 text-amber-500 border-amber-500/20", label: "Morno" },
    frio: { className: "bg-blue-500/10 text-blue-500 border-blue-500/20", label: "Frio" },
  }

  const variant = temperature ? variants[temperature] : null

  if (!variant) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        —
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className={variant.className}>
      {variant.label}
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

export default function LeadsPage() {
  const router = useRouter()
  const [searchInput, setSearchInput] = useState("")
  const [temperature, setTemperature] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState("updated_at")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const limit = 20

  const debouncedSearch = useDebounce(searchInput, 300)

  const params: LeadsListParams = useMemo(() => ({
    temperature: temperature !== "all" ? temperature as "frio" | "morno" | "quente" : undefined,
    search: debouncedSearch || undefined,
    page,
    limit,
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [temperature, debouncedSearch, page, sortBy, sortOrder])

  const { data, isLoading, isError, error } = useLeads(params)

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(field)
      setSortOrder("desc")
    }
    setPage(1)
  }

  const handleRowClick = (lead: Lead) => {
    router.push(`/leads/${encodeURIComponent(lead.phone)}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Leads</h1>
        <p className="text-muted-foreground">
          Visualize e gerencie os leads qualificados pelo agente
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por nome, telefone ou cidade..."
            className="pl-9"
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value)
              setPage(1)
            }}
          />
        </div>
        <Select
          value={temperature}
          onValueChange={(value) => {
            setTemperature(value)
            setPage(1)
          }}
        >
          <SelectTrigger className="w-[180px]">
            <Thermometer className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Temperatura" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="quente">🔥 Quente</SelectItem>
            <SelectItem value="morno">🌡️ Morno</SelectItem>
            <SelectItem value="frio">❄️ Frio</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Error State */}
      {isError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Erro ao carregar leads</p>
                <p className="text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Verifique a conexão com o backend"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      {data && (
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            {data.total} lead{data.total !== 1 ? "s" : ""} encontrado{data.total !== 1 ? "s" : ""}
          </span>
          {debouncedSearch && (
            <Badge variant="secondary" className="gap-1">
              Busca: {debouncedSearch}
            </Badge>
          )}
          {temperature !== "all" && (
            <TemperatureBadge temperature={temperature} />
          )}
        </div>
      )}

      {/* Table */}
      <Card>
        <CardHeader className="pb-0">
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Lista de Leads
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">
                    <Button
                      variant="ghost"
                      className="h-8 p-0 font-medium hover:bg-transparent"
                      onClick={() => handleSort("name")}
                    >
                      Nome
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      className="h-8 p-0 font-medium hover:bg-transparent"
                      onClick={() => handleSort("phone")}
                    >
                      Telefone
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Cidade</TableHead>
                  <TableHead>Produto</TableHead>
                  <TableHead className="text-center">
                    <Button
                      variant="ghost"
                      className="h-8 p-0 font-medium hover:bg-transparent"
                      onClick={() => handleSort("temperature")}
                    >
                      Temperatura
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="text-right">
                    <Button
                      variant="ghost"
                      className="h-8 p-0 font-medium hover:bg-transparent"
                      onClick={() => handleSort("updated_at")}
                    >
                      Última Interação
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  // Loading skeletons
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-36" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell className="text-center"><Skeleton className="h-6 w-16 mx-auto" /></TableCell>
                      <TableCell className="text-right"><Skeleton className="h-4 w-28 ml-auto" /></TableCell>
                    </TableRow>
                  ))
                ) : data?.items && data.items.length > 0 ? (
                  data.items.map((lead) => (
                    <TableRow
                      key={lead.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleRowClick(lead)}
                    >
                      <TableCell className="font-medium">
                        {lead.name || <span className="text-muted-foreground">Sem nome</span>}
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-sm flex items-center gap-1">
                          <Phone className="h-3 w-3 text-muted-foreground" />
                          {formatPhone(lead.phone)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {lead.city ? (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            {lead.city}{lead.uf ? `, ${lead.uf}` : ""}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {lead.product || <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell className="text-center">
                        <TemperatureBadge temperature={lead.temperature} />
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {formatDate(lead.updated_at)}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <Users className="h-8 w-8" />
                        <p>Nenhum lead encontrado</p>
                        {(debouncedSearch || temperature !== "all") && (
                          <Button
                            variant="link"
                            className="text-sm"
                            onClick={() => {
                              setSearchInput("")
                              setTemperature("all")
                            }}
                          >
                            Limpar filtros
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {data && totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Página {page} de {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Próxima
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
