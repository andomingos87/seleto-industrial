"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { useProduct, useCreateProduct, useUpdateProduct } from "@/hooks"
import type { ProductCategory, ProductCreateRequest, ProductUpdateRequest } from "@/lib/api/types"

const CATEGORY_OPTIONS: { value: ProductCategory; label: string }[] = [
  { value: "formadora", label: "Formadora" },
  { value: "cortadora", label: "Cortadora" },
  { value: "ensacadeira", label: "Ensacadeira" },
  { value: "misturador", label: "Misturador" },
  { value: "linha_automatica", label: "Linha Automática" },
]

interface ProductDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  productId: string | null
}

export function ProductDialog({ open, onOpenChange, productId }: ProductDialogProps) {
  const isEditing = !!productId
  const { data: product, isLoading: loadingProduct } = useProduct(productId || "")
  
  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()

  const [formData, setFormData] = useState<{
    name: string
    category: ProductCategory
    description: string
    specifications: string
    productivity: string
    is_available: boolean
  }>({
    name: "",
    category: "formadora",
    description: "",
    specifications: "",
    productivity: "",
    is_available: true,
  })

  // Reset form when dialog opens/closes or product changes
  useEffect(() => {
    if (open && product && isEditing) {
      setFormData({
        name: product.name,
        category: product.category,
        description: product.description,
        specifications: product.specifications.join("\n"),
        productivity: product.productivity || "",
        is_available: product.is_available,
      })
    } else if (open && !isEditing) {
      setFormData({
        name: "",
        category: "formadora",
        description: "",
        specifications: "",
        productivity: "",
        is_available: true,
      })
    }
  }, [open, product, isEditing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      toast.error("Nome é obrigatório")
      return
    }

    const specifications = formData.specifications
      .split("\n")
      .map(s => s.trim())
      .filter(s => s.length > 0)

    try {
      if (isEditing && productId) {
        const updateData: ProductUpdateRequest = {
          name: formData.name,
          category: formData.category,
          description: formData.description,
          specifications,
          productivity: formData.productivity || undefined,
          is_available: formData.is_available,
        }
        await updateProduct.mutateAsync({ id: productId, data: updateData })
        toast.success("Produto atualizado com sucesso")
      } else {
        const createData: ProductCreateRequest = {
          name: formData.name,
          category: formData.category,
          description: formData.description,
          specifications,
          productivity: formData.productivity || undefined,
          is_available: formData.is_available,
        }
        await createProduct.mutateAsync(createData)
        toast.success("Produto criado com sucesso")
      }
      onOpenChange(false)
    } catch {
      toast.error(isEditing ? "Erro ao atualizar produto" : "Erro ao criar produto")
    }
  }

  const isSubmitting = createProduct.isPending || updateProduct.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Editar Produto" : "Novo Produto"}
          </DialogTitle>
          <DialogDescription>
            {isEditing 
              ? "Atualize as informações do produto"
              : "Preencha as informações do novo produto"}
          </DialogDescription>
        </DialogHeader>

        {loadingProduct && isEditing ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Nome *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ex: Formadora Automática FB700"
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="category">Categoria *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, category: value as ProductCategory }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione uma categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORY_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Descrição do produto..."
                  rows={3}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="specifications">Especificações (uma por linha)</Label>
                <Textarea
                  id="specifications"
                  value={formData.specifications}
                  onChange={(e) => setFormData(prev => ({ ...prev, specifications: e.target.value }))}
                  placeholder="Reservatório de 10kg&#10;Totalmente automática&#10;Painel digital"
                  rows={4}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="productivity">Produtividade</Label>
                <Input
                  id="productivity"
                  value={formData.productivity}
                  onChange={(e) => setFormData(prev => ({ ...prev, productivity: e.target.value }))}
                  placeholder="Ex: 700 hambúrgueres/hora"
                />
              </div>

              <div className="flex items-center gap-2">
                <Switch
                  id="is_available"
                  checked={formData.is_available}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_available: checked }))}
                />
                <Label htmlFor="is_available">Produto disponível</Label>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isEditing ? "Salvar" : "Criar"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
