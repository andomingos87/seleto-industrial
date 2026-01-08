"use client"

import { useQuery } from "@tanstack/react-query"
import { api, SystemStatusResponse } from "@/lib/api"

/**
 * Hook to fetch system status with auto-refresh
 */
export function useSystemStatus(refetchInterval = 30000) {
  return useQuery<SystemStatusResponse>({
    queryKey: ["system-status"],
    queryFn: () => api.get<SystemStatusResponse>("/api/admin/status"),
    refetchInterval,
    retry: 1,
  })
}
