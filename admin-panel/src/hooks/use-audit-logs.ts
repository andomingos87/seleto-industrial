/**
 * Hooks for Audit Logs
 */

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  AuditLog,
  AuditLogsListResponse,
  AuditLogsListParams,
} from "@/lib/api/types"

export function useAuditLogs(params: AuditLogsListParams = {}) {
  const queryParams = new URLSearchParams()
  
  if (params.action) queryParams.set("action", params.action)
  if (params.entity_type) queryParams.set("entity_type", params.entity_type)
  if (params.start_date) queryParams.set("start_date", params.start_date)
  if (params.end_date) queryParams.set("end_date", params.end_date)
  if (params.user_id) queryParams.set("user_id", params.user_id)
  if (params.page) queryParams.set("page", String(params.page))
  if (params.limit) queryParams.set("limit", String(params.limit))

  const queryString = queryParams.toString()
  const endpoint = `/api/admin/logs/audit${queryString ? `?${queryString}` : ""}`

  return useQuery<AuditLogsListResponse>({
    queryKey: ["audit-logs", params],
    queryFn: () => api.get<AuditLogsListResponse>(endpoint),
    staleTime: 30000, // 30 seconds
  })
}

export function useAuditLog(id: string) {
  return useQuery<AuditLog>({
    queryKey: ["audit-log", id],
    queryFn: () => api.get<AuditLog>(`/api/admin/logs/audit/${id}`),
    enabled: !!id,
  })
}
