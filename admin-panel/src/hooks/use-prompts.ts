/**
 * Hooks for Prompts management
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { api } from "@/lib/api"
import type {
  Prompt,
  PromptListResponse,
  PromptSaveRequest,
  PromptBackupsListResponse,
  RestoreBackupRequest,
  ReloadPromptResponse,
} from "@/lib/api/types"

export function usePromptsList() {
  return useQuery<PromptListResponse>({
    queryKey: ["prompts-list"],
    queryFn: () => api.get<PromptListResponse>("/api/admin/config/prompts"),
    staleTime: 60000, // 1 minute
  })
}

export function usePrompt(name: string) {
  return useQuery<Prompt>({
    queryKey: ["prompt", name],
    queryFn: () => api.get<Prompt>(`/api/admin/config/prompts/${name}`),
    enabled: !!name,
    staleTime: 30000, // 30 seconds
  })
}

export function useSavePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: PromptSaveRequest }) =>
      api.put<{ success: boolean; message: string; backup_path: string }>(
        `/api/admin/config/prompts/${name}`,
        data
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["prompt", variables.name] })
      queryClient.invalidateQueries({ queryKey: ["prompt-backups", variables.name] })
      toast.success("Prompt salvo com sucesso", {
        description: "Um backup foi criado automaticamente"
      })
    },
    onError: (error: Error) => {
      toast.error("Erro ao salvar prompt", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

export function usePromptBackups(name: string) {
  return useQuery<PromptBackupsListResponse>({
    queryKey: ["prompt-backups", name],
    queryFn: () => api.get<PromptBackupsListResponse>(`/api/admin/config/prompts/${name}/backups`),
    enabled: !!name,
    staleTime: 30000, // 30 seconds
  })
}

export function useRestoreBackup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: RestoreBackupRequest }) =>
      api.post<{ success: boolean; message: string }>(
        `/api/admin/config/prompts/${name}/restore`,
        data
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["prompt", variables.name] })
      queryClient.invalidateQueries({ queryKey: ["prompt-backups", variables.name] })
      toast.success("Backup restaurado com sucesso")
    },
    onError: (error: Error) => {
      toast.error("Erro ao restaurar backup", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}

export function useReloadAgent() {
  return useMutation({
    mutationFn: () =>
      api.post<ReloadPromptResponse>("/api/admin/agent/reload-prompt"),
    onSuccess: () => {
      toast.success("Agente recarregado com sucesso", {
        description: "O novo prompt está ativo"
      })
    },
    onError: (error: Error) => {
      toast.error("Erro ao recarregar agente", {
        description: error.message || "Tente novamente mais tarde"
      })
    },
  })
}
