"use client"

import { useState } from "react"
import { MessageSquareWarning, Check, ExternalLink, ChevronDown, ChevronUp } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Skeleton } from "@/components/ui/skeleton"
import { useTechnicalQuestions, useMarkQuestionAnswered } from "@/hooks"

function formatPhone(phone: string): string {
  // Format: 5511999999999 -> (11) 99999-9999
  const digits = phone.replace(/\D/g, "")
  if (digits.length === 13) {
    return `(${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9)}`
  }
  if (digits.length === 12) {
    return `(${digits.slice(2, 4)}) ${digits.slice(4, 8)}-${digits.slice(8)}`
  }
  return phone
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default function TechnicalQuestionsPage() {
  const [filter, setFilter] = useState<"all" | "pending" | "answered">("pending")
  const [page, setPage] = useState(1)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [answerText, setAnswerText] = useState<Record<string, string>>({})

  const { data, isLoading, error } = useTechnicalQuestions({
    answered: filter === "all" ? undefined : filter === "answered",
    page,
    limit: 20,
  })

  const markAnswered = useMarkQuestionAnswered()

  const handleMarkAnswered = async (id: string) => {
    await markAnswered.mutateAsync({
      id,
      data: { answer: answerText[id] || undefined },
    })
    setAnswerText(prev => ({ ...prev, [id]: "" }))
    setExpandedId(null)
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Perguntas Técnicas</h1>
          <p className="text-muted-foreground">Gerencie perguntas técnicas dos leads</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">Erro ao carregar perguntas. Verifique a conexão com o backend.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Perguntas Técnicas</h1>
          <p className="text-muted-foreground">
            Perguntas que requerem resposta de um especialista
          </p>
        </div>
        <Link href="/products">
          <Button variant="outline">
            Voltar para Produtos
          </Button>
        </Link>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Filtrar por:</span>
            <Select
              value={filter}
              onValueChange={(value) => { setFilter(value as typeof filter); setPage(1) }}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pending">Pendentes</SelectItem>
                <SelectItem value="answered">Respondidas</SelectItem>
                <SelectItem value="all">Todas</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Questions Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquareWarning className="h-5 w-5" />
            Fila de Perguntas
            {data && (
              <Badge variant="secondary" className="ml-2">
                {data.total} {data.total === 1 ? "pergunta" : "perguntas"}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-64" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-8 w-24" />
                </div>
              ))}
            </div>
          ) : data?.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-in">
              <div className="rounded-full bg-muted p-4 mb-4">
                <MessageSquareWarning className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {filter === "pending" 
                  ? "Nenhuma pergunta pendente"
                  : filter === "answered"
                  ? "Nenhuma pergunta respondida"
                  : "Nenhuma pergunta registrada"}
              </h3>
              <p className="text-muted-foreground max-w-md">
                {filter === "pending" 
                  ? "Ótimo! Todas as perguntas técnicas foram respondidas."
                  : filter === "answered"
                  ? "Nenhuma pergunta foi marcada como respondida ainda."
                  : "Perguntas técnicas dos leads aparecerão aqui quando o agente não souber responder."}
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[150px]">Telefone</TableHead>
                    <TableHead>Pergunta</TableHead>
                    <TableHead className="w-[150px]">Data</TableHead>
                    <TableHead className="w-[120px]">Status</TableHead>
                    <TableHead className="w-[100px] text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((question) => (
                    <Collapsible
                      key={question.id}
                      open={expandedId === question.id}
                      onOpenChange={(open) => setExpandedId(open ? question.id : null)}
                      asChild
                    >
                      <>
                        <TableRow className="group">
                          <TableCell>
                            <Link
                              href={`/leads/${question.phone}`}
                              className="text-primary hover:underline flex items-center gap-1"
                            >
                              {formatPhone(question.phone)}
                              <ExternalLink className="h-3 w-3" />
                            </Link>
                          </TableCell>
                          <TableCell>
                            <p className="line-clamp-2">{question.question}</p>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {formatDate(question.timestamp)}
                          </TableCell>
                          <TableCell>
                            {question.answered ? (
                              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                                <Check className="h-3 w-3 mr-1" />
                                Respondida
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
                                Pendente
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <CollapsibleTrigger asChild>
                              <Button variant="ghost" size="sm">
                                {expandedId === question.id ? (
                                  <ChevronUp className="h-4 w-4" />
                                ) : (
                                  <ChevronDown className="h-4 w-4" />
                                )}
                              </Button>
                            </CollapsibleTrigger>
                          </TableCell>
                        </TableRow>
                        <CollapsibleContent asChild>
                          <tr>
                            <td colSpan={5} className="p-0">
                              <div className="bg-muted/50 p-4 border-t">
                                {question.context && (
                                  <div className="mb-4">
                                    <p className="text-sm font-medium mb-1">Contexto:</p>
                                    <p className="text-sm text-muted-foreground bg-background p-3 rounded-md">
                                      {question.context}
                                    </p>
                                  </div>
                                )}
                                
                                <div className="mb-4">
                                  <p className="text-sm font-medium mb-1">Pergunta completa:</p>
                                  <p className="text-sm bg-background p-3 rounded-md">
                                    {question.question}
                                  </p>
                                </div>

                                {question.answered && question.answer && (
                                  <div className="mb-4">
                                    <p className="text-sm font-medium mb-1">Resposta:</p>
                                    <p className="text-sm text-muted-foreground bg-background p-3 rounded-md">
                                      {question.answer}
                                    </p>
                                    {question.answered_at && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        Respondida em {formatDate(question.answered_at)}
                                      </p>
                                    )}
                                  </div>
                                )}

                                {!question.answered && (
                                  <div className="space-y-3">
                                    <div>
                                      <p className="text-sm font-medium mb-1">Resposta (opcional):</p>
                                      <Textarea
                                        placeholder="Digite uma resposta para registro..."
                                        value={answerText[question.id] || ""}
                                        onChange={(e) => setAnswerText(prev => ({ ...prev, [question.id]: e.target.value }))}
                                        rows={3}
                                      />
                                    </div>
                                    <div className="flex justify-end gap-2">
                                      <Link href={`/leads/${question.phone}`}>
                                        <Button variant="outline" size="sm">
                                          Ver Conversa
                                        </Button>
                                      </Link>
                                      <Button
                                        size="sm"
                                        onClick={() => handleMarkAnswered(question.id)}
                                        disabled={markAnswered.isPending}
                                      >
                                        <Check className="h-4 w-4 mr-1" />
                                        Marcar como Respondida
                                      </Button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        </CollapsibleContent>
                      </>
                    </Collapsible>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Página {page} de {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Próxima
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
