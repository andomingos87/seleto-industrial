"use client"

import { useState } from "react"
import { Package, Plus, Search, Pencil, Trash2, Check, X, MessageSquareWarning } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useProducts,
  useDeleteProduct,
  useToggleProductAvailability,
  useTechnicalQuestions,
} from "@/hooks"
import { useDebounce } from "@/hooks/use-debounce"
import type { ProductCategory } from "@/lib/api/types"
import { ProductDialog } from "./product-dialog"

const CATEGORY_LABELS: Record<ProductCategory, string> = {
  formadora: "Formadora",
  cortadora: "Cortadora",
  ensacadeira: "Ensacadeira",
  misturador: "Misturador",
  linha_automatica: "Linha Automática",
}

const CATEGORY_COLORS: Record<ProductCategory, string> = {
  formadora: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  cortadora: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  ensacadeira: "bg-green-500/10 text-green-500 border-green-500/20",
  misturador: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  linha_automatica: "bg-pink-500/10 text-pink-500 border-pink-500/20",
}

export default function ProductsPage() {
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState<ProductCategory | "all">("all")
  const [page, setPage] = useState(1)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const debouncedSearch = useDebounce(search, 300)

  const { data, isLoading, error } = useProducts({
    search: debouncedSearch || undefined,
    category: category === "all" ? undefined : category,
    page,
    limit: 20,
  })

  const { data: questionsData } = useTechnicalQuestions({ answered: false, limit: 1 })
  const pendingQuestionsCount = questionsData?.total || 0

  const deleteProduct = useDeleteProduct()
  const toggleAvailability = useToggleProductAvailability()

  const handleDelete = async () => {
    if (!deleteId) return
    await deleteProduct.mutateAsync(deleteId)
    setDeleteId(null)
  }

  const handleToggleAvailability = async (id: string, currentValue: boolean) => {
    await toggleAvailability.mutateAsync({ id, is_available: !currentValue })
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Produtos</h1>
          <p className="text-muted-foreground">Gerencie os produtos do catálogo</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">Erro ao carregar produtos. Verifique a conexão com o backend.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Produtos</h1>
          <p className="text-muted-foreground">Gerencie os produtos do catálogo</p>
        </div>
        <div className="flex gap-2">
          <Link href="/products/questions">
            <Button variant="outline" className="relative">
              <MessageSquareWarning className="mr-2 h-4 w-4" />
              Perguntas Técnicas
              {pendingQuestionsCount > 0 && (
                <Badge 
                  variant="destructive" 
                  className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs"
                >
                  {pendingQuestionsCount}
                </Badge>
              )}
            </Button>
          </Link>
          <Button onClick={() => { setEditingProduct(null); setDialogOpen(true) }}>
            <Plus className="mr-2 h-4 w-4" />
            Novo Produto
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                className="pl-9"
              />
            </div>
            <Select
              value={category}
              onValueChange={(value) => { setCategory(value as ProductCategory | "all"); setPage(1) }}
            >
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue placeholder="Categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as categorias</SelectItem>
                {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Produtos Cadastrados
            {data && (
              <Badge variant="secondary" className="ml-2">
                {data.total} {data.total === 1 ? "produto" : "produtos"}
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
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                  <Skeleton className="h-8 w-20" />
                </div>
              ))}
            </div>
          ) : data?.items.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {search || category !== "all" 
                ? "Nenhum produto encontrado com os filtros aplicados"
                : "Nenhum produto cadastrado"}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead className="hidden md:table-cell">Produtividade</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{product.name}</p>
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {product.description}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={CATEGORY_COLORS[product.category]}
                        >
                          {CATEGORY_LABELS[product.category]}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        {product.productivity || "-"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={product.is_available}
                            onCheckedChange={() => handleToggleAvailability(product.id, product.is_available)}
                          />
                          <span className="text-sm">
                            {product.is_available ? (
                              <span className="text-green-600 flex items-center gap-1">
                                <Check className="h-3 w-3" /> Disponível
                              </span>
                            ) : (
                              <span className="text-muted-foreground flex items-center gap-1">
                                <X className="h-3 w-3" /> Indisponível
                              </span>
                            )}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => { setEditingProduct(product.id); setDialogOpen(true) }}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setDeleteId(product.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
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

      {/* Product Dialog */}
      <ProductDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        productId={editingProduct}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir produto?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O produto será permanentemente removido do catálogo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
