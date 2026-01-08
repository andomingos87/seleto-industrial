"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { api, AgentStatusResponse, PauseResumeResponse, ReloadPromptResponse } from "@/lib/api"

/**
 * Hook to fetch agent status
 */
export function useAgentStatus() {
  return useQuery<AgentStatusResponse>({
    queryKey: ["agent-status"],
    queryFn: () => api.get<AgentStatusResponse>("/api/admin/agent/status"),
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

/**
 * Hook to pause agent for a specific phone or globally
 */
export function usePauseAgent() {
  const queryClient = useQueryClient()

  return useMutation<PauseResumeResponse, Error, { phone?: string }>({
    mutationFn: (data) => api.post<PauseResumeResponse>("/api/admin/agent/pause", data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["agent-status"] })
      toast.success(
        variables.phone 
          ? `Agente pausado para ${variables.phone}` 
          : "Agente pausado globalmente"
      )
    },
    onError: (error) => {
      toast.error("Erro ao pausar agente", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

/**
 * Hook to resume agent for a specific phone or globally
 */
export function useResumeAgent() {
  const queryClient = useQueryClient()

  return useMutation<PauseResumeResponse, Error, { phone?: string }>({
    mutationFn: (data) => api.post<PauseResumeResponse>("/api/admin/agent/resume", data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["agent-status"] })
      toast.success(
        variables.phone 
          ? `Agente retomado para ${variables.phone}` 
          : "Agente retomado globalmente"
      )
    },
    onError: (error) => {
      toast.error("Erro ao retomar agente", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

/**
 * Hook to reload system prompt
 */
export function useReloadPrompt() {
  return useMutation<ReloadPromptResponse, Error, void>({
    mutationFn: () => api.post<ReloadPromptResponse>("/api/admin/agent/reload-prompt"),
    onSuccess: () => {
      toast.success("Prompt recarregado com sucesso")
    },
    onError: (error) => {
      toast.error("Erro ao recarregar prompt", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}
