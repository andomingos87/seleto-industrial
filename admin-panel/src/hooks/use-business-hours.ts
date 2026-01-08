"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api, BusinessHoursResponse, BusinessHoursUpdateRequest } from "@/lib/api"

/**
 * Hook to fetch business hours configuration
 */
export function useBusinessHours() {
  return useQuery<BusinessHoursResponse>({
    queryKey: ["business-hours"],
    queryFn: () => api.get<BusinessHoursResponse>("/api/admin/config/business-hours"),
  })
}

/**
 * Hook to update business hours configuration
 */
export function useUpdateBusinessHours() {
  const queryClient = useQueryClient()

  return useMutation<BusinessHoursResponse, Error, BusinessHoursUpdateRequest>({
    mutationFn: (data) => api.put<BusinessHoursResponse>("/api/admin/config/business-hours", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["business-hours"] })
    },
  })
}
