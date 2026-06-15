import { http } from './http'
import type { ApiResponse } from '@/types/api'

export type ControlPoint = {
  id: string
  project_id: string
  pixel_x: number
  pixel_y: number
  longitude: number
  latitude: number
  residual: number | null
  delta_x: number | null
  delta_y: number | null
  predicted_longitude: number | null
  predicted_latitude: number | null
  delta_x_meters: number | null
  delta_y_meters: number | null
  residual_meters: number | null
  role: 'fit' | 'check'
  enabled: boolean
  create_time: string
  update_time: string
}

export type ControlPointCreatePayload = {
  project_id: string
  pixel_x: number
  pixel_y: number
  longitude: number
  latitude: number
  role?: 'fit' | 'check'
  enabled?: boolean
}

export type ControlPointUpdatePayload = Partial<
  Pick<ControlPoint, 'pixel_x' | 'pixel_y' | 'longitude' | 'latitude' | 'role' | 'enabled'>
>

export async function createControlPoint(payload: ControlPointCreatePayload) {
  const response = await http.post<ApiResponse<ControlPoint>>('/control-point/create', payload)
  return response.data
}

export async function listControlPoints(projectId: string) {
  const response = await http.get<ApiResponse<ControlPoint[]>>('/control-point/list', {
    params: { project_id: projectId },
  })
  return response.data
}

export async function updateControlPoint(id: string, payload: ControlPointUpdatePayload) {
  const response = await http.patch<ApiResponse<ControlPoint>>(`/control-point/${id}`, payload)
  return response.data
}

export async function deleteControlPoint(id: string) {
  const response = await http.delete<ApiResponse<{ deleted: boolean }>>(`/control-point/${id}`)
  return response.data
}
