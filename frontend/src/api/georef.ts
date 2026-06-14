import { http } from './http'
import type { ControlPoint } from './controlPoints'
import type { ApiResponse } from '@/types/api'

export type GeorefRunResult = {
  project_id: string
  transform_matrix: number[][]
  rms: number
  control_points: ControlPoint[]
}

export type RmsResult = {
  project_id: string
  rms: number | null
  enabled_control_point_count: number
  minimum_required_count: number
  control_points: ControlPoint[]
}

export async function runGeoref(projectId: string) {
  const response = await http.post<ApiResponse<GeorefRunResult>>('/georef/run', {
    project_id: projectId,
  })
  return response.data
}

export async function getRms(projectId: string) {
  const response = await http.get<ApiResponse<RmsResult>>('/georef/rms', {
    params: { project_id: projectId },
  })
  return response.data
}
