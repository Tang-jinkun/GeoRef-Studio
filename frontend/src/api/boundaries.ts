import { http } from './http'
import type { ApiResponse } from '@/types/api'

export type BoundaryDataset = {
  id: string
  file_name: string
  size_bytes: number
}

export type BoundaryGeoJson = GeoJSON.FeatureCollection

export async function listBoundaryDatasets() {
  const response = await http.get<ApiResponse<BoundaryDataset[]>>('/boundary/list')
  return response.data
}

export async function getBoundaryGeoJson(datasetId: string) {
  const response = await http.get<BoundaryGeoJson>(`/boundary/${datasetId}/geojson`)
  return response.data
}
