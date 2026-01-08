/**
 * Hooks for Knowledge Base management
 * 
 * Products CRUD and Technical Questions queue
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { api } from "@/lib/api"
import type {
  Product,
  ProductsListResponse,
  ProductsListParams,
  ProductCreateRequest,
  ProductUpdateRequest,
  TechnicalQuestion,
  TechnicalQuestionsListResponse,
  TechnicalQuestionsListParams,
  MarkAnsweredRequest,
} from "@/lib/api/types"

// --- Products Hooks ---

export function useProducts(params: ProductsListParams = {}) {
  const queryParams = new URLSearchParams()
  
  if (params.category) queryParams.set("category", params.category)
  if (params.search) queryParams.set("search", params.search)
  if (params.is_available !== undefined) queryParams.set("is_available", String(params.is_available))
  if (params.page) queryParams.set("page", String(params.page))
  if (params.limit) queryParams.set("limit", String(params.limit))

  const queryString = queryParams.toString()
  const endpoint = `/api/admin/knowledge/products${queryString ? `?${queryString}` : ""}`

  return useQuery<ProductsListResponse>({
    queryKey: ["products", params],
    queryFn: () => api.get<ProductsListResponse>(endpoint),
    staleTime: 30000, // 30 seconds
  })
}

export function useProduct(id: string) {
  return useQuery<Product>({
    queryKey: ["product", id],
    queryFn: () => api.get<Product>(`/api/admin/knowledge/products/${id}`),
    enabled: !!id,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProductCreateRequest) =>
      api.post<Product>("/api/admin/knowledge/products", data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      toast.success("Produto criado com sucesso", {
        description: data.name
      })
    },
    onError: (error: Error) => {
      toast.error("Erro ao criar produto", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductUpdateRequest }) =>
      api.put<Product>(`/api/admin/knowledge/products/${id}`, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      queryClient.invalidateQueries({ queryKey: ["product", variables.id] })
      toast.success("Produto atualizado com sucesso", {
        description: data.name
      })
    },
    onError: (error: Error) => {
      toast.error("Erro ao atualizar produto", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) =>
      api.delete<{ success: boolean; message: string }>(`/api/admin/knowledge/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      toast.success("Produto excluído com sucesso")
    },
    onError: (error: Error) => {
      toast.error("Erro ao excluir produto", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

export function useToggleProductAvailability() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, is_available }: { id: string; is_available: boolean }) =>
      api.put<Product>(`/api/admin/knowledge/products/${id}`, { is_available }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      queryClient.invalidateQueries({ queryKey: ["product", variables.id] })
      toast.success(
        variables.is_available 
          ? "Produto marcado como disponível" 
          : "Produto marcado como indisponível",
        { description: data.name }
      )
    },
    onError: (error: Error) => {
      toast.error("Erro ao atualizar disponibilidade", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

// --- Technical Questions Hooks ---

export function useTechnicalQuestions(params: TechnicalQuestionsListParams = {}) {
  const queryParams = new URLSearchParams()
  
  if (params.answered !== undefined) queryParams.set("answered", String(params.answered))
  if (params.page) queryParams.set("page", String(params.page))
  if (params.limit) queryParams.set("limit", String(params.limit))

  const queryString = queryParams.toString()
  const endpoint = `/api/admin/knowledge/questions${queryString ? `?${queryString}` : ""}`

  return useQuery<TechnicalQuestionsListResponse>({
    queryKey: ["technical-questions", params],
    queryFn: () => api.get<TechnicalQuestionsListResponse>(endpoint),
    staleTime: 30000, // 30 seconds
  })
}

export function useMarkQuestionAnswered() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MarkAnsweredRequest }) =>
      api.put<TechnicalQuestion>(`/api/admin/knowledge/questions/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["technical-questions"] })
      toast.success("Pergunta marcada como respondida")
    },
    onError: (error: Error) => {
      toast.error("Erro ao marcar pergunta", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}
