"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-status"] })
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-status"] })
    },
  })
}

/**
 * Hook to reload system prompt
 */
export function useReloadPrompt() {
  return useMutation<ReloadPromptResponse, Error, void>({
    mutationFn: () => api.post<ReloadPromptResponse>("/api/admin/agent/reload-prompt"),
  })
}
