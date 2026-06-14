import { http } from './http'

export type HealthPayload = {
  service: string
  environment: string
  status: string
}

export type ApiResponse<T> = {
  code: number
  message: string
  data: T
}

export async function getHealth() {
  const response = await http.get<ApiResponse<HealthPayload>>('/health')
  return response.data
}

