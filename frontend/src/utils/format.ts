export function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

export function formatDate(value: string | null | undefined) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export function formatNumber(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined) return '-'
  return value.toFixed(digits)
}

export function statusBadgeClass(status: string) {
  if (status === '已导出') return 'accent'
  if (status === '已配准') return 'ok'
  return 'neutral'
}
