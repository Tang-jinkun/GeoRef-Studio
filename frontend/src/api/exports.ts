import { http } from './http'
import type { ApiResponse } from '@/types/api'

export type ExportArtifact = {
  id: string
  project_id: string
  artifact_type: string
  file_name: string
  storage_path: string
  size_bytes: number
  status: string
  message: string | null
  create_time: string
}

export async function exportGeoTiff(projectId: string) {
  const response = await http.post<ApiResponse<ExportArtifact>>('/export/geotiff', {
    project_id: projectId,
  })
  return response.data
}

export async function listExportArtifacts(projectId: string) {
  const response = await http.get<ApiResponse<ExportArtifact[]>>('/export/list', {
    params: { project_id: projectId },
  })
  return response.data
}

export function artifactDownloadUrl(artifactId: string) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api'
  return `${baseUrl}/export/${artifactId}/download`
}
