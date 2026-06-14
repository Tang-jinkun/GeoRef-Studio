import { http } from './http'
import type { ApiResponse } from '@/types/api'

export type ImageFile = {
  id: string
  original_name: string
  storage_path: string
  width: number
  height: number
  size_bytes: number
  format: string
  upload_time: string
}

export async function uploadImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await http.post<ApiResponse<ImageFile>>('/image/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

