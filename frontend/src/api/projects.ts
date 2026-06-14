import { http } from './http'
import type { ImageFile } from './images'
import type { ApiResponse } from '@/types/api'

export type Project = {
  id: string
  name: string
  description: string | null
  image_id: string
  image_path: string
  status: string
  transform_matrix: number[][] | null
  rms_error: number | null
  georef_time: string | null
  create_time: string
  update_time: string
  image: ImageFile | null
}

export type ProjectCreatePayload = {
  name: string
  description?: string
  image_id: string
}

export async function createProject(payload: ProjectCreatePayload) {
  const response = await http.post<ApiResponse<Project>>('/project/create', payload)
  return response.data
}

export async function listProjects() {
  const response = await http.get<ApiResponse<Project[]>>('/project/list')
  return response.data
}

export async function getProject(projectId: string) {
  const response = await http.get<ApiResponse<Project>>(`/project/${projectId}`)
  return response.data
}
