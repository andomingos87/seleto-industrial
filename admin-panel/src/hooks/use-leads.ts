"use client"

import { useQuery } from "@tanstack/react-query"
import { api, Lead, LeadsListResponse, LeadsListParams, ConversationResponse } from "@/lib/api"

/**
 * Hook to fetch leads list with pagination and filters
 */
export function useLeads(params: LeadsListParams = {}) {
  const queryParams = new URLSearchParams()
  
  if (params.temperature) queryParams.set("temperature", params.temperature)
  if (params.search) queryParams.set("search", params.search)
  if (params.page) queryParams.set("page", params.page.toString())
  if (params.limit) queryParams.set("limit", params.limit.toString())
  if (params.sort_by) queryParams.set("sort_by", params.sort_by)
  if (params.sort_order) queryParams.set("sort_order", params.sort_order)

  const queryString = queryParams.toString()
  const endpoint = `/api/admin/leads${queryString ? `?${queryString}` : ""}`

  return useQuery<LeadsListResponse>({
    queryKey: ["leads", params],
    queryFn: () => api.get<LeadsListResponse>(endpoint),
  })
}

/**
 * Hook to fetch a single lead by phone
 */
export function useLead(phone: string) {
  return useQuery<Lead>({
    queryKey: ["lead", phone],
    queryFn: () => api.get<Lead>(`/api/admin/leads/${encodeURIComponent(phone)}`),
    enabled: !!phone,
  })
}

/**
 * Hook to fetch conversation history for a lead
 */
export function useLeadConversation(phone: string) {
  return useQuery<ConversationResponse>({
    queryKey: ["lead-conversation", phone],
    queryFn: () => api.get<ConversationResponse>(`/api/admin/leads/${encodeURIComponent(phone)}/conversation`),
    enabled: !!phone,
  })
}
