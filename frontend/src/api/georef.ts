import { http } from './http'
import type { ControlPoint } from './controlPoints'
import type { ApiResponse } from '@/types/api'

export type GeorefRunResult = {
  project_id: string
  transform_matrix: number[][]
  transform_type: string
  target_crs: string
  rms: number
  rms_meters: number | null
  preview_available: boolean
  control_points: ControlPoint[]
}

export type RmsResult = {
  project_id: string
  rms: number | null
  rms_meters: number | null
  transform_type: string | null
  target_crs: string | null
  enabled_control_point_count: number
  minimum_required_count: number
  control_points: ControlPoint[]
}

export type GeorefPreviewResult = {
  project_id: string
  image_id: string
  image_url: string
  coordinates: [[number, number], [number, number], [number, number], [number, number]]
  opacity: number
}

export type TransformOption = {
  value: string
  label: string
  minimum_control_points: number
}

export async function runGeoref(projectId: string, transformType = 'auto', targetCrs = 'EPSG:3857') {
  const response = await http.post<ApiResponse<GeorefRunResult>>('/georef/run', {
    project_id: projectId,
    transform_type: transformType,
    target_crs: targetCrs,
  })
  return response.data
}

export async function getRms(projectId: string) {
  const response = await http.get<ApiResponse<RmsResult>>('/georef/rms', {
    params: { project_id: projectId },
  })
  return response.data
}

export async function getGeorefPreview(projectId: string) {
  const response = await http.get<ApiResponse<GeorefPreviewResult>>('/georef/preview', {
    params: { project_id: projectId },
  })
  return response.data
}

export async function listTransformOptions() {
  const response = await http.get<ApiResponse<TransformOption[]>>('/georef/transform-options')
  return response.data
}
